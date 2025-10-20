from .models import Grade

LETTER_POINTS = {
    'A': 5,
    'B': 4,
    'C': 3,
    'D': 2,
    'F': 0,
}

def calculate_gpa(student):
    grades = Grade.objects.filter(student=student)
    if not grades.exists():
        return 0  # GPA

    total_points = 0
    total_credits = 0

    for grade in grades:
        points = LETTER_POINTS.get(grade.letter, 0)
        total_points += points * grade.course.credit_units
        total_credits += grade.course.credit_units

    gpa = total_points / total_credits if total_credits else 0
    return round(gpa, 2)

def calculate_cgpa(student):
    grades = student.grade_set.all()  # all grades for the student
    total_points = 0
    total_credits = 0

    for grade in grades:
        points = LETTER_POINTS.get(grade.letter, 0)
        total_points += points * grade.course.credit_units
        total_credits += grade.course.credit_units

    if total_credits == 0:
        return 0
    return round(total_points / total_credits, 2)
