
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    gpa = models.FloatField(default=0)  # New field for GPA

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200)
    credit_units = models.IntegerField()
    lecturer = models.CharField(max_length=200)
    students = models.ManyToManyField(Student, related_name='courses', blank=True)

    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    
class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    score = models.IntegerField()
    letter = models.CharField(max_length=2, blank=True)  # new field

    def save(self, *args, **kwargs):
        if self.score is not None:
            self.score = int(self.score)
        self.letter = self.get_letter_grade()
        super().save(*args, **kwargs)

    def get_letter_grade(self):
        try:
            score = int(self.score)
        except (TypeError, ValueError):
            return 'F'
        if score >= 70:
            return 'A'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C'
        elif score >= 40:
            return 'D'
        else:
            return 'F'

    
    @property
    def grade_point(self):
        LETTER_POINTS = {
            'A': 5,
            'B': 4,
            'C': 3,
            'D': 2,
            'F': 0,
        }
        return LETTER_POINTS.get(self.letter, 0)   

    def __str__(self):
        return f"{self.student.name} - {self.course}: {self.score} ({self.letter})"
    
    @property
    def np_status(self):
        # Normal Progress if grade is A-D
        if self.letter in ['A', 'B', 'C', 'D']:
            return "NP"
        return "BNP"  # Not in Normal Progress



class CourseReview (models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.course.name} - {self.rating} by {self.student.name}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
       ("student", "Student"),
       ("lecturer", "Lecturer"),
       ("admin", "Admin"), 
    ])
    courses = models.ManyToManyField('Course', blank=True, related_name='lecturer_profiles')
    name = models.CharField(max_length=100)
    student = models.OneToOneField(Student, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.name} ({self.role})"
    
# Automatically create/update Profile when User is created/updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, name=instance.username)

