-- SSVM Rota — Forgot PIN: members reset their own PIN (run AFTER member-admin.sql)
--
-- Paste this whole file into Supabase → SQL Editor → New query → Run.
--
-- What it does:
--   • On the sign-in screen an approved member enters their name/email and a new
--     PIN, and can sign in with it straight away. (New sign-ups still need approval.)
--   • Admin accounts can't be reset this way — use rota_set_member_pin (see the end).
--   • 5 resets per name per hour.
--   • Removes the earlier request/approve version if it was installed.

begin;

drop function if exists public.rota_request_pin_reset(text, text);
drop function if exists public.rota_pin_requests(uuid);
drop function if exists public.rota_pin_request_decide(uuid, text, boolean);
drop table if exists public.rota_pin_requests;

create or replace function public.rota_reset_pin(p_ident text, p_pin text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  v_q text := lower(trim(coalesce(p_ident, '')));
  v_m jsonb;
begin
  if v_q = '' then return jsonb_build_object('error', 'Please enter your name or email'); end if;
  if length(trim(coalesce(p_pin, ''))) < 4 then return jsonb_build_object('error', 'PIN must be at least 4 digits'); end if;
  if _rota_too_many('reset:' || v_q, 5, interval '1 hour') then
    return jsonb_build_object('error', 'Too many attempts. Please wait an hour and try again.');
  end if;
  perform _rota_note('reset:' || v_q);

  select m into v_m from app_data, jsonb_array_elements(value) m
  where key = 'rota-members' and (lower(m->>'email') = v_q or lower(m->>'name') = v_q)
  limit 1;
  if v_m is null then
    return jsonb_build_object('error', 'No account found. Please check your name/email or sign up.');
  end if;
  if v_m->>'approved' = 'rejected' then
    return jsonb_build_object('error', 'Your registration was declined. Please sign up again to re-apply.');
  end if;
  if v_m->'approved' = 'false'::jsonb then
    return jsonb_build_object('error', 'Your registration is still pending admin approval.');
  end if;
  if v_m->'isAdmin' = 'true'::jsonb then
    return jsonb_build_object('error', 'Admin PINs can''t be reset here. Please ask another admin.');
  end if;

  perform _rota_set_pin(v_m->>'id', p_pin);
  delete from rota_sessions where member_id = v_m->>'id';
  return jsonb_build_object('ok', true, 'name', v_m->>'name');
end $$;

-- Set any member's PIN, admins included — run from the SQL Editor only (not callable from the browser)
create or replace function public.rota_set_member_pin(p_ident text, p_pin text)
returns text language plpgsql security definer set search_path = public as $$
declare
  v_q text := lower(trim(coalesce(p_ident, '')));
  v_m jsonb;
begin
  if length(trim(coalesce(p_pin, ''))) < 4 then raise exception 'PIN must be at least 4 digits'; end if;
  select m into v_m from app_data, jsonb_array_elements(value) m
  where key = 'rota-members' and (lower(m->>'email') = v_q or lower(m->>'name') = v_q)
  limit 1;
  if v_m is null then raise exception 'No member found with name or email "%"', p_ident; end if;
  perform _rota_set_pin(v_m->>'id', p_pin);
  delete from rota_sessions where member_id = v_m->>'id';
  return 'PIN set for ' || (v_m->>'name');
end $$;

revoke execute on function public.rota_set_member_pin(text, text) from public, anon, authenticated;
revoke execute on function public.rota_reset_pin(text, text) from public;
grant  execute on function public.rota_reset_pin(text, text) to anon, authenticated;

commit;

-- ── If you forget your own admin PIN ───────────────────────────────────────
-- Open a NEW query, fill in the quotes, Run:
--
--   select rota_set_member_pin('Ramki', 'your-new-pin');
