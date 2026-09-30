import csv
import sqlite3

DB_FILE = "grades.db"

# Grade scale: (minimum percentage, letter, grade points)
GRADE_SCALE = [
    (90, "A", 4.0),
    (80, "B", 3.0),
    (70, "C", 2.0),
    (60, "D", 1.0),
    (0, "F", 0.0),
]


# ---------------------------------------------------------------- database
def connect():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                id      TEXT PRIMARY KEY,
                name    TEXT NOT NULL,
                email   TEXT
            );
            CREATE TABLE IF NOT EXISTS courses (
                code    TEXT PRIMARY KEY,
                title   TEXT NOT NULL,
                credits INTEGER NOT NULL DEFAULT 3
            );
            CREATE TABLE IF NOT EXISTS grades (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                course     TEXT NOT NULL REFERENCES courses(code) ON DELETE CASCADE,
                item       TEXT NOT NULL,
                score      REAL NOT NULL,
                max_score  REAL NOT NULL,
                weight     REAL NOT NULL
            );
            """
        )


# ----------------------------------------------------------------- helpers
def ask(prompt):
    return input(prompt).strip()


def ask_float(prompt, low=None, high=None):
    while True:
        try:
            value = float(ask(prompt))
            if (low is not None and value < low) or (high is not None and value > high):
                print(f"  Enter a value between {low} and {high}.")
                continue
            return value
        except ValueError:
            print("  Please enter a number.")


def ask_int(prompt, default=None):
    while True:
        raw = ask(prompt)
        if raw == "" and default is not None:
            return default
        try:
            return int(raw)
        except ValueError:
            print("  Please enter a whole number.")


def letter_and_points(percent):
    for minimum, letter, points in GRADE_SCALE:
        if percent >= minimum:
            return letter, points
    return "F", 0.0


def student_exists(conn, sid):
    return conn.execute("SELECT 1 FROM students WHERE id=?", (sid,)).fetchone()


def course_exists(conn, code):
    return conn.execute("SELECT 1 FROM courses WHERE code=?", (code,)).fetchone()


def course_percent(conn, sid, code):
    """Weighted percentage for one student in one course (None if no grades)."""
    rows = conn.execute(
        "SELECT score, max_score, weight FROM grades WHERE student_id=? AND course=?",
        (sid, code),
    ).fetchall()
    total_weight = sum(w for _, _, w in rows)
    if not rows or total_weight == 0:
        return None
    return sum((s / m) * w for s, m, w in rows) / total_weight * 100


def student_gpa(conn, sid):
    courses = conn.execute(
        """SELECT DISTINCT c.code, c.credits FROM courses c
           JOIN grades g ON g.course = c.code WHERE g.student_id=?""",
        (sid,),
    ).fetchall()
    points = credits = 0
    for code, cr in courses:
        pct = course_percent(conn, sid, code)
        if pct is not None:
            points += letter_and_points(pct)[1] * cr
            credits += cr
    return points / credits if credits else None


# ------------------------------------------------------------------ actions
def add_student():
    sid = ask("Student ID: ")
    name = ask("Name: ")
    email = ask("Email (optional): ")
    if not sid or not name:
        print("ID and name are required.")
        return
    with connect() as conn:
        try:
            conn.execute("INSERT INTO students VALUES (?,?,?)", (sid, name, email))
            print("Student added.")
        except sqlite3.IntegrityError:
            print("A student with that ID already exists.")


def list_students():
    with connect() as conn:
        rows = conn.execute("SELECT id, name, email FROM students ORDER BY name").fetchall()
    if not rows:
        print("No students yet.")
        return
    print(f"\n{'ID':<12}{'Name':<25}Email")
    print("-" * 55)
    for sid, name, email in rows:
        print(f"{sid:<12}{name:<25}{email or ''}")


def delete_student():
    sid = ask("Student ID to delete: ")
    with connect() as conn:
        if not student_exists(conn, sid):
            print("Student not found.")
            return
        if ask("This also deletes their grades. Type YES to confirm: ") == "YES":
            conn.execute("DELETE FROM students WHERE id=?", (sid,))
            print("Student deleted.")


def add_course():
    code = ask("Course code: ").upper()
    title = ask("Course title: ")
    credits = ask_int("Credits [3]: ", default=3)
    if not code or not title:
        print("Code and title are required.")
        return
    with connect() as conn:
        try:
            conn.execute("INSERT INTO courses VALUES (?,?,?)", (code, title, credits))
            print("Course added.")
        except sqlite3.IntegrityError:
            print("A course with that code already exists.")


def list_courses():
    with connect() as conn:
        rows = conn.execute("SELECT code, title, credits FROM courses ORDER BY code").fetchall()
    if not rows:
        print("No courses yet.")
        return
    print(f"\n{'Code':<10}{'Title':<30}Credits")
    print("-" * 47)
    for code, title, credits in rows:
        print(f"{code:<10}{title:<30}{credits}")


def add_grade():
    sid = ask("Student ID: ")
    code = ask("Course code: ").upper()
    with connect() as conn:
        if not student_exists(conn, sid):
            print("Student not found.")
            return
        if not course_exists(conn, code):
            print("Course not found.")
            return
        item = ask("Assessment name (e.g. Midterm): ")
        score = ask_float("Score: ", low=0)
        max_score = ask_float("Maximum score: ", low=0.01)
        if score > max_score:
            print("Score cannot exceed the maximum.")
            return
        weight = ask_float("Weight (e.g. 30 for 30%): ", low=0)
        conn.execute(
            "INSERT INTO grades (student_id, course, item, score, max_score, weight) "
            "VALUES (?,?,?,?,?,?)",
            (sid, code, item, score, max_score, weight),
        )
        print("Grade recorded.")


def view_student_report():
    sid = ask("Student ID: ")
    with connect() as conn:
        student = conn.execute("SELECT name FROM students WHERE id=?", (sid,)).fetchone()
        if not student:
            print("Student not found.")
            return
        print(f"\n=== Report for {student[0]} ({sid}) ===")
        courses = conn.execute(
            """SELECT DISTINCT c.code, c.title, c.credits FROM courses c
               JOIN grades g ON g.course = c.code
               WHERE g.student_id=? ORDER BY c.code""",
            (sid,),
        ).fetchall()
        if not courses:
            print("No grades recorded.")
            return
        for code, title, credits in courses:
            pct = course_percent(conn, sid, code)
            letter, _ = letter_and_points(pct)
            print(f"\n{code} - {title} ({credits} cr)")
            for item, score, mx, w in conn.execute(
                "SELECT item, score, max_score, weight FROM grades "
                "WHERE student_id=? AND course=?",
                (sid, code),
            ):
                print(f"   {item:<20}{score:>6g}/{mx:<6g} weight {w:g}")
            print(f"   Course grade: {pct:.1f}% ({letter})")
        gpa = student_gpa(conn, sid)
        print(f"\nGPA: {gpa:.2f}" if gpa is not None else "\nGPA: n/a")


def class_summary():
    code = ask("Course code: ").upper()
    with connect() as conn:
        course = conn.execute("SELECT title FROM courses WHERE code=?", (code,)).fetchone()
        if not course:
            print("Course not found.")
            return
        students = conn.execute(
            """SELECT DISTINCT s.id, s.name FROM students s
               JOIN grades g ON g.student_id = s.id WHERE g.course=?""",
            (code,),
        ).fetchall()
        results = []
        for sid, name in students:
            pct = course_percent(conn, sid, code)
            if pct is not None:
                results.append((name, pct))
    if not results:
        print("No grades for this course.")
        return
    results.sort(key=lambda r: r[1], reverse=True)
    print(f"\n=== {code} - {course[0]} ===")
    print(f"{'Rank':<6}{'Student':<25}{'Percent':<10}Grade")
    for rank, (name, pct) in enumerate(results, 1):
        print(f"{rank:<6}{name:<25}{pct:<10.1f}{letter_and_points(pct)[0]}")
    avg = sum(p for _, p in results) / len(results)
    print(f"\nClass average: {avg:.1f}%  |  Highest: {results[0][1]:.1f}%  |  Lowest: {results[-1][1]:.1f}%")


def export_csv():
    filename = ask("Output file [grades_export.csv]: ") or "grades_export.csv"
    with connect() as conn, open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["student_id", "name", "course", "assessment", "score", "max_score", "weight"])
        writer.writerows(
            conn.execute(
                """SELECT s.id, s.name, g.course, g.item, g.score, g.max_score, g.weight
                   FROM grades g JOIN students s ON s.id = g.student_id
                   ORDER BY s.name, g.course"""
            )
        )
    print(f"Exported to {filename}")


# --------------------------------------------------------------------- menu
MENU = [
    ("Add student", add_student),
    ("List students", list_students),
    ("Delete student", delete_student),
    ("Add course", add_course),
    ("List courses", list_courses),
    ("Record grade", add_grade),
    ("Student report (grades + GPA)", view_student_report),
    ("Class summary (ranking + average)", class_summary),
    ("Export grades to CSV", export_csv),
]


def main():
    init_db()
    while True:
        print("\n===== Student Grade Management System =====")
        for i, (label, _) in enumerate(MENU, 1):
            print(f"{i}. {label}")
        print("0. Exit")
        choice = ask("Choose: ")
        if choice == "0":
            print("Goodbye!")
            break
        if choice.isdigit() and 1 <= int(choice) <= len(MENU):
            MENU[int(choice) - 1][1]()
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
