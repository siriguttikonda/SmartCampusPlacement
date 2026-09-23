from app import db


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)

    # Student who owns this skill
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    # Example: Python, Java, SQL
    skill_name = db.Column(
        db.String(100),
        nullable=False
    )