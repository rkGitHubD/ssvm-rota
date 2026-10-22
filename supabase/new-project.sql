-- Rota — FIRST script for a brand-new Supabase project (new organisation)
--
-- Paste this whole file into Supabase → SQL Editor → New query → Run,
-- then run the other scripts in the order listed in supabase/README.md.
-- Not needed for SSVM (its table already exists). Safe to re-run.

create table if not exists public.app_data (
  key   text primary key,
  value jsonb not null
);
