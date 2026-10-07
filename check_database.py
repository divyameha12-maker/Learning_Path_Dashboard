import sqlite3

# Connect to the database
connection = sqlite3.connect("learning_path.db")
connection.row_factory = sqlite3.Row

# Create cursor
cursor = connection.cursor()


# ===================================================
# SHOW ALL TABLES
# ===================================================

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    ORDER BY name
""")

tables = cursor.fetchall()

print("Tables in the database:")
print("=======================")

for table in tables:
    print("-", table["name"])


# ===================================================
# SHOW ACADEMIC PUBLICATIONS
# ===================================================

print()
print("Academic Publications:")
print("======================")

# Check whether publications table exists
publication_table = connection.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    AND name='publications'
""").fetchone()


if publication_table:

    publications = connection.execute("""
        SELECT
            publication_id,
            title,
            authors,
            year,
            topic,
            source
        FROM publications
        ORDER BY publication_id
    """).fetchall()

    if publications:

        for publication in publications:

            print(
                "ID:", publication["publication_id"],
                "| Title:", publication["title"],
                "| Authors:", publication["authors"],
                "| Year:", publication["year"],
                "| Topic:", publication["topic"],
                "| Source:", publication["source"]
            )

    else:

        print("No academic publications found.")

else:

    print("Publications table does not exist.")


# ===================================================
# CLOSE DATABASE
# ===================================================

connection.close()

print()
print("Database check completed.")