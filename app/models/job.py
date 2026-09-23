from app import db


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=True
    )

    company = db.relationship(
        "Company",
        backref="jobs"
    )

    job_title = db.Column(
        db.String(100),
        nullable=False
    )

    location = db.Column(
        db.String(100),
        nullable=False
    )

    job_type = db.Column(
        db.String(50),
        nullable=False
    )

    minimum_cgpa = db.Column(
        db.Float,
        nullable=True
    )

    graduation_year = db.Column(
        db.Text,
        nullable=True
    )

    required_skills = db.Column(
        db.Text,
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    deadline = db.Column(
        db.Date,
        nullable=True
    )

    salary = db.Column(
        db.String(100),
        nullable=True
    )

    eligible_departments = db.Column(
        db.Text,
        nullable=True
    )

    backlog_requirement = db.Column(
        db.String(100),
        nullable=True
    )

    selection_process = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Pending"
    )