-- SSVM Rota — admin becomes a tick-box on a member (run AFTER lockdown.sql)
--
-- Paste this whole file into Supabase → SQL Editor → New query → Run.
-- AFTER RUNNING: make yourself admin in a separate query (see the end of this file).
--
-- What it does:
--   • Members with "isAdmin": true sign in with their own name/email + PIN and
--     get a full-access session. The separate admin PIN sign-in is removed.
--   • Only an admin can tick/untick Admin on anyone (including themselves),
--     change an admin's PIN, or remove an admin from the member list.

begin;

-- ── Member sign-in: admin flag comes from the member record ────────────────
create or replace function public.rota_login(p_ident text, p_pin text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  v_q    text := lower(trim(coalesce(p_ident, '')));
  v_m    jsonb;
  v_hash text;
  v_tok  uuid;
  v_adm  boolean;
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

  v_adm := coalesce(v_m->'isAdmin' = 'true'::jsonb, false);
  delete from rota_sessions where expires_at < now();
  insert into rota_sessions (member_id, is_admin) values (v_m->>'id', v_adm) returning token into v_tok;
  return jsonb_build_object('token', v_tok, 'member', jsonb_build_object(
    'id', v_m->>'id', 'name', v_m->>'name', 'email', v_m->>'email', 'role', v_m->>'role', 'isAdmin', v_adm));
end $$;

-- ── Save one data set (signed-in users only) ───────────────────────────────
-- Admin: anything. Rota Leads: anything except settings and admin flags.
-- Other members: settings blocked; on the member list they can only edit
-- their own record and cannot change roles/approval/admin or remove anyone.
create or replace function public.rota_save(p_token uuid, p_key text, p_value jsonb)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  s        public.rota_sessions := _rota_session(p_token);
  v_role   text;
  v_old    jsonb;
  v_m      jsonb;
  v_manage boolean;
  v_admins text[];
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
  elsif p_key = 'rota-members' then
    if jsonb_typeof(p_value) <> 'array' then return jsonb_build_object('error', 'Bad member list'); end if;
    select value into v_old from app_data where key = 'rota-members' for update;
    v_old := coalesce(v_old, '[]'::jsonb);
    select coalesce(array_agg(o->>'id'), '{}') into v_admins
    from jsonb_array_elements(v_old) o where o->'isAdmin' = 'true'::jsonb;

    if v_manage and not s.is_admin and exists (
      select 1 from unnest(v_admins) a
      where not exists (select 1 from jsonb_array_elements(p_value) x where x->>'id' = a)) then
      return jsonb_build_object('error', 'Only an admin can remove an admin');
    end if;

    for v_m in select * from jsonb_array_elements(p_value) loop
      if length(trim(coalesce(v_m->>'pin', ''))) >= 4
         and (s.is_admin or v_m->>'id' = s.member_id
              or (v_manage and not (v_m->>'id' = any(v_admins)))) then
        perform _rota_set_pin(v_m->>'id', v_m->>'pin');
      end if;
    end loop;

    if not v_manage then
      -- keep stored list; take only the caller's own record, minus role/approval/admin changes
      p_value := (
        select coalesce(jsonb_agg(
          case when o->>'id' = s.member_id and n.m is not null
               then (n.m - 'role' - 'approved' - 'isAdmin')
                    || jsonb_build_object('id', o->>'id')
                    || jsonb_strip_nulls(jsonb_build_object('role', o->'role', 'approved', o->'approved', 'isAdmin', o->'isAdmin'))
               else o end order by i), '[]'::jsonb)
        from jsonb_array_elements(v_old) with ordinality as t(o, i)
        left join lateral (select x as m from jsonb_array_elements(p_value) x where x->>'id' = o->>'id' limit 1) n on true);
    elsif not s.is_admin then
      -- Rota Lead: any edits, but admin flags stay as stored
      p_value := (
        select coalesce(jsonb_agg(
          (x - 'isAdmin') || case when x->>'id' = any(v_admins)
                                  then jsonb_build_object('isAdmin', true) else '{}'::jsonb end
          order by i), '[]'::jsonb)
        from jsonb_array_elements(p_value) with ordinality as t(x, i));
    end if;
  end if;

  insert into app_data (key, value) values (p_key, _rota_strip(p_key, p_value))
  on conflict (key) do update set value = excluded.value;
  return jsonb_build_object('ok', true);
end $$;

-- Tick/untick Admin on a member — run from the SQL Editor only (not callable from the browser)
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
                      then (m - 'isAdmin') || case when p_on then jsonb_build_object('isAdmin', true) else '{}'::jsonb end
                      else m end order by i)
               from jsonb_array_elements(value) with ordinality as t(m, i))
  where key = 'rota-members';
  delete from rota_sessions;  -- everyone signs in again, so the change takes effect
  return case when p_on then v_name || ' is now an admin' else v_name || ' is no longer an admin' end;
end $$;

-- ── Retire the separate admin PIN sign-in ──────────────────────────────────
drop function if exists public.rota_admin_login(text);
drop function if exists public.rota_set_admin_pin(text);
drop table if exists public.rota_admin;
delete from public.rota_sessions where member_id is null;

revoke execute on function public.rota_set_member_admin(text, boolean) from public, anon, authenticated;
revoke execute on function public.rota_login(text, text), public.rota_save(uuid, text, jsonb) from public;
grant  execute on function public.rota_login(text, text), public.rota_save(uuid, text, jsonb) to anon, authenticated;

commit;

-- ── NEXT: make yourself admin ──────────────────────────────────────────────
-- You need a member record with a PIN first (Master Data → Members).
-- Open a NEW query, put your name or email between the quotes, Run:
--
--   select rota_set_member_admin('your name or email');
--
-- To remove someone:  select rota_set_member_admin('their name or email', false);
-- Once you're admin you can also tick/untick Admin in Master Data → Members.
