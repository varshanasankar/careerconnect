Backend setup for CareerConnect

This project uses MySQL (MariaDB or MySQL server).

1) Create the `careerconnect` database and tables using the provided `schema.sql` file.

Using the MySQL CLI (recommended):

```powershell
# Edit user/password as needed
mysql -u root -p < schema.sql
```

Or connect and run inside the mysql prompt:

```sql
SOURCE schema.sql;
```

2) Verify `config.py` matches your database credentials. Defaults are:

- `MYSQL_HOST` = localhost
- `MYSQL_USER` = root
- `MYSQL_PASSWORD` = varshana
- `MYSQL_DB` = careerconnect

3) Start the Flask app with your virtualenv activated:

```powershell
Set-Location 'C:\Users\hp\Downloads\CareerConnect'
.\venv\Scripts\Activate.ps1
.\venv\Scripts\python.exe app.py
```

4) Notes

- The `schema.sql` file also seeds a few sample jobs in the `jobs` table.
- If you prefer to run SQL from a GUI (MySQL Workbench, phpMyAdmin), open `schema.sql` and run the statements there.
- Do NOT commit credentials to source control; consider using environment variables for production.
