from flask import Blueprint, session, redirect, url_for, render_template, request
from datetime import datetime

from app import db
from app.models.job import Job
from app.models.application import Application
from app.models.student import Student
from app.models.company import Company


admin_bp = Blueprint("admin", __name__)


# =========================================================
# ADMIN AUTHENTICATION CHECK
# =========================================================

def admin_required():

    if "user_id" not in session:
        return False

    if session.get("user_role") != "admin":
        return False

    return True


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@admin_bp.route("/admin/dashboard")
def dashboard():

    if not admin_required():
        return redirect(url_for("auth.login"))

    # =====================================================
    # 1. DASHBOARD OVERVIEW
    # =====================================================

    total_students = Student.query.count()

    total_companies = Company.query.count()

    total_jobs = Job.query.count()

    total_applications = Application.query.count()

    # =====================================================
    # 2. APPLICATION / PLACEMENT PIPELINE
    # =====================================================
    #
    # Complete workflow:
    #
    # Applied
    #     ↓
    # Under Review
    #     ↓
    # Verified
    #     ↓
    # Forwarded
    #     ↓
    # Shortlisted
    #     ↓
    # Interview
    #     ↓
    # Selected
    #
    # Alternative outcomes:
    #
    # Applied / Review → Not Eligible
    # Company stages   → Rejected
    #
    # The dashboard counts stages reached, NOT just the
    # current status.
    # =====================================================

    # -----------------------------------------------------
    # APPLIED
    # -----------------------------------------------------
    #
    # Every Application record means the student applied.
    #
    # Therefore an application that eventually becomes
    # Selected must still count under Applied.
    # -----------------------------------------------------

    applied_count = Application.query.count()

    # -----------------------------------------------------
    # UNDER REVIEW
    # -----------------------------------------------------
    #
    # Any application that has moved beyond Applied has
    # entered the Placement Cell review process.
    #
    # We also count all company-stage applications because
    # they necessarily passed through the review stage.
    #
    # Not Eligible applications are also counted here because
    # they were reviewed before being marked ineligible.
    # -----------------------------------------------------

    under_review_count = Application.query.filter(
        Application.faculty_status.in_([
            "Under Review",
            "Verified",
            "Forwarded",
            "Not Eligible"
        ])
    ).count()

    # -----------------------------------------------------
    # VERIFIED
    # -----------------------------------------------------
    #
    # Verified and Forwarded applications have passed
    # verification.
    #
    # Company-stage applications also count because they
    # could only be forwarded after verification.
    # -----------------------------------------------------

    verified_count = Application.query.filter(
        Application.faculty_status.in_([
            "Verified",
            "Forwarded"
        ])
    ).count()

    # -----------------------------------------------------
    # FORWARDED
    # -----------------------------------------------------
    #
    # Use forwarded_at because this records that the
    # Placement Cell actually forwarded the candidate.
    # -----------------------------------------------------

    forwarded_count = Application.query.filter(
        Application.forwarded_at.isnot(None)
    ).count()

    # -----------------------------------------------------
    # NOT ELIGIBLE
    # -----------------------------------------------------

    not_eligible_count = Application.query.filter_by(
        faculty_status="Not Eligible"
    ).count()

    # =====================================================
    # 3. COMPANY RECRUITMENT PIPELINE
    # =====================================================
    #
    # Use timestamps rather than current company_status.
    #
    # Example:
    #
    # Shortlisted → Interview → Selected
    #
    # After Selected:
    #
    # company_status = "Selected"
    #
    # But:
    #
    # shortlisted_at != NULL
    # interview_date != NULL
    # selected_at != NULL
    #
    # Therefore all three historical stages can be counted.
    # =====================================================

    # -----------------------------------------------------
    # SHORTLISTED
    # -----------------------------------------------------

    shortlisted_count = Application.query.filter(
        Application.shortlisted_at.isnot(None)
    ).count()

    # -----------------------------------------------------
    # INTERVIEW
    # -----------------------------------------------------

    interview_count = Application.query.filter(
        Application.interview_date.isnot(None)
    ).count()

    # -----------------------------------------------------
    # SELECTED
    # -----------------------------------------------------

    selected_count = Application.query.filter(
        Application.selected_at.isnot(None)
    ).count()

    # -----------------------------------------------------
    # REJECTED
    # -----------------------------------------------------

    rejected_count = Application.query.filter_by(
        company_status="Rejected"
    ).count()

    # =====================================================
    # 4. JOB APPROVAL STATUS
    # =====================================================

    pending_jobs = Job.query.filter_by(
        status="Pending"
    ).count()

    published_jobs = Job.query.filter_by(
        status="Published"
    ).count()

    rejected_jobs = Job.query.filter_by(
        status="Rejected"
    ).count()

    # =====================================================
    # 5. RENDER ADMIN DASHBOARD
    # =====================================================

    return render_template(
        "admin_dashboard.html",

        # -------------------------------------------------
        # OVERVIEW
        # -------------------------------------------------

        name=session.get("user_name"),

        total_students=total_students,
        total_companies=total_companies,
        total_jobs=total_jobs,
        total_applications=total_applications,

        # -------------------------------------------------
        # APPLICATION PIPELINE
        # -------------------------------------------------

        applied_count=applied_count,
        under_review_count=under_review_count,
        verified_count=verified_count,
        forwarded_count=forwarded_count,

        # -------------------------------------------------
        # COMPANY RECRUITMENT PIPELINE
        # -------------------------------------------------

        shortlisted_count=shortlisted_count,
        interview_count=interview_count,
        selected_count=selected_count,
        rejected_count=rejected_count,

        # -------------------------------------------------
        # OTHER OUTCOME
        # -------------------------------------------------

        not_eligible_count=not_eligible_count,

        # -------------------------------------------------
        # JOB APPROVAL
        # -------------------------------------------------

        pending_jobs=pending_jobs,
        published_jobs=published_jobs,
        rejected_jobs=rejected_jobs
    )


# =========================================================
# MANAGE JOBS
# VIEW + APPROVE + REJECT JOBS
# =========================================================

@admin_bp.route("/admin/jobs")
def manage_jobs():

    if not admin_required():
        return redirect(url_for("auth.login"))

    jobs = (
        Job.query
        .order_by(Job.id.desc())
        .all()
    )

    pending_jobs = [
        job for job in jobs
        if job.status == "Pending"
    ]

    published_jobs = [
        job for job in jobs
        if job.status == "Published"
    ]

    rejected_jobs = [
        job for job in jobs
        if job.status == "Rejected"
    ]

    return render_template(
        "admin_manage_jobs.html",
        jobs=jobs,
        pending_jobs=pending_jobs,
        published_jobs=published_jobs,
        rejected_jobs=rejected_jobs
    )


# =========================================================
# APPROVE JOB
# Pending → Published
# =========================================================

@admin_bp.route(
    "/admin/jobs/<int:job_id>/approve",
    methods=["POST"]
)
def approve_job(job_id):

    if not admin_required():
        return redirect(url_for("auth.login"))

    job = Job.query.get_or_404(job_id)

    job.status = "Published"

    db.session.commit()

    return redirect(
        url_for("admin.manage_jobs")
    )


# =========================================================
# REJECT JOB
# Pending → Rejected
# =========================================================

@admin_bp.route(
    "/admin/jobs/<int:job_id>/reject",
    methods=["POST"]
)
def reject_job(job_id):

    if not admin_required():
        return redirect(url_for("auth.login"))

    job = Job.query.get_or_404(job_id)

    job.status = "Rejected"

    db.session.commit()

    return redirect(
        url_for("admin.manage_jobs")
    )


# =========================================================
# MANAGE STUDENTS
# =========================================================

@admin_bp.route("/admin/students")
def manage_students():

    if not admin_required():
        return redirect(url_for("auth.login"))

    students = (
        Student.query
        .order_by(Student.id.desc())
        .all()
    )

    return render_template(
        "admin_students.html",
        students=students
    )


# =========================================================
# STUDENT DETAILS
# =========================================================

@admin_bp.route("/admin/students/<int:student_id>")
def student_details(student_id):

    if not admin_required():
        return redirect(url_for("auth.login"))

    student = Student.query.get_or_404(student_id)

    return render_template(
        "admin_student_details.html",
        student=student
    )


# =========================================================
# APPLICATIONS
# =========================================================

@admin_bp.route("/admin/applications")
def applications():

    if not admin_required():
        return redirect(url_for("auth.login"))

    applications = (
        Application.query
        .order_by(
            Application.application_date.desc()
        )
        .all()
    )

    return render_template(
        "admin_applications.html",
        applications=applications
    )


# =========================================================
# UPDATE APPLICATION FACULTY / PLACEMENT CELL STATUS
#
# Applied
# Under Review
# Verified
# Forwarded
# Not Eligible
# =========================================================

@admin_bp.route(
    "/admin/applications/<int:application_id>/status",
    methods=["POST"]
)
def update_application_status(application_id):

    if not admin_required():
        return redirect(url_for("auth.login"))

    application = Application.query.get_or_404(
        application_id
    )

    status = request.form.get(
        "status"
    )

    allowed_statuses = [
        "Applied",
        "Under Review",
        "Verified",
        "Forwarded",
        "Not Eligible"
    ]

    if status not in allowed_statuses:
        return "Invalid application status.", 400

    # -----------------------------------------------------
    # UPDATE FACULTY / PLACEMENT CELL STATUS
    # -----------------------------------------------------

    application.faculty_status = status

    # -----------------------------------------------------
    # FORWARDED TIMESTAMP
    # -----------------------------------------------------

    if status == "Forwarded":

        if application.forwarded_at is None:
            application.forwarded_at = datetime.utcnow()

    db.session.commit()

    return redirect(
        url_for("admin.applications")
    )


# =========================================================
# UPDATE STUDENT APPLICATION STATUS
# Used from Student Details page
# =========================================================

@admin_bp.route(
    "/admin/students/<int:student_id>/applications/<int:application_id>/status",
    methods=["POST"]
)
def update_student_application_status(
    student_id,
    application_id
):

    if not admin_required():
        return redirect(url_for("auth.login"))

    application = (
        Application.query
        .filter_by(
            id=application_id,
            student_id=student_id
        )
        .first_or_404()
    )

    status = request.form.get(
        "status"
    )

    allowed_statuses = [
        "Applied",
        "Under Review",
        "Verified",
        "Forwarded",
        "Not Eligible"
    ]

    if status not in allowed_statuses:
        return "Invalid application status.", 400

    # -----------------------------------------------------
    # UPDATE FACULTY / PLACEMENT CELL STATUS
    # -----------------------------------------------------

    application.faculty_status = status

    # -----------------------------------------------------
    # FORWARDED TIMESTAMP
    # -----------------------------------------------------

    if status == "Forwarded":

        if application.forwarded_at is None:
            application.forwarded_at = datetime.utcnow()

    db.session.commit()

    return redirect(
        url_for(
            "admin.student_details",
            student_id=student_id
        )
    )


# =========================================================
# EDIT JOB
# =========================================================

@admin_bp.route(
    "/admin/jobs/edit/<int:job_id>",
    methods=["GET", "POST"]
)
def edit_job(job_id):

    if not admin_required():
        return redirect(url_for("auth.login"))

    job = Job.query.get_or_404(job_id)

    if request.method == "POST":

        # -------------------------------------------------
        # BASIC JOB INFORMATION
        # -------------------------------------------------

        job.job_title = request.form.get(
            "job_title"
        )

        job.location = request.form.get(
            "location"
        )

        job.job_type = request.form.get(
            "job_type"
        )

        # -------------------------------------------------
        # MINIMUM CGPA
        # -------------------------------------------------

        minimum_cgpa = request.form.get(
            "minimum_cgpa"
        )

        if minimum_cgpa:

            try:

                job.minimum_cgpa = float(
                    minimum_cgpa
                )

            except ValueError:

                job.minimum_cgpa = None

        else:

            job.minimum_cgpa = None

        # -------------------------------------------------
        # GRADUATION YEAR
        # -------------------------------------------------

        graduation_years = request.form.getlist(
            "graduation_year"
        )

        if graduation_years:

            job.graduation_year = ",".join(
                graduation_years
            )

        else:

            job.graduation_year = None

        # -------------------------------------------------
        # REQUIRED SKILLS
        # -------------------------------------------------

        required_skills = request.form.getlist(
            "required_skills"
        )

        if required_skills:

            job.required_skills = ",".join(
                required_skills
            )

        else:

            job.required_skills = None

        # -------------------------------------------------
        # DESCRIPTION
        # -------------------------------------------------

        job.description = request.form.get(
            "description"
        )

        # -------------------------------------------------
        # DEADLINE
        # -------------------------------------------------

        deadline = request.form.get(
            "deadline"
        )

        if deadline:

            try:

                job.deadline = datetime.strptime(
                    deadline,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                job.deadline = None

        else:

            job.deadline = None

        # -------------------------------------------------
        # ADDITIONAL JOB FIELDS
        # -------------------------------------------------

        job.salary = request.form.get(
            "salary"
        )

        job.eligible_departments = request.form.get(
            "eligible_departments"
        )

        job.backlog_requirement = request.form.get(
            "backlog_requirement"
        )

        job.selection_process = request.form.get(
            "selection_process"
        )

        # -------------------------------------------------
        # SAVE
        # -------------------------------------------------

        db.session.commit()

        return redirect(
            url_for("admin.manage_jobs")
        )

    return render_template(
        "admin_edit_job.html",
        job=job
    )


# =========================================================
# DELETE JOB
# =========================================================

@admin_bp.route(
    "/admin/jobs/delete/<int:job_id>",
    methods=["POST"]
)
def delete_job(job_id):

    if not admin_required():
        return redirect(url_for("auth.login"))

    job = Job.query.get_or_404(job_id)

    # -----------------------------------------------------
    # DELETE APPLICATIONS FIRST
    # -----------------------------------------------------

    Application.query.filter_by(
        job_id=job.id
    ).delete(
        synchronize_session=False
    )

    # -----------------------------------------------------
    # DELETE JOB
    # -----------------------------------------------------

    db.session.delete(job)

    db.session.commit()

    return redirect(
        url_for("admin.manage_jobs")
    )


# =========================================================
# MANAGE COMPANIES
# =========================================================

@admin_bp.route("/admin/companies")
def manage_companies():

    if not admin_required():
        return redirect(url_for("auth.login"))

    companies = (
        Company.query
        .order_by(Company.id.desc())
        .all()
    )

    return render_template(
        "admin_companies.html",
        companies=companies
    )