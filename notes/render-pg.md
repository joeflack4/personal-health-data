Ok, we're going to use the Render.com free postgres service. For the credentails and other info, please see:
_archive/temp/render-pg-creds.txt

please update .env to hold this information. Create an environment variable as well called ACTIVE_ENV and in .env, set
it to 'local'. But when the app loads, if it doesn't see this var, Python should set the active env to 'production'.
When the active env is production, staging, or test, use connection url internal. in all other cases, i was thining to
use use connection url external. use the environment variables you create for these. one exception. also create an env
var called USE_SQLITE. If this is present and set to True (case insensitive), then use our existing sqlite setup.

if the app is currently connected to postgres instead of sqlite, let's do things a bit differently. ideally i'd like to
do the whole temporary backup process, but for our MVP, when we do a sync, we can just delete all of the tables we care
about, and then recreate them. For initialization, we should have some way of checking if the db is initialized. I'll
let you figure that out, whether it be the presence of all tables and the fact that they are not empty, or some db var.

But yeah, we want to basically use this postgres url basically when we're in production, and we want the initialization
and sync to still work.

If you have any questions before we begin, please create a render-pg-questions.md and then prompt me to respond.
