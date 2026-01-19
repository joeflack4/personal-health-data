# PostgreSQL Migration - Clarifying Questions

## 1. Database Migration
Do you want me to (a) create a script to migrate existing SQLite data to PostgreSQL, or (b) will you initialize the 
PostgreSQL database from scratch by fetching fresh data from Google Sheets?

A: Interesting idea. Create an .env var called PG_INIT_MIGRATE_SQLITE and set it to False. But if it is set to True, 
then go with the implementation of (a). But otherwise if it is not set or set to something other than True, do (b). 
Implement both.

## 2. PostgreSQL Dependency
I'll need to add `psycopg2-binary` (or `psycopg2`) to the dependencies for PostgreSQL connections. Should I add this? 
Any preference between the two?

A: I've used both, but I can't remember why I've had more luck with -binary in the past. Use your best judgement. This 
will need to work inside of render.com's environment.

## 3. Table Deletion Strategy (Sync)
When syncing in PostgreSQL, you mentioned "delete all of the tables we care about". Should I:
- **Option A**: `DROP TABLE` and recreate them (slower, but cleaner)
- **Option B**: `TRUNCATE TABLE` (faster, keeps structure)
- **Option C**: `DELETE FROM` each table (slowest, but works with foreign keys)

Which approach do you prefer?

A: Option A

## 4. Initialization Check
For checking if the DB is initialized, I'm planning:
i. Check if all required tables exist (`raw_events`, `alcohol_events`, `alcohol_weekly`, `db_metadata`)
ii. Check if `db_metadata` table has the `last_updated` key
iii. Optionally check if tables have data

Does this sound good? Any specific requirements?

I guess (ii) sounds good. I guess first check if the table exists and that if so, it has `last_updated` and 
`last_updated` is not null. If that's the case, then we can consider that the DB has already been initialized. But if 
that fails, then we should consider the database uninitialized.

A: If it's uninitialized, then I think we'll want to follow some of the same steps as sync; namely drop all the tables. 
Why? Because if a previous initialization failed halfway through, then this is the best way to ensure that the next 
initialization will happen correctly. 

## 5. Schema Updates for PostgreSQL
SQLite and PostgreSQL have some differences:
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
- `TEXT` → `VARCHAR` or keep as `TEXT`
- Boolean handling

Should I:
- **Option A**: Keep schema as SQLite-compatible as possible (easier to switch back)
- **Option B**: Update to PostgreSQL best practices (better performance/standards)

A: Optoin A

## 6. Environment Variable Naming
Should I use:
- **Option A**: Full connection URLs (`PG_CONNECTION_URL_INTERNAL`, `PG_CONNECTION_URL_EXTERNAL`)
- **Option B**: Individual components (`PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PG_DATABASE`)

Option A is simpler. Option B is more flexible (easier to swap components).

A: Create all the variables in env/.env. But when connecting, let's just go with "A" for now.

## 7. Error Handling
What should happen if PostgreSQL connection fails during runtime?
a. Raise error and stop?
b. Log error and continue (if possible)?
c. Fall back to SQLite (if `USE_SQLITE` is available)?

A: Option 'a'

## 8. Credentials in .env
Should I add the actual PostgreSQL credentials to `.env` or create `.env.example` with placeholder values?
(I'm assuming you'll manually add real credentials to `.env` which is gitignored, and I'll add placeholders to a 
template)

A: Both. First, create .env.example with dummy values or leave them blank. Then update .env, using the values shown in 
_archive/temp/render-pg-creds.txt as I mentioned.
