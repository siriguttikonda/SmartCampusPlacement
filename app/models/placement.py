from app import db
from datetime import datetime


class Placement(db.Model):
    __tablename__ = "placements"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False
    )

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id"),
        nullable=False
    )

    placement_year = db.Column(
        db.Integer,
        nullable=False
    )

    package = db.Column(
        db.Float,
        nullable=True
    )

    placement_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    student = db.relationship(
        "Student",
        backref="placements"
    )

    company = db.relationship(
        "Company",
        backref="placements"
    )

    job = db.relationship(
        "Job",
        backref="placements"
    )