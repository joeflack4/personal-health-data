# Implementation Questions - Answered

## 1. Google Sheets Access

### Question
Is the Google Sheet containing your health data publicly accessible (can be accessed via export URL without 
authentication), or does it require Google OAuth authentication?

### Answer
<!-- Please specify: "public" or "requires authentication" -->
public

### Follow-up
If it requires authentication, would you prefer to:
- Make the sheet public (simpler but less secure)
- Set up Google OAuth (more complex but more secure)
- Use a different authentication method

### Answer
<!-- Your preference here -->
n/a

---

## 2. Sheet ID Configuration

### Question
Should the `SHEET_ID` be stored in:
- `config.yaml` (if the sheet is public and you're okay with it being in version control)
- `env/.env` (if you want to keep it private)

### Answer
<!-- Please specify: "config.yaml" or "env/.env" -->
That's not for you to do, that's for me to do, and I've already done it. Set the logic up to check config.yaml first 
and if it doesn't find it there, it should check env/.env.

---

## 3. Render.com Deployment

### Question
Do you have a Render.com account already set up? If so, do you have an API key for the Render CLI, or would you prefer 
to deploy manually through the Render web interface?

### Answer
<!-- Please provide details about your Render.com setup -->
Yeah, actually go ahead and don't worry about Render right now. I'll handle the deployment.

### Follow-up
Would you like documentation for:
- CLI-based deployment (if you have/want to use Render API key)
- Manual deployment via web interface (simpler for first time)
- Both options

### Answer
<!-- Your preference here -->
No docs.

---

## 4. Database Location

### Question
The implementation guides assume the SQLite database should be stored in the root of the repository (e.g., 
`health_data.db`). Is this acceptable, or would you prefer it in a different location?

### Answer
<!-- Specify: "root is fine" or provide preferred path -->
Yeah; root. Name it `db.db`.

---

## 5. Python Version

### Question
What Python version would you like to use? (Recommended: 3.11 or 3.12 for modern features and good performance)

### Answer
<!-- Your preferred version here -->
3.12

---

## 6. Initial Data Load

### Question
When the app is first deployed and the database doesn't exist yet, would you prefer:
- **Option A**: Auto-initialize database on first app load (may cause slow first page load)
- **Option B**: Show a button that says "Initialize Database" that the user must click
- **Option C**: Require manual CLI command to be run before starting the app

### Answer
<!-- Please specify: A, B, or C -->
Actually I like B. But just make sure that the app doesn't time out. We won't be using any web workers, so I think the 
best flow is to have the user do that, and when that happens, before responding, at least create the database and use 
some kind of 'manage' table to store a variable that tracks the status of the database, as I mentioned in my mvp.md. 
Basically should store the datetime that the db was updated, or null if it hasn't been fully updated yet. So when you 
create the db, create this var but leave that datetime null. Then tell the user to come back in a few minutes. If the 
user refreshes and the value is still null, then tell the user that the update is still in progress. Then when the db 
is updated and it displays a datetime for this var, follow the rest of the instructions as laid out in mvp.md.

Actually, I think that I want to expand on this further. I want to tell you about how to handle not only the initial 
data load, but the syncing as well. I mentioned in mvp.md that you should have a sync button and show the datetime that 
the db was last updated. However when pressing that sync button, you'll want to track if the db update is currently in 
progress or not. I mentioned backing up the db and making a fresh new db... so actually, I guess that you can use very 
similar behavior to handle this syncing as you do to handle initialization. After doing the back up and creating a fresh 
db, you can also let the user know that things are still in progress.

Actually, I don't know if you can have very good UX in this situation without a web worker. Just go ahead and do your 
best. We can really only have 1 server process. 

---

## 7. Google Sheet Structure Validation

### Question
Can you provide:
- The actual SHEET_ID so I can inspect the structure?
- OR a few sample rows (anonymized if needed) showing the exact column names and data formats?

This will help ensure the implementation handles your specific data format correctly.

### Answer
I already told you that in mvp.md, that it will be in config.yaml, else env/.env. Go ahead and find that, and you can 
do a fetch and see. If you want to download some content just for inspection purposes, you can use the dir: 
_archive/temp/ 

---

## 8. Time Zone

### Question
What timezone are you in? This is important for correctly interpreting the timestamps in your health data.

### Answer
<!-- Your timezone (e.g., "America/New_York", "Asia/Tokyo", etc.) -->
EST

---

## 9. Week Start Day

### Question
For weekly aggregation of alcohol consumption, should weeks start on:
- Sunday (default for many systems)
- Monday (ISO 8601 standard)
- Other day?

### Answer
<!-- Specify day of week -->
Great question! Let's do Monday.

---

## 10. Additional Features for MVP

### Question
The current MVP focuses on displaying weekly alcohol consumption as a line chart with trend line. Are there any other 
simple features you'd like included in the MVP, such as:
- Summary statistics (average drinks per week, total, max, min)
- Comparison to goals or thresholds
- Export data to CSV
- Other?

### Answer
<!-- List any additional MVP features, or "none" if satisfied with current scope -->
none

---

## 11. Testing Data

### Question
Would you like me to create sample/mock health data for testing purposes, or will you provide actual data for testing?

### Answer
<!-- Specify preference -->
You can and should create mock data.

---

## 12. Deployment Priority

### Question
For the MVP, would you like to:
- **Option A**: Focus on getting it working locally first, defer Render deployment
- **Option B**: Ensure Render deployment is fully working as part of MVP
- **Option C**: Both, but prioritize local development if time is limited

### Answer
<!-- Please specify: A, B, or C -->
A

# Implementation Questions - Unanswered
