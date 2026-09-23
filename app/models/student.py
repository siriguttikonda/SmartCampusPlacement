from app import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Connect this profile to one user account
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    # Relationship with User
    user = db.relationship(
        "User",
        backref="student_profile"
    )

    # Relationship with Skills
    skills = db.relationship(
        "Skill",
        backref="student",
        cascade="all, delete-orphan"
    )

    student_id = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    department = db.Column(
        db.String(100),
        nullable=False
    )

    course = db.Column(
        db.String(100),
        nullable=False
    )

    graduation_year = db.Column(
        db.Integer,
        nullable=False
    )

    tenth_percentage = db.Column(
        db.Float,
        nullable=True
    )

    twelfth_percentage = db.Column(
        db.Float,
        nullable=True
    )

    current_cgpa = db.Column(
        db.Float,
        nullable=True
    )

    active_backlogs = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )