from app import db
from datetime import datetime


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id"),
        nullable=False
    )

    application_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # -----------------------------
    # FACULTY / PLACEMENT CELL
    # -----------------------------

    faculty_status = db.Column(
        db.String(30),
        nullable=False,
        default="Applied"
    )

    # -----------------------------
    # COMPANY / RECRUITER
    # -----------------------------

    company_status = db.Column(
        db.String(30),
        nullable=True
    )

    # -----------------------------
    # IMPORTANT DATES
    # -----------------------------

    forwarded_at = db.Column(
        db.DateTime,
        nullable=True
    )

    shortlisted_at = db.Column(
        db.DateTime,
        nullable=True
    )

    interview_date = db.Column(
        db.DateTime,
        nullable=True
    )

    selected_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # -----------------------------
    # FACULTY / COMPANY REMARKS
    # -----------------------------

    remarks = db.Column(
        db.Text,
        nullable=True
    )

    # -----------------------------
    # RELATIONSHIPS
    # -----------------------------

    job = db.relationship(
        "Job",
        backref="applications"
    )

    student = db.relationship(
        "Student",
        backref="applications"
    )