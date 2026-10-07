import sqlite3

connection = sqlite3.connect("learning_path.db")

cursor = connection.cursor()

# Delete only the duplicate publication
cursor.execute("""
    DELETE FROM publications
    WHERE publication_id = ?
""", (4,))

connection.commit()

print("Duplicate publication with ID 4 deleted successfully.")

connection.close()