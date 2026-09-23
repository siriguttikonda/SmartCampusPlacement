from flask import Blueprint, session, redirect, url_for, render_template, request
from datetime import datetime
from sqlalchemy import text

from app import db
from app.models.company import Company
from app.models.job import Job
from app.models.application import Application


company_bp = Blueprint("company", __name__)


# =========================================================
# COMPANY ACCESS CHECK
# =========================================================

def company_required():

    if "user_id" not in session:
        return False

    if session.get("user_role") != "company":
        return False

    return True


# =========================================================
# COMPANY DASHBOARD
# =========================================================

@company_bp.route("/company/dashboard")
def dashboard():

    if not company_required():
        return redirect(url_for("auth.login"))

    company = Company.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return "Company profile not found."

    # =====================================================
    # 1. COMPANY JOBS
    # =====================================================

    jobs = (
        Job.query
        .filter_by(company_id=company.id)
        .order_by(Job.id.desc())
        .all()
    )

    total_jobs = len(jobs)

    active_jobs = Job.query.filter_by(
        company_id=company.id,
        status="Published"
    ).count()

    # =====================================================
    # 2. APPLICATIONS
    # =====================================================

    applications = (
        Application.query
        .join(Job)
        .filter(
            Job.company_id == company.id
        )
        .all()
    )

    total_applications = len(applications)

    # =====================================================
    # 3. FORWARDED CANDIDATES
    # =====================================================
    #
    # Admin / Placement Cell has forwarded the candidate.
    # =====================================================

    forwarded_candidates = (
        Application.query
        .join(Job)
        .filter(
            Job.company_id == company.id,
            Application.faculty_status == "Forwarded"
        )
        .count()
    )

    # =====================================================
    # 4. SHORTLISTED
    # =====================================================
    #
    # IMPORTANT:
    # Use shortlisted_at instead of company_status.
    #
    # Why?
    # A candidate who reaches:
    #
    # Shortlisted → Interview → Selected
    #
    # will have company_status = "Selected".
    #
    # But shortlisted_at remains populated, so we can
    # correctly show that the candidate passed through
    # the shortlisted stage.
    # =====================================================

    shortlisted_candidates = (
        Application.query
        .join(Job)
        .filter(
            Job.company_id == company.id,
            Application.shortlisted_at.isnot(None)
        )
        .count()
    )

    # =====================================================
    # 5. INTERVIEWS
    # =====================================================
    #
    # Use interview_date so completed interview stages
    # remain visible in the recruitment pipeline.
    # =====================================================

    interview_candidates = (
        Application.query
        .join(Job)
        .filter(
            Job.company_id == company.id,
            Application.interview_date.isnot(None)
        )
        .count()
    )

    # =====================================================
    # 6. SELECTED
    # =====================================================

    selected_candidates = (
        Application.query
        .join(Job)
        .filter(
            Job.company_id == company.id,
            Application.selected_at.isnot(None)
        )
        .count()
    )

    # =====================================================
    # 7. REJECTED
    # =====================================================
    #
    # Rejected remains a current company outcome.
    # =====================================================

    rejected_candidates = (
        Application.query
        .join(Job)
        .filter(
            Job.company_id == company.id,
            Application.company_status == "Rejected"
        )
        .count()
    )

    # =====================================================
    # 8. RENDER COMPANY DASHBOARD
    # =====================================================

    return render_template(
        "company_dashboard.html",

        company=company,
        jobs=jobs,

        # Overview
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applications=total_applications,

        # Recruitment pipeline
        forwarded_candidates=forwarded_candidates,
        shortlisted_candidates=shortlisted_candidates,
        interview_candidates=interview_candidates,
        selected_candidates=selected_candidates,
        rejected_candidates=rejected_candidates
    )


# =========================================================
# COMPANY — JOBS
# =========================================================

@company_bp.route("/company/jobs")
def jobs():

    if not company_required():
        return redirect(url_for("auth.login"))

    company = Company.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return "Company profile not found."

    jobs = (
        Job.query
        .filter_by(company_id=company.id)
        .order_by(Job.id.desc())
        .all()
    )

    job_data = []

    for job in jobs:

        # -------------------------------------------------
        # TOTAL APPLICATIONS
        # -------------------------------------------------

        application_count = Application.query.filter_by(
            job_id=job.id
        ).count()

        # -------------------------------------------------
        # FORWARDED
        # -------------------------------------------------

        forwarded_count = (
            Application.query
            .filter_by(
                job_id=job.id,
                faculty_status="Forwarded"
            )
            .count()
        )

        # -------------------------------------------------
        # SELECTED
        # -------------------------------------------------

        selected_count = (
            Application.query
            .filter(
                Application.job_id == job.id,
                Application.selected_at.isnot(None)
            )
            .count()
        )

        job_data.append({
            "job": job,
            "application_count": application_count,
            "forwarded_count": forwarded_count,
            "selected_count": selected_count
        })

    return render_template(
        "company_jobs.html",
        company=company,
        job_data=job_data
    )


# =========================================================
# COMPANY — POST JOB
# =========================================================

@company_bp.route(
    "/company/jobs/post",
    methods=["GET", "POST"]
)
def post_job():

    if not company_required():
        return redirect(url_for("auth.login"))

    company = Company.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return "Company profile not found."

    if request.method == "POST":

        # -------------------------------------------------
        # MINIMUM CGPA
        # -------------------------------------------------

        minimum_cgpa = request.form.get(
            "minimum_cgpa"
        )

        try:
            minimum_cgpa = (
                float(minimum_cgpa)
                if minimum_cgpa
                else None
            )
        except ValueError:
            minimum_cgpa = None

        # -------------------------------------------------
        # DEADLINE
        # -------------------------------------------------

        deadline = request.form.get(
            "deadline"
        )

        if deadline:
            try:
                deadline = datetime.strptime(
                    deadline,
                    "%Y-%m-%d"
                ).date()
            except ValueError:
                deadline = None
        else:
            deadline = None

        # -------------------------------------------------
        # CREATE JOB
        # -------------------------------------------------

        job = Job(
            company_id=company.id,

            job_title=request.form.get(
                "job_title"
            ),

            location=request.form.get(
                "location"
            ),

            job_type=request.form.get(
                "job_type"
            ),

            minimum_cgpa=minimum_cgpa,

            graduation_year=request.form.get(
                "graduation_year"
            ),

            required_skills=request.form.get(
                "required_skills"
            ),

            description=request.form.get(
                "description"
            ),

            deadline=deadline,

            salary=request.form.get(
                "salary"
            ),

            eligible_departments=request.form.get(
                "eligible_departments"
            ),

            backlog_requirement=request.form.get(
                "backlog_requirement"
            ),

            selection_process=request.form.get(
                "selection_process"
            ),

            # Company posts job → Admin must approve
            status="Pending"
        )

        db.session.add(job)

        db.session.commit()

        return redirect(
            url_for("company.jobs")
        )

    return render_template(
        "company_post_job.html",
        company=company
    )


# =========================================================
# COMPANY — CANDIDATES
# =========================================================

@company_bp.route("/company/candidates")
def candidates():

    if not company_required():
        return redirect(url_for("auth.login"))

    company = Company.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return "Company profile not found."

    # =====================================================
    # ONLY CANDIDATES FORWARDED BY ADMIN
    # FOR JOBS BELONGING TO THIS COMPANY
    # =====================================================

    applications = (
        Application.query
        .join(Job)
        .filter(
            Job.company_id == company.id,
            Application.faculty_status == "Forwarded"
        )
        .order_by(
            Application.forwarded_at.desc()
        )
        .all()
    )

    # =====================================================
    # SUMMARY COUNTS
    # =====================================================

    total_candidates = len(applications)

    pending_candidates = sum(
        1
        for application in applications
        if not application.company_status
    )

    # Historical stage counts
    shortlisted_candidates = sum(
        1
        for application in applications
        if application.shortlisted_at is not None
    )

    interview_candidates = sum(
        1
        for application in applications
        if application.interview_date is not None
    )

    selected_candidates = sum(
        1
        for application in applications
        if application.selected_at is not None
    )

    rejected_candidates = sum(
        1
        for application in applications
        if application.company_status == "Rejected"
    )

    return render_template(
        "company_candidates.html",

        company=company,
        applications=applications,

        total_candidates=total_candidates,
        pending_candidates=pending_candidates,
        shortlisted_candidates=shortlisted_candidates,
        interview_candidates=interview_candidates,
        selected_candidates=selected_candidates,
        rejected_candidates=rejected_candidates
    )


# =========================================================
# COMPANY — UPDATE CANDIDATE STATUS
# =========================================================
#
# Company workflow:
#
# Forwarded
#     ↓
# Shortlisted
#     ↓
# Interview
#     ↓
# Selected
#
# OR
#
# Rejected
#
# =========================================================

@company_bp.route(
    "/company/candidates/<int:application_id>/status",
    methods=["POST"]
)
def update_candidate_status(application_id):

    if not company_required():
        return redirect(url_for("auth.login"))

    company = Company.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return "Company profile not found."

    # =====================================================
    # FIND APPLICATION
    # =====================================================

    application = (
        Application.query
        .join(Job)
        .filter(
            Application.id == application_id,
            Job.company_id == company.id,
            Application.faculty_status == "Forwarded"
        )
        .first()
    )

    if not application:
        return (
            "Candidate not found or not forwarded by admin.",
            404
        )

    # =====================================================
    # GET REQUESTED STATUS
    # =====================================================

    status = request.form.get(
        "status"
    )

    allowed_statuses = [
        "Shortlisted",
        "Interview",
        "Selected",
        "Rejected"
    ]

    if status not in allowed_statuses:
        return "Invalid candidate status.", 400

    current_status = application.company_status

    # =====================================================
    # WORKFLOW VALIDATION
    # =====================================================

    # -----------------------------------------------------
    # FORWARDED → SHORTLISTED
    # -----------------------------------------------------

    if status == "Shortlisted":

        if current_status not in [None, ""]:

            return (
                "Candidate has already moved beyond the "
                "initial review stage.",
                400
            )

    # -----------------------------------------------------
    # SHORTLISTED → INTERVIEW
    # -----------------------------------------------------

    elif status == "Interview":

        if current_status != "Shortlisted":

            return (
                "Candidate must be shortlisted before "
                "moving to interview.",
                400
            )

    # -----------------------------------------------------
    # INTERVIEW → SELECTED
    # -----------------------------------------------------

    elif status == "Selected":

        if current_status != "Interview":

            return (
                "Candidate must complete the interview "
                "stage before selection.",
                400
            )

    # -----------------------------------------------------
    # ANY STAGE → REJECTED
    # -----------------------------------------------------

    elif status == "Rejected":

        if current_status == "Selected":

            return (
                "A selected candidate cannot be rejected.",
                400
            )

    # =====================================================
    # UPDATE COMPANY STATUS
    # =====================================================

    application.company_status = status

    # =====================================================
    # SHORTLISTED
    # =====================================================

    if status == "Shortlisted":

        if application.shortlisted_at is None:

            application.shortlisted_at = datetime.utcnow()

    # =====================================================
    # INTERVIEW
    # =====================================================

    elif status == "Interview":

        if application.interview_date is None:

            application.interview_date = datetime.utcnow()

    # =====================================================
    # SELECTED
    # =====================================================

    elif status == "Selected":

        if application.selected_at is None:

            application.selected_at = datetime.utcnow()

        # =================================================
        # CREATE PLACEMENT RECORD
        # =================================================

        existing_placement = db.session.execute(
            text(
                """
                SELECT id
                FROM placements
                WHERE student_id = :student_id
                  AND company_id = :company_id
                  AND job_id = :job_id
                LIMIT 1
                """
            ),
            {
                "student_id": application.student_id,
                "company_id": company.id,
                "job_id": application.job_id
            }
        ).first()

        # -------------------------------------------------
        # ONLY CREATE PLACEMENT ONCE
        # -------------------------------------------------

        if not existing_placement:

            placement_year = datetime.utcnow().year

            package = None

            if application.job:
                package = application.job.salary

            db.session.execute(
                text(
                    """
                    INSERT INTO placements
                    (
                        student_id,
                        company_id,
                        job_id,
                        placement_year,
                        package,
                        placement_date
                    )
                    VALUES
                    (
                        :student_id,
                        :company_id,
                        :job_id,
                        :placement_year,
                        :package,
                        :placement_date
                    )
                    """
                ),
                {
                    "student_id": application.student_id,
                    "company_id": company.id,
                    "job_id": application.job_id,
                    "placement_year": placement_year,
                    "package": package,
                    "placement_date": datetime.utcnow()
                }
            )

    # =====================================================
    # REJECTED
    # =====================================================

    elif status == "Rejected":

        # No additional timestamp required.
        pass

    # =====================================================
    # SAVE
    # =====================================================

    db.session.commit()

    # =====================================================
    # RETURN TO ORIGINAL PAGE
    # =====================================================

    source = request.form.get(
        "source"
    )

    if source == "interviews":

        return redirect(
            url_for("company.interviews")
        )

    return redirect(
        url_for("company.candidates")
    )


# =========================================================
# COMPANY — INTERVIEWS
# =========================================================

@company_bp.route("/company/interviews")
def interviews():

    if not company_required():
        return redirect(url_for("auth.login"))

    company = Company.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return "Company profile not found."

    interviews = (
        Application.query
        .join(Job)
        .filter(
            Job.company_id == company.id,
            Application.faculty_status == "Forwarded",
            Application.company_status == "Interview"
        )
        .order_by(
            Application.interview_date.desc()
        )
        .all()
    )

    return render_template(
        "company_interviews.html",
        company=company,
        interviews=interviews
    )


# =========================================================
# COMPANY — PROFILE
# =========================================================

@company_bp.route(
    "/company/profile",
    methods=["GET", "POST"]
)
def profile():

    if not company_required():
        return redirect(url_for("auth.login"))

    company = Company.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return "Company profile not found."

    # =====================================================
    # UPDATE PROFILE
    # =====================================================

    if request.method == "POST":

        company.company_name = request.form.get(
            "company_name"
        )

        company.industry = request.form.get(
            "industry"
        )

        company.website = request.form.get(
            "website"
        )

        company.location = request.form.get(
            "location"
        )

        company.description = request.form.get(
            "description"
        )

        company.contact_email = request.form.get(
            "contact_email"
        )

        company.contact_phone = request.form.get(
            "contact_phone"
        )

        db.session.commit()

        return redirect(
            url_for("company.profile")
        )

    return render_template(
        "company_profile.html",
        company=company
    )