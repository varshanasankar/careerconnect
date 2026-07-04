import os
import re
import sys
import zipfile
from collections import Counter
from xml.etree import ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from flask import Flask, render_template, session, request, redirect, url_for, flash
    from config import Config
    from database_module import mysql
    from werkzeug.utils import secure_filename
    from werkzeug.security import generate_password_hash, check_password_hash
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure Flask, config, and database modules are installed and accessible.")
    sys.exit(1)

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
except ImportError:
    pdfminer_extract_text = None

try:
    import fitz  # PyMuPDF — most reliable for complex/scanned PDFs
except ImportError:
    fitz = None

app = Flask(__name__)

app.config.from_object(Config)
app.secret_key = app.config.get("SECRET_KEY")

mysql.init_app(app)

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
STOPWORDS = {
    "and", "or", "the", "a", "an", "in", "on", "for", "with", "to",
    "of", "at", "by", "from", "is", "are", "as", "this", "that",
    "be", "have", "has", "had", "will", "can", "also", "other",
    "skills", "experience", "work", "job", "role", "using",
    "background", "project", "projects", "team", "based", "years",
    "year", "management", "development", "customer", "service", "support",
    "strong", "good", "able", "including",
}

# Single authoritative job data — used by all routes
JOB_SAMPLE_DATA = [
    {
        "id": 1,
        "title": "Python Developer",
        "company_name": "Google",
        "location": "Mountain View, CA",
        "salary": "$120k - $140k",
        "experience": "2-4 years",
        "category": "IT",
        "description": "Build backend services and APIs using Python.",
    },
    {
        "id": 2,
        "title": "Frontend Developer",
        "company_name": "Microsoft",
        "location": "Redmond, WA",
        "salary": "$110k - $130k",
        "experience": "2-4 years",
        "category": "IT",
        "description": "Create responsive UI components with React.",
    },
    {
        "id": 3,
        "title": "Data Analyst",
        "company_name": "Amazon",
        "location": "Seattle, WA",
        "salary": "$95k - $115k",
        "experience": "1-3 years",
        "category": "Finance",
        "description": "Analyze business metrics and build dashboards.",
    },
    {
        "id": 4,
        "title": "Product Designer",
        "company_name": "Spotify",
        "location": "New York, NY",
        "salary": "$100k - $125k",
        "experience": "2-5 years",
        "category": "Design",
        "description": "Create delightful, user-first product experiences.",
    },
    {
        "id": 5,
        "title": "DevOps Engineer",
        "company_name": "Netflix",
        "location": "Los Gatos, CA",
        "salary": "$130k - $160k",
        "experience": "3-6 years",
        "category": "IT",
        "description": "Manage CI/CD pipelines and cloud infrastructure at scale.",
    },
    {
        "id": 6,
        "title": "Marketing Manager",
        "company_name": "HubSpot",
        "location": "Boston, MA",
        "salary": "$90k - $110k",
        "experience": "3-5 years",
        "category": "Marketing",
        "description": "Lead growth campaigns and digital marketing strategy.",
    },
]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_sample_jobs():
    return JOB_SAMPLE_DATA


def extract_text_from_pdf(filepath):
    """Try PyMuPDF → pdfplumber → pdfminer in order of reliability."""
    # 1. PyMuPDF (handles most PDFs including complex layouts)
    if fitz:
        try:
            doc = fitz.open(filepath)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            if text.strip():
                return text
        except Exception:
            pass

    # 2. pdfplumber fallback
    if pdfplumber:
        try:
            text_parts = []
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    content = page.extract_text()
                    if content:
                        text_parts.append(content)
            result = "\n".join(text_parts)
            if result.strip():
                return result
        except Exception:
            pass

    # 3. pdfminer fallback
    if pdfminer_extract_text:
        try:
            return pdfminer_extract_text(filepath) or ""
        except Exception:
            pass

    return ""


def extract_text_from_docx(filepath):
    try:
        with zipfile.ZipFile(filepath) as docx_file:
            xml_content = docx_file.read("word/document.xml")
            root = ET.fromstring(xml_content)
            texts = [node.text for node in root.iter() if node.tag.endswith("}t") and node.text]
            return " ".join(texts)
    except Exception:
        return ""


def extract_resume_text(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(filepath)
    if ext == ".docx":
        return extract_text_from_docx(filepath)
    return ""


def extract_keywords_from_text(text, top_n=20):
    text = text.lower()
    tokens = re.findall(r"\b[a-z0-9+\-.]{2,}\b", text)
    filtered = [token for token in tokens if token not in STOPWORDS and not token.isdigit()]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(top_n)]


def score_job_match(job, keywords):
    haystack = " ".join([
        job["title"],
        job["company_name"],
        job["description"],
        job["location"],
        job["category"],
    ]).lower()
    return sum(haystack.count(keyword.lower()) for keyword in keywords)


def match_jobs_by_keywords(keywords, jobs):
    scored = []
    for job in jobs:
        score = score_job_match(job, keywords)
        if score > 0:
            scored.append((score, job))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [job for _, job in scored]


def get_resume_path(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT resume_path FROM resumes WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    return row["resume_path"] if row else None


def get_user_by_email(email):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()
    return user


# Test DB connection on startup and print status
try:
    with app.app_context():
        conn = mysql.connection
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
    print("Database connected successfully")
except Exception as e:
    print("Database connection failed:", e)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("seekerdashboard.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email)
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["fullname"] or user["email"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not fullname or not email or not password:
            flash("Please fill in all required fields.")
            return render_template("register.html")

        if get_user_by_email(email):
            flash("This email is already registered.")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)
        cur = mysql.connection.cursor()
        cur.execute(
            """
            INSERT INTO users (fullname, email, password)
            VALUES (%s, %s, %s)
            """,
            (fullname, email, hashed_password),
        )
        mysql.connection.commit()
        cur.close()

        user = get_user_by_email(email)
        session["user_id"] = user["id"]
        session["name"] = user["fullname"] or user["email"]
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/jobs")
def jobs():
    keyword = request.args.get("keyword", "").strip().lower()
    location = request.args.get("location", "").strip().lower()
    category = request.args.get("category", "").strip()

    filtered_jobs = []
    for job in get_sample_jobs():
        matches_keyword = (
            not keyword
            or keyword in job["title"].lower()
            or keyword in job["company_name"].lower()
            or keyword in job["description"].lower()
        )
        matches_location = not location or location in job["location"].lower()
        matches_category = not category or category.lower() == job["category"].lower()
        if matches_keyword and matches_location and matches_category:
            filtered_jobs.append(job)

    return render_template(
        "jobs.html",
        jobs=filtered_jobs,
        keyword=request.args.get("keyword", ""),
        location=request.args.get("location", ""),
        category=category,
    )


@app.route("/apply-job/<int:job_id>", methods=["POST"])
def apply_job(job_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    # prevent duplicate applications
    cur.execute("SELECT id FROM applications WHERE user_id=%s AND job_id=%s", (session["user_id"], job_id))
    if cur.fetchone():
        flash("You have already applied to this job.")
        cur.close()
        return redirect(url_for("jobs"))

    cur.execute(
        "INSERT INTO applications (user_id, job_id, status) VALUES (%s, %s, %s)",
        (session["user_id"], job_id, "applied"),
    )
    mysql.connection.commit()
    cur.close()
    flash("Application submitted successfully.")
    return redirect(url_for("jobs"))


@app.route("/save-job/<int:job_id>", methods=["POST"])
def save_job(job_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    cur = mysql.connection.cursor()
    # avoid duplicates
    cur.execute("SELECT id FROM saved_jobs WHERE user_id=%s AND job_id=%s", (session["user_id"], job_id))
    if cur.fetchone():
        flash("Job already in your saved list.")
        cur.close()
        return redirect(url_for("jobs"))

    cur.execute("INSERT INTO saved_jobs (user_id, job_id) VALUES (%s, %s)", (session["user_id"], job_id))
    mysql.connection.commit()
    cur.close()
    flash("Job saved to your list.")
    return redirect(url_for("jobs"))


@app.route("/saved-jobs")
def saved_jobs():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT job_id FROM saved_jobs WHERE user_id=%s ORDER BY saved_at DESC",
        (session["user_id"],),
    )
    rows = cur.fetchall()
    cur.close()

    # Match saved job_ids against the in-memory sample data
    saved_ids = {row["job_id"] for row in rows}
    jobs_map = {job["id"]: job for job in get_sample_jobs()}
    saved_job_list = [jobs_map[jid] for jid in saved_ids if jid in jobs_map]

    return render_template("saved_jobs.html", jobs=saved_job_list)


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/recommendations")
def recommendations():
    if "user_id" not in session:
        return redirect(url_for("login"))

    resume_path = get_resume_path(session["user_id"])
    keywords = []
    recommended_jobs = []
    extraction_failed = False

    if resume_path:
        resume_local_path = os.path.join(app.root_path, "static", *resume_path.split("/"))
        resume_text = extract_resume_text(resume_local_path)
        if resume_text:
            keywords = extract_keywords_from_text(resume_text)
            recommended_jobs = match_jobs_by_keywords(keywords, get_sample_jobs())
        else:
            extraction_failed = True

    return render_template(
        "recommendations.html",
        resume=resume_path,
        keywords=keywords,
        jobs=recommended_jobs,
        extraction_failed=extraction_failed,
    )


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()
        skills = request.form.get("skills", "").strip()
        education = request.form.get("education", "").strip()
        experience = request.form.get("experience", "").strip()

        cur.execute(
            """
            UPDATE users
            SET
                fullname=%s,
                phone=%s,
                location=%s,
                skills=%s,
                education=%s,
                experience=%s
            WHERE id=%s
            """,
            (
                fullname,
                phone,
                location,
                skills,
                education,
                experience,
                session["user_id"],
            ),
        )
        mysql.connection.commit()
        cur.close()
        flash("Profile updated successfully.")
        return redirect(url_for("profile"))

    cur.execute(
        """
        SELECT *
        FROM users
        WHERE id=%s
        """,
        (session["user_id"],),
    )
    user = cur.fetchone()
    cur.close()

    return render_template("profile.html", user=user)


@app.route("/resume", methods=["GET", "POST"])
def resume():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    if request.method == "POST":
        file = request.files.get("resume")
        if not file or not file.filename:
            flash("Please select a file before uploading.")
            return redirect(url_for("resume"))

        if not allowed_file(file.filename):
            flash("Invalid file type. Please upload a PDF, DOC, or DOCX file.")
            return redirect(url_for("resume"))

        filename = secure_filename(file.filename)
        # Always resolve to an absolute path so file.save() works regardless of CWD
        upload_folder = os.path.join(app.root_path, "static", "uploads", "resumes")
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # db_path is relative to static/ — matches url_for('static', filename=...)
        db_path = "uploads/resumes/" + filename

        cur.execute(
            """
            SELECT *
            FROM resumes
            WHERE user_id=%s
            """,
            (session["user_id"],),
        )
        old = cur.fetchone()

        if old:
            cur.execute(
                """
                UPDATE resumes
                SET resume_path=%s
                WHERE user_id=%s
                """,
                (db_path, session["user_id"]),
            )
        else:
            cur.execute(
                """
                INSERT INTO resumes
                (user_id, resume_path)
                VALUES(%s, %s)
                """,
                (session["user_id"], db_path),
            )
        mysql.connection.commit()
        cur.close()
        flash("Resume uploaded successfully! ✅")
        return redirect(url_for("resume"))

    cur.execute(
        """
        SELECT resume_path
        FROM resumes
        WHERE user_id=%s
        """,
        (session["user_id"],),
    )
    resume_row = cur.fetchone()
    cur.close()

    return render_template(
        "resume_upload.html",
        resume=resume_row["resume_path"] if resume_row else None,
    )


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    user_id = session["user_id"]

    if request.method == "POST":
        # Notification toggles (checkbox = present in form only when checked)
        notif_job_alerts    = 1 if request.form.get("notif_job_alerts") else 0
        notif_app_status    = 1 if request.form.get("notif_app_status") else 0
        notif_weekly_digest = 1 if request.form.get("notif_weekly_digest") else 0
        notif_profile_views = 1 if request.form.get("notif_profile_views") else 0

        # Job preferences
        pref_category   = request.form.get("pref_category", "").strip()
        pref_location   = request.form.get("pref_location", "").strip()
        pref_salary     = request.form.get("pref_salary", "").strip()
        pref_experience = request.form.get("pref_experience", "").strip()
        pref_job_type   = request.form.get("pref_job_type", "").strip()

        # Upsert into user_settings
        cur.execute("SELECT id FROM user_settings WHERE user_id=%s", (user_id,))
        exists = cur.fetchone()

        if exists:
            cur.execute(
                """
                UPDATE user_settings
                SET notif_job_alerts=%s, notif_app_status=%s,
                    notif_weekly_digest=%s, notif_profile_views=%s,
                    pref_category=%s, pref_location=%s,
                    pref_salary=%s, pref_experience=%s, pref_job_type=%s
                WHERE user_id=%s
                """,
                (notif_job_alerts, notif_app_status, notif_weekly_digest,
                 notif_profile_views, pref_category, pref_location,
                 pref_salary, pref_experience, pref_job_type, user_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO user_settings
                (user_id, notif_job_alerts, notif_app_status, notif_weekly_digest,
                 notif_profile_views, pref_category, pref_location,
                 pref_salary, pref_experience, pref_job_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, notif_job_alerts, notif_app_status, notif_weekly_digest,
                 notif_profile_views, pref_category, pref_location,
                 pref_salary, pref_experience, pref_job_type),
            )
        mysql.connection.commit()
        cur.close()
        flash("Settings saved successfully! ✅")
        return redirect(url_for("settings"))

    # GET — load current settings
    cur.execute("SELECT * FROM user_settings WHERE user_id=%s", (user_id,))
    user_settings = cur.fetchone()
    cur.close()

    return render_template("settings.html", settings=user_settings)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
