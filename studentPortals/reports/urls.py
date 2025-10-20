from django.urls import path
from. import views
from django.contrib.auth import views as auth_views


urlpatterns = [

    # Login page
    path('login/', auth_views.LoginView.as_view(template_name='reports/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),


    #student dashboard urls
    #path('', views.student_list, name='student_list'),#
    path ('<int:student_id>/', views.student_detail, name='student_detail'),
    path('<int:student_id>/courses/', views.course_list, name='course_list'),
    path('<int:course_id>/', views.toggle_enrollment, name='toggle_enrollment'),
    path('<int:course_id>/', views.add_review, name='add_review'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),


    #lecturer dashboard urls
    path('dashboard/lecturer/', views.lecturer_dashboard, name='lecturer_dashboard'),
    
    path('dashboard/lecturer/course/<int:course_id>/reviews/', views.course_reviews, name='course_reviews'),
    path('dashboard/lecturer/course/<int:course_id>/students/', views.course_students, name='course_students'),
    path('dashboard/lecturer/course/<int:course_id>/grade/<int:student_id>/', views.update_grade, name='update_grade'),
    path('dashboard/lecturer/course/create/', views.create_course, name='create_course'),
    path('dashboard/lecturer/course/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('reports/courses/<int:course_id>/review/', views.submit_review, name='submit_review'),
    path('<int:student_id>/courses/', views.my_courses, name='my_courses'),
    path('reports/courses/<int:course_id>/add_review', views.add_review, name='add_review'),

    #admin dashboard urls
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/courses/', views.admin_courses, name='admin_courses'),
    path('dashboard/admin/students/', views.admin_students, name='admin_students'),
    path('dashboard/admin/grades/', views.admin_grades, name='admin_grades'),
    path('dashboard/admin/reviews/', views.admin_reviews, name='admin_reviews'),
    path('dashboard/admin/lecturers/', views.admin_lecturers, name='admin_lecturers'),
    path('dashboard/admin/lecturers/add/', views.add_lecturer, name='add_lecturer'),
    path('dashboard/admin/lecturers/delete/<int:lecturer_id>/', views.delete_lecturer, name='delete_lecturer'),
    path('dashboard/admin/lecturers/<int:lecturer_id>/edit/', views.edit_lecturer, name='edit_lecturer'),
    path('dashboard/admin/course/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path('dashboard/admin/create_course/', views.admin_create_course, name='admin_create_course'),
    path('admin/student/<int:student_id>/', views.student_report, name='student_report'),
    path('dashboard/admin/course/<int:course_id>/students/', views.admin_course_students, name='admin_course_students'),
    
    #download btns urls
    path('download/courses/', views.download_courses_csv, name='download_courses_csv'),
    path('download/students-per-course/', views.download_students_per_course_csv, name='download_students_per_course_csv'),
    path('download/reviews/', views.download_reviews_csv, name='download_reviews_csv'),
    path('download/summary/', views.download_summary_csv, name='download_summary_csv'),


    path('logout/', views.logout_view, name='logout'),

    # Generic redirect after login
    path('dashboard/', views.login_redirect, name='login_redirect'),

]