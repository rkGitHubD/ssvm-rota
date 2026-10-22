-- SSVM Rota — Forgot PIN with a security question + date of birth (run AFTER member-admin.sql)
--
-- Paste this whole file into Supabase → SQL Editor → New query → Run.
--
-- What it does:
--   • New members choose a security question, its answer and their date of birth
--     when they register. Existing members are asked for them at their next sign-in.
--     Answers and dates of birth are stored hashed — nobody can read them back.
--   • Forgot PIN: name/email → their question is shown → correct answer + date of
--     birth + new PIN → they can sign in straight away.
--   • 5 wrong attempts locks resets for that account for 24 hours.
--   • Removes earlier Forgot PIN versions if they were installed.

begin;

drop function if exists public.rota_request_pin_reset(text, text);
drop function if exists public.rota_pin_requests(uuid);
drop function if exists public.rota_pin_request_decide(uuid, text, boolean);
drop function if exists public.rota_reset_pin(text, text);
drop table if exists public.rota_pin_requests;

create table if not exists public.rota_recovery (
  member_id   text primary key,
  question    text not null,
  answer_hash text not null,
  dob_hash    text not null,
  updated_at  timestamptz not null default now()
);
alter table public.rota_recovery enable row level security;
revoke all on public.rota_recovery from anon, authenticated;

-- ── Internal helpers ───────────────────────────────────────────────────────
-- Answers compare ignoring case and extra spaces
create or replace function public._rota_norm(p text)
returns text language sql immutable as $$
  select lower(regexp_replace(trim(coalesce(p, '')), '\s+', ' ', 'g'));
$$;

-- Validates the three recovery fields; returns an error message or null
create or replace function public._rota_recovery_problem(p_question text, p_answer text, p_dob text)
returns text language plpgsql stable as $$
declare v_dob date;
begin
  if length(trim(coalesce(p_question, ''))) < 5 then return 'Please choose or write a security question'; end if;
  if length(_rota_norm(p_answer)) < 2 then return 'Please give an answer to your security question'; end if;
  begin
    v_dob := p_dob::date;
  exception when others then
    return 'Please enter your date of birth';
  end;
  if v_dob is null or v_dob < date '1900-01-01' or v_dob > current_date then
    return 'Please enter a valid date of birth';
  end if;
  return null;
end $$;

create or replace function public._rota_save_recovery(p_member_id text, p_question text, p_answer text, p_dob text)
returns void language sql security definer set search_path = public as $$
  insert into rota_recovery (member_id, question, answer_hash, dob_hash)
  values (p_member_id, trim(p_question),
          extensions.crypt(_rota_norm(p_answer), extensions.gen_salt('bf')),
          extensions.crypt(p_dob::date::text, extensions.gen_salt('bf')))
  on conflict (member_id) do update set question = excluded.question, answer_hash = excluded.answer_hash,
                                        dob_hash = excluded.dob_hash, updated_at = now();
$$;

-- ── Register: now also takes question / answer / dob ───────────────────────
create or replace function public.rota_register(p jsonb)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  v_name  text := trim(coalesce(p->>'name', ''));
  v_email text := lower(trim(coalesce(p->>'email', '')));
  v_pin   text := trim(coalesce(p->>'pin', ''));
  v_bad   text := _rota_recovery_problem(p->>'question', p->>'answer', p->>'dob');
  v_list  jsonb;
  v_old   jsonb;
  v_id    text;
begin
  if v_name = '' then return jsonb_build_object('error', 'Full name is required'); end if;
  if v_email !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then return jsonb_build_object('error', 'Please enter a valid email address'); end if;
  if length(v_pin) < 4 then return jsonb_build_object('error', 'PIN must be at least 4 digits'); end if;
  if v_bad is not null then return jsonb_build_object('error', v_bad); end if;
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
  perform _rota_save_recovery(v_id, p->>'question', p->>'answer', p->>'dob');
  return jsonb_build_object('ok', true);
end $$;

-- ── Sign-in: also says whether the member still needs to set up recovery ───
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
  return jsonb_build_object('token', v_tok,
    'needsRecovery', not exists (select 1 from rota_recovery where member_id = v_m->>'id'),
    'member', jsonb_build_object(
      'id', v_m->>'id', 'name', v_m->>'name', 'email', v_m->>'email', 'role', v_m->>'role', 'isAdmin', v_adm));
end $$;

-- ── Signed-in member sets or changes their own security question ──────────
create or replace function public.rota_set_recovery(p_token uuid, p_question text, p_answer text, p_dob text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  s     public.rota_sessions := _rota_session(p_token);
  v_bad text := _rota_recovery_problem(p_question, p_answer, p_dob);
begin
  if s.token is null or s.member_id is null then return jsonb_build_object('error', 'session'); end if;
  if v_bad is not null then return jsonb_build_object('error', v_bad); end if;
  perform _rota_save_recovery(s.member_id, p_question, p_answer, p_dob);
  return jsonb_build_object('ok', true);
end $$;

-- ── Forgot PIN step 1: show the member's own question ─────────────────────
create or replace function public.rota_recovery_question(p_ident text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  v_q  text := lower(trim(coalesce(p_ident, '')));
  v_m  jsonb;
  v_qn text;
begin
  if v_q = '' then return jsonb_build_object('error', 'Please enter your name or email'); end if;
  if _rota_too_many('question:' || v_q, 20, interval '1 hour') then
    return jsonb_build_object('error', 'Too many attempts. Please wait an hour and try again.');
  end if;
  perform _rota_note('question:' || v_q);

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

  select question into v_qn from rota_recovery where member_id = v_m->>'id';
  if v_qn is null then
    return jsonb_build_object('error', 'You haven''t set up a security question yet. Please ask the admin or a Rota Lead to reset your PIN.');
  end if;
  return jsonb_build_object('question', v_qn);
end $$;

-- ── Forgot PIN step 2: answer + date of birth → new PIN ───────────────────
create or replace function public.rota_reset_pin(p_ident text, p_answer text, p_dob text, p_pin text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  v_q   text := lower(trim(coalesce(p_ident, '')));
  v_m   jsonb;
  v_r   public.rota_recovery;
  v_dob date;
begin
  if length(trim(coalesce(p_pin, ''))) < 4 then return jsonb_build_object('error', 'PIN must be at least 4 digits'); end if;

  select m into v_m from app_data, jsonb_array_elements(value) m
  where key = 'rota-members' and (lower(m->>'email') = v_q or lower(m->>'name') = v_q)
  limit 1;
  if v_m is null then
    return jsonb_build_object('error', 'No account found. Please check your name/email or sign up.');
  end if;
  if v_m->>'approved' = 'rejected' or v_m->'approved' = 'false'::jsonb then
    return jsonb_build_object('error', 'This account is not approved yet.');
  end if;
  if _rota_too_many('resetfail:' || (v_m->>'id'), 5, interval '24 hours') then
    return jsonb_build_object('error', 'Too many wrong answers. Please try again tomorrow, or ask the admin or a Rota Lead to reset your PIN.');
  end if;

  select * into v_r from rota_recovery where member_id = v_m->>'id';
  if v_r.member_id is null then
    return jsonb_build_object('error', 'You haven''t set up a security question yet. Please ask the admin or a Rota Lead to reset your PIN.');
  end if;
  begin v_dob := p_dob::date; exception when others then v_dob := null; end;

  if v_dob is null
     or v_r.answer_hash <> extensions.crypt(_rota_norm(p_answer), v_r.answer_hash)
     or v_r.dob_hash    <> extensions.crypt(v_dob::text, v_r.dob_hash) then
    perform _rota_note('resetfail:' || (v_m->>'id'));
    return jsonb_build_object('error', 'Your answer or date of birth doesn''t match. Please check and try again.');
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

-- ── Who can call what ──────────────────────────────────────────────────────
revoke execute on function
  public._rota_norm(text), public._rota_recovery_problem(text, text, text),
  public._rota_save_recovery(text, text, text, text), public.rota_set_member_pin(text, text)
  from public, anon, authenticated;
revoke execute on function
  public.rota_register(jsonb), public.rota_login(text, text), public.rota_set_recovery(uuid, text, text, text),
  public.rota_recovery_question(text), public.rota_reset_pin(text, text, text, text)
  from public;
grant execute on function
  public.rota_register(jsonb), public.rota_login(text, text), public.rota_set_recovery(uuid, text, text, text),
  public.rota_recovery_question(text), public.rota_reset_pin(text, text, text, text)
  to anon, authenticated;

commit;

-- ── If you forget your own PIN and security answers ────────────────────────
-- Open a NEW query, fill in the quotes, Run:
--
--   select rota_set_member_pin('Ramki', 'your-new-pin');
