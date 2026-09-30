# Student-Grade-Management-System
This project is all about statistics of student's grades in school.
# Student Grade Management System

A menu-driven command-line application written in Python for managing students, courses, and weighted grades. Data is stored in a local SQLite database, and reports can be exported to CSV.

## Features

- **Student management** – add, list, and delete students (deleting a student also removes their grades).
- **Course management** – add and list courses with configurable credit values.
- **Grade recording** – record scores for individual assessments (e.g. Midterm, Final) with a maximum score and a weight.
- **Student report** – view all grades per course, the weighted course percentage and letter grade, and the overall GPA.
- **Class summary** – rank students in a course and see the class average, highest, and lowest percentages.
- **CSV export** – export all grades to a CSV file.
- **Input validation** – handles invalid numbers, duplicate IDs/codes, missing students/courses, and scores above the maximum.

## Requirements

- Python 3.6 or newer
- No external packages needed (uses only the standard library: `sqlite3` and `csv`)

## Getting Started

1. Save the script, for example as `grades.py`.
2. Run it:

   ```bash
   python grades.py
   ```

3. On first run, a `grades.db` SQLite file is created automatically in the current directory.

## Usage

The main menu looks like this:

```
===== Student Grade Management System =====
1. Add student
2. List students
3. Delete student
4. Add course
5. List courses
6. Record grade
7. Student report (grades + GPA)
8. Class summary (ranking + average)
9. Export grades to CSV
0. Exit
```

Type the number of an option and follow the prompts.

### Typical workflow

1. **Add a course** (option 4), e.g. code `CS101`, title `Intro to Programming`, credits `3`.
2. **Add a student** (option 1), e.g. ID `S001`, name `Asha`.
3. **Record grades** (option 6) for the student and course, e.g. `Midterm`, score `42`, max `50`, weight `30`.
4. **View the report** (option 7) or the **class summary** (option 8).
5. **Export** everything with option 9.

## How Grades Are Calculated

**Course percentage** is a weighted average of all assessments for that student in that course:

```
percentage = sum((score / max_score) * weight) / sum(weight) * 100
```

The weights do not need to add up to 100; they are normalised automatically.

**Letter grades and grade points:**

| Percentage | Letter | Grade Points |
|------------|--------|--------------|
| 90 and above | A | 4.0 |
| 80 – 89.99 | B | 3.0 |
| 70 – 79.99 | C | 2.0 |
| 60 – 69.99 | D | 1.0 |
| Below 60 | F | 0.0 |

**GPA** is the credit-weighted average of grade points across all courses in which the student has grades:

```
GPA = sum(grade_points * credits) / sum(credits)
```

The scale can be changed by editing the `GRADE_SCALE` list at the top of the script.

## Database Schema

The database (`grades.db`) contains three tables:

| Table | Columns |
|-------|---------|
| `students` | `id` (primary key), `name`, `email` |
| `courses` | `code` (primary key), `title`, `credits` (default 3) |
| `grades` | `id` (auto), `student_id`, `course`, `item`, `score`, `max_score`, `weight` |

Foreign keys are enabled with `ON DELETE CASCADE`, so deleting a student or course removes the related grades.

## CSV Export Format

The exported file contains the following columns:

```
student_id, name, course, assessment, score, max_score, weight
```

The default filename is `grades_export.csv`; you can enter a different name when prompted.

## Project Structure

```
.
├── grades.py          # the application
├── grades.db          # SQLite database (created on first run)
└── grades_export.csv  # generated when you export (optional)
```

## Notes and Limitations

- Student IDs are case-sensitive; course codes are converted to uppercase automatically.
- Courses cannot be deleted from the menu (only students can).
- Grades cannot be edited or deleted individually from the menu; they can be changed directly in the database if needed.
- The app is single-user and intended for learning or small-scale use.

## License

This project is provided for educational use. Add your preferred license here.
