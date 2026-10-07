-- Sunny Garden: anonymous, opt-in sharing of individual sunflowers.
-- Run once in the Supabase SQL editor. Safe to re-run.
--
-- Design: the table has RLS on and NO policies, so the public (anon) key cannot
-- read or write it directly. Everything goes through the security-definer
-- functions below, which never return the owner's key, hash or any identity.

create table if not exists public.sunny_shared (
  id          bigint generated always as identity primary key,
  owner_hash  text    not null,                 -- sha256 of a per-device secret; never returned
  entry_date  date    not null,
  question    text    not null check (char_length(question) <= 400),
  answer      text    not null check (char_length(answer)   <= 5000),
  reports     int     not null default 0,
  hidden      boolean not null default false,   -- auto-set once reported enough times
  created_at  timestamptz not null default now(),
  unique (owner_hash, entry_date)
);

alter table public.sunny_shared enable row level security;
revoke all on public.sunny_shared from anon, authenticated;

create or replace function public.sunny_hash(p_key text) returns text
language sql immutable as $$
  select encode(sha256(convert_to(p_key, 'utf8')), 'hex');
$$;

-- Share (or re-share) one sunflower. Keeps report count / hidden flag on update.
create or replace function public.share_entry(p_key text, p_date date, p_question text, p_answer text)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_key is null or char_length(p_key) < 32 then
    raise exception 'invalid key';
  end if;
  insert into sunny_shared (owner_hash, entry_date, question, answer)
  values (sunny_hash(p_key), p_date, p_question, p_answer)
  on conflict (owner_hash, entry_date)
  do update set question = excluded.question, answer = excluded.answer;
end;
$$;

create or replace function public.unshare_entry(p_key text, p_date date)
returns void language sql security definer set search_path = public as $$
  delete from sunny_shared where owner_hash = sunny_hash(p_key) and entry_date = p_date;
$$;

create or replace function public.unshare_all(p_key text)
returns void language sql security definer set search_path = public as $$
  delete from sunny_shared where owner_hash = sunny_hash(p_key);
$$;

-- One random garden (all visible sunflowers of one random person), excluding the caller's own.
create or replace function public.random_garden(p_key text default null)
returns jsonb language sql security definer set search_path = public as $$
  with pick as (
    select owner_hash from sunny_shared
    where not hidden and (p_key is null or owner_hash <> sunny_hash(p_key))
    group by owner_hash
    order by random()
    limit 1
  )
  select coalesce(
    jsonb_agg(jsonb_build_object('id', s.id, 'date', s.entry_date, 'question', s.question, 'answer', s.answer)
              order by s.entry_date desc),
    '[]'::jsonb)
  from sunny_shared s join pick using (owner_hash)
  where not s.hidden;
$$;

-- Three reports hide a sunflower until the owner re-shares an edited one or you review it.
create or replace function public.report_entry(p_id bigint)
returns void language sql security definer set search_path = public as $$
  update sunny_shared set reports = reports + 1, hidden = (reports + 1 >= 3) where id = p_id;
$$;

revoke all on function public.share_entry(text, date, text, text) from public;
revoke all on function public.unshare_entry(text, date) from public;
revoke all on function public.unshare_all(text) from public;
revoke all on function public.random_garden(text) from public;
revoke all on function public.report_entry(bigint) from public;
revoke all on function public.sunny_hash(text) from public;

grant execute on function public.share_entry(text, date, text, text) to anon, authenticated;
grant execute on function public.unshare_entry(text, date) to anon, authenticated;
grant execute on function public.unshare_all(text) to anon, authenticated;
grant execute on function public.random_garden(text) to anon, authenticated;
grant execute on function public.report_entry(bigint) to anon, authenticated;
