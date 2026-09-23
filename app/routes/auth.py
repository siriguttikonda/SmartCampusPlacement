from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models.user import User


auth_bp = Blueprint("auth", __name__)


# REGISTER ROUTE
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            return "Passwords do not match!"

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "This email is already registered!"

        password_hash = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            role="student"
        )

        db.session.add(new_user)
        db.session.commit()

        # Automatically log the student in
        session["user_id"] = new_user.id
        session["user_name"] = new_user.name
        session["user_role"] = new_user.role

        return redirect(url_for("student.dashboard"))

    return render_template("register.html")

# LOGIN ROUTE
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        # Find the user using their email
        user = User.query.filter_by(email=email).first()

        # Check whether the password is correct
        if user and check_password_hash(user.password_hash, password):

            # Save user information in the session
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_role"] = user.role

            # Redirect based on user role

            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))

            elif user.role == "faculty":
                return redirect(url_for("faculty.dashboard"))

            elif user.role == "company":
                return redirect(url_for("company.dashboard"))

            return redirect(url_for("student.dashboard"))

        return "Invalid email or password!"

    return render_template("login.html")


# LOGOUT ROUTE
@auth_bp.route("/logout")
def logout():

    # Remove all user information from the session
    session.clear()

    # Send the user back to the login page
    return redirect(url_for("auth.login"))