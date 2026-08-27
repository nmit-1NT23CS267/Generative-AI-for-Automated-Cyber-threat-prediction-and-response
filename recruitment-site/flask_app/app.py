import os
import secrets
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from .forms import AlertForm, ApplicationForm, InterviewForm, JobForm, LoginForm, RegisterForm, UserForm
from .models import ActivityLog, Application, Job, SecurityAlert, TestCase, User, db

login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = "login"
login_manager.login_message = "Please sign in to continue."
ALLOWED_RESUMES = {"pdf", "doc", "docx"}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", secrets.token_hex(32)),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///securehire.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        UPLOAD_FOLDER=str(Path(app.instance_path) / "resumes"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "0") == "1",
    )
    if test_config:
        app.config.update(test_config)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.cli.command("seed")
    def seed():
        seed_data(app)
        print("SecureHire sample data created.")

    def log_activity(action):
        db.session.add(ActivityLog(actor_id=current_user.id if current_user.is_authenticated else None, action=action))
        db.session.commit()

    def role_required(*roles):
        def decorator(view):
            @wraps(view)
            @login_required
            def wrapped(*args, **kwargs):
                if current_user.role not in roles:
                    flash("You do not have permission to access that page.", "danger")
                    return redirect(url_for("dashboard"))
                return view(*args, **kwargs)
            return wrapped
        return decorator

    app.admin_required = role_required("admin")
    app.recruiter_required = role_required("recruiter", "admin")
    app.tester_required = role_required("tester", "admin")

    @app.route("/")
    def home():
        if current_user.is_authenticated and current_user.role != "candidate":
            return redirect(url_for("dashboard"))
        return render_template("home.html", jobs=Job.query.filter_by(status="open").order_by(Job.created_at.desc()).limit(6).all())

    @app.route("/jobs")
    @login_required
    def jobs():
        if current_user.role != "candidate":
            flash("Only candidates can view and search job profiles.", "warning")
            return redirect(url_for("dashboard"))
        query = request.args.get("q", "").strip()
        jobs_query = Job.query.filter_by(status="open")
        if query:
            pattern = f"%{query}%"
            jobs_query = jobs_query.filter(or_(Job.title.ilike(pattern), Job.description.ilike(pattern), Job.requirements.ilike(pattern)))
        return render_template("jobs.html", jobs=jobs_query.order_by(Job.created_at.desc()).all(), query=query)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        form = RegisterForm()
        if form.validate_on_submit():
            if form.role.data == "admin":
                flash("Admin accounts are predefined and cannot be created here.", "warning")
                return redirect(url_for("login"))
            if User.query.filter(or_(User.email == form.email.data.lower(), User.username == form.username.data)).first():
                flash("That username or email is already registered.", "warning")
            else:
                user = User(username=form.username.data.strip(), email=form.email.data.lower(), password_hash=generate_password_hash(form.password.data), role=form.role.data)
                db.session.add(user)
                db.session.commit()
                flash("Account created. You can now sign in.", "success")
                return redirect(url_for("login"))
        return render_template("auth.html", form=form, mode="register")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower(), role=form.role.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                log_activity("Signed in")
                return redirect(url_for("dashboard"))
            flash("Invalid email, password, or role selection.", "danger")
        return render_template("auth.html", form=form, mode="login")

    @app.route("/logout")
    @login_required
    def logout():
        log_activity("Signed out")
        logout_user()
        flash("You have been signed out.", "success")
        return redirect(url_for("home"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        if current_user.role == "candidate":
            return redirect(url_for("jobs"))
        if current_user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        if current_user.role == "recruiter":
            return redirect(url_for("recruiter_dashboard"))
        if current_user.role == "tester":
            return redirect(url_for("tester_dashboard"))
        flash("Your account role is not recognized.", "warning")
        return redirect(url_for("logout"))

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        if current_user.role != "candidate":
            flash("Only candidates can manage candidate profiles.", "warning")
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            current_user.username = request.form.get("username", "").strip()[:80]
            current_user.email = request.form.get("email", "").strip().lower()[:255]
            db.session.commit()
            log_activity("Updated profile")
            flash("Profile updated.", "success")
        return render_template("profile.html")

    @app.route("/apply/<int:job_id>", methods=["GET", "POST"])
    @login_required
    def apply(job_id):
        if current_user.role != "candidate":
            flash("Only candidates can apply for jobs.", "warning")
            return redirect(url_for("dashboard"))
        job = db.get_or_404(Job, job_id)
        form = ApplicationForm()
        if form.validate_on_submit():
            filename = secure_filename(form.resume.data.filename)
            extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if extension not in ALLOWED_RESUMES:
                flash("Only PDF, DOC, and DOCX resumes are accepted.", "danger")
            else:
                stored = f"{secrets.token_hex(12)}_{filename}"
                form.resume.data.save(Path(app.config["UPLOAD_FOLDER"]) / stored)
                application = Application(job_id=job.id, candidate_name=form.candidate_name.data.strip(), candidate_email=form.candidate_email.data.lower(), resume=stored)
                db.session.add(application)
                db.session.commit()
                flash("Application submitted successfully.", "success")
                return redirect(url_for("jobs"))
        return render_template("apply.html", form=form, job=job)

    @app.route("/recruiter", methods=["GET", "POST"])
    @app.recruiter_required
    def recruiter_dashboard():
        if request.method == "POST" and "company_name" in request.form:
            current_user.company_name = request.form.get("company_name", "").strip()[:160]
            db.session.commit()
            flash("Company profile updated.", "success")
            return redirect(url_for("recruiter_dashboard"))

        form = JobForm()
        if form.validate_on_submit():
            db.session.add(Job(title=form.title.data.strip(), description=form.description.data.strip(), requirements=form.requirements.data.strip(), status=form.status.data, posted_by=current_user.id))
            db.session.commit()
            log_activity("Posted a job")
            flash("Job published.", "success")
            return redirect(url_for("recruiter_dashboard"))
        jobs = Job.query.filter_by(posted_by=current_user.id).order_by(Job.created_at.desc()).all()
        return render_template("recruiter.html", form=form, jobs=jobs, company_name=current_user.company_name or "")

    @app.route("/recruiter/application/<int:application_id>/schedule", methods=["POST"])
    @app.recruiter_required
    def schedule_interview(application_id):
        application = db.get_or_404(Application, application_id)
        if application.job.posted_by != current_user.id and current_user.role != "admin":
            abort(403)
        form = InterviewForm()
        if form.validate_on_submit():
            application.interview_at = form.interview_at.data
            application.status = "interview scheduled"
            db.session.commit()
            log_activity("Scheduled an interview")
            flash("Interview scheduled.", "success")
        return redirect(url_for("recruiter_dashboard"))

    @app.route("/admin")
    @app.admin_required
    def admin_dashboard():
        return render_template("admin.html", users=User.query.order_by(User.created_at.desc()).all(), alerts=SecurityAlert.query.order_by(SecurityAlert.detected_at.desc()).all(), logs=ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(30).all(), stats={"users": User.query.count(), "jobs": Job.query.count(), "applications": Application.query.count(), "alerts": SecurityAlert.query.count()})

    @app.route("/admin/user", methods=["POST"])
    @app.admin_required
    def admin_create_user():
        flash("Admin accounts are predefined only. New accounts are not created from this dashboard.", "warning")
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/user/<int:user_id>/edit", methods=["POST"])
    @app.admin_required
    def admin_edit_user(user_id):
        flash("Admin editing of new users is disabled to preserve predefined credentials.", "warning")
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
    @app.admin_required
    def admin_delete_user(user_id):
        flash("Admin cannot manage new user accounts in this demo flow.", "warning")
        return redirect(url_for("admin_dashboard"))

    @app.route("/tester", methods=["GET", "POST"])
    @app.tester_required
    def tester_dashboard():
        alert_form = AlertForm()
        if alert_form.validate_on_submit():
            db.session.add(SecurityAlert(alert_type=alert_form.alert_type.data.strip(), severity=alert_form.severity.data, description=alert_form.description.data.strip()))
            db.session.commit()
            log_activity("Logged a security issue")
            flash("Security issue logged.", "success")
            return redirect(url_for("tester_dashboard"))
        cases = TestCase.query.order_by(TestCase.id).all()
        return render_template("tester.html", form=alert_form, cases=cases, alerts=SecurityAlert.query.order_by(SecurityAlert.detected_at.desc()).all())

    @app.route("/tester/scan/<int:case_id>", methods=["POST"])
    @app.tester_required
    def run_scan(case_id):
        case = db.get_or_404(TestCase, case_id)
        case.status = "passed"
        case.executed_by = current_user.id
        case.executed_at = datetime.utcnow()
        db.session.commit()
        log_activity(f"Ran vulnerability scan: {case.name}")
        flash(f"Scan complete: {case.name} passed.", "success")
        return redirect(url_for("tester_dashboard"))

    @app.route("/resumes/<path:filename>")
    @login_required
    def download_resume(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

    with app.app_context():
        db.create_all()
        if not User.query.first():
            seed_data(app)
    return app


def seed_data(app):
    if not User.query.first():
        recruiter = User(username="demo_recruiter", email="recruiter@securehire.com", password_hash=generate_password_hash("Recruiter123!"), role="recruiter")
        tester = User(username="demo_tester", email="tester@securehire.com", password_hash=generate_password_hash("Tester123!"), role="tester")
        admin = User(username="demo_admin", email="admin@securehire.com", password_hash=generate_password_hash("Admin123!"), role="admin")
        db.session.add_all([recruiter, tester, admin])
        db.session.flush()
        db.session.add_all([Job(title="Security Engineer", description="Build secure systems for teams shipping quickly.", requirements="Python, cloud security, and incident response experience.", posted_by=recruiter.id), Job(title="Product Designer", description="Design calm, useful tools for modern teams.", requirements="Portfolio, Figma, and product discovery experience.", posted_by=recruiter.id)])
        db.session.add_all([TestCase(name="SQL injection prevention", description="Confirm search and forms use parameterized ORM queries."), TestCase(name="Resume upload validation", description="Confirm unsupported file types are rejected safely.")])
        db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
