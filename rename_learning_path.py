import sqlite3

connection = sqlite3.connect("learning_path.db")
cursor = connection.cursor()

cursor.execute("""
    UPDATE learning_paths
    SET title = ?
    WHERE path_id = ?
""", (
    "Probability and Statistics for Machine Learning",
    2
))

connection.commit()

if cursor.rowcount > 0:
    print("Learning path name updated successfully!")
else:
    print("Learning path ID 2 was not found.")

connection.close()