from app import create_app, db
from app.models import User, Company, Job
from werkzeug.security import generate_password_hash


app = create_app()

with app.app_context():

    # -----------------------------------
    # Check whether TCS user already exists
    # -----------------------------------

    user = User.query.filter_by(
        email="tcs@smartcampus.com"
    ).first()

    if user:
        print("TCS user already exists.")

    else:
        user = User(
            name="TCS",
            email="tcs@smartcampus.com",
            password_hash=generate_password_hash("tcs123"),
            role="company"
        )

        db.session.add(user)
        db.session.commit()

        print("TCS company user created.")

    # -----------------------------------
    # Check whether company profile exists
    # -----------------------------------

    company = Company.query.filter_by(
        user_id=user.id
    ).first()

    if company:
        print("TCS company profile already exists.")

    else:
        company = Company(
            user_id=user.id,
            company_name="TCS",
            industry="Information Technology",
            website="https://www.tcs.com",
            description="Tata Consultancy Services",
            location="Hyderabad",
            contact_email="tcs@smartcampus.com"
        )

        db.session.add(company)
        db.session.commit()

        print("TCS company profile created.")

    # -----------------------------------
    # Connect existing jobs to TCS
    # -----------------------------------

    jobs = Job.query.all()

    for job in jobs:

        if job.company_id is None:

            job.company_id = company.id

            print(
                f"Connected job '{job.job_title}' "
                f"to TCS company."
            )

    db.session.commit()

    print("TCS setup completed successfully.")