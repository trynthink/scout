# PostgreSQL Tests

## Prerequisites

1. Install PostgreSQL

`$ brew install postgresql`

2. Initialize PostgreSQL database

`$ initdb /usr/local/var/postgres -E utf8`

3. Start PostgreSQL locally

`$ brew services start postgresql`
(possibly also required) `pg_ctl -D /usr/local/var/postgres -l /usr/local/var/postgres/server.log start`

4. Update environment variables

Create the following environment variables customized with your database credentials. Screaming snake case (matching the table) is _strongly_ recommended:

| Variable     | Value            |
|--------------|------------------|
| SCOUT_HOST   | 127.0.0.1        |
| SCOUT_DB     | scout            |
| SCOUT_SCHEMA | scout_db         |
| SCOUT_USER   | scout            |
| SCOUT_PASS   | xxxxxxxxx        |

To update the environment variables (on a Mac using bash), edit the `.bash_profile`:

`$ open ~/.bash_profile`

And add the variables on their own lines as, e.g.:

`export SCOUT_HOST=127.0.0.1`

And set `SCOUT_PASS` to a value of your choice.

5. Create `scout` database and `scout` user in PostgreSQL service

Launch the PostgreSQL database: 

`$ psql -d postgres`

Within PostgreSQL:

```
CREATE ROLE scout WITH LOGIN PASSWORD 'xxxxxxxxx' WITH CREATEDB;
CREATE DATABASE scout;
GRANT ALL PRIVILEGES ON DATABASE scout TO scout;
```

The password should match the password set in the environment variables.

6. If needed, run `ecm_prep.py` and `run.py`

Running `test.py` assumes that `ecm_prep.py` and `run.py` have previously run with one or more ECMs and generated output files. 

## Running the Tests

The following command will append `_tests` to the schema name, delete any existing contents, recreate the schema structure, and populate the database using previously generated outputs:

`python3 populate_tests_schema.py`

Then run the tests:

`python3 test.py`