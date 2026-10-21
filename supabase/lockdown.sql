-- ═══════════════════════════════════════════════════════════════════════════
-- SSVM Rota — lock down app_data
-- Run ONCE in Supabase → SQL Editor → New query.
--
-- AFTER RUNNING: set the admin PIN in a separate query (see the end of this file).
--
-- What this does:
--   • Blocks all direct access to app_data with the public (anon) key
--   • Moves member PINs and the admin PIN into hashed, unreadable tables
--   • Adds server-side functions the app calls: public config, login,
--     admin login, register, load, save — with a session token per login
--   • Throttles repeated wrong PINs (5 tries / 15 min per name/email)
-- Safe to re-run: it only hashes PINs that are still in plain text.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

create extension if not exists pgcrypto with schema extensions;

-- ── Private tables ─────────────────────────────────────────────────────────
create table if not exists public.rota_pins (
  member_id text primary key,
  pin_hash  text not null
);
create table if not exists public.rota_admin (
  id       int primary key default 1 check (id = 1),
  pin_hash text not null
);
create table if not exists public.rota_sessions (
  token      uuid primary key default gen_random_uuid(),
  member_id  text,
  is_admin   boolean not null default false,
  expires_at timestamptz not null default now() + interval '12 hours'
);
create table if not exists public.rota_events (
  ident text not null,
  at    timestamptz not null default now()
);
create index if not exists rota_events_ident_at on public.rota_events (ident, at);

-- ── No direct table access from the browser ────────────────────────────────
do $$
declare p record;
begin
  for p in select policyname from pg_policies where schemaname = 'public' and tablename = 'app_data' loop
    execute format('drop policy %I on public.app_data', p.policyname);
  end loop;
end $$;

alter table public.app_data      enable row level security;
alter table public.rota_pins     enable row level security;
alter table public.rota_admin    enable row level security;
alter table public.rota_sessions enable row level security;
alter table public.rota_events   enable row level security;
revoke all on public.app_data, public.rota_pins, public.rota_admin,
              public.rota_sessions, public.rota_events from anon, authenticated;

-- ── Migrate PINs out of the JSON ───────────────────────────────────────────
insert into public.rota_pins (member_id, pin_hash)
select m->>'id', extensions.crypt(trim(m->>'pin'), extensions.gen_salt('bf'))
from public.app_data, jsonb_array_elements(value) m
where key = 'rota-members' and coalesce(trim(m->>'pin'), '') <> ''
on conflict (member_id) do update set pin_hash = excluded.pin_hash;

update public.app_data
set value = (select coalesce(jsonb_agg(m - 'pin' order by i), '[]'::jsonb)
             from jsonb_array_elements(value) with ordinality as t(m, i))
where key = 'rota-members';

update public.app_data set value = value - 'adminPin' where key = 'rota-config';
delete from public.app_data where key = 'rota-supabase-cfg';

-- ── Internal helpers (not callable from the browser) ──────────────────────
create or replace function public._rota_session(p_token uuid)
returns public.rota_sessions language sql stable security definer set search_path = public as $$
  select * from rota_sessions where token = p_token and expires_at > now();
$$;

create or replace function public._rota_too_many(p_ident text, p_max int, p_window interval)
returns boolean language sql stable security definer set search_path = public as $$
  select count(*) >= p_max from rota_events where ident = p_ident and at > now() - p_window;
$$;

create or replace function public._rota_note(p_ident text)
returns void language sql security definer set search_path = public as $$
  delete from rota_events where at < now() - interval '1 day';
  insert into rota_events (ident) values (p_ident);
$$;

create or replace function public._rota_set_pin(p_member_id text, p_pin text)
returns void language sql security definer set search_path = public as $$
  insert into rota_pins (member_id, pin_hash)
  values (p_member_id, extensions.crypt(trim(p_pin), extensions.gen_salt('bf')))
  on conflict (member_id) do update set pin_hash = excluded.pin_hash;
$$;

create or replace function public._rota_strip(p_key text, p_value jsonb)
returns jsonb language sql immutable as $$
  select case p_key
    when 'rota-config'  then p_value - 'adminPin'
    when 'rota-members' then (select coalesce(jsonb_agg(m - 'pin' order by i), '[]'::jsonb)
                              from jsonb_array_elements(p_value) with ordinality as t(m, i))
    else p_value end;
$$;

-- ── Public: org name/location for the sign-in screen ──────────────────────
create or replace function public.rota_public()
returns jsonb language sql stable security definer set search_path = public as $$
  select jsonb_build_object('rota-config',
    coalesce((select value - 'adminPin' from app_data where key = 'rota-config'), '{}'::jsonb));
$$;

-- ── Member sign-in ─────────────────────────────────────────────────────────
create or replace function public.rota_login(p_ident text, p_pin text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  v_q    text := lower(trim(coalesce(p_ident, '')));
  v_m    jsonb;
  v_hash text;
  v_tok  uuid;
begin
  if v_q = '' then return jsonb_build_object('error', 'Please enter your name or email'); end if;
  if coalesce(trim(p_pin), '') = '' then return jsonb_build_object('error', 'Please enter your PIN'); end if;
  if _rota_too_many('login:' || v_q, 5, interval '15 minutes') then
    return jsonb_build_object('error', 'Too many attempts. Please wait 15 minutes and try again.');
  end if;

  select m into v_m from app_data, jsonb_array_elements(value) m
  where key = 'rota-members' and (lower(m->>'email') = v_q or lower(m->>'name') = v_q)
  limit 1;

  if v_m is null then
    perform _rota_note('login:' || v_q);
    return jsonb_build_object('error', 'No account found. Please check your name/email or sign up.');
  end if;

  select pin_hash into v_hash from rota_pins where member_id = v_m->>'id';
  if v_hash is null then
    return jsonb_build_object('error', 'No PIN has been set for your account yet. Please ask the admin to set one.');
  end if;
  if v_hash <> extensions.crypt(trim(p_pin), v_hash) then
    perform _rota_note('login:' || v_q);
    return jsonb_build_object('error', 'Incorrect PIN. Please try again.');
  end if;

  if v_m->>'approved' = 'rejected' then
    return jsonb_build_object('error', 'Your registration was declined. Please sign up again to re-apply.');
  end if;
  if v_m->'approved' = 'false'::jsonb then
    return jsonb_build_object('error', 'Your registration is pending admin approval. You will be notified once approved.');
  end if;

  delete from rota_sessions where expires_at < now();
  insert into rota_sessions (member_id) values (v_m->>'id') returning token into v_tok;
  return jsonb_build_object('token', v_tok, 'member', jsonb_build_object(
    'id', v_m->>'id', 'name', v_m->>'name', 'email', v_m->>'email', 'role', v_m->>'role'));
end $$;

-- ── Admin sign-in ──────────────────────────────────────────────────────────
create or replace function public.rota_admin_login(p_pin text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  v_hash text;
  v_tok  uuid;
begin
  if _rota_too_many('admin', 10, interval '15 minutes') then
    return jsonb_build_object('error', 'Too many attempts. Please wait 15 minutes and try again.');
  end if;
  select pin_hash into v_hash from rota_admin where id = 1;
  if v_hash is null or v_hash <> extensions.crypt(coalesce(p_pin, ''), v_hash) then
    perform _rota_note('admin');
    return jsonb_build_object('error', 'Incorrect PIN. Please try again.');
  end if;
  delete from rota_sessions where expires_at < now();
  insert into rota_sessions (is_admin) values (true) returning token into v_tok;
  return jsonb_build_object('token', v_tok);
end $$;

-- ── Self-registration (creates a pending member) ───────────────────────────
create or replace function public.rota_register(p jsonb)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  v_name  text := trim(coalesce(p->>'name', ''));
  v_email text := lower(trim(coalesce(p->>'email', '')));
  v_pin   text := trim(coalesce(p->>'pin', ''));
  v_list  jsonb;
  v_old   jsonb;
  v_id    text;
begin
  if v_name = '' then return jsonb_build_object('error', 'Full name is required'); end if;
  if v_email !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then return jsonb_build_object('error', 'Please enter a valid email address'); end if;
  if length(v_pin) < 4 then return jsonb_build_object('error', 'PIN must be at least 4 digits'); end if;
  if _rota_too_many('register', 30, interval '1 hour') then
    return jsonb_build_object('error', 'Too many registrations right now. Please try again later.');
  end if;
  perform _rota_note('register');

  select value into v_list from app_data where key = 'rota-members' for update;
  v_list := coalesce(v_list, '[]'::jsonb);
  select m into v_old from jsonb_array_elements(v_list) m where lower(m->>'email') = v_email limit 1;

  if v_old is not null then
    if v_old->>'approved' is distinct from 'rejected' then
      return jsonb_build_object('error', 'An account with this email already exists. Please sign in instead.');
    end if;
    v_id := v_old->>'id';
    v_list := (select jsonb_agg(case when m->>'id' = v_id then m || jsonb_build_object(
                  'name', v_name, 'phone', trim(coalesce(p->>'phone', '')), 'area', trim(coalesce(p->>'area', '')),
                  'city', trim(coalesce(p->>'city', '')), 'approved', false, 'notes', 'Re-applied after rejection')
                else m end order by i)
               from jsonb_array_elements(v_list) with ordinality as t(m, i));
  else
    v_id := substr(md5(random()::text || clock_timestamp()::text), 1, 7);
    v_list := v_list || jsonb_build_array(jsonb_build_object(
      'id', v_id, 'name', v_name, 'email', v_email,
      'phone', trim(coalesce(p->>'phone', '')), 'area', trim(coalesce(p->>'area', '')),
      'city', trim(coalesce(p->>'city', '')), 'role', 'volunteer', 'approved', false,
      'notes', 'Self sign-up — pending approval'));
  end if;

  insert into app_data (key, value) values ('rota-members', v_list)
  on conflict (key) do update set value = excluded.value;
  perform _rota_set_pin(v_id, v_pin);
  return jsonb_build_object('ok', true);
end $$;

-- ── Load everything (signed-in users only) ─────────────────────────────────
create or replace function public.rota_load(p_token uuid)
returns jsonb language plpgsql stable security definer set search_path = public as $$
begin
  if (_rota_session(p_token)).token is null then return jsonb_build_object('error', 'session'); end if;
  return jsonb_build_object('data', (
    select coalesce(jsonb_object_agg(key, _rota_strip(key, value)), '{}'::jsonb)
    from app_data where key like 'rota-%' and key <> 'rota-supabase-cfg'));
end $$;

-- ── Save one data set (signed-in users only) ───────────────────────────────
-- Admin: anything. Rota Leads: anything except settings.
-- Other members: settings blocked; on the member list they can only edit
-- their own record and cannot change roles/approval or remove anyone.
create or replace function public.rota_save(p_token uuid, p_key text, p_value jsonb)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  s        public.rota_sessions := _rota_session(p_token);
  v_role   text;
  v_old    jsonb;
  v_m      jsonb;
  v_manage boolean;
begin
  if s.token is null then return jsonb_build_object('error', 'session'); end if;
  if p_key !~ '^rota-[a-z]+$' or p_key = 'rota-supabase-cfg' then
    return jsonb_build_object('error', 'Unknown data set');
  end if;

  if not s.is_admin then
    select m->>'role' into v_role from app_data, jsonb_array_elements(value) m
    where key = 'rota-members' and m->>'id' = s.member_id;
  end if;
  v_manage := s.is_admin or v_role = 'primary';

  if p_key = 'rota-config' then
    if not s.is_admin then return jsonb_build_object('error', 'Only the admin can change settings'); end if;
    if length(coalesce(p_value->>'adminPin', '')) >= 6 then
      update rota_admin set pin_hash = extensions.crypt(p_value->>'adminPin', extensions.gen_salt('bf')) where id = 1;
    end if;
  elsif p_key = 'rota-members' then
    if jsonb_typeof(p_value) <> 'array' then return jsonb_build_object('error', 'Bad member list'); end if;
    select value into v_old from app_data where key = 'rota-members' for update;
    v_old := coalesce(v_old, '[]'::jsonb);

    for v_m in select * from jsonb_array_elements(p_value) loop
      if length(trim(coalesce(v_m->>'pin', ''))) >= 4 and (v_manage or v_m->>'id' = s.member_id) then
        perform _rota_set_pin(v_m->>'id', v_m->>'pin');
      end if;
    end loop;

    if not v_manage then
      -- keep stored list; take only the caller's own record, minus role/approval changes
      p_value := (
        select coalesce(jsonb_agg(
          case when o->>'id' = s.member_id and n.m is not null
               then (n.m - 'role' - 'approved')
                    || jsonb_build_object('id', o->>'id')
                    || jsonb_strip_nulls(jsonb_build_object('role', o->'role', 'approved', o->'approved'))
               else o end order by i), '[]'::jsonb)
        from jsonb_array_elements(v_old) with ordinality as t(o, i)
        left join lateral (select x as m from jsonb_array_elements(p_value) x where x->>'id' = o->>'id' limit 1) n on true);
    end if;
  end if;

  insert into app_data (key, value) values (p_key, _rota_strip(p_key, p_value))
  on conflict (key) do update set value = excluded.value;
  return jsonb_build_object('ok', true);
end $$;

-- Set the admin PIN — run from the SQL Editor only (not callable from the browser)
create or replace function public.rota_set_admin_pin(p_pin text)
returns text language plpgsql security definer set search_path = public as $$
begin
  if length(coalesce(p_pin, '')) < 6 then raise exception 'Admin PIN must be at least 6 characters'; end if;
  insert into rota_admin (id, pin_hash) values (1, extensions.crypt(p_pin, extensions.gen_salt('bf')))
  on conflict (id) do update set pin_hash = excluded.pin_hash;
  return 'Admin PIN set';
end $$;

create or replace function public.rota_logout(p_token uuid)
returns void language sql security definer set search_path = public as $$
  delete from rota_sessions where token = p_token;
$$;

-- ── Who can call what ──────────────────────────────────────────────────────
revoke execute on function
  public._rota_session(uuid), public._rota_too_many(text, int, interval),
  public._rota_note(text), public._rota_set_pin(text, text), public._rota_strip(text, jsonb),
  public.rota_set_admin_pin(text)
  from public, anon, authenticated;

revoke execute on function
  public.rota_public(), public.rota_login(text, text), public.rota_admin_login(text),
  public.rota_register(jsonb), public.rota_load(uuid), public.rota_save(uuid, text, jsonb),
  public.rota_logout(uuid)
  from public;
grant execute on function
  public.rota_public(), public.rota_login(text, text), public.rota_admin_login(text),
  public.rota_register(jsonb), public.rota_load(uuid), public.rota_save(uuid, text, jsonb),
  public.rota_logout(uuid)
  to anon, authenticated;

commit;

-- ── NEXT: set the admin PIN ─────────────────────────────────────────────────
-- Open a NEW query, paste this one line, put your PIN between the quotes, Run:
--
--   select rota_set_admin_pin('your-new-pin');
--
-- (At least 6 characters. Run it again any time to change the admin PIN.)

-- Quick check — should list your data keys WITHOUT any pins:
-- select key, jsonb_typeof(value) from app_data;
