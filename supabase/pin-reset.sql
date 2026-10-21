-- SSVM Rota — Forgot PIN: volunteer requests, admin/Rota Lead approves (run AFTER member-admin.sql)
--
-- Paste this whole file into Supabase → SQL Editor → New query → Run.
--
-- What it does:
--   • On the sign-in screen a member enters their name/email and chooses a new PIN.
--     The new PIN is stored hashed as a request; their old PIN keeps working until then.
--   • Admins and Rota Leads see the request in Requests and Approve or Decline it.
--     Only an admin can approve a reset for an admin.
--   • Requests expire after 7 days.

begin;

create table if not exists public.rota_pin_requests (
  member_id  text primary key,
  pin_hash   text not null,
  created_at timestamptz not null default now()
);
alter table public.rota_pin_requests enable row level security;
revoke all on public.rota_pin_requests from anon, authenticated;

-- ── Volunteer asks for a new PIN (no sign-in needed) ───────────────────────
create or replace function public.rota_request_pin_reset(p_ident text, p_pin text)
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

  insert into rota_pin_requests (member_id, pin_hash)
  values (v_m->>'id', extensions.crypt(trim(p_pin), extensions.gen_salt('bf')))
  on conflict (member_id) do update set pin_hash = excluded.pin_hash, created_at = now();
  return jsonb_build_object('ok', true, 'name', v_m->>'name');
end $$;

-- ── Admin / Rota Lead: list waiting requests ───────────────────────────────
create or replace function public.rota_pin_requests(p_token uuid)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  s      public.rota_sessions := _rota_session(p_token);
  v_role text;
begin
  if s.token is null then return jsonb_build_object('error', 'session'); end if;
  if not s.is_admin then
    select m->>'role' into v_role from app_data, jsonb_array_elements(value) m
    where key = 'rota-members' and m->>'id' = s.member_id;
    if v_role is distinct from 'primary' then return jsonb_build_object('requests', '[]'::jsonb); end if;
  end if;

  delete from rota_pin_requests where created_at < now() - interval '7 days';
  return jsonb_build_object('requests', (
    select coalesce(jsonb_agg(jsonb_build_object('memberId', r.member_id, 'name', m->>'name', 'createdAt', r.created_at)
                              order by r.created_at), '[]'::jsonb)
    from rota_pin_requests r
    join app_data d on d.key = 'rota-members'
    cross join lateral jsonb_array_elements(d.value) m
    where m->>'id' = r.member_id
      and (s.is_admin or not coalesce(m->'isAdmin' = 'true'::jsonb, false))));
end $$;

-- ── Admin / Rota Lead: approve or decline ──────────────────────────────────
create or replace function public.rota_pin_request_decide(p_token uuid, p_member_id text, p_approve boolean)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  s        public.rota_sessions := _rota_session(p_token);
  v_role   text;
  v_target jsonb;
  v_hash   text;
begin
  if s.token is null then return jsonb_build_object('error', 'session'); end if;
  if not s.is_admin then
    select m->>'role' into v_role from app_data, jsonb_array_elements(value) m
    where key = 'rota-members' and m->>'id' = s.member_id;
    if v_role is distinct from 'primary' then
      return jsonb_build_object('error', 'Only an admin or Rota Lead can approve PIN resets');
    end if;
  end if;

  select m into v_target from app_data, jsonb_array_elements(value) m
  where key = 'rota-members' and m->>'id' = p_member_id;
  if not s.is_admin and coalesce(v_target->'isAdmin' = 'true'::jsonb, false) then
    return jsonb_build_object('error', 'Only an admin can approve a PIN reset for an admin');
  end if;

  delete from rota_pin_requests where member_id = p_member_id
    and created_at >= now() - interval '7 days'
  returning pin_hash into v_hash;
  if v_hash is null then return jsonb_build_object('error', 'This request has expired or was already handled'); end if;

  if p_approve then
    insert into rota_pins (member_id, pin_hash) values (p_member_id, v_hash)
    on conflict (member_id) do update set pin_hash = excluded.pin_hash;
    delete from rota_sessions where member_id = p_member_id;
  end if;
  return jsonb_build_object('ok', true);
end $$;

revoke execute on function
  public.rota_request_pin_reset(text, text), public.rota_pin_requests(uuid),
  public.rota_pin_request_decide(uuid, text, boolean)
  from public;
grant execute on function
  public.rota_request_pin_reset(text, text), public.rota_pin_requests(uuid),
  public.rota_pin_request_decide(uuid, text, boolean)
  to anon, authenticated;

commit;
