import sqlite3
import sys

def run_sql_file(sql_file):
    conn = sqlite3.connect('football.db')
    cursor = conn.cursor()

    try:
        # Read the SQL file
        with open(sql_file, 'r') as file:
            sql_script = file.read()

        # Execute the SQL script
        cursor.executescript(sql_script)
        conn.commit()
        print(f"Successfully executed {sql_file}")
    except Exception as e:
        conn.rollback()
        print(f"Failed to execute {sql_file}: {e}")
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python execute.py <sql_file>")
        sys.exit(1)


    sql_file = sys.argv[1]

    run_sql_file(sql_file)