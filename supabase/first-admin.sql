-- Rota — make a member the admin, approving them if needed (run AFTER member-admin.sql)
--
-- Paste this whole file into Supabase → SQL Editor → New query → Run.
--
-- Why: a new organisation starts empty. Its first person registers in the app,
-- which leaves them "pending approval" — but there is no admin yet to approve
-- them. rota_set_member_admin now also approves the member when it makes them
-- admin, so one line in the SQL Editor gets the first admin in.
-- Safe to run on an existing organisation: it only changes how that function works.

begin;

create or replace function public.rota_set_member_admin(p_ident text, p_on boolean default true)
returns text language plpgsql security definer set search_path = public as $$
declare
  v_q    text := lower(trim(coalesce(p_ident, '')));
  v_name text;
begin
  select m->>'name' into v_name from app_data, jsonb_array_elements(value) m
  where key = 'rota-members' and (lower(m->>'email') = v_q or lower(m->>'name') = v_q)
  limit 1;
  if v_name is null then raise exception 'No member found with name or email "%"', p_ident; end if;

  update app_data
  set value = (select jsonb_agg(
                 case when lower(m->>'email') = v_q or lower(m->>'name') = v_q
                      then (m - 'isAdmin')
                           || case when p_on then jsonb_build_object('isAdmin', true, 'approved', true) else '{}'::jsonb end
                      else m end order by i)
               from jsonb_array_elements(value) with ordinality as t(m, i))
  where key = 'rota-members';
  delete from rota_sessions;  -- everyone signs in again, so the change takes effect
  return case when p_on then v_name || ' is now an approved admin' else v_name || ' is no longer an admin' end;
end $$;

revoke execute on function public.rota_set_member_admin(text, boolean) from public, anon, authenticated;

commit;

-- ── Make someone admin ─────────────────────────────────────────────────────
-- Open a NEW query, put their name or email between the quotes, Run:
--
--   select rota_set_member_admin('their name or email');
--
-- To remove admin:  select rota_set_member_admin('their name or email', false);
