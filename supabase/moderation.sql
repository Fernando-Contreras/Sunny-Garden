-- Moderation cheatsheet for Sunny Garden. Run these by hand in the Supabase SQL editor.
-- A sunflower is hidden from everyone once 3 different devices report it (it is NOT deleted).
-- The owner still sees it in their own garden; hidden stays hidden even if they re-share it.

-- 1. What has been hidden or reported? (text included so you can judge it)
select id, entry_date, reports, hidden, question, answer
from public.sunny_shared
where hidden or reports > 0
order by reports desc, created_at desc;

-- 2. It was fine after all: bring it back and forget the reports.
--    update public.sunny_shared set hidden = false, reports = 0 where id = <ID>;
--    delete from public.sunny_reports where entry_id = <ID>;

-- 3. It really is bad: delete it for good (its reports go with it).
--    delete from public.sunny_shared where id = <ID>;

-- 4. Leftovers: sunflowers whose owner lost their key (cleared data, private window) cannot be
--    unshared by the owner. Only you can remove them, as in 3.
