from flask import (

    Flask,

    render_template,

    request,

    send_from_directory,

    redirect,

    url_for,

    session

)

import sqlite3

import os

from datetime import datetime

# ===================================================

# FLASK APPLICATION

# ===================================================

app = Flask(__name__)

app.secret_key = "learning_path_dashboard_secret_key"

# ===================================================

# DATABASE PATH

# ===================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE = os.path.join(
    BASE_DIR,
    os.environ.get("DATABASE_FILE", "learning_path.db")
)

# ===================================================

# DATABASE CONNECTION

# ===================================================

def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection

# ===================================================

# CREATE USERS TABLE

# ===================================================

def create_users_table():

    connection = get_db_connection()

    connection.execute("""

        CREATE TABLE IF NOT EXISTS users (

            user_id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL

        )

    """)

    connection.commit()

    connection.close()

# ===================================================

# ENSURE READING SESSION COLUMNS

# ===================================================

def ensure_reading_session_columns():

    connection = get_db_connection()

    connection.execute("""

        CREATE TABLE IF NOT EXISTS reading_sessions (

            session_id INTEGER PRIMARY KEY AUTOINCREMENT,

            learner_id INTEGER NOT NULL,

            resource_id INTEGER NOT NULL,

            start_time TEXT NOT NULL,

            end_time TEXT,

            duration_seconds INTEGER DEFAULT 0

        )

    """)

    columns = connection.execute("""

        PRAGMA table_info(reading_sessions)

    """).fetchall()

    column_names = [

        column["name"]

        for column in columns

    ]

    if "end_time" not in column_names:

        connection.execute("""

            ALTER TABLE reading_sessions

            ADD COLUMN end_time TEXT

        """)

    if "duration_seconds" not in column_names:

        connection.execute("""

            ALTER TABLE reading_sessions

            ADD COLUMN duration_seconds INTEGER DEFAULT 0

        """)

    connection.commit()

    connection.close()

# ===================================================

# INITIALIZE DATABASE

# ===================================================

create_users_table()

ensure_reading_session_columns()

# ===================================================

# HOME PAGE

# ===================================================

@app.route("/")

def home():

    return redirect(

        url_for("login")

    )

# ===================================================

# COMMON LOGIN PAGE

# ===================================================

@app.route("/login")

def login():

    return render_template(

        "login.html"

    )

# ===================================================

# TEST DATABASE

# ===================================================

@app.route("/test-db")

def test_database():

    connection = get_db_connection()

    result = connection.execute("""

        SELECT COUNT(*\\\\**) AS count

        FROM users

    """).fetchone()

    connection.close()

    return (

        f"Database connected successfully! "

        f"Users count: {result['count']}"

    )

# ===================================================

# INSTRUCTOR REGISTRATION

# ===================================================

@app.route(

    "/register",

    methods=["GET", "POST"]

)

def register():

    if request.method == "POST":

        name = request.form.get(

            "name",

            ""

        ).strip()

        email = request.form.get(

            "email",

            ""

        ).strip()

        password = request.form.get(

            "password",

            ""

        )

        if not name or not email or not password:

            return render_template(

                "register.html",

                error="Please fill all fields."

            )

        connection = get_db_connection()

        try:

            connection.execute("""

                INSERT INTO users

                (

                    name,

                    email,

                    password,

                    role

                )

                VALUES (?, ?, ?, ?)

            """, (

                name,

                email,

                password,

                "Instructor"

            ))

            connection.commit()

            connection.close()

            return redirect(

                url_for("login")

            )

        except sqlite3.IntegrityError:

            connection.close()

            return render_template(

                "register.html",

                error="This email is already registered."

            )

    return render_template(

        "register.html"

    )

# ===================================================

# INSTRUCTOR LOGIN

# ===================================================

@app.route(

    "/instructor-login",

    methods=["GET", "POST"]

)

def instructor_login():

    if request.method == "POST":

        email = request.form.get(

            "email",

            ""

        ).strip()

        password = request.form.get(

            "password",

            ""

        )

        connection = get_db_connection()

        instructor = connection.execute("""

            SELECT

                user_id,

                name,

                email,

                password

            FROM users

            WHERE email = ?

            AND role = 'Instructor'

        """, (

            email,

        )).fetchone()

        connection.close()

        if instructor and instructor["password"] == password:

            session.pop(

                "learner_id",

                None

            )

            session["instructor_id"] = instructor["user_id"]

            return redirect(

                url_for("instructor_dashboard")

            )

        return render_template(

            "login.html",

            instructor_error="Invalid instructor email or password."

        )

    return render_template(

        "login.html"

    )

# ===================================================

# INSTRUCTOR LOGOUT

# ===================================================

@app.route("/instructor-logout")

def instructor_logout():

    session.pop(

        "instructor_id",

        None

    )

    return redirect(

        url_for("login")

    )

# ===================================================

# INSTRUCTOR DASHBOARD

# ===================================================

@app.route("/instructor-dashboard")

def instructor_dashboard():

    instructor_id = session.get(

        "instructor_id"

    )

    if instructor_id is None:

        return redirect(

            url_for("login")

        )

    connection = get_db_connection()

    instructor = connection.execute("""

        SELECT

            user_id,

            name,

            email

        FROM users

        WHERE user_id = ?

        AND role = 'Instructor'

    """, (

        instructor_id,

    )).fetchone()

    if instructor is None:

        session.pop(

            "instructor_id",

            None

        )

        connection.close()

        return redirect(

            url_for("login")

        )

    connection.close()

    return render_template(

        "instructor_dashboard.html",

        instructor=instructor

    )

# ===================================================

# ENSURE PUBLICATIONS TABLE

# ===================================================

def ensure_publications_table():

    connection = get_db_connection()

    connection.execute("""

        CREATE TABLE IF NOT EXISTS publications (

            publication_id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            authors TEXT NOT NULL,

            year INTEGER,

            url TEXT,

            topic TEXT,

            source TEXT

        )

    """)

    connection.commit()

    connection.close()

ensure_publications_table()

# ===================================================

# ENSURE LEARNING PATH PUBLICATIONS TABLE

# ===================================================

def ensure_learning_path_publications_table():

    connection = get_db_connection()

    connection.execute("""

        CREATE TABLE IF NOT EXISTS learning_path_publications (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            path_id INTEGER NOT NULL,

            publication_id INTEGER NOT NULL,

            UNIQUE(path_id, publication_id)

        )

    """)

    connection.commit()

    connection.close()

ensure_learning_path_publications_table()

# ===================================================

# ACADEMIC PUBLICATIONS

# ===================================================

@app.route("/publications", methods=["GET", "POST"])

def publications():

    instructor_id = session.get("instructor_id")

    if instructor_id is None:

        return redirect(url_for("login"))

    connection = get_db_connection()

    if request.method == "POST":

        title = request.form.get("title", "").strip()

        authors = request.form.get("authors", "").strip()

        year_text = request.form.get("year", "").strip()

        topic = request.form.get("topic", "").strip()

        source = request.form.get("source", "").strip()

        url = request.form.get("url", "").strip()

        if not title or not authors or not year_text or not topic or not source:

            publications_list = connection.execute("""

                SELECT publication_id, title, authors, year, url, topic, source

                FROM publications

                ORDER BY year DESC, publication_id DESC

            """).fetchall()

            connection.close()

            return render_template(

                "publications.html",

                publications=publications_list,

                error="Please fill all required fields."

            )

        try:

            year = int(year_text)

        except ValueError:

            publications_list = connection.execute("""

                SELECT publication_id, title, authors, year, url, topic, source

                FROM publications

                ORDER BY year DESC, publication_id DESC

            """).fetchall()

            connection.close()

            return render_template(

                "publications.html",

                publications=publications_list,

                error="Publication year must be a number."

            )

        connection.execute("""

            INSERT INTO publications

            (title, authors, year, url, topic, source)

            VALUES (?, ?, ?, ?, ?, ?)

        """, (

            title, authors, year, url, topic, source

        ))

        connection.commit()

    publications_list = connection.execute("""

        SELECT publication_id, title, authors, year, url, topic, source

        FROM publications

        ORDER BY year DESC, publication_id DESC

    """).fetchall()

    connection.close()

    return render_template(

        "publications.html",

        publications=publications_list

    )

# ===================================================

# ===================================================

# EDIT ACADEMIC PUBLICATION

# ===================================================

@app.route(

    "/edit-publication/<int:publication_id>",

    methods=["GET", "POST"]

)

def edit_publication(publication_id):

    instructor_id = session.get("instructor_id")

    if instructor_id is None:

        return redirect(url_for("login"))

    connection = get_db_connection()

    publication = connection.execute("""

        SELECT publication_id, title, authors, year, url, topic, source

        FROM publications

        WHERE publication_id = ?

    """, (publication_id,)).fetchone()

    if publication is None:

        connection.close()

        return "Publication not found."

    if request.method == "POST":

        title = request.form.get("title", "").strip()

        authors = request.form.get("authors", "").strip()

        year_text = request.form.get("year", "").strip()

        topic = request.form.get("topic", "").strip()

        source = request.form.get("source", "").strip()

        url = request.form.get("url", "").strip()

        if not title or not authors or not year_text or not topic or not source:

            connection.close()

            return render_template("edit_publication.html", publication=publication, error="Please fill all required fields.")

        try:

            year = int(year_text)

        except ValueError:

            connection.close()

            return render_template("edit_publication.html", publication=publication, error="Publication year must be a number.")

        connection.execute("""

            UPDATE publications

            SET title = ?, authors = ?, year = ?, url = ?, topic = ?, source = ?

            WHERE publication_id = ?

        """, (title, authors, year, url, topic, source, publication_id))

        connection.commit()

        connection.close()

        return redirect(url_for("publications"))

    connection.close()

    return render_template("edit_publication.html", publication=publication)

# LEARNER REGISTRATION

# ===================================================

@app.route(

    "/learner-register",

    methods=["GET", "POST"]

)

def learner_register():

    if request.method == "POST":

        name = request.form.get(

            "name",

            ""

        ).strip()

        email = request.form.get(

            "email",

            ""

        ).strip()

        password = request.form.get(

            "password",

            ""

        )

        if not name or not email or not password:

            return render_template(

                "learner_register.html",

                error="Please fill all fields."

            )

        connection = get_db_connection()

        try:

            connection.execute("""

                INSERT INTO users

                (

                    name,

                    email,

                    password,

                    role

                )

                VALUES (?, ?, ?, ?)

            """, (

                name,

                email,

                password,

                "Learner"

            ))

            connection.commit()

            connection.close()

            return redirect(

                url_for("login")

            )

        except sqlite3.IntegrityError:

            connection.close()

            return render_template(

                "learner_register.html",

                error="This email is already registered."

            )

    return render_template(

        "learner_register.html"

    )

# ===================================================

# LEARNER LOGIN

# ===================================================

@app.route(

    "/learner-login",

    methods=["GET", "POST"]

)

def learner_login():

    if request.method == "POST":

        email = request.form.get(

            "email",

            ""

        ).strip()

        password = request.form.get(

            "password",

            ""

        )

        connection = get_db_connection()

        learner = connection.execute("""

            SELECT

                user_id,

                name,

                email,

                password

            FROM users

            WHERE email = ?

            AND role = 'Learner'

        """, (

            email,

        )).fetchone()

        connection.close()

        if learner and learner["password"] == password:

            session.pop(

                "instructor_id",

                None

            )

            session["learner_id"] = learner["user_id"]

            return redirect(

                url_for("learner_dashboard")

            )

        return render_template(

            "login.html",

            learner_error="Invalid learner email or password."

        )

    return render_template(

        "login.html"

    )

# ===================================================

# LEARNER LOGOUT

# ===================================================

@app.route("/learner-logout")

def learner_logout():

    session.pop(

        "learner_id",

        None

    )

    return redirect(

        url_for("login")

    )

# ===================================================

# CREATE SKILL

# ===================================================

@app.route(

    "/create-skill",

    methods=["GET", "POST"]

)

def create_skill():

    instructor_id = session.get(

        "instructor_id"

    )

    if instructor_id is None:

        return redirect(

            url_for("login")

        )

    if request.method == "POST":

        skill_name = request.form.get(

            "skill_name",

            ""

        ).strip()

        description = request.form.get(

            "description",

            ""

        ).strip()

        if not skill_name:

            return render_template(

                "create_skill.html",

                error="Skill name is required."

            )

        connection = get_db_connection()

        connection.execute("""

            INSERT INTO skills

            (

                skill_name,

                description

            )

            VALUES (?, ?)

        """, (

            skill_name,

            description

        ))

        connection.commit()

        connection.close()

        return "Skill created successfully!"

    return render_template(

        "create_skill.html"

    )

# ===================================================

# CREATE LEARNING PATH

# ===================================================

@app.route(

    "/create-learning-path",

    methods=["GET", "POST"]

)

def create_learning_path():
    instructor_id = session.get("instructor_id")

    if instructor_id is None:
        return redirect(url_for("login"))

    connection = get_db_connection()

    skills = connection.execute("""
        SELECT skill_id, skill_name
        FROM skills
        ORDER BY skill_name
    """).fetchall()

    publications_list = connection.execute("""
        SELECT publication_id, title, authors, year, topic, source, url
        FROM publications
        ORDER BY year DESC, publication_id DESC
    """).fetchall()

    if request.method == "POST":
        skill_id = request.form.get("skill_id")
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        publication_ids = request.form.getlist("publication_ids")

        if not skill_id or not title:
            connection.close()
            return render_template(
                "create_learning_path.html",
                skills=skills,
                publications=publications_list,
                error="Please fill all required fields."
            )

        cursor = connection.execute("""
            INSERT INTO learning_paths
            (
                skill_id,
                title,
                description,
                created_by
            )
            VALUES (?, ?, ?, ?)
        """, (
            skill_id,
            title,
            description,
            instructor_id
        ))

        path_id = cursor.lastrowid

        for publication_id in publication_ids:
            try:
                connection.execute("""
                    INSERT OR IGNORE INTO learning_path_publications
                    (
                        path_id,
                        publication_id
                    )
                    VALUES (?, ?)
                """, (
                    path_id,
                    int(publication_id)
                ))
            except (ValueError, TypeError):
                continue

        connection.commit()
        connection.close()

        return "Learning path created successfully!"

    connection.close()

    return render_template(
        "create_learning_path.html",
        skills=skills,
        publications=publications_list
    )

# ===================================================

# ADD LEARNING RESOURCE

# ===================================================

@app.route(

    "/add-resource",

    methods=["GET", "POST"]

)

def add_resource():

    instructor_id = session.get(

        "instructor_id"

    )

    if instructor_id is None:

        return redirect(

            url_for("login")

        )

    connection = get_db_connection()

    learning_paths = connection.execute("""

        SELECT

            path_id,

            title

        FROM learning_paths

        WHERE created_by = ?

        ORDER BY title

    """, (

        instructor_id,

    )).fetchall()

    if request.method == "POST":

        path_id = request.form.get(

            "path_id"

        )

        title = request.form.get(

            "title",

            ""

        ).strip()

        resource_type = request.form.get(

            "resource_type",

            ""

        ).strip()

        description = request.form.get(

            "description",

            ""

        ).strip()

        url = request.form.get(

            "url",

            ""

        ).strip()

        file_path = None

        # -----------------------------------------------

        # HANDLE FILE UPLOAD

        # -----------------------------------------------

        if "resource_file" in request.files:

            file = request.files[

                "resource_file"

            ]

            if file and file.filename:

                filename = file.filename

                upload_folder = os.path.join(

                    BASE_DIR,

                    "uploads"

                )

                os.makedirs(

                    upload_folder,

                    exist_ok=True

                )

                file_path = os.path.join(

                    upload_folder,

                    filename

                )

                file.save(

                    file_path

                )

        # -----------------------------------------------

        # INSERT RESOURCE

        # -----------------------------------------------

        cursor = connection.execute("""

            INSERT INTO resources

            (

                title,

                resource_type,

                file_path,

                url,

                description

            )

            VALUES (?, ?, ?, ?, ?)

        """, (

            title,

            resource_type,

            file_path,

            url,

            description

        ))

        resource_id = cursor.lastrowid

        # -----------------------------------------------

        # FIND NEXT ORDER

        # -----------------------------------------------

        result = connection.execute("""

            SELECT

                MAX(sequence_order) AS max_order

            FROM learning_path_resources

            WHERE path_id = ?

        """, (

            path_id,

        )).fetchone()

        if result["max_order"] is None:

            sequence_order = 1

        else:

            sequence_order = (

                result["max_order"] + 1

            )

        # -----------------------------------------------

        # LINK RESOURCE TO PATH

        # -----------------------------------------------

        connection.execute("""

            INSERT INTO learning_path_resources

            (

                path_id,

                resource_id,

                sequence_order

            )

            VALUES (?, ?, ?)

        """, (

            path_id,

            resource_id,

            sequence_order

        ))

        connection.commit()

        connection.close()

        return "Learning resource added successfully!"

    connection.close()

    return render_template(

        "add_resource.html",

        learning_paths=learning_paths

    )

# ===================================================

# VIEW LEARNING PATH

# ===================================================

@app.route(

    "/learning-path/<int:path_id>"

)

def view_learning_path(path_id):

    connection = get_db_connection()

    learning_path = connection.execute("""

        SELECT

            lp.path_id,

            lp.title,

            lp.description,

            s.skill_name

        FROM learning_paths lp

        LEFT JOIN skills s

        ON lp.skill_id = s.skill_id

        WHERE lp.path_id = ?

    """, (

        path_id,

    )).fetchone()

    if learning_path is None:

        connection.close()

        return "Learning path not found."

    resources = connection.execute("""

        SELECT

            r.resource_id,

            r.title,

            r.resource_type,

            r.file_path,

            r.url,

            r.description,

            lpr.sequence_order

        FROM learning_path_resources lpr

        JOIN resources r

        ON lpr.resource_id = r.resource_id

        WHERE lpr.path_id = ?

        ORDER BY lpr.sequence_order

    """, (

        path_id,

    )).fetchall()

    connection.close()

    return render_template(

        "learning_path.html",

        learning_path=learning_path,

        resources=resources

    )

# ===================================================

# SERVE UPLOADED RESOURCE

# ===================================================

@app.route(

    "/uploads/<path:filename>"

)

def uploaded_resource(filename):

    upload_folder = os.path.join(

        BASE_DIR,

        "uploads"

    )

    return send_from_directory(

        upload_folder,

        filename

    )

# ===================================================

# LEARNER DASHBOARD

# ===================================================

@app.route("/learner-dashboard")

def learner_dashboard():

    learner_id = session.get(

        "learner_id"

    )

    if learner_id is None:

        return redirect(

            url_for("login")

        )

    selected_path_id = request.args.get(

        "path_id",

        type=int

    )

    connection = get_db_connection()

    # -----------------------------------------------

    # GET LEARNER

    # -----------------------------------------------

    learner = connection.execute("""

        SELECT

            user_id,

            name,

            email

        FROM users

        WHERE user_id = ?

        AND role = 'Learner'

    """, (

        learner_id,

    )).fetchone()

    if learner is None:

        session.pop(

            "learner_id",

            None

        )

        connection.close()

        return redirect(

            url_for("login")

        )

    # -----------------------------------------------

    # GET ALL LEARNING PATHS

    # -----------------------------------------------

    learning_paths = connection.execute("""

        SELECT

            lp.path_id,

            lp.title,

            lp.description,

            s.skill_name

        FROM learning_paths lp

        LEFT JOIN skills s

        ON lp.skill_id = s.skill_id

        ORDER BY lp.path_id

    """).fetchall()

    # -----------------------------------------------

    # SELECT FIRST PATH IF NONE SELECTED

    # -----------------------------------------------

    if selected_path_id is None and learning_paths:

        selected_path_id = learning_paths[0]["path_id"]

    # -----------------------------------------------

    # CHECK SELECTED PATH EXISTS

    # -----------------------------------------------

    selected_path = None

    if selected_path_id is not None:

        selected_path = connection.execute("""

            SELECT

                lp.path_id,

                lp.title,

                lp.description,

                s.skill_name

            FROM learning_paths lp

            LEFT JOIN skills s

            ON lp.skill_id = s.skill_id

            WHERE lp.path_id = ?

        """, (

            selected_path_id,

        )).fetchone()

    # -----------------------------------------------

    # IF INVALID PATH WAS SELECTED

    # -----------------------------------------------

    if selected_path is None and learning_paths:

        selected_path_id = learning_paths[0]["path_id"]

        selected_path = connection.execute("""

            SELECT

                lp.path_id,

                lp.title,

                lp.description,

                s.skill_name

            FROM learning_paths lp

            LEFT JOIN skills s

            ON lp.skill_id = s.skill_id

            WHERE lp.path_id = ?

        """, (

            selected_path_id,

        )).fetchone()

    # -----------------------------------------------

    # GET RESOURCES FOR SELECTED PATH

    # -----------------------------------------------

    resources = []

    if selected_path:

        resources = connection.execute("""

            SELECT

                r.resource_id,

                r.title,

                r.resource_type,

                r.file_path,

                r.url,

                r.description,

                COALESCE(

                    lp.status,

                    'Not Started'

                ) AS status,

                COALESCE(

                    lp.progress_percentage,

                    0

                ) AS progress_percentage

            FROM learning_path_resources lpr

            JOIN resources r

            ON lpr.resource_id = r.resource_id

            LEFT JOIN learner_progress lp

            ON lp.resource_id = r.resource_id

            AND lp.learner_id = ?

            WHERE lpr.path_id = ?

            ORDER BY lpr.sequence_order

        """, (

            learner_id,

            selected_path_id

        )).fetchall()

    # -----------------------------------------------

    # OVERALL PROGRESS

    # -----------------------------------------------

    if resources:

        total_progress = sum(

            resource["progress_percentage"]

            for resource in resources

        )

        overall_progress = round(

            total_progress / len(resources),

            2

        )

    else:

        overall_progress = 0

    # -----------------------------------------------

    # TOTAL LEARNING TIME FOR SELECTED PATH

    # -----------------------------------------------

    if selected_path:

        total_time_result = connection.execute("""

            SELECT

                COALESCE(

                    SUM(rs.duration_seconds),

                    0

                ) AS total_seconds

            FROM reading_sessions rs

            JOIN learning_path_resources lpr

            ON rs.resource_id = lpr.resource_id

            WHERE rs.learner_id = ?

            AND lpr.path_id = ?

            AND rs.duration_seconds > 0

        """, (

            learner_id,

            selected_path_id

        )).fetchone()

    else:

        total_time_result = {

            "total_seconds": 0

        }

    total_seconds = total_time_result[

        "total_seconds"

    ]

    total_learning_minutes = round(

        total_seconds / 60,

        1

    )

    # -----------------------------------------------

    # AVERAGE LEARNING TIME FOR SELECTED PATH

    # -----------------------------------------------

    if selected_path:

        average_time_result = connection.execute("""

            SELECT

                COALESCE(

                    AVG(rs.duration_seconds),

                    0

                ) AS average_seconds

            FROM reading_sessions rs

            JOIN learning_path_resources lpr

            ON rs.resource_id = lpr.resource_id

            WHERE rs.learner_id = ?

            AND lpr.path_id = ?

            AND rs.duration_seconds > 0

        """, (

            learner_id,

            selected_path_id

        )).fetchone()

    else:

        average_time_result = {

            "average_seconds": 0

        }

    average_seconds = average_time_result[

        "average_seconds"

    ]

    average_learning_minutes = round(

        average_seconds / 60,

        1

    )

    # -----------------------------------------------

    # COMPLETED COUNT FOR SELECTED PATH

    # -----------------------------------------------

    completed_count = sum(

        1

        for resource in resources

        if resource["status"] == "Completed"

    )

    # -----------------------------------------------

    # IN-PROGRESS COUNT FOR SELECTED PATH

    # -----------------------------------------------

    in_progress_count = sum(

        1

        for resource in resources

        if resource["status"] == "In Progress"

    )

    connection.close()

    return render_template(

        "learner_dashboard.html",

        learner=learner,

        learning_paths=learning_paths,

        selected_path=selected_path,

        selected_path_id=selected_path_id,

        resources=resources,

        overall_progress=overall_progress,

        total_learning_minutes=total_learning_minutes,

        average_learning_minutes=average_learning_minutes,

        completed_count=completed_count,

        in_progress_count=in_progress_count

    )

# ===================================================

# COMPLETE LEARNING RESOURCE

# ===================================================

@app.route(

    "/complete-resource/<int:resource_id>",

    methods=["POST"]

)

def complete_resource(resource_id):

    learner_id = session.get(

        "learner_id"

    )

    if learner_id is None:

        return redirect(

            url_for("login")

        )

    connection = get_db_connection()

    # -----------------------------------------------

    # FIND PATH FOR RESOURCE

    # -----------------------------------------------

    path_result = connection.execute("""

        SELECT

            path_id

        FROM learning_path_resources

        WHERE resource_id = ?

        ORDER BY path_id

        LIMIT 1

    """, (

        resource_id,

    )).fetchone()

    path_id = (

        path_result["path_id"]

        if path_result

        else None

    )

    # -----------------------------------------------

    # CHECK LEARNER

    # -----------------------------------------------

    learner = connection.execute("""

        SELECT

            user_id

        FROM users

        WHERE user_id = ?

        AND role = 'Learner'

    """, (

        learner_id,

    )).fetchone()

    if learner is None:

        session.pop(

            "learner_id",

            None

        )

        connection.close()

        return redirect(

            url_for("login")

        )

    # -----------------------------------------------

    # CHECK RESOURCE

    # -----------------------------------------------

    resource = connection.execute("""

        SELECT

            resource_id

        FROM resources

        WHERE resource_id = ?

    """, (

        resource_id,

    )).fetchone()

    if resource is None:

        connection.close()

        return "Learning resource not found."

    # -----------------------------------------------

    # CHECK EXISTING PROGRESS

    # -----------------------------------------------

    existing_progress = connection.execute("""

        SELECT

            progress_id

        FROM learner_progress

        WHERE learner_id = ?

        AND resource_id = ?

    """, (

        learner_id,

        resource_id

    )).fetchone()

    completed_at = datetime.now().strftime(

        "%Y-%m-%d %H:%M:%S"

    )

    if existing_progress:

        connection.execute("""

            UPDATE learner_progress

            SET

                status = ?,

                progress_percentage = ?,

                completed_at = ?

            WHERE progress_id = ?

        """, (

            "Completed",

            100,

            completed_at,

            existing_progress["progress_id"]

        ))

    else:

        connection.execute("""

            INSERT INTO learner_progress

            (

                learner_id,

                resource_id,

                status,

                progress_percentage,

                completed_at

            )

            VALUES (?, ?, ?, ?, ?)

        """, (

            learner_id,

            resource_id,

            "Completed",

            100,

            completed_at

        ))

    # -----------------------------------------------

    # CLOSE ACTIVE READING SESSION

    # -----------------------------------------------

    active_session = connection.execute("""

        SELECT

            session_id,

            start_time

        FROM reading_sessions

        WHERE learner_id = ?

        AND resource_id = ?

        AND duration_seconds = 0

        ORDER BY session_id DESC

        LIMIT 1

    """, (

        learner_id,

        resource_id

    )).fetchone()

    if active_session:

        end_time = datetime.now()

        start_time = datetime.strptime(

            active_session["start_time"],

            "%Y-%m-%d %H:%M:%S"

        )

        duration_seconds = int(

            (end_time - start_time).total_seconds()

        )

        if duration_seconds < 0:

            duration_seconds = 0

        connection.execute("""

            UPDATE reading_sessions

            SET

                end_time = ?,

                duration_seconds = ?

            WHERE session_id = ?

        """, (

            end_time.strftime(

                "%Y-%m-%d %H:%M:%S"

            ),

            duration_seconds,

            active_session["session_id"]

        ))

    connection.commit()

    connection.close()

    # -----------------------------------------------

    # RETURN TO SAME LEARNING PATH

    # -----------------------------------------------

    if path_id is not None:

        return redirect(

            url_for(

                "learner_dashboard",

                path_id=path_id

            )

        )

    return redirect(

        url_for("learner_dashboard")

    )

# ===================================================

# START LEARNING SESSION

# ===================================================

@app.route(

    "/start-learning/<int:resource_id>"

)

def start_learning(resource_id):

    learner_id = session.get(

        "learner_id"

    )

    if learner_id is None:

        return redirect(

            url_for("login")

        )

    connection = get_db_connection()

    # -----------------------------------------------

    # CHECK LEARNER

    # -----------------------------------------------

    learner = connection.execute("""

        SELECT

            user_id

        FROM users

        WHERE user_id = ?

        AND role = 'Learner'

    """, (

        learner_id,

    )).fetchone()

    if learner is None:

        session.pop(

            "learner_id",

            None

        )

        connection.close()

        return redirect(

            url_for("login")

        )

    # -----------------------------------------------

    # GET RESOURCE

    # -----------------------------------------------

    resource = connection.execute("""

        SELECT

            resource_id,

            file_path,

            url

        FROM resources

        WHERE resource_id = ?

    """, (

        resource_id,

    )).fetchone()

    if resource is None:

        connection.close()

        return "Learning resource not found."

    # -----------------------------------------------

    # CHECK ACTIVE SESSION

    # -----------------------------------------------

    active_session = connection.execute("""

        SELECT

            session_id

        FROM reading_sessions

        WHERE learner_id = ?

        AND resource_id = ?

        AND duration_seconds = 0

        ORDER BY session_id DESC

        LIMIT 1

    """, (

        learner_id,

        resource_id

    )).fetchone()

    # -----------------------------------------------

    # CREATE NEW READING SESSION

    # -----------------------------------------------

    if active_session is None:

        start_time = datetime.now().strftime(

            "%Y-%m-%d %H:%M:%S"

        )

        connection.execute("""

            INSERT INTO reading_sessions

            (

                learner_id,

                resource_id,

                start_time,

                end_time,

                duration_seconds

            )

            VALUES (?, ?, ?, ?, ?)

        """, (

            learner_id,

            resource_id,

            start_time,

            None,

            0

        ))

    # -----------------------------------------------

    # UPDATE RESOURCE STATUS

    # -----------------------------------------------

    existing_progress = connection.execute("""

        SELECT

            progress_id,

            status

        FROM learner_progress

        WHERE learner_id = ?

        AND resource_id = ?

    """, (

        learner_id,

        resource_id

    )).fetchone()

    if existing_progress:

        if existing_progress["status"] != "Completed":

            connection.execute("""

                UPDATE learner_progress

                SET

                    status = ?,

                    progress_percentage = ?

                WHERE progress_id = ?

            """, (

                "In Progress",

                50,

                existing_progress["progress_id"]

            ))

    else:

        connection.execute("""

            INSERT INTO learner_progress

            (

                learner_id,

                resource_id,

                status,

                progress_percentage

            )

            VALUES (?, ?, ?, ?)

        """, (

            learner_id,

            resource_id,

            "In Progress",

            50

        ))

    connection.commit()

    connection.close()

    # -----------------------------------------------

    # OPEN UPLOADED FILE

    # -----------------------------------------------

    if resource["file_path"]:

        filename = os.path.basename(

            resource["file_path"]

        )

        return redirect(

            url_for(

                "uploaded_resource",

                filename=filename

            )

        )

    # -----------------------------------------------

    # OPEN ONLINE RESOURCE

    # -----------------------------------------------

    elif resource["url"]:

        return redirect(

            resource["url"]

        )

    return "Learning resource has no file or URL."

# ===================================================

# FINISH LEARNING SESSION

# ===================================================

@app.route(

    "/finish-learning/<int:resource_id>",

    methods=["POST"]

)

def finish_learning(resource_id):

    learner_id = session.get(

        "learner_id"

    )

    if learner_id is None:

        return redirect(

            url_for("login")

        )

    connection = get_db_connection()

    # -----------------------------------------------

    # FIND PATH FOR RESOURCE

    # -----------------------------------------------

    path_result = connection.execute("""

        SELECT

            path_id

        FROM learning_path_resources

        WHERE resource_id = ?

        ORDER BY path_id

        LIMIT 1

    """, (

        resource_id,

    )).fetchone()

    path_id = (

        path_result["path_id"]

        if path_result

        else None

    )

    # -----------------------------------------------

    # CHECK LEARNER

    # -----------------------------------------------

    learner = connection.execute("""

        SELECT

            user_id

        FROM users

        WHERE user_id = ?

        AND role = 'Learner'

    """, (

        learner_id,

    )).fetchone()

    if learner is None:

        session.pop(

            "learner_id",

            None

        )

        connection.close()

        return redirect(

            url_for("login")

        )

    # -----------------------------------------------

    # FIND ACTIVE SESSION

    # -----------------------------------------------

    reading_session = connection.execute("""

        SELECT

            session_id,

            start_time

        FROM reading_sessions

        WHERE learner_id = ?

        AND resource_id = ?

        AND duration_seconds = 0

        ORDER BY session_id DESC

        LIMIT 1

    """, (

        learner_id,

        resource_id

    )).fetchone()

    # -----------------------------------------------

    # NO ACTIVE SESSION

    # -----------------------------------------------

    if reading_session is None:

        connection.close()

        if path_id is not None:

            return redirect(

                url_for(

                    "learner_dashboard",

                    path_id=path_id

                )

            )

        return redirect(

            url_for("learner_dashboard")

        )

    # -----------------------------------------------

    # CALCULATE DURATION

    # -----------------------------------------------

    end_time = datetime.now()

    start_time = datetime.strptime(

        reading_session["start_time"],

        "%Y-%m-%d %H:%M:%S"

    )

    duration_seconds = int(

        (end_time - start_time).total_seconds()

    )

    if duration_seconds < 0:

        duration_seconds = 0

    end_time_string = end_time.strftime(

        "%Y-%m-%d %H:%M:%S"

    )

    # -----------------------------------------------

    # UPDATE READING SESSION

    # -----------------------------------------------

    connection.execute("""

        UPDATE reading_sessions

        SET

            end_time = ?,

            duration_seconds = ?

        WHERE session_id = ?

    """, (

        end_time_string,

        duration_seconds,

        reading_session["session_id"]

    ))

    # -----------------------------------------------

    # UPDATE PROGRESS

    # -----------------------------------------------

    existing_progress = connection.execute("""

        SELECT

            progress_id,

            status

        FROM learner_progress

        WHERE learner_id = ?

        AND resource_id = ?

    """, (

        learner_id,

        resource_id

    )).fetchone()

    if existing_progress:

        if existing_progress["status"] != "Completed":

            connection.execute("""

                UPDATE learner_progress

                SET

                    status = ?,

                    progress_percentage = ?

                WHERE progress_id = ?

            """, (

                "In Progress",

                50,

                existing_progress["progress_id"]

            ))

    else:

        connection.execute("""

            INSERT INTO learner_progress

            (

                learner_id,

                resource_id,

                status,

                progress_percentage

            )

            VALUES (?, ?, ?, ?)

        """, (

            learner_id,

            resource_id,

            "In Progress",

            50

        ))

    connection.commit()

    connection.close()

    # -----------------------------------------------

    # RETURN TO SAME LEARNING PATH

    # -----------------------------------------------

    if path_id is not None:

        return redirect(

            url_for(

                "learner_dashboard",

                path_id=path_id

            )

        )

    return redirect(

        url_for("learner_dashboard")

    )

# ===================================================

# RUN APPLICATION

# ===================================================

if __name__ == "__main__":

    app.run(

        debug=True

    )
