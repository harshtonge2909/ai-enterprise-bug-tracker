from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from dotenv import load_dotenv

import os
load_dotenv()
from werkzeug.utils import secure_filename
from groq import Groq
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
def predict_severity(description):

    description = description.lower()

    high_keywords = [
        "crash",
        "payment",
        "security",
        "database",
        "failure",
        "server",
        "data loss"
    ]

    medium_keywords = [
        "slow",
        "delay",
        "lag",
        "timeout",
        "performance"
    ]

    for word in high_keywords:

        if word in description:

            return "High"

    for word in medium_keywords:

        if word in description:

            return "Medium"

    return "Low"


def generate_summary(text):

    response = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[

            {
                "role": "system",

                "content":
                "You are an AI bug analysis assistant."
            },

            {
                "role": "user",

                "content":
                f"""
                Summarize this software bug in ONLY ONE SHORT PROFESSIONAL SENTENCE.

                Bug:
                {text}
                """
            }

        ]

    )

    return response.choices[0].message.content
def predict_severity(description):

    description = description.lower()

    high_keywords = [
        "crash",
        "payment",
        "security",
        "database",
        "failure",
        "server",
        "data loss"
    ]

    medium_keywords = [
        "slow",
        "delay",
        "lag",
        "timeout",
        "performance"
    ]

    for word in high_keywords:

        if word in description:

            return "High"

    for word in medium_keywords:

        if word in description:

            return "Medium"

    return "Low"

app = Flask(__name__)
app.secret_key = "mysecretkey"
app.config["UPLOAD_FOLDER"] = "static/uploads"

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bugtracker.db"

db = SQLAlchemy(app)


# User Table
class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(100),
        nullable=False
    )

    role = db.Column(
        db.String(50),
        nullable=False
    )
# Home Page
# Bug Table
class Bug(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    description = db.Column(db.Text, nullable=False)

    priority = db.Column(db.String(50), nullable=False)

    status = db.Column(db.String(50), default="Open")
    
    assigned_to = db.Column(
        db.String(100),
        nullable=True
    )
    file_name = db.Column(
        db.String(200),
        nullable=True
    )
    ai_summary = db.Column(
        db.String(300),
        nullable=True
    )   
class Comment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    author = db.Column(
        db.String(100),
        nullable=False
    )

    bug_id = db.Column(
        db.Integer,
        db.ForeignKey("bug.id"),
        nullable=False
    )

class Activity(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    action = db.Column(
        db.String(300),
        nullable=False
    )

    user = db.Column(
        db.String(100),
        nullable=False
    )

    bug_id = db.Column(
        db.Integer,
        db.ForeignKey("bug.id"),
        nullable=False
    )
@app.route("/")
def home():
    return render_template("index.html")


# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        print(user)

        if user:

            print(user.username)
            print(user.password)

        if user and check_password_hash(
            user.password,
            password
        ):

            session["user"] = username
            session["role"] = user.role

            return redirect("/view_bugs")

        else:

            return "Invalid Username or Password"

    return render_template("login.html")
# Register Page
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)
        
        role = request.form["role"]

        new_user = User(
                username=username,
                password=hashed_password,
                role=role
            )

        db.session.add(new_user)

        db.session.commit()

        return f"User {username} registered successfully!"

    return render_template("register.html")

@app.route("/create_bug", methods=["GET", "POST"])
def create_bug():

    if "user" not in session:

        return redirect("/login")

    if session["role"] not in ["Tester", "Admin"]:

        return "Access Denied"

    if request.method == "POST":

        title = request.form["title"]

        description = request.form["description"]

        description = request.form["description"]

        priority = predict_severity(description)
        
        combined_text = title + " " + description

        priority = predict_severity(combined_text)

        ai_summary = generate_summary(description)
        
        
        uploaded_file = request.files["bug_file"]
        
        filename = None

        if uploaded_file and uploaded_file.filename != "":

            filename = secure_filename(
                uploaded_file.filename
            )

            uploaded_file.save(
                f"{app.config['UPLOAD_FOLDER']}/{filename}"
            )

        new_bug = Bug(

            title=title,

            description=description,

            priority=priority,
            
            ai_summary=ai_summary,  

            file_name=filename

        )

        db.session.add(new_bug)

        db.session.commit()

        activity = Activity(

            action="Created bug",

            user=session["user"],

            bug_id=new_bug.id

        )

        db.session.add(activity)

        db.session.commit()

        return redirect("/view_bugs")

    return render_template("create_bug.html")

@app.route("/view_bugs")
def view_bugs():

    search = request.args.get("search")

    priority = request.args.get("priority")

    status = request.args.get("status")

    bugs = Bug.query

    # Search by title
    if search:

        bugs = bugs.filter(
            Bug.title.ilike(f"%{search}%")
        )

    # Filter by priority
    if priority and priority != "All":

        bugs = bugs.filter_by(priority=priority)

    # Filter by status
    if status and status != "All":

        bugs = bugs.filter_by(status=status)

    bugs = bugs.all()

    # Analytics
    total_bugs = Bug.query.count()

    open_bugs = Bug.query.filter_by(
        status="Open"
    ).count()

    in_progress_bugs = Bug.query.filter_by(
        status="In Progress"
    ).count()

    resolved_bugs = Bug.query.filter_by(
        status="Resolved"
    ).count()

    return render_template(
        "view_bugs.html",
        bugs=bugs,
        total_bugs=total_bugs,
        open_bugs=open_bugs,
        in_progress_bugs=in_progress_bugs,
        resolved_bugs=resolved_bugs
    )

@app.route("/update_bug/<int:bug_id>")
def update_bug(bug_id):

    if "user" not in session:

        return redirect("/login")

    if session["role"] not in ["Developer", "Admin"]:

        return "Access Denied"

    bug = Bug.query.get_or_404(bug_id)

    if bug.status == "Open":

        bug.status = "In Progress"

    elif bug.status == "In Progress":

        bug.status = "Resolved"

    else:

        bug.status = "Open"

    db.session.commit()
    activity = Activity(

        action=f"Changed status to {bug.status}",

        user=session["user"],

        bug_id=bug.id

    )

    db.session.add(activity)

    db.session.commit()

    return redirect("/view_bugs")

@app.route("/delete_bug/<int:bug_id>")
def delete_bug(bug_id):

    if "user" not in session:

        return redirect("/login")

    if session["role"] != "Admin":

        return "Access Denied"

    bug = Bug.query.get_or_404(bug_id)

    db.session.delete(bug)

    db.session.commit()

    return redirect("/view_bugs")

@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/login")

@app.route("/bug/<int:bug_id>", methods=["GET", "POST"])
def bug_details(bug_id):

    if "user" not in session:

        return redirect("/login")

    bug = Bug.query.get_or_404(bug_id)

    comments = Comment.query.filter_by(
        bug_id=bug_id
    ).all()
    activities = Activity.query.filter_by(
        bug_id=bug_id
    ).all()

    if request.method == "POST":

        content = request.form["content"]

        new_comment = Comment(

            content=content,

            author=session["user"],

            bug_id=bug_id

        )

        db.session.add(new_comment)

        db.session.commit()

        activity = Activity(

            action="Added comment",

            user=session["user"],

            bug_id=bug.id

        )

        db.session.add(activity)

        db.session.commit()

        return redirect(f"/bug/{bug_id}")

    return render_template(

        "bug_details.html",

        bug=bug,

        comments=comments,

        activities=activities

    )


@app.route("/init")
def init_app():

    with app.app_context():
        db.create_all()

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    return "Initialization complete. Database and uploads folder are ready."


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)