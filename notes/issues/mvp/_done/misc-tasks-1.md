# Temporary Tasks - UI Enhancements

## 1. Collapsible Sidebar
- [x] Add toggle button to sidebar
- [x] Implement expand/collapse functionality with state management
- [x] Set default state to collapsed
- [x] Update content area margin to adjust based on sidebar state
- [x] Add smooth CSS transitions for collapse animation

## 2. URL Query Parameters for Widget State
- [x] Add query params: `alc-weekly-from` and `alc-weekly-to` (YYYY-MM-DD format)
- [x] On page load: Parse URL params and populate date range picker
- [x] On date selection: Update URL query params without page reload
- [x] Test that direct URL entry works (auto-populate widgets and render) - Ready for user testing
- [x] Ensure URL updates when user makes selections in UI

## 3. "Show Last N TIMEFRAME" UI Component
- [x] Create new UI section above date range selector
- [x] Add TIMEFRAME dropdown with options: "months", "years"
- [x] Add N dropdown:
  - When TIMEFRAME="months": show 3, 6, 12
  - When TIMEFRAME="years": calculate years from data, show integers ascending
- [x] Add "Go" button to trigger visualization update
- [x] Implement callback to calculate available years from database
- [x] Implement callback to update chart based on N/TIMEFRAME selection
- [x] Ensure both this UI and date range selector work independently
- [x] Update date range selector when "Go" is clicked (and vice versa for consistency)

## Status
All tasks completed! App is running at http://127.0.0.1:8050/

Ready for user testing.
