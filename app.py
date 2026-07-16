from flask import Flask, render_template, request
import json
from datetime import datetime
from openpyxl import Workbook
from flask import send_file

app = Flask(__name__)


# ===========================
# HOME PAGE
# ===========================

@app.route("/")
def home():
    return render_template("login.html")


# ===========================
# STUDENT LOGIN
# ===========================

@app.route("/instructions", methods=["POST"])
def instructions():

    regno = request.form["regno"].strip()
    name = request.form["name"].strip()

    # Read student list
    with open("student.json", "r") as file:
        students = json.load(file)

    valid = False

    for student in students:

        if (
            student["regno"].strip().lower() == regno.lower()
            and student["name"].strip().lower() == name.lower()
        ):
            valid = True
            break

    if not valid:

        return render_template(
            "login.html",
            error="Invalid Register Number or Student Name"
        )

    # Check already submitted

    with open("submitted.json", "r") as file:
        submitted = json.load(file)

    for student in submitted:

        if student["regno"] == regno:

            return render_template(
                "login.html",
                error="You have already submitted this assessment."
            )

    return render_template(
        "instructions.html",
        regno=regno,
        name=name
    )


# ===========================
# EXAM PAGE
# ===========================

@app.route("/exam", methods=["POST"])
def exam():

    regno = request.form["regno"]
    name = request.form["name"]

    with open("questions.json", "r") as file:
        questions = json.load(file)

    return render_template(
        "exam.html",
        regno=regno,
        name=name,
        questions=questions
    )


# ===========================
# SUBMIT EXAM
# ===========================

@app.route("/submit", methods=["POST"])
def submit():

    regno = request.form["regno"]
    name = request.form["name"]

    # Read previous answers

    with open("answers.json", "r") as file:
        answers = json.load(file)

    student_answers = {}

    # Store every answer

    for key in request.form:

        if key.startswith("q"):

            student_answers[key] = request.form[key]

    record = {

        "regno": regno,
        "name": name,
        "submitted_at": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "answers": student_answers

    }

    answers.append(record)

    with open("answers.json", "w") as file:

        json.dump(
            answers,
            file,
            indent=4
        )

    # Store submitted students

    with open("submitted.json", "r") as file:
        submitted = json.load(file)

    submitted.append({

        "regno": regno,
        "name": name

    })

    with open("submitted.json", "w") as file:

        json.dump(
            submitted,
            file,
            indent=4
        )

    return render_template("submit.html")
    # ===========================
# ADMIN LOGIN
# ===========================

@app.route("/admin")
def admin():
    return render_template("admin_login.html")


# ===========================
# FACULTY DASHBOARD
# ===========================

@app.route("/dashboard", methods=["POST"])
def dashboard():

    username = request.form["username"]
    password = request.form["password"]

    if username != "admin" or password != "admin123":
        return "Invalid Admin Login"

    # Read all students
    with open("student.json", "r") as file:
        all_students = json.load(file)

    # Remove Roll No. 41 (Dropout)
    all_students = [s for s in all_students if s["regno"] != "41"]

    # Read submitted answers
    with open("answers.json", "r") as file:
        students = json.load(file)

    # Read questions
    with open("questions.json", "r") as file:
        data = json.load(file)

    questions = data["mcq"]

    highest = 0
    total_score = 0

    # Calculate score for every student
    for student in students:

        score = 0

        for q in questions:

            qid = "q" + str(q["id"])

            if student["answers"].get(qid) == q["answer"]:
                score += 1

        student["score"] = score

        total_score += score

        if score > highest:
            highest = score

    total_students = len(all_students)

    attended = len(students)

    pending = total_students - attended

    average = round(total_score / attended, 2) if attended > 0 else 0

    return render_template(
        "dashboard.html",
        students=students,
        total_students=total_students,
        attended=attended,
        pending=pending,
        highest=highest,
        average=average
    )


# ===========================
# VIEW STUDENT ANSWERS
# ===========================

@app.route("/view/<int:index>")
def view(index):

    with open("answers.json", "r") as file:
        students = json.load(file)

    student = students[index]

    with open("questions.json", "r") as file:
        data = json.load(file)

    questions = data["mcq"]

    results = []

    score = 0

    for q in questions:

        qid = "q" + str(q["id"])

        student_answer = student["answers"].get(qid, "Not Answered")

        correct_answer = q["answer"]

        correct = student_answer == correct_answer

        if correct:
            score += 1

        results.append({
            "question": q["question"],
            "student_answer": student_answer,
            "correct_answer": correct_answer,
            "correct": correct
        })

    return render_template(
        "view_answers.html",
        student=student,
        results=results,
        score=score,
        total=len(questions)
    )
    # ===========================
# SHOW ALL STUDENTS
# ===========================

@app.route("/dashboard_all")
def dashboard_all():

    with open("answers.json", "r") as file:
        students = json.load(file)

    with open("student.json", "r") as file:
        all_students = json.load(file)

    # Remove Roll No. 41 (Dropout)
    all_students = [s for s in all_students if s["regno"] != "41"]

    with open("questions.json", "r") as file:
        data = json.load(file)

    questions = data["mcq"]

    highest = 0
    total_score = 0

    for student in students:

        score = 0

        for q in questions:

            qid = "q" + str(q["id"])

            if student["answers"].get(qid) == q["answer"]:
                score += 1

        student["score"] = score

        total_score += score

        if score > highest:
            highest = score

    total_students = len(all_students)
    attended = len(students)
    pending = total_students - attended
    average = round(total_score / attended, 2) if attended > 0 else 0

    return render_template(
        "dashboard.html",
        students=students,
        total_students=total_students,
        attended=attended,
        pending=pending,
        highest=highest,
        average=average
    )


# ===========================
# SEARCH STUDENT
# ===========================

@app.route("/dashboard_search")
def dashboard_search():

    search = request.args.get("search", "").strip().lower()

    with open("answers.json", "r") as file:
        students = json.load(file)

    with open("student.json", "r") as file:
        all_students = json.load(file)

    # Remove Roll No. 41 (Dropout)
    all_students = [s for s in all_students if s["regno"] != "41"]

    with open("questions.json", "r") as file:
        data = json.load(file)

    questions = data["mcq"]

    filtered = []

    highest = 0
    total_score = 0

    for student in students:

        score = 0

        for q in questions:

            qid = "q" + str(q["id"])

            if student["answers"].get(qid) == q["answer"]:
                score += 1

        student["score"] = score

        total_score += score

        if score > highest:
            highest = score

        if (
            search in student["regno"].lower()
            or search in student["name"].lower()
        ):
            filtered.append(student)

    total_students = len(all_students)
    attended = len(students)
    pending = total_students - attended
    average = round(total_score / attended, 2) if attended > 0 else 0

    return render_template(
        "dashboard.html",
        students=filtered,
        total_students=total_students,
        attended=attended,
        pending=pending,
        highest=highest,
        average=average
    )


# ===========================
# RUN APPLICATION
# ===========================
@app.route("/export")
def export():

    wb = Workbook()

    ws = wb.active

    ws.title = "Assessment Results"

    # Header Row
    ws.append([
        "Register Number",
        "Student Name",
        "Score",
        "Submission Time"
    ])

    # Read student answers
    with open("answers.json", "r") as file:
        students = json.load(file)

    # Read questions
    with open("questions.json", "r") as file:
        data = json.load(file)

    questions = data["mcq"]

    # Calculate score for each student
    for student in students:

        score = 0

        for q in questions:

            qid = "q" + str(q["id"])

            if student["answers"].get(qid) == q["answer"]:
                score += 1

        ws.append([
            student["regno"],
            student["name"],
            score,
            student["submitted_at"]
        ])

    filename = "Assessment_Results.xlsx"

    wb.save(filename)

    return send_file(
        filename,
        as_attachment=True
    )
if __name__ == "__main__":
    app.run(debug=True)