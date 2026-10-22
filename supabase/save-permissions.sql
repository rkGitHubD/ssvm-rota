-- SSVM Rota — who can save which data (run AFTER member-admin.sql)
--
-- Paste this whole file into Supabase → SQL Editor → New query → Run.
--
-- Before this, any signed-in member could save any data set (e.g. cash or
-- sponsorships) by calling the server directly, even without the tab.
-- This makes the server enforce the same access the app's tabs give.

begin;

-- ── Save one data set (signed-in users only) ───────────────────────────────
-- Admin: anything.
-- Rota Leads: rotas, offers, members (not admin flags) and
--   the Rota Sheet data (sheets, registers, ticket entries, cash in hand).
-- Other members: rotas, offers and only their own member record (no
--   role/approval/admin changes, no removing anyone).
-- Everything else (settings, services, sponsorships, inventory, itineraries,
--   prasadham, priests, activities, special occasions) is admin-only.
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

  if not s.is_admin and not (
       p_key in ('rota-rotas', 'rota-offers', 'rota-members')
    or (v_manage and p_key in ('rota-sheets', 'rota-registers', 'rota-regentries', 'rota-cash'))) then
    return jsonb_build_object('error', case when p_key = 'rota-config' then 'Only the admin can change settings'
                                            else 'You don''t have permission to change this' end);
  end if;

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

revoke execute on function public.rota_save(uuid, text, jsonb) from public;
grant  execute on function public.rota_save(uuid, text, jsonb) to anon, authenticated;

commit;
