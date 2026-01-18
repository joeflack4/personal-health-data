# Test tasks

## General
### Mock Data Creation to put in tests/input/
- [x] Create mock health data for testing. Can use a real subsample from: _archive/temp/health_data_sample.csv
  - [x] Create `_archive/temp/` directory
  - [x] Generate sample CSV data matching expected schema (downloaded actual data for inspection)
  - [ ] Include drink events ("飲み物") with various quantities
  - [ ] Include both "今" and "別時" events
  - [ ] Include paired Start/Stop events for testing validation

### Initial Testing
- [x] Create basic test structure
  - [x] Create `tests/` directory
  - [x] Create `tests/test_lib/` for library tests
  - [x] Create `tests/test_app/` for app tests
- [x] Create `conftest.py` with shared fixtures (If you are not able to fully implement this on your own and need the user for something, prompt them for what you need)

## From lib setup
### Phase 2.2: Data Fetching
- [x] Create tests for fetcher
- [x] Test URL construction
- [x] Test with mocked HTTP responses
- [x] Test error handling scenarios

### Phase 2.3: Data Parsing
- [x] Create tests for parser
- [x] Test datetime parsing with various formats
- [x] Test next-day cutoff logic
- [x] Test with malformed data

### Phase 2.4: Data Validation
- [x] Create tests for validator
- [x] Test paired Start/Stop validation
- [x] Test timespan <= 24 hours validation
- [x] Test unpaired event detection
- [x] Test error reporting structure

### Phase 2.5: Alcohol Use Data Transformation
- [x] Create tests for alcohol transformer
  - [x] Test drink event filtering
  - [x] Test quantity parsing from comments
  - [x] Test weekly aggregation
  - [x] Test edge cases (empty comments, invalid numbers)

### Phase 2.7: Database Operations
- [x] Create tests for database operations
  - [x] Test database creation
  - [x] Test backup and restore (including cleanup of old backups)
  - [x] Test update with valid data
  - [x] Test update with invalid data (rollback)

### Phase 2.10: Testing & Documentation
- [x] Write comprehensive unit tests
  - [x] Test configuration loading
  - [x] Test data fetching (with mocks)
  - [x] Test parsing logic
  - [x] Test validation logic
  - [x] Test transformation logic
  - [x] Test database operations
  - [ ] Aim for >80% code coverage (can measure with pytest-cov)

- [x] Write integration tests
  - [x] Create mock health data CSV (inline in test fixtures)
  - [x] Test full pipeline with sample data (mocked fetcher)
  - [x] Test error recovery scenarios
  - [x] Test backup and restore workflow
  - [x] Created optional test for real data (marked with @pytest.mark.skip)

- [ ] Create usage examples (partially done in README)

## From app setup
### Phase 3.2: Database Interface
- [x] Create tests for database interface
  - [x] Test with missing database
  - [x] Test with empty database
  - [x] Test with populated database
  - [x] Test date range filtering

### Phase 3.11: Testing
- [x] Set up test fixtures for database
- [x] Create sample data for testing

- [x] Write component tests
  - [x] Test database query functions
  - [x] Test chart generation functions
  - [ ] Test layout generation (lower priority)
  - [x] Test CLI commands (init, status, update)

- [ ] Write integration tests
  - [ ] Test full app initialization
  - [ ] Test callback interactions
  - [ ] Test with empty database
  - [ ] Test with populated database
  - [ ] Test date range filtering

### Phase 3.13: Local Development Testing
- [ ] Test locally with mock data
  - [ ] Use mock CSV data from _archive/temp/
  - [ ] Test all three database states (no DB, null last_updated, populated)
  - [ ] Verify polling interval works correctly
  - [ ] Test Sync button functionality

- [ ] Performance testing
  - [ ] Test with realistic data volumes
  - [ ] Verify background updates complete successfully
  - [ ] Check that UI remains responsive during updates
