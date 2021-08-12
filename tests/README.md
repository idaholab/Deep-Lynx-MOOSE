## MOOSE Adapter Tests

To get started with testing, first follow the instructions for the Poetry installation in the README.md located in the root of the repository. Additionally, a `.env` file must exist in the root directory (copied from `.env_sample`).  

To run all tests and view statement coverage, please run the following commands:
- `coverage run -m pytest tests/ --cov=adapter --junit-xml=tests/reports/test-results.xml --cov-report html`  
- `python -m http.server`  This will start a web browser to which you can navigate to view all tested files as well as covered and uncovered lines.  
Generally viewable at http://0.0.0.0:8000/htmlcov/  

To run an individual test file, use `pytest tests/test_file_name.py`
Option `-rP` can be added to print `print` statements to console during test
Option `-k "test_my_test"` may be used to test only the test `test_my_test` in the specified `.py` file  

### Test Development
This application uses [pytest](https://docs.pytest.org/en/stable/) for testing.
