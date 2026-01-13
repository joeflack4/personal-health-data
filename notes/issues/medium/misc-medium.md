# Misc improvements
## Lib
n/a

## App
- [ ] Handle concurrent update prevention
  - [ ] If last_updated is null, disable Sync/Initialize buttons
  - [ ] Prevent multiple simultaneous updates
  - [x] Show clear messaging about update in progress
- [ ] Validate that end_date >= start_date (basic validation implemented)
- [ ] Disable sync button while sync in progress (not implemented - button still clickable)
- [ ] Invalid date range selection (not validated)
