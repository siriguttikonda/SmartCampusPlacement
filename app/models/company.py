from app import db


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    company_name = db.Column(
        db.String(150),
        nullable=False
    )

    industry = db.Column(
        db.String(100),
        nullable=True
    )

    website = db.Column(
        db.String(255),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    location = db.Column(
        db.String(150),
        nullable=True
    )

    contact_email = db.Column(
        db.String(120),
        nullable=True
    )

    contact_phone = db.Column(
        db.String(30),
        nullable=True
    )

    user = db.relationship(
        "User",
        backref="company_profile"
    )