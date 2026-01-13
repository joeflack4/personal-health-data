# Plotly Cloud Deployment Guide

## Prerequisites
- [ ] Plotly Cloud account (@user)
- [ ] Google Sheets publicly accessible or API credentials configured (@user)
- [ ] Repository pushed to GitHub (@user)

## Local Setup Tasks

### 1. Install Dash Cloud Package
- [ ] Run: `pip install "dash[cloud]"` or `uv add "dash[cloud]"`
- [ ] Update pyproject.toml with dash cloud dependencies
- [ ] Test locally that app still runs

### 2. Configuration Updates
- [ ] Verify APP_HOST can be set via environment variable (currently hardcoded to 127.0.0.1)
- [ ] Update app/config.py to read HOST from env: `APP_HOST = os.getenv('HOST', '0.0.0.0')`
- [ ] Update app/config.py to read PORT from env: `APP_PORT = int(os.getenv('PORT', '8050'))`
- [ ] Ensure DEBUG defaults to False in production (already done)

### 3. Create Deployment Files
- [ ] Create `.plotly` directory (if required by Plotly Cloud)
- [ ] Create requirements.txt from pyproject.toml: `uv pip compile pyproject.toml -o requirements.txt`
- [ ] Verify all dependencies are included
- [ ] Add Python version specification file if needed

### 4. Database Considerations
- [ ] Decide on database location:
  - Option A: Use Plotly Cloud persistent storage
  - Option B: Use external database (SQLite may not persist on Plotly Cloud)
  - Option C: Use PostgreSQL/MySQL for production
- [ ] Update DB_PATH to use environment variable or cloud storage path
- [ ] Consider migrating to PostgreSQL for production (SQLite files may not persist)

### 5. Environment Variables Setup
- [ ] Document all required environment variables:
  - `SHEET_ID` - Google Sheets ID
  - `DEBUG` - Set to False for production
  - `HOST` - Set to 0.0.0.0 for cloud
  - `PORT` - Set by Plotly Cloud
  - `DB_PATH` - Path to database in cloud storage
- [ ] Create environment variables in Plotly Cloud dashboard (@user)

## Plotly Cloud Deployment Tasks

### 6. Initial Deployment
- [ ] Install Plotly Cloud CLI: `pip install plotly-dash-cloud` (@user if needed)
- [ ] Login to Plotly Cloud: `dash login` (@user)
- [ ] Initialize app: `dash init` or deploy via web UI (@user)
- [ ] Configure app name and settings (@user)

### 7. Deploy Application
- [ ] Deploy app: `dash deploy` or via GitHub integration (@user)
- [ ] Monitor deployment logs for errors
- [ ] Verify all dependencies installed correctly

### 8. Post-Deployment Configuration
- [ ] Set environment variables in Plotly Cloud UI (@user)
- [ ] Configure database initialization:
  - Option A: Run `health-data init` command manually
  - Option B: Auto-initialize on first load
- [ ] Test database sync functionality
- [ ] Verify Google Sheets data fetching works

## Testing & Verification

### 9. Functionality Testing
- [ ] Test app loads without errors
- [ ] Test database initialization
- [ ] Test data sync from Google Sheets
- [ ] Test all three database states:
  - No database (show Initialize button)
  - Updating (show spinner)
  - Ready (show charts)
- [ ] Test sidebar collapse/expand
- [ ] Test URL query params (alc-weekly-from, alc-weekly-to)
- [ ] Test quick date range selector
- [ ] Test custom date range selector
- [ ] Test chart interactions (zoom, pan, hover)
- [ ] Test Options page sync button

### 10. Performance & Monitoring
- [ ] Check app performance with full dataset
- [ ] Monitor memory usage
- [ ] Check database update times
- [ ] Verify background updates complete successfully
- [ ] Set up error monitoring/logging if available

## Documentation Updates

### 11. Update README
- [ ] Add deployment section to README.md
- [ ] Document environment variables
- [ ] Add troubleshooting section
- [ ] Include link to deployed app

## Potential Issues & Solutions

### Database Persistence
**Issue**: SQLite database may not persist between deployments on Plotly Cloud
**Solutions**:
1. Use Plotly Cloud persistent storage (if available)
2. Migrate to PostgreSQL/MySQL
3. Store database in external storage (S3, etc.)
4. Accept re-initialization on each deployment

### Google Sheets Access
**Issue**: Need to ensure Google Sheets is publicly accessible or use API credentials
**Solution**:
- Verify sheet has "Anyone with the link can view" permissions
- Or set up Google Sheets API credentials with service account

### Background Updates
**Issue**: Background threading may not work as expected on serverless/cloud platforms
**Solution**:
- Consider using Plotly Cloud's background job scheduling
- Or use external scheduler (cron job, celery, etc.)

## Notes
- Plotly Cloud may have specific requirements for app structure
- Check Plotly Cloud documentation for any additional configuration files needed
- Consider using Plotly Cloud's database options if SQLite persistence is an issue
- Ensure all paths are relative and cloud-compatible
