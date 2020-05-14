# PostgreSQL Tests

### Prerequisites
Running `test.py` assumes that `ecm_prep.py` and `run.py` have previously run and generated output files

Create the following environment variables customized with your database credentials.  Snake case is _strongly_ recommended:

| Variable     | Value            |
|--------------|------------------|
| SCOUT_HOST   | 127.0.0.1        |
| SCOUT_DB     | scout            |
| SCOUT_SCHEMA | scout_db         |
| SCOUT_USER   | scout            |
| SCOUT_PASS   | XXXXXXXXXXXXXXXX |

### Running the tests
The following command will append `_tests` to the schema name, delete any existing contents, recreate the schema structure, and populate the database using previously generated outputs:

`python3 populate_tests_schema.py`

Then run the tests:

`python3 test.py`
