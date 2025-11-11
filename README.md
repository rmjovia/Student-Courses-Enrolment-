Student Courses & Enrolment Portal

A modern **Django-based web application** for managing student data, course enrolment, performance reports, and reviews.
It provides a clean interface for students, teachers, and admins to interact with academic information — now with **cloud integration via Supabase** for authentication, data storage, and deployment.

---

##  Features

###  Student Management

* Add, view, and edit student profiles.
* Track enrolment history and course performance.
* View GPA and CGPA summaries dynamically.

### Course Management

* Create and manage course details.
* Enroll students into courses easily.
* Display semester remarks and computed results in tabular format.

### Reviews System

* Students can submit and edit reviews for courses.
* Ratings (1–5) and comments are stored securely.
* Dynamic editing and validation on the same page.

###  Reports Dashboard

* Generate student-specific course reports.
* View total units, grades, and semester remarks.
* Integrated GPA and CGPA calculations.

### Cloud Integration (Supabase)

* **Supabase** handles cloud database hosting and authentication.
* Real-time updates synced with Django backend.
* Secure storage of student data and reviews.
* Supabase storage used for static/media file management.

### Deployment

* Hosted and connected via **Supabase backend**.
* Frontend templates rendered dynamically using Django’s templating engine.
* Production-ready configuration for remote hosting.

---

##  Tech Stack

| Layer               | Technology                                  |
| ------------------- | ------------------------------------------- |
| **Backend**         | Django (Python)                             |
| **Frontend**        | HTML, CSS, Bootstrap (via Django templates) |
| **Database**        | PostgreSQL (via Supabase)                   |
| **Authentication**  | Supabase Auth                               |
| **Deployment**      | Supabase / GitHub integration               |
| **Version Control** | Git & GitHub                                |
| **Hosting**         | Supabase Cloud                              |

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/rmjovia/Student-Courses-Enrolment.git
cd Student-Courses---enrolment
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/Scripts/activate   # On Windows
# OR
source venv/bin/activate       # On Mac/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Connect to Supabase

* Go to [https://supabase.com](https://supabase.com)
* Create a new project and copy your connection credentials (URL + anon/public keys).
* In your Django project, open **`settings.py`** and update:

```python
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-api-key"
```

If you used the **Supabase Python client**, install it:

```bash
pip install supabase
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a Superuser

```bash
python manage.py createsuperuser
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

Then visit:
 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

##  Project Structure

```
studentPortals/
│
├── reports/                     # Core app for reports, reviews, GPA
│   ├── templates/reports/
│   │   ├── base.html
│   │   ├── student_detail.html
│   │   ├── add_review.html
│   └── views.py
│
├── static/                      # Static assets (CSS, JS)
├── manage.py
├── settings.py
└── requirements.txt
```

---

##  Key Templates

### **student_detail.html**

Displays:

* Student info, courses, and grades
* GPA, CGPA, and semester remarks
* Enrolled course summary table

### **add_review.html**

Allows:

* Submitting and editing course reviews
* Ratings (1–5) dropdown
* Review list preview below the form

---

##  Example Use Case

1. Admin logs in and creates students and courses.
2. Students log in and view enrolled courses with grades.
3. Students can leave or update feedback for each course.
4. Reports auto-calculate **GPA**, **CGPA**, and **semester remarks**.
5. All updates sync in real-time with **Supabase cloud database**.

---

##  Deployment (Supabase + GitHub)

1. Push your latest code to GitHub:

```bash
git add .
git commit -m "Deploy updated version with Supabase integration"
git push origin main
```

2. In Supabase:

   * Connect your GitHub repo.
   * Enable **automatic deployments**.
   * Add environment variables under “Settings → API”.
   * Configure **Django ALLOWED_HOSTS** to include your Supabase domain.

---

##  Environment Variables

Create a `.env` file in your project root:

```
DEBUG=True
SECRET_KEY=your-secret-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-api-key
DATABASE_URL=postgresql://user:password@db.supabase.co:5432/dbname
```

Then load it in `settings.py`:

```python
import os
from dotenv import load_dotenv
load_dotenv()
```

##  Author

**Rachel Mukisa**
🎓 *Aspiring Computer Scientist | AI & Machine Learning Enthusiast*
💻 Passionate about web and mobile development for social impact
🔗 [GitHub Profile](https://github.com/rmjovia)

---

