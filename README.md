# CrediRate

CrediRate is a Flask + MySQL credibility-weighted rating system for demonstrating explainable trust scores.

## Stack

- Backend: Flask
- Database: MySQL
- Frontend: HTML, CSS, JavaScript

## Database

The app connects to local MySQL with these defaults:

```python
host = "127.0.0.1"
user = "root"
password = ""
database = "credirate"
```

If your MySQL credentials differ, update both:

- `app.py`
- `db_setup.py`

## Local Run

1. Start MySQL locally. XAMPP MySQL works fine.
2. Open a terminal in this folder.
3. Run:

```bat
build.bat
run.bat
```

4. Open:

```text
http://127.0.0.1:5000
```

## What `build.bat` Does

- creates `venv`
- installs Python dependencies
- creates the `credirate` MySQL database
- creates tables and views
- seeds professor-demo sample data

## Notes

- The old `trust_ledger.db` file is no longer used after this MySQL conversion.
- New user names entered in the UI are created automatically in MySQL when a review is submitted.
