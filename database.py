import sqlite3
import os

# Always use the database inside the backend folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "learning_path.db")


def create_database():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    # ---------------------------------------------------
    # USERS
    # ---------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # ---------------------------------------------------
    # SKILLS
    # ---------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL,
            description TEXT
        )
    """)

    # ---------------------------------------------------
    # LEARNING PATHS
    # ---------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_paths (
            path_id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            created_by INTEGER NOT NULL,
            FOREIGN KEY (skill_id) REFERENCES skills(skill_id),
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        )
    """)

    # ---------------------------------------------------
    # RESOURCES
    # ---------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            file_path TEXT,
            url TEXT,
            description TEXT
        )
    """)

    # ---------------------------------------------------
    # LEARNING PATH RESOURCES
    # ---------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_path_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path_id INTEGER NOT NULL,
            resource_id INTEGER NOT NULL,
            sequence_order INTEGER NOT NULL,
            FOREIGN KEY (path_id) REFERENCES learning_paths(path_id),
            FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
        )
    """)

    # ---------------------------------------------------
    # PUBLICATIONS
    # ---------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS publications (
            publication_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            authors TEXT,
            year INTEGER,
            url TEXT,
            topic TEXT,
            source TEXT
        )
    """)

    # ---------------------------------------------------
    # LEARNER PROGRESS
    # ---------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learner_progress (
            progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id INTEGER NOT NULL,
            resource_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Not Started',
            progress_percentage REAL DEFAULT 0,
            completed_at TEXT,
            FOREIGN KEY (learner_id) REFERENCES users(user_id),
            FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
        )
    """)

    # ---------------------------------------------------
    # READING SESSIONS
    # ---------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reading_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id INTEGER NOT NULL,
            resource_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration_seconds INTEGER DEFAULT 0,
            FOREIGN KEY (learner_id) REFERENCES users(user_id),
            FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
        )
    """)

    connection.commit()
    connection.close()

    print("All database tables created successfully!")


if __name__ == "__main__":
    create_database()