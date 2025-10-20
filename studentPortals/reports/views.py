
from django.shortcuts import render,  get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .decorators import student_required, lecturer_required, admin_required
from .models import Student, Grade, Course, CourseReview, Profile
from django.contrib.auth import authenticate, login, logout
from .forms import CourseForm
from .utils import calculate_gpa, calculate_cgpa
from django.contrib import messages
import csv
from django.http import HttpResponse



# Create your views here.

def student_list(request):
    students = Student.objects.all()
    return render(request, "reports/student_list.html", {"students": students})



@login_required
@user_passes_test(student_required)
def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    # Courses enrolled via ManyToManyField
    enrolled_courses_m2m = list(student.courses.all())

    # Courses that the student has grades for
    courses_with_grades = list(Course.objects.filter(grade__student=student).distinct())

    # Merge the two lists, remove duplicates
    enrolled_courses = list({c.id: c for c in enrolled_courses_m2m + courses_with_grades}.values())
    


    # Available courses for enrollment (exclude already enrolled)
    available_courses = Course.objects.exclude(id__in=[c.id for c in enrolled_courses])

    # Handle enroll/unenroll
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        if student in course.students.all():
            course.students.remove(student)
        else:
            course.students.add(student)
        return redirect('student_detail', student_id=student.id)

    # Grades and reviews
    grades = Grade.objects.filter(student=student)

    # Semester remark
    if all(grade.np_status == "NP" for grade in grades):
        semester_remark = "Normal Progress"
    else:
        semester_remark = "Attention Needed"
    
    # Calculate GPA dynamically (or use stored value)
    gpa = calculate_gpa(student)
    cgpa = calculate_cgpa(student)  # cumulative
    
    # Prepare a list for template
    courses_with_reviews = []
    for course in enrolled_courses:
        review = course.reviews.filter(student=student).first()
        courses_with_reviews.append({
            'course': course,
            'review': review
        })

    context = {
        'student': student,
        'enrolled_courses': enrolled_courses,
        'available_courses': available_courses,
        'grades': grades,
        'gpa' : gpa,
        'cgpa' : cgpa,
        'semester_remark': semester_remark,
        'enrolled_courses': enrolled_courses,
    }
    return render(request, 'reports/student_detail.html', context)

@login_required
@user_passes_test(student_required)
def course_list(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    # Courses the student already has grades for
    graded_course_ids = Grade.objects.filter(student=student).values_list('course_id', flat=True)

    # Courses available to enroll (not graded yet)
    available_courses = Course.objects.exclude(id__in=graded_course_ids)

    # Optional search/filter
    query = request.GET.get('q')
    if query:
        available_courses = available_courses.filter(name__icontains=query)

    # Handle enroll/unenroll
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        if student in course.students.all():
            course.students.remove(student)
        else:
            course.students.add(student)
        return redirect('course_list', student_id=student.id)  # back to the same page

    context = {
        'student': student,
        'available_courses': available_courses,
        'query': query or "",
    }
    return render(request, 'reports/course_list.html', context)


def toggle_enrollment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    student = Student.objects.get(user=request.user)
    if student in course.students.all():
        course.students.remove(student)
    else:
        course.students.add(student)
    return redirect('course_list')


@login_required
def add_review(request, course_id):
    student = get_object_or_404(Student, user=request.user)
    course = get_object_or_404(Course, id=course_id)
    enrolled_courses = student.courses.all()  # all courses student is enrolled in
    reviews = CourseReview.objects.filter(student=student)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        # Update existing review or create new
        review, created = CourseReview.objects.update_or_create(
            student=student,
            course=course,
            defaults={'rating': rating, 'comment': comment}
        )
        return redirect('student_detail', student_id=student.id)

    return render(request, 'reports/add_review.html', {
        'student': student,
        'enrolled_courses': enrolled_courses,
        'reviews': reviews,
        'selected_course': course  # new
    })

@login_required
@user_passes_test(lecturer_required)
def lecturer_dashboard(request):
    lecturer = Profile.objects.get(user=request.user)
    courses = Course.objects.filter(lecturer=lecturer.name)

    context = {
        'lecturer': lecturer,
        'courses': courses
    }
    return render(request, 'reports/lecturer_dashboard.html', context)

@login_required
@user_passes_test(student_required)
def student_dashboard(request):
    # student-specific actions
    return render(request, 'students/student_detail.html')


@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == 'admin')
def admin_dashboard(request):
    courses = Course.objects.all().order_by('-id')
    students = Student.objects.all()
    grades = Grade.objects.all()

    # basic stats
    total_students = students.count()
    total_lecturers = Profile.objects.filter(role='lecturer').count()
    total_courses = courses.count()
    total_grades = grades.count()

    # recent courses (limit 8)
    recent_courses = courses[:8]

    # simple top students sample: compute GPA per student and pick top 5
    top_students = []
    for student in students:
        gset = Grade.objects.filter(student=student)
        total_points = sum((g.grade_point or 0) * g.course.credit_units for g in gset)
        total_units = sum(g.course.credit_units for g in gset)
        gpa = round(total_points / total_units, 2) if total_units > 0 else 0
         
        top_students.append({'student': student, 'gpa': gpa})
    top_students = sorted(top_students, key=lambda x: x['gpa'], reverse=True)[:5]

    context = {
        'courses': courses,
        'students': students,
        'total_students': total_students,
        'total_lecturers': total_lecturers,
        'total_courses': total_courses,
        'total_grades': total_grades,
        'recent_courses': recent_courses,
        'top_students': top_students,
        
    }
    return render(request, 'reports/admin_dashboard.html', context)

@login_required
@user_passes_test(admin_required)
def admin_courses(request):
    courses = Course.objects.all()
    return render(request, 'reports/admin_courses.html', {'courses': courses})

@login_required
@user_passes_test(admin_required)
def admin_students(request):
    students = Student.objects.all()
    students_with_gpa = []

    for student in students:
        student_grades = Grade.objects.filter(student=student)
        total_points = sum((g.grade_point or 0) * g.course.credit_units for g in student_grades)
        total_units = sum(g.course.credit_units for g in student_grades)
        gpa = round(total_points / total_units, 2) if total_units > 0 else 0

        # For simplicity, CGPA = GPA here (or calculate across semesters if available)
        cgpa = gpa

        students_with_gpa.append({
            'student': student,
            'gpa': gpa,
            'cgpa': cgpa,
        })

    return render(request, 'reports/admin_students.html', {
        'students_with_gpa': students_with_gpa
    })

@login_required
@user_passes_test(admin_required)
def student_report(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    grades = Grade.objects.filter(student=student)
    gpa = calculate_gpa(student)
    cgpa = calculate_cgpa(student)

    context = {
        'student': student,
        'grades': grades,
        'gpa': gpa,
        'cgpa': cgpa,
    }
    return render(request, 'reports/student_report.html', context)


@login_required
@user_passes_test(admin_required)
def admin_grades(request):
    grades = Grade.objects.all()
    return render(request, 'reports/admin_grades.html', {'grades': grades})

@login_required
@user_passes_test(admin_required)
def admin_reviews(request):
    reviews = CourseReview.objects.all()
    return render(request, 'reports/admin_reviews.html', {'reviews': reviews})


@login_required
@user_passes_test(admin_required)
def admin_lecturers(request):
    lecturers = Profile.objects.filter(role='lecturer')
    courses = Course.objects.all()  # fetch all courses

    context = {
        'lecturers': lecturers,
        'courses': courses,  # pass to template
    }

    return render(request, 'reports/admin_lecturers.html', context)

@login_required
@user_passes_test(admin_required)
def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.lecturer = request.user.profile.name
            course.save()
            return redirect('admin_dashboard')
    else:
        form = CourseForm()
    return render(request, 'reports/create_course.html', {'form': form})

def add_lecturer(request):
    courses = Course.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        course_ids = request.POST.getlist('courses')

        if name and email and password:
            # Create a new user and lecturer
            user = user.objects.create_user(username=name, email=email, password=password)
            lecturer = lecturer.objects.create(user=user)

            # Assign selected courses
            selected_courses = Course.objects.filter(id__in=course_ids)
            lecturer.courses.set(selected_courses)
            lecturer.save()

            messages.success(request, f'Lecturer {name} added successfully with assigned courses!')
            return redirect('admin_lecturers')

    return render(request, 'reports/add_lecturer.html', {'courses': courses})

def delete_lecturer(request, lecturer_id):
    lecturer = get_object_or_404(lecturer, id=lecturer_id)
    lecturer.user.delete()  # deletes both lecturer and linked user
    
    messages.success(request, 'Lecturer deleted successfully!')
    return redirect('admin_lecturers')


@login_required
def admin_create_course(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        credit_units = request.POST.get('credit_units')
        lecturer_name = request.POST.get('lecturer')  # select from dropdown maybe

        if name and code and credit_units and lecturer_name:
            Course.objects.create(
                name=name,
                code=code,
                credit_units=credit_units,
                lecturer=lecturer_name
            )
            messages.success(request, 'Course added successfully!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Please fill all fields.')

    lecturers = Profile.objects.filter(role='lecturer')
    return render(request, 'reports/admin_create_course.html', {'lecturers': lecturers})

@login_required
@user_passes_test(admin_required)
def admin_course_students(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Students explicitly enrolled via ManyToMany
    students_from_m2m = list(course.students.all())
    # Students who have grades (may not be in M2M)
    students_from_grades = [grade.student for grade in Grade.objects.filter(course=course)]
    # Merge and remove duplicates
    students = list({student.id: student for student in students_from_m2m + students_from_grades}.values())

    # Prepare data for template
    students_with_grades = []
    for student in students:
        grade = Grade.objects.filter(student=student, course=course).first()
        students_with_grades.append({'student': student, 'grade': grade})

    return render(request, 'reports/admin_course_students.html', {
        'course': course,
        'students_with_grades': students_with_grades
    })



@login_required
@user_passes_test(admin_required)  # make sure you have this decorator
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course.delete()
        messages.success(request, f"Course '{course.name}' has been deleted.")
        return redirect('admin_courses')  # redirect to admin courses page
    return render(request, 'reports/confirm_delete.html', {'object': course, 'type': 'Course'})

def edit_lecturer(request, lecturer_id):
    # Assuming Profile model has a 'user' field linked to User and a 'role' field
    lecturer = get_object_or_404(Profile, id=lecturer_id, role='lecturer')
    courses = Course.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        course_ids = request.POST.getlist('courses')

        # Update lecturer's user info
        lecturer.user.username = name
        lecturer.user.email = email
        if password:
            lecturer.user.set_password(password)
        lecturer.user.save()

        # Update assigned courses
        selected_courses = Course.objects.filter(id__in=course_ids)
        lecturer.courses.set(selected_courses)
        lecturer.save()

        messages.success(request, f"Lecturer {name}'s details were updated successfully.")
        return redirect('admin_lecturers')

    context = {
        'lecturer': lecturer,
        'courses': courses,
    }
    return render(request, 'reports/edit_lecturer.html', context)


@login_required
def login_redirect(request):
    profile = request.user.profile

    if profile.role == 'student':
        # Find the corresponding Student instance
        try:
            student = Student.objects.get(email=request.user.email)
            return redirect('student_detail', student_id=student.id)
        except Student.DoesNotExist:
            # fallback if Student record missing
            return redirect('lecturer_dashboard')
    elif profile.role == 'lecturer':
        return redirect('lecturer_dashboard')
    elif profile.role == 'admin':
        return redirect('admin_dashboard')
    

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@user_passes_test(lecturer_required)
def course_students(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Students explicitly enrolled via M2M
    students_from_m2m = list(course.students.all())
    students_from_grades = [grade.student for grade in Grade.objects.filter(course=course)]
    students = list({student.id: student for student in students_from_m2m + students_from_grades}.values())

    # Handle grade submission
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        score = request.POST.get('score')
        student = get_object_or_404(Student, id=student_id)
        grade, created = Grade.objects.get_or_create(student=student, course=course, defaults={'score': score})
        if not created:
            grade.score = score
            grade.save()
        return redirect('course_students', course_id=course.id)
    
    

    # Prepare data for template
    students_with_grades = []
    for student in students:
        grade = Grade.objects.filter(student=student, course=course).first()
        students_with_grades.append({'student': student, 'grade': grade})

    return render(request, 'reports/course_students.html', {
        'course': course,
        'students_with_grades': students_with_grades
    })



    

@login_required
@user_passes_test(lecturer_required)  # Make sure this decorator exists
def update_grade(request, course_id, student_id):
    course = get_object_or_404(Course, id=course_id)
    student = get_object_or_404(Student, id=student_id)

    # Get or create the grade object
    grade, created = Grade.objects.get_or_create(student=student, course=course)

    if request.method == 'POST':
        score = request.POST.get('score')
        if score:
            grade.score = int(score)
            grade.save()
        # Redirect back to the students list to show updated grade
        return redirect('course_students', course_id=course.id)

    return render(request, 'reports/update_grade.html', {
        'grade': grade,
        'student': student,
        'course': course
    })


@login_required
@user_passes_test(lecturer_required)  # ensures only lecturers can access
def course_reviews(request, course_id):
    # Make sure the course belongs to this lecturer
    course = get_object_or_404(Course, id=course_id, lecturer=request.user.profile.name)
    
    # Fetch reviews efficiently with related student info
    reviews = CourseReview.objects.filter(course=course).select_related('student')
    
    return render(request, 'reports/course_reviews.html', {'course': course, 'reviews': reviews})


@login_required
@user_passes_test(lecturer_required)
def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.lecturer = request.user.profile.name
            course.save()
            return redirect('lecturer_dashboard')
    else:
        form = CourseForm()
    return render(request, 'reports/create_course.html', {'form': form})


@login_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Optional: Restrict lecturers to only edit their own courses
    if hasattr(request.user, 'profile'):
        if request.user.profile.role == 'lecturer' and course.lecturer != request.user.profile:
            return redirect('lecturer_dashboard')

    if request.method == 'POST':
        course.name = request.POST.get('name')
        course.code = request.POST.get('code')
        course.credit_units = request.POST.get('credit_units')

        lecturer_id = request.POST.get('lecturer')
        if lecturer_id:
            course.lecturer = get_object_or_404(Profile, id=lecturer_id)

        course.save()

        # Redirect based on who made the edit
        if request.user.profile.role == 'lecturer':
            return redirect('lecturer_dashboard')
        else:
            return redirect('courses_management')

    lecturers = Profile.objects.filter(role='lecturer')
    return render(request, 'reports/edit_course.html', {'course': course, 'lecturers': lecturers})

@login_required
@user_passes_test(student_required)
def submit_review(request, course_id):
    #student = request.user.profile.student  # get the logged-in student
    
    student = Student.objects.get(email=request.user.email)
    course = get_object_or_404(Course, id=course_id)

    # Rating options
    rating_choices = [1, 2, 3, 4, 5]

    # Get existing review if any
    review = CourseReview.objects.filter(student=student, course=course).first()

    if request.method == 'POST':
        rating = int(request.POST['rating'])
        comment = request.POST['comment'].strip()
        if review:
            review.rating = rating
            review.comment = comment
            review.save()
        else:
            CourseReview.objects.create(student=student, course=course, rating=rating, comment=comment)
        return redirect('student_detail', student_id=student.id)

    context = {
        'course': course,
        'review': review,
        'rating_choices': rating_choices,
        'student': student,
    }
    return render(request, 'reports/submit_review.html', context)


@login_required
@user_passes_test(student_required)
def my_courses(request):
    student = request.user.profile
    courses = student.courses.all()  # ManyToManyField
    return render(request, 'reports/my_courses.html', {'courses': courses})



#csv donload views

def download_courses_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="courses.csv"'
    writer = csv.writer(response)
    writer.writerow(['Course Name', 'Code', 'Credit Units', 'Lecturer'])

    for course in Course.objects.all():
        writer.writerow([course.name, course.code, course.credit_units, course.lecturer])

    return response


def download_students_per_course_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students_per_course.csv"'
    writer = csv.writer(response)
    writer.writerow(['Course', 'Student Name', 'Email'])

    for course in Course.objects.all():
        for student in course.students.all():
            writer.writerow([course.name, student.name, student.email])

    return response


def download_reviews_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="course_reviews.csv"'
    writer = csv.writer(response)
    writer.writerow(['Course', 'Student', 'Rating', 'Comment'])

    for review in CourseReview.objects.all():
        writer.writerow([review.course.name, review.student.name, review.rating, review.comment])

    return response


def download_summary_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="system_summary.csv"'
    writer = csv.writer(response)
    writer.writerow(['Summary Type', 'Count'])

    writer.writerow(['Total Courses', Course.objects.count()])
    writer.writerow(['Total Students', sum(c.students.count() for c in Course.objects.all())])
    writer.writerow(['Total Lecturers', len(set(c.lecturer for c in Course.objects.all() if c.lecturer))])
    writer.writerow(['Total Reviews', CourseReview.objects.count()])

    return response

from django.shortcuts import render,  get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .decorators import student_required, lecturer_required, admin_required
from .models import Student, Grade, Course, CourseReview
from django.contrib.auth import authenticate, login, logout
from .forms import CourseForm


# Create your views here.

def student_list(request):
    students = Student.objects.all()
    return render(request, "reports/student_list.html", {"students": students})



@login_required
@user_passes_test(student_required)
def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    # Courses enrolled via ManyToManyField
    enrolled_courses_m2m = list(student.courses.all())

    # Courses that the student has grades for
    courses_with_grades = list(Course.objects.filter(grade__student=student).distinct())

    # Merge the two lists, remove duplicates
    enrolled_courses = list({c.id: c for c in enrolled_courses_m2m + courses_with_grades}.values())

    # Available courses for enrollment (exclude already enrolled)
    available_courses = Course.objects.exclude(id__in=[c.id for c in enrolled_courses])

    # Handle enroll/unenroll
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        if student in course.students.all():
            course.students.remove(student)
        else:
            course.students.add(student)
        return redirect('student_detail', student_id=student.id)

    # Grades and reviews
    grades = Grade.objects.filter(student=student)

    # Prepare a list for template
    courses_with_reviews = []
    for course in enrolled_courses:
        review = course.reviews.filter(student=student).first()
        courses_with_reviews.append({
            'course': course,
            'review': review
        })

    context = {
        'student': student,
        'enrolled_courses': enrolled_courses,
        'available_courses': available_courses,
        'grades': grades,
        
    }
    return render(request, 'reports/student_detail.html', context)

@login_required
@user_passes_test(student_required)
def course_list(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    # Courses the student already has grades for
    graded_course_ids = Grade.objects.filter(student=student).values_list('course_id', flat=True)

    # Courses available to enroll (not graded yet)
    available_courses = Course.objects.exclude(id__in=graded_course_ids)

    # Optional search/filter
    query = request.GET.get('q')
    if query:
        available_courses = available_courses.filter(name__icontains=query)

    # Handle enroll/unenroll
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        if student in course.students.all():
            course.students.remove(student)
        else:
            course.students.add(student)
        return redirect('course_list', student_id=student.id)  # back to the same page

    context = {
        'student': student,
        'available_courses': available_courses,
        'query': query or "",
    }
    return render(request, 'reports/course_list.html', context)


def toggle_enrollment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    student = Student.objects.get(user=request.user)
    if student in course.students.all():
        course.students.remove(student)
    else:
        course.students.add(student)
    return redirect('course_list')


@login_required
def add_review(request, course_id):
    student = get_object_or_404(Student, user=request.user)
    course = get_object_or_404(Course, id=course_id)
    enrolled_courses = student.courses.all()  # all courses student is enrolled in
    reviews = CourseReview.objects.filter(student=student)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        # Update existing review or create new
        review, created = CourseReview.objects.update_or_create(
            student=student,
            course=course,
            defaults={'rating': rating, 'comment': comment}
        )
        return redirect('student_detail', student_id=student.id)

    return render(request, 'reports/add_review.html', {
        'student': student,
        'enrolled_courses': enrolled_courses,
        'reviews': reviews,
        'selected_course': course  # new
    })

@login_required
@user_passes_test(student_required)
def student_dashboard(request):
    # student-specific actions
    return render(request, 'students/student_detail.html')

@login_required
@user_passes_test(lecturer_required)
def lecturer_dashboard(request):
    lecturer_name = request.user.username  # assuming lecturer name = username
    courses = Course.objects.filter(lecturer=request.user)
    return render(request, 'reports/lecturer_dashboard.html', {'courses': courses})

@login_required
@user_passes_test(admin_required)
def admin_dashboard(request):
    # Example: admin can manage everything
    students = Student.objects.all()
    courses = Course.objects.all()
    return render(request, 'reports/admin_dashboard.html', {'students': students, 'courses': courses})



@login_required
def login_redirect(request):
    profile = request.user.profile

    if profile.role == 'student':
        # Find the corresponding Student instance
        try:
            student = Student.objects.get(email=request.user.email)
            return redirect('student_detail', student_id=student.id)
        except Student.DoesNotExist:
            # fallback if Student record missing
            return redirect('lecturer_dashboard')
    elif profile.role == 'lecturer':
        return redirect('lecturer_dashboard')
    elif profile.role == 'admin':
        return redirect('admin_dashboard')
    

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@user_passes_test(lecturer_required)
def course_students(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Students explicitly enrolled via M2M
    students_from_m2m = list(course.students.all())
    students_from_grades = [grade.student for grade in Grade.objects.filter(course=course)]
    students = list({student.id: student for student in students_from_m2m + students_from_grades}.values())

    # Handle grade submission
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        score = request.POST.get('score')
        student = get_object_or_404(Student, id=student_id)
        grade, created = Grade.objects.get_or_create(student=student, course=course, defaults={'score': score})
        if not created:
            grade.score = score
            grade.save()
        return redirect('course_students', course_id=course.id)

    # Prepare data for template
    students_with_grades = []
    for student in students:
        grade = Grade.objects.filter(student=student, course=course).first()
        students_with_grades.append({'student': student, 'grade': grade})

    return render(request, 'reports/course_students.html', {
        'course': course,
        'students_with_grades': students_with_grades
    })

@login_required
@user_passes_test(lecturer_required)  # Make sure this decorator exists
def update_grade(request, course_id, student_id):
    course = get_object_or_404(Course, id=course_id)
    student = get_object_or_404(Student, id=student_id)

    # Get or create the grade object
    grade, created = Grade.objects.get_or_create(student=student, course=course)

    if request.method == 'POST':
        score = request.POST.get('score')
        if score:
            grade.score = int(score)
            grade.save()
        # Redirect back to the students list to show updated grade
        return redirect('course_students', course_id=course.id)

    return render(request, 'reports/update_grade.html', {
        'grade': grade,
        'student': student,
        'course': course
    })


@login_required
@user_passes_test(lecturer_required)  # ensures only lecturers can access
def course_reviews(request, course_id):
    # Make sure the course belongs to this lecturer
    course = get_object_or_404(Course, id=course_id, lecturer=request.user)
    
    # Fetch reviews efficiently with related student info
    reviews = CourseReview.objects.filter(course=course).select_related('student')
    
    return render(request, 'reports/course_reviews.html', {'course': course, 'reviews': reviews})


@login_required
@user_passes_test(lecturer_required)
def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.lecturer = request.user
            course.save()
            return redirect('lecturer_dashboard')
    else:
        form = CourseForm()
    return render(request, 'reports/create_course.html', {'form': form})

@login_required
@user_passes_test(lecturer_required)
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, lecturer=request.user)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('lecturer_dashboard')
    else:
        form = CourseForm(instance=course)
    return render(request, 'reports/edit_course.html', {'form': form, 'course': course})

@login_required
@user_passes_test(student_required)
def submit_review(request, course_id):
    #student = request.user.profile.student  # get the logged-in student
    
    student = Student.objects.get(email=request.user.email)
    course = get_object_or_404(Course, id=course_id)

    # Rating options
    rating_choices = [1, 2, 3, 4, 5]

    # Get existing review if any
    review = CourseReview.objects.filter(student=student, course=course).first()

    if request.method == 'POST':
        rating = int(request.POST['rating'])
        comment = request.POST['comment'].strip()
        if review:
            review.rating = rating
            review.comment = comment
            review.save()
        else:
            CourseReview.objects.create(student=student, course=course, rating=rating, comment=comment)
        return redirect('student_detail', student_id=student.id)

    context = {
        'course': course,
        'review': review,
        'rating_choices': rating_choices,
        'student': student,
    }
    return render(request, 'reports/submit_review.html', context)


@login_required
@user_passes_test(student_required)
def my_courses(request):
    student = request.user.profile
    courses = student.courses.all()  # ManyToManyField
    return render(request, 'reports/my_courses.html', {'courses': courses})

