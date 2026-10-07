-- Migration: per-device reports, and "visit another garden" never repeats a garden.
-- Run once in the Supabase SQL editor (after sunny_shared.sql). Safe to re-run.

-- One row per (sunflower, reporting device). A device can only count once per sunflower,
-- so nobody can hide someone else's sunflower by reporting it three times alone.
create table if not exists public.sunny_reports (
  entry_id      bigint not null references public.sunny_shared(id) on delete cascade,
  reporter_hash text   not null,
  created_at    timestamptz not null default now(),
  primary key (entry_id, reporter_hash)
);
alter table public.sunny_reports enable row level security;
revoke all on public.sunny_reports from anon, authenticated;

-- The old anonymous, uncounted report function must go, or it keeps bypassing the rule above.
drop function if exists public.report_entry(bigint);
drop function if exists public.random_garden(text);

create or replace function public.report_entry(p_key text, p_id bigint)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_key is null or char_length(p_key) < 32 then
    raise exception 'invalid key';
  end if;
  insert into sunny_reports (entry_id, reporter_hash)
  select p_id, sunny_hash(p_key)
  where exists (select 1 from sunny_shared where id = p_id)
  on conflict do nothing;
  -- Three different devices hide a sunflower for everyone.
  update sunny_shared s
     set reports = c.n, hidden = (c.n >= 3)
    from (select count(*)::int as n from sunny_reports where entry_id = p_id) c
   where s.id = p_id;
end;
$$;

-- One random garden: never the caller's own, never sunflowers the caller reported,
-- and never a garden that has any sunflower id listed in p_seen.
create or replace function public.random_garden(p_key text default null, p_seen bigint[] default '{}')
returns jsonb language sql security definer set search_path = public as $$
  with me as (
    select case when p_key is null then null else sunny_hash(p_key) end as h
  ),
  ok as (
    select s.* from sunny_shared s, me
    where not s.hidden
      and (me.h is null or s.owner_hash <> me.h)
      and (me.h is null or not exists (
            select 1 from sunny_reports r where r.entry_id = s.id and r.reporter_hash = me.h))
  ),
  pick as (
    select owner_hash from ok
    group by owner_hash
    having not (array_agg(id) && p_seen)
    order by random()
    limit 1
  )
  select coalesce(
    jsonb_agg(jsonb_build_object('id', o.id, 'date', o.entry_date, 'question', o.question, 'answer', o.answer)
              order by o.entry_date desc),
    '[]'::jsonb)
  from ok o join pick using (owner_hash);
$$;

revoke all on function public.report_entry(text, bigint) from public;
revoke all on function public.random_garden(text, bigint[]) from public;
grant execute on function public.report_entry(text, bigint) to anon, authenticated;
grant execute on function public.random_garden(text, bigint[]) to anon, authenticated;
