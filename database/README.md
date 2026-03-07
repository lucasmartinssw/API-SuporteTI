# Database Migrations

This directory contains everything needed to create the MySQL database and
initial tables used by the project.

## Files

* `migration.sql` – SQL script that can be opened and executed in MySQL
  Workbench.  It is idempotent (`IF NOT EXISTS`) and also inserts some
  starter data.
* `run_migration.py` – Python helper that reads the same SQL file and runs
  each statement using the connection settings from `app/config.py`.  You
  can execute it with:

```sh
python -m database.run_migration
```

(make sure your virtual environment is activated and `mysql-connector-python`
is installed).

## Usage

1. Copy or adapt the connection values in `app/config.py` (or set
   environment variables).
2. Run the helper script, or open `migration.sql` in MySQL Workbench and
   execute the contents.
3. The database `projetofinal` (name configurable in the SQL) will be
   created along with all necessary tables and some lookup data.
