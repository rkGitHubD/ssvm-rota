# Database scripts

Run each file in Supabase → SQL Editor → New query → paste the whole file → Run.

## Setting up a new organisation (empty Supabase project)

1. `new-project.sql` — creates the data table
2. `lockdown.sql` — locks the table; all access goes through server functions
3. `member-admin.sql` — admin is a tick-box on a member
4. `pin-reset.sql` — Forgot PIN with security question + date of birth
5. `save-permissions.sql` — who may save which data
6. `first-admin.sql` — lets the first admin in

Then:

7. The first admin registers in the app (Register on the sign-in screen).
8. In a new SQL query: `select rota_set_member_admin('their email');`
   This approves them and makes them admin.
9. They sign in, set up their security question, and add everything else
   (Settings, logo, members, special occasions…) from the Admin tab.

## Handy one-liners (SQL Editor only — not callable from the app)

- Make / remove an admin: `select rota_set_member_admin('name or email');` · `select rota_set_member_admin('name or email', false);`
- Set anyone's PIN: `select rota_set_member_pin('name or email', '1234');`
