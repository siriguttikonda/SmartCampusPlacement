from datetime import datetime, date

from flask import (
    Blueprint,
    session,
    redirect,
    url_for,
    render_template,
    request
)

from app import db
from app.models.student import Student
from app.models.skill import Skill
from app.models.job import Job
from app.models.application import Application


student_bp = Blueprint("student", __name__)


# ============================================================
# STUDENT AUTHENTICATION
# ============================================================

def student_required():
    """Check that a logged-in user is a student."""

    if "user_id" not in session:
        return False

    if session.get("user_role") != "student":
        return False

    return True


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_logged_in_student():
    """Return the Student record for the logged-in user."""

    return Student.query.filter_by(
        user_id=session.get("user_id")
    ).first()


def get_student_skills(student):
    """Return student's skills as a lowercase set."""

    skills = Skill.query.filter_by(
        student_id=student.id
    ).all()

    return {
        skill.skill_name.strip().lower()
        for skill in skills
        if skill.skill_name
    }


def check_job_eligibility(student, job, student_skill_names=None):
    """
    Check whether a student is eligible for a job.

    Eligibility:
    1. Minimum CGPA
    2. Graduation year
    3. Required skills
    4. Eligible department
    5. Backlog requirement
    """

    if student_skill_names is None:
        student_skill_names = get_student_skills(student)

    # --------------------------------------------------------
    # 1. CGPA
    # --------------------------------------------------------

    if job.minimum_cgpa is None:
        cgpa_eligible = True
    else:
        cgpa_eligible = (
            student.current_cgpa is not None
            and student.current_cgpa >= job.minimum_cgpa
        )

    # --------------------------------------------------------
    # 2. GRADUATION YEAR
    # --------------------------------------------------------

    if not job.graduation_year:
        graduation_eligible = True
    else:
        eligible_years = [
            year.strip()
            for year in job.graduation_year.split(",")
            if year.strip()
        ]

        graduation_eligible = (
            str(student.graduation_year) in eligible_years
        )

    # --------------------------------------------------------
    # 3. REQUIRED SKILLS
    # --------------------------------------------------------

    if not job.required_skills:
        skills_eligible = True
    else:
        required_skills = [
            skill.strip().lower()
            for skill in job.required_skills.split(",")
            if skill.strip()
        ]

        skills_eligible = all(
            skill in student_skill_names
            for skill in required_skills
        )

    # --------------------------------------------------------
    # 4. DEPARTMENT
    # --------------------------------------------------------

    if not job.eligible_departments:
        department_eligible = True
    else:
        eligible_departments = [
            department.strip().lower()
            for department in job.eligible_departments.split(",")
            if department.strip()
        ]

        department_eligible = (
            student.department is not None
            and student.department.strip().lower()
            in eligible_departments
        )

    # --------------------------------------------------------
    # 5. BACKLOG REQUIREMENT
    # --------------------------------------------------------

    backlog_eligible = True

    if job.backlog_requirement:
        requirement = job.backlog_requirement.strip().lower()

        if (
            "no backlog" in requirement
            or "0 backlog" in requirement
            or "zero backlog" in requirement
        ):
            backlog_eligible = (
                student.active_backlogs is not None
                and student.active_backlogs == 0
            )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    return (
        cgpa_eligible
        and graduation_eligible
        and skills_eligible
        and department_eligible
        and backlog_eligible
    )


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@student_bp.route("/student/dashboard")
def dashboard():

    if not student_required():
        return redirect(url_for("auth.login"))

    student = get_logged_in_student()

    # Student profile not created yet
    if not student:
        return redirect(url_for("student.profile"))

    applications = Application.query.filter_by(
        student_id=student.id
    ).all()

    # --------------------------------------------------------
    # Application statistics
    # --------------------------------------------------------

    total_applications = len(applications)

    applied_count = sum(
        1 for app in applications
        if app.faculty_status == "Applied"
    )

    under_review_count = sum(
        1 for app in applications
        if app.faculty_status == "Under Review"
    )

    verified_count = sum(
        1 for app in applications
        if app.faculty_status == "Verified"
    )

    forwarded_count = sum(
        1 for app in applications
        if app.faculty_status == "Forwarded"
    )

    not_eligible_count = sum(
        1 for app in applications
        if app.faculty_status == "Not Eligible"
    )

    shortlisted_count = sum(
        1 for app in applications
        if app.company_status == "Shortlisted"
    )

    interview_count = sum(
        1 for app in applications
        if app.company_status == "Interview"
    )

    selected_count = sum(
        1 for app in applications
        if app.company_status == "Selected"
    )

    rejected_count = sum(
        1 for app in applications
        if app.company_status == "Rejected"
    )

    # --------------------------------------------------------
    # Published jobs
    # --------------------------------------------------------

    published_jobs_count = Job.query.filter_by(
        status="Published"
    ).count()

    # --------------------------------------------------------
    # Skills
    # --------------------------------------------------------

    skills_count = Skill.query.filter_by(
        student_id=student.id
    ).count()

    # --------------------------------------------------------
    # Placement status
    # --------------------------------------------------------

    placement_status = "Not Placed"

    if selected_count > 0:
        placement_status = "Selected"

    return render_template(
        "student_dashboard.html",
        name=session.get("user_name"),
        student=student,

        total_applications=total_applications,
        applied_count=applied_count,
        under_review_count=under_review_count,
        verified_count=verified_count,
        forwarded_count=forwarded_count,
        not_eligible_count=not_eligible_count,

        shortlisted_count=shortlisted_count,
        interview_count=interview_count,
        selected_count=selected_count,
        rejected_count=rejected_count,

        published_jobs_count=published_jobs_count,
        skills_count=skills_count,
        placement_status=placement_status
    )


# ============================================================
# STUDENT PROFILE
# ============================================================

@student_bp.route("/student/profile", methods=["GET", "POST"])
def profile():

    if not student_required():
        return redirect(url_for("auth.login"))

    user_id = session.get("user_id")

    student = Student.query.filter_by(
        user_id=user_id
    ).first()

    if request.method == "POST":

        student_id = request.form.get("student_id")
        department = request.form.get("department")
        course = request.form.get("course")
        graduation_year = request.form.get("graduation_year")
        tenth_percentage = request.form.get("tenth_percentage")
        twelfth_percentage = request.form.get("twelfth_percentage")
        current_cgpa = request.form.get("current_cgpa")
        active_backlogs = request.form.get("active_backlogs")

        try:
            graduation_year_value = int(graduation_year)
            tenth_value = (
                float(tenth_percentage)
                if tenth_percentage
                else None
            )
            twelfth_value = (
                float(twelfth_percentage)
                if twelfth_percentage
                else None
            )
            cgpa_value = (
                float(current_cgpa)
                if current_cgpa
                else None
            )
            backlog_value = (
                int(active_backlogs)
                if active_backlogs
                else 0
            )

        except (ValueError, TypeError):
            return redirect(url_for("student.profile"))

        if not student:

            student = Student(
                user_id=user_id,
                student_id=student_id,
                department=department,
                course=course,
                graduation_year=graduation_year_value,
                tenth_percentage=tenth_value,
                twelfth_percentage=twelfth_value,
                current_cgpa=cgpa_value,
                active_backlogs=backlog_value
            )

            db.session.add(student)

        else:

            student.student_id = student_id
            student.department = department
            student.course = course
            student.graduation_year = graduation_year_value
            student.tenth_percentage = tenth_value
            student.twelfth_percentage = twelfth_value
            student.current_cgpa = cgpa_value
            student.active_backlogs = backlog_value

        db.session.commit()

        return redirect(url_for("student.profile"))

    return render_template(
        "student_profile.html",
        student=student
    )


# ============================================================
# MY SKILLS
# ============================================================

@student_bp.route("/student/skills", methods=["GET", "POST"])
def skills():

    if not student_required():
        return redirect(url_for("auth.login"))

    student = get_logged_in_student()

    if not student:
        return redirect(url_for("student.profile"))

    if request.method == "POST":

        skill_name = request.form.get("skill_name")

        if skill_name:
            skill_name = skill_name.strip()

            existing_skill = Skill.query.filter(
                Skill.student_id == student.id,
                db.func.lower(Skill.skill_name) == skill_name.lower()
            ).first()

            if not existing_skill:

                new_skill = Skill(
                    student_id=student.id,
                    skill_name=skill_name
                )

                db.session.add(new_skill)
                db.session.commit()

        return redirect(url_for("student.skills"))

    student_skills = Skill.query.filter_by(
        student_id=student.id
    ).all()

    return render_template(
        "student_skills.html",
        skills=student_skills
    )


# ============================================================
# DELETE SKILL
# ============================================================

@student_bp.route(
    "/student/skills/delete/<int:skill_id>",
    methods=["POST"]
)
def delete_skill(skill_id):

    if not student_required():
        return redirect(url_for("auth.login"))

    student = get_logged_in_student()

    if not student:
        return redirect(url_for("student.profile"))

    skill = Skill.query.filter_by(
        id=skill_id,
        student_id=student.id
    ).first()

    if skill:
        db.session.delete(skill)
        db.session.commit()

    return redirect(url_for("student.skills"))


# ============================================================
# JOB OPPORTUNITIES
# ============================================================

@student_bp.route("/student/jobs")
def jobs():

    if not student_required():
        return redirect(url_for("auth.login"))

    student = get_logged_in_student()

    if not student:
        return redirect(url_for("student.profile"))

    student_skill_names = get_student_skills(student)

    # ONLY PUBLISHED JOBS ARE VISIBLE TO STUDENTS
    all_jobs = Job.query.filter_by(
        status="Published"
    ).order_by(
        Job.deadline.asc()
    ).all()

    for job in all_jobs:

        job.is_eligible = check_job_eligibility(
            student,
            job,
            student_skill_names
        )

    return render_template(
        "student_jobs.html",
        jobs=all_jobs
    )


# ============================================================
# RECOMMENDED JOBS
# ============================================================

@student_bp.route("/student/recommended-jobs")
def recommended_jobs():

    if not student_required():
        return redirect(url_for("auth.login"))

    student = get_logged_in_student()

    if not student:
        return redirect(url_for("student.profile"))

    student_skill_names = get_student_skills(student)

    all_jobs = Job.query.filter_by(
        status="Published"
    ).order_by(
        Job.deadline.asc()
    ).all()

    recommended_jobs = []

    for job in all_jobs:

        if check_job_eligibility(
            student,
            job,
            student_skill_names
        ):
            recommended_jobs.append(job)

    return render_template(
        "recommended_jobs.html",
        jobs=recommended_jobs
    )


# ============================================================
# APPLY FOR JOB
# ============================================================

@student_bp.route("/student/apply/<int:job_id>")
def apply_job(job_id):

    if not student_required():
        return redirect(url_for("auth.login"))

    student = get_logged_in_student()

    if not student:
        return redirect(url_for("student.profile"))

    job = Job.query.get_or_404(job_id)

    # Only published jobs can be applied to
    if job.status != "Published":
        return redirect(url_for("student.jobs"))

    # Deadline check
    if job.deadline and job.deadline < date.today():
        return redirect(url_for("student.jobs"))

    # Server-side eligibility check
    student_skill_names = get_student_skills(student)

    if not check_job_eligibility(
        student,
        job,
        student_skill_names
    ):
        return redirect(url_for("student.jobs"))

    # Duplicate application check
    existing_application = Application.query.filter_by(
        student_id=student.id,
        job_id=job.id
    ).first()

    if existing_application:
        return redirect(url_for("student.my_applications"))

    # Show application preview
    return render_template(
        "application_preview.html",
        student=student,
        job=job
    )


# ============================================================
# CONFIRM APPLICATION
# ============================================================

@student_bp.route(
    "/student/apply/<int:job_id>/confirm",
    methods=["POST"]
)
def confirm_application(job_id):

    if not student_required():
        return redirect(url_for("auth.login"))

    student = get_logged_in_student()

    if not student:
        return redirect(url_for("student.profile"))

    job = Job.query.get_or_404(job_id)

    # Only published jobs
    if job.status != "Published":
        return redirect(url_for("student.jobs"))

    # Deadline check
    if job.deadline and job.deadline < date.today():
        return redirect(url_for("student.jobs"))

    # Eligibility check
    student_skill_names = get_student_skills(student)

    if not check_job_eligibility(
        student,
        job,
        student_skill_names
    ):
        return redirect(url_for("student.jobs"))

    # Duplicate application check
    existing_application = Application.query.filter_by(
        student_id=student.id,
        job_id=job.id
    ).first()

    if existing_application:
        return redirect(url_for("student.my_applications"))

    # IMPORTANT:
    # Application model now uses faculty_status,
    # not the old status column.
    new_application = Application(
        student_id=student.id,
        job_id=job.id,
        faculty_status="Applied"
    )

    db.session.add(new_application)
    db.session.commit()

    return redirect(url_for("student.my_applications"))


# ============================================================
# MY APPLICATIONS
# ============================================================

@student_bp.route("/student/applications")
def my_applications():

    if not student_required():
        return redirect(url_for("auth.login"))

    student = get_logged_in_student()

    if not student:
        return redirect(url_for("student.profile"))

    applications = Application.query.filter_by(
        student_id=student.id
    ).order_by(
        Application.application_date.desc()
    ).all()

    return render_template(
        "my_applications.html",
        applications=applications
    )


# ============================================================
# SKILL GAP ANALYSIS
# ============================================================

@student_bp.route("/student/skill-gap")
def skill_gap():

    if not student_required():
        return redirect(url_for("auth.login"))

    student = get_logged_in_student()

    if not student:
        return redirect(url_for("student.profile"))

    student_skill_names = get_student_skills(student)

    # Only analyse currently published jobs
    all_jobs = Job.query.filter_by(
        status="Published"
    ).all()

    skill_gap_data = []

    for job in all_jobs:

        if not job.required_skills:
            continue

        required_skills = [
            skill.strip()
            for skill in job.required_skills.split(",")
            if skill.strip()
        ]

        missing_skills = []

        for skill in required_skills:

            if skill.lower() not in student_skill_names:
                missing_skills.append(skill)

        if missing_skills:

            skill_gap_data.append({
                "job": job,
                "missing_skills": missing_skills
            })

    return render_template(
        "skill_gap.html",
        skill_gap_data=skill_gap_data
    )