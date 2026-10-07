import sqlite3
import shutil
import os

SOURCE_DB = "learning_path.db"
DEPLOY_DB = "learning_path_deploy.db"

if os.path.exists(DEPLOY_DB):
    os.remove(DEPLOY_DB)

shutil.copy2(SOURCE_DB, DEPLOY_DB)

connection = sqlite3.connect(DEPLOY_DB)

# Remove personal/user activity data from the deployment copy.
connection.execute("DELETE FROM learner_progress")
connection.execute("DELETE FROM reading_sessions")
connection.execute("DELETE FROM users")

connection.commit()
connection.close()

print("Deployment database created successfully!")
print("Original learning_path.db was not changed.")