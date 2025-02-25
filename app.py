from flask import Flask, render_template, request, redirect, session, flash, url_for, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime, timedelta
import os
import random
import string
from math import radians, sin, cos, sqrt, atan2
import uuid
from werkzeug.utils import secure_filename
from functools import wraps
from init_db import init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'pdf'}

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database tables
init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    db = sqlite3.connect('campus_connect.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cursor = db.cursor()
    
    # Create all tables
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS student (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            student_type TEXT NOT NULL CHECK(student_type IN ('hosteller', 'day_scholar')),
            FOREIGN KEY (user_id) REFERENCES user (id)
        );

        CREATE TABLE IF NOT EXISTS class_teacher (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );

        CREATE TABLE IF NOT EXISTS hod (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );

        CREATE TABLE IF NOT EXISTS printer_shop (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );

        CREATE TABLE IF NOT EXISTS hostel_warden (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            hostel_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );

        CREATE TABLE IF NOT EXISTS student_care (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );

        CREATE TABLE IF NOT EXISTS health_centre (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            doctor_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );

        CREATE TABLE IF NOT EXISTS leave_application (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reason TEXT NOT NULL,
            class_teacher_status TEXT DEFAULT 'pending',
            hod_status TEXT DEFAULT 'pending',
            warden_status TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student (id)
        );

        CREATE TABLE IF NOT EXISTS print_request (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            drive_link TEXT,
            is_color BOOLEAN NOT NULL,
            is_double_sided BOOLEAN NOT NULL,
            copies INTEGER NOT NULL,
            pages INTEGER NOT NULL,
            total_cost REAL NOT NULL,
            pickup_code TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student(id)
        );

        CREATE TABLE IF NOT EXISTS lost_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            phone_number TEXT,
            image_path TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'found', 'returned')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            found_at TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student (id)
        );

        CREATE TABLE IF NOT EXISTS student_notification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            type TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student (id)
        );

        CREATE TABLE IF NOT EXISTS club (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            coordinator_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (coordinator_id) REFERENCES user (id)
        );

        CREATE TABLE IF NOT EXISTS club_member (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            club_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('member', 'president', 'secretary')),
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (club_id) REFERENCES club (id),
            FOREIGN KEY (student_id) REFERENCES student (id)
        );

        CREATE TABLE IF NOT EXISTS venue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            capacity INTEGER NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            club_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            expected_participants INTEGER NOT NULL,
            event_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            venue_id INTEGER,
            needs_transport BOOLEAN NOT NULL DEFAULT 0,
            transport_details TEXT,
            needs_food BOOLEAN NOT NULL DEFAULT 0,
            food_details TEXT,
            coordinator_approval TEXT DEFAULT 'pending',
            principal_approval TEXT DEFAULT 'pending',
            transport_approval TEXT DEFAULT NULL,
            food_approval TEXT DEFAULT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (club_id) REFERENCES club (id),
            FOREIGN KEY (venue_id) REFERENCES venue (id)
        );

        CREATE TABLE IF NOT EXISTS venue_booking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venue_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            booking_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (venue_id) REFERENCES venue (id),
            FOREIGN KEY (event_id) REFERENCES event (id)
        );

        CREATE TABLE IF NOT EXISTS notification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );

        CREATE TABLE IF NOT EXISTS ride_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            pickup_lat REAL NOT NULL,
            pickup_lng REAL NOT NULL,
            drop_lat REAL NOT NULL,
            drop_lng REAL NOT NULL,
            pickup_address TEXT NOT NULL,
            drop_address TEXT NOT NULL,
            departure_time TEXT NOT NULL,
            gender_preference TEXT,
            additional_notes TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            matched_with INTEGER,
            FOREIGN KEY (student_id) REFERENCES student (id),
            FOREIGN KEY (matched_with) REFERENCES ride_requests (id)
        );

        -- Index for faster location-based queries
        CREATE INDEX IF NOT EXISTS idx_ride_locations 
        ON ride_requests (pickup_lat, pickup_lng, drop_lat, drop_lng);
        
        -- Index for status and time based queries
        CREATE INDEX IF NOT EXISTS idx_ride_status_time 
        ON ride_requests (status, departure_time);
    ''')
    
    db.commit()
    db.close()

def init_sample_data():
    db = get_db()
    cursor = db.cursor()
    
    # Check if data already exists
    user_count = cursor.execute('SELECT COUNT(*) FROM user').fetchone()[0]
    if user_count > 0:
        print("Sample data already exists, skipping initialization")
        db.close()
        return
        
    password = generate_password_hash('password123')
    
    # Add new roles to users list
    users = [
        ('admin@campus.com', password, 'admin'),
        ('printer@campus.com', password, 'printer'),
        ('warden@campus.com', password, 'warden'),
        ('hod_cse@campus.com', password, 'hod'),
        ('hod_ece@campus.com', password, 'hod'),  # Add ECE HOD
        ('teacher_cse@campus.com', password, 'class_teacher'),
        ('teacher_ece@campus.com', password, 'class_teacher'),
        ('studentcare@campus.com', password, 'student_care'),
        ('doctor@campus.com', password, 'doctor'),
        ('student1@campus.com', password, 'student'),
        ('student2@campus.com', password, 'student'),
        ('transport@campus.com', password, 'transport'),
        ('food@campus.com', password, 'food'),
        ('coordinator1@campus.com', password, 'coordinator'),
        ('coordinator2@campus.com', password, 'coordinator'),
        ('principal@campus.com', password, 'principal')
    ]
    
    # Dictionary to store user IDs
    user_ids = {}
    
    print("\nInserted users:")
    for email, pwd, role in users:
        cursor.execute('INSERT INTO user (email, password, role) VALUES (?, ?, ?)', 
                      (email, pwd, role))
        user_id = cursor.lastrowid
        user_ids[email] = user_id  # Store ID in dictionary
        print(f"ID: {user_id}, Email: {email}, Role: {role}")
    
    # Insert class teachers
    cursor.execute('''
        INSERT INTO class_teacher (user_id, name, department)
        VALUES (?, ?, ?)
    ''', (user_ids['teacher_cse@campus.com'], 'Prof. Johnson', 'Computer Science'))
    
    cursor.execute('''
        INSERT INTO class_teacher (user_id, name, department)
        VALUES (?, ?, ?)
    ''', (user_ids['teacher_ece@campus.com'], 'Prof. Williams', 'Electronics'))
    
    # Insert HODs
    cursor.execute('''
        INSERT INTO hod (user_id, name, department)
        VALUES (?, ?, ?)
    ''', (user_ids['hod_cse@campus.com'], 'Dr. Smith', 'Computer Science'))
    
    cursor.execute('''
        INSERT INTO hod (user_id, name, department)
        VALUES (?, ?, ?)
    ''', (user_ids['hod_ece@campus.com'], 'Dr. Brown', 'Electronics'))
    
    # Insert students
    cursor.execute('''
        INSERT INTO student (user_id, name, roll_number, department, student_type)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_ids['student1@campus.com'], 'John Doe', '2023CSE001', 'Computer Science', 'hosteller'))
    student1_db_id = cursor.lastrowid
    
    # Add student2
    cursor.execute('''
        INSERT INTO student (user_id, name, roll_number, department, student_type)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_ids['student2@campus.com'], 'Jane Smith', '2023CSE002', 'Computer Science', 'day_scholar'))
    student2_db_id = cursor.lastrowid
    
    # Add sample clubs
    clubs = [
        ('Enactus Club', 'Social entrepreneurship club', user_ids['coordinator1@campus.com']),
        ('Coding Club', 'Programming and technology club', user_ids['coordinator2@campus.com'])
    ]
    
    print("\nCreating clubs:")
    for name, desc, coord_id in clubs:
        cursor.execute('''
            INSERT INTO club (name, description, coordinator_id)
            VALUES (?, ?, ?)
        ''', (name, desc, coord_id))
        club_id = cursor.lastrowid
        print(f"Created club: {name} with ID: {club_id}")
        
        # If it's Enactus Club, add student1 as president
        if name == 'Enactus Club':
            cursor.execute('''
                INSERT INTO club_member (club_id, student_id, role)
                VALUES (?, ?, 'president')
            ''', (club_id, student1_db_id))
            print(f"Added student1 as president of {name}")
    
    # Add venues
    venues = [
        ('Purple Hall', 500, 'Main auditorium'),
        ('Main Seminar Hall', 300, 'Secondary auditorium'),
        ('Indoor Auditorium', 200, 'Air-conditioned hall'),
        ('Idea Lab 1', 50, 'Innovation lab'),
        ('Idea Lab 2', 50, 'Innovation lab'),
        ('Idea Lab 3', 50, 'Innovation lab'),
        ('Heritage Hall', 150, 'Traditional styled hall'),
        ('Conference Hall', 100, 'Meeting room')
    ]
    
    print("\nCreating venues:")
    for name, capacity, desc in venues:
        cursor.execute('''
            INSERT INTO venue (name, capacity, description)
            VALUES (?, ?, ?)
        ''', (name, capacity, desc))
        print(f"Created venue: {name}")
    
    # Create printer shop entry
    cursor.execute('''
        INSERT INTO printer_shop (user_id)
        VALUES (?)
    ''', (user_ids['printer@campus.com'],))
    
    db.commit()
    db.close()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = get_db()
        cursor = db.cursor()
        user = cursor.execute('SELECT * FROM user WHERE email = ?', (email,)).fetchone()
        db.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            
            # Special handling for student_care role
            if user['role'] == 'student_care':
                return redirect(url_for('student_care_lost_items'))  # Redirect directly to lost items page
            
            return redirect('/')
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/leave/apply', methods=['GET', 'POST'])
def apply_leave():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Please login as a student')
        return redirect('/login')
    
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        # Get student details including type
        student = cursor.execute('''
            SELECT id, student_type, department FROM student WHERE user_id = ?
        ''', (session['user_id'],)).fetchone()
        
        if not student:
            flash('Student record not found')
            return redirect('/')
        
        # Print debug info
        print(f"\nCreating leave application:")
        print(f"Student ID: {student['id']}")
        print(f"Department: {student['department']}")
        print(f"Type: {student['student_type']}")
        
        # Set warden_status based on student type
        warden_status = 'pending' if student['student_type'] == 'hosteller' else None
        
        cursor.execute('''
            INSERT INTO leave_application 
            (student_id, start_date, end_date, reason, warden_status, class_teacher_status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (
            student['id'],
            request.form['start_date'],
            request.form['end_date'],
            request.form['reason'],
            warden_status
        ))
        
        # Print the inserted application
        app_id = cursor.lastrowid
        print(f"Created application ID: {app_id}")
        
        db.commit()
        db.close()
        flash('Leave application submitted successfully')
        return redirect('/leave/status')
        
    return render_template('leave_apply.html')

@app.route('/leave/status')
def leave_status():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Please login as a student')
        return redirect('/login')
        
    db = get_db()
    cursor = db.cursor()
    
    # Get student's leave applications with all statuses
    applications = cursor.execute('''
        SELECT 
            leave_application.*,
            student.name as student_name,
            student.student_type,
            class_teacher.name as teacher_name,
            hod.name as hod_name
        FROM leave_application 
        JOIN student ON student.id = leave_application.student_id
        LEFT JOIN class_teacher ON class_teacher.department = student.department
        LEFT JOIN hod ON hod.department = student.department
        WHERE student.user_id = ?
        ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    if not session.get('student_type'):
        student = cursor.execute('SELECT student_type FROM student WHERE user_id = ?', 
                               (session['user_id'],)).fetchone()
        if student:
            session['student_type'] = student['student_type']
    
    db.close()
    return render_template('leave_status.html', applications=applications)

@app.route('/leave/<int:application_id>/teacher-review', methods=['POST'])
def teacher_review_action(application_id):
    if 'user_id' not in session or session['role'] != 'class_teacher':
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify teacher is assigned to student's department
        is_teacher = cursor.execute('''
            SELECT 1 FROM leave_application
            JOIN student ON student.id = leave_application.student_id
            JOIN class_teacher ON class_teacher.department = student.department
            WHERE leave_application.id = ? 
            AND class_teacher.user_id = ?
        ''', (application_id, session['user_id'])).fetchone()
        
        if not is_teacher:
            return jsonify({'error': 'Not authorized for this student'}), 403
            
        # Update application status
        cursor.execute('''
            UPDATE leave_application 
            SET class_teacher_status = ?,
                hod_status = CASE 
                    WHEN ? = 'approved' THEN 'pending'
                    ELSE NULL
                END
            WHERE id = ?
        ''', (status, status, application_id))
        
        db.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/leave/review/hod')
def hod_review():
    if 'user_id' not in session or session['role'] != 'hod':
        flash('Unauthorized access')
        return redirect('/')
        
    db = get_db()
    cursor = db.cursor()
    
    # Get class-teacher approved applications for HOD's department
    applications = cursor.execute('''
        SELECT leave_application.*, 
               student.name as student_name, 
               student.roll_number, 
               student.department
        FROM leave_application 
        JOIN student ON student.id = leave_application.student_id
        JOIN hod ON hod.department = student.department
        WHERE hod.user_id = ? 
        AND class_teacher_status = 'approved' 
        AND hod_status = 'pending'
        ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    db.close()
    return render_template('hod_review.html', applications=applications)

@app.route('/leave/review/warden')
def warden_review():
    if 'user_id' not in session or session['role'] != 'warden':
        flash('Unauthorized access')
        return redirect('/')
        
    db = get_db()
    cursor = db.cursor()
    
    # Get HOD-approved applications for hostellers only
    applications = cursor.execute('''
        SELECT leave_application.*, 
               student.name as student_name, 
               student.roll_number, 
               student.department
        FROM leave_application 
        JOIN student ON student.id = leave_application.student_id
        JOIN hostel_warden ON hostel_warden.user_id = ?
        WHERE class_teacher_status = 'approved'
        AND hod_status = 'approved' 
        AND warden_status = 'pending'
        AND student.student_type = 'hosteller'
        ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    db.close()
    return render_template('warden_review.html', applications=applications)

@app.route('/leave/action/<int:application_id>', methods=['POST'])
def leave_action(application_id):
    if 'user_id' not in session:
        return 'Unauthorized', 401
        
    action = request.form['action']
    role = session['role']
    
    db = get_db()
    cursor = db.cursor()
    
    if role == 'class_teacher':
        cursor.execute('''
            UPDATE leave_application 
            SET class_teacher_status = ?
            WHERE id = ?
        ''', (action, application_id))
        redirect_url = 'teacher_review'
    elif role == 'hod':
        cursor.execute('''
            UPDATE leave_application 
            SET hod_status = ?
            WHERE id = ?
        ''', (action, application_id))
        redirect_url = 'hod_review'
    elif role == 'warden':
        # Only update warden status for hostellers
        cursor.execute('''
            UPDATE leave_application 
            SET warden_status = ?
            WHERE id = ? AND 
                  EXISTS (
                      SELECT 1 FROM student 
                      WHERE student.id = leave_application.student_id 
                      AND student.student_type = 'hosteller'
                  )
        ''', (action, application_id))
        redirect_url = 'warden_review'
    
    db.commit()
    db.close()
    
    flash('Application status updated')
    return redirect(url_for(redirect_url))

@app.route('/leave/<int:application_id>/hod-review', methods=['POST'])
def hod_review_action(application_id):
    if 'user_id' not in session or session['role'] != 'hod':
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
        
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify HOD is assigned to student's department
        is_hod = cursor.execute('''
            SELECT 1 FROM leave_application
            JOIN student ON student.id = leave_application.student_id
            JOIN hod ON hod.department = student.department
            WHERE leave_application.id = ? 
            AND hod.user_id = ?
        ''', (application_id, session['user_id'])).fetchone()
        
        if not is_hod:
            return jsonify({'error': 'Not authorized for this student'}), 403
            
        # Update application status
        cursor.execute('''
            UPDATE leave_application 
            SET hod_status = ?,
                warden_status = CASE 
                    WHEN ? = 'approved' AND 
                         EXISTS (
                             SELECT 1 FROM student 
                             WHERE student.id = leave_application.student_id 
                             AND student.student_type = 'hosteller'
                         ) 
                    THEN 'pending'
                    ELSE warden_status
                END
            WHERE id = ?
        ''', (status, status, application_id))
        
        db.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/leave/<int:application_id>/warden-review', methods=['POST'])
def warden_review_action(application_id):
    if 'user_id' not in session or session['role'] != 'warden':
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
        
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify this is a hostel student
        is_valid = cursor.execute('''
            SELECT 1 FROM leave_application
            JOIN student ON student.id = leave_application.student_id
            WHERE leave_application.id = ? 
            AND student.student_type = 'hosteller'
        ''', (application_id,)).fetchone()
        
        if not is_valid:
            return jsonify({'error': 'Not a hostel student'}), 403
            
        # Update application status
        cursor.execute('''
            UPDATE leave_application 
            SET warden_status = ?
            WHERE id = ?
        ''', (status, application_id))
        
        db.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

def generate_pickup_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def save_file(file):
    """Save file to local storage and return filename"""
    if file and file.filename:
        # Generate unique filename
        ext = os.path.splitext(file.filename)[1]
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{generate_pickup_code()}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

def delete_file(filename):
    """Delete file from local storage"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception as e:
        print(f"Error deleting file: {e}")
    return False

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    if 'user_id' not in session or session['role'] not in ['student', 'printer']:
        return 'Unauthorized', 401
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/print/request', methods=['GET', 'POST'])
@login_required
def print_request():
    if request.method == 'POST':
        try:
            if 'document' not in request.files:
                flash('No file uploaded')
                return redirect(request.url)

            file = request.files['document']
            
            if file.filename == '':
                flash('No file selected')
                return redirect(request.url)

            if file and allowed_file(file.filename):
                # Secure the filename
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                unique_filename = timestamp + filename
                
                # Save the file
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                # Get form data
                pages = int(request.form.get('pages', 1))
                copies = int(request.form.get('copies', 1))
                is_color = 'color' in request.form
                is_double_sided = 'double_sided' in request.form
                
                # Calculate cost
                cost_per_page = 2  # Base cost
                if is_color:
                    cost_per_page += 5
                if is_double_sided:
                    cost_per_page -= 1
                
                total_cost = pages * copies * cost_per_page
                
                # Generate pickup code
                pickup_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                
                # Get student ID
                db = get_db()
                cursor = db.cursor()
                student = cursor.execute('SELECT id FROM student WHERE user_id = ?', 
                                      (session['user_id'],)).fetchone()
                
                if not student:
                    raise Exception("Student record not found")
                
                # Save to database with correct columns and number of parameters
                cursor.execute('''
                    INSERT INTO print_request 
                    (student_id, file_path, drive_link, is_color, is_double_sided, 
                     copies, pages, total_cost, pickup_code, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    student['id'], 
                    unique_filename,
                    '',  # drive_link
                    is_color,
                    is_double_sided,
                    copies,
                    pages,
                    total_cost,
                    pickup_code,
                    'pending'
                ))
                
                db.commit()
                db.close()
                
                flash(f'Print request submitted successfully! Your pickup code is: {pickup_code}')
                return redirect(url_for('print_status'))
                
            else:
                flash('Invalid file type. Please upload a PDF file.')
                return redirect(request.url)
                
        except Exception as e:
            print(f"Error in file upload: {str(e)}")  # For debugging
            flash('Error processing your request. Please try again.')
            return redirect(request.url)

    return render_template('print_request.html')

@app.route('/print/dashboard')
def printer_dashboard():
    if 'user_id' not in session or session['role'] != 'printer':
        flash('Unauthorized access')
        return redirect('/')
        
    db = get_db()
    cursor = db.cursor()
    
    # Get all print requests with student details
    requests = cursor.execute('''
        SELECT 
            print_request.*,
            student.name as student_name,
            student.roll_number
        FROM print_request
        JOIN student ON student.id = print_request.student_id
        ORDER BY 
            CASE status
                WHEN 'pending' THEN 1
                WHEN 'ready' THEN 2
                WHEN 'completed' THEN 3
            END,
            created_at DESC
    ''').fetchall()
    
    db.close()
    return render_template('printer_dashboard.html', requests=requests)

@app.route('/print/update-status/<pickup_code>', methods=['POST'])
@login_required
def update_print_status(pickup_code):
    if session['role'] != 'printer':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    try:
        new_status = request.json.get('status')
        if new_status not in ['ready', 'completed']:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            UPDATE print_request 
            SET status = ? 
            WHERE pickup_code = ?
        ''', (new_status, pickup_code))
        
        db.commit()
        db.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error updating status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/print/status')
def print_status():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Please login as a student')
        return redirect('/login')
        
    db = get_db()
    cursor = db.cursor()
    
    # Get student's print requests
    requests = cursor.execute('''
        SELECT print_request.*
        FROM print_request
        JOIN student ON student.id = print_request.student_id
        WHERE student.user_id = ?
        ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    db.close()
    return render_template('print_status.html', requests=requests)

@app.route('/printer/login', methods=['GET', 'POST'])
def printer_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        cursor = db.cursor()
        
        # First check if user exists
        user = cursor.execute('SELECT * FROM user WHERE email = ?', (email,)).fetchone()
        
        if not user:
            flash('Invalid email or password')
            db.close()
            return render_template('printer_login.html')
            
        # Then check if they're a printer
        if user['role'] != 'printer':
            flash('This account is not authorized as a printer')
            db.close()
            return render_template('printer_login.html')
            
        # Finally check printer_shop entry and password
        printer = cursor.execute('''
            SELECT user.*, printer_shop.id as printer_id 
            FROM user 
            JOIN printer_shop ON printer_shop.user_id = user.id 
            WHERE user.id = ?
        ''', (user['id'],)).fetchone()
        
        if printer and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['printer_id'] = printer['printer_id']
            session['email'] = user['email']
            
            db.close()
            flash('Welcome to Printer Dashboard!')
            return redirect(url_for('printer_dashboard'))
        
        flash('Invalid email or password')
        db.close()
        
    return render_template('printer_login.html')

@app.route('/lost-item/report', methods=['GET', 'POST'])
def report_lost_item():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Please login as a student')
        return redirect('/login')
    
    if request.method == 'POST':
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Get student ID
            student = cursor.execute(
                'SELECT id FROM student WHERE user_id = ?', 
                (session['user_id'],)
            ).fetchone()
            
            description = request.form['description']
            location = request.form['location']
            phone_number = request.form.get('phone_number', '')
            
            # Handle image upload
            image_path = None
            if 'image' in request.files:
                image = request.files['image']
                if image and image.filename:
                    # Generate unique filename for image
                    ext = os.path.splitext(image.filename)[1]
                    filename = f"lost_item_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                    image_path = os.path.join('lost_items', filename)
                    
                    # Ensure lost_items directory exists
                    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'lost_items'), exist_ok=True)
                    
                    # Save image
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_path))
            
            # Create lost item record
            cursor.execute('''
                INSERT INTO lost_item (
                    student_id, description, location, 
                    phone_number, image_path
                ) VALUES (?, ?, ?, ?, ?)
            ''', (student['id'], description, location, phone_number, image_path))
            
            db.commit()
            flash('Lost item reported successfully')
            return redirect(url_for('my_lost_items'))
            
        except Exception as e:
            flash(f'Error reporting lost item: {str(e)}')
            return redirect(request.url)
    
    return render_template('report_lost_item.html')

@app.route('/lost-items/my')
def my_lost_items():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Please login as a student')
        return redirect('/login')
    
    db = get_db()
    cursor = db.cursor()
    
    items = cursor.execute('''
        SELECT lost_item.*, student_notification.message as notification
        FROM lost_item 
        LEFT JOIN student_notification ON 
            student_notification.student_id = lost_item.student_id AND 
            student_notification.type = 'lost_item' AND 
            student_notification.is_read = 0
        WHERE lost_item.student_id = (
            SELECT id FROM student WHERE user_id = ?
        )
        ORDER BY lost_item.created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    db.close()
    return render_template('my_lost_items.html', items=items)

@app.route('/student-care/lost-items')
def student_care_lost_items():
    if 'user_id' not in session or session['role'] != 'student_care':
        flash('Unauthorized access')
        return redirect('/')
    
    db = get_db()
    cursor = db.cursor()
    
    items = cursor.execute('''
        SELECT 
            lost_item.*,
            student.name as student_name,
            student.roll_number
        FROM lost_item 
        JOIN student ON student.id = lost_item.student_id
        ORDER BY 
            CASE status
                WHEN 'pending' THEN 1
                WHEN 'found' THEN 2
                WHEN 'returned' THEN 3
            END,
            created_at DESC
    ''').fetchall()
    
    db.close()
    return render_template('student_care_lost_items.html', items=items)

@app.route('/lost-item/<int:item_id>/status', methods=['POST'])
def update_lost_item_status(item_id):
    if 'user_id' not in session or session['role'] != 'student_care':
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['found', 'returned']:
        return jsonify({'error': 'Invalid status'}), 400
        
    try:
        db = get_db()
        cursor = db.cursor()
        
        if status == 'found':
            # Mark item as found and create notification
            cursor.execute('''
                UPDATE lost_item 
                SET status = ?, found_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (status, item_id))
            
            # Get student info
            student = cursor.execute('''
                SELECT student.id, student.name 
                FROM lost_item 
                JOIN student ON student.id = lost_item.student_id 
                WHERE lost_item.id = ?
            ''', (item_id,)).fetchone()
            
            # Create notification
            cursor.execute('''
                INSERT INTO student_notification (
                    student_id, message, type
                ) VALUES (?, ?, 'lost_item')
            ''', (
                student['id'], 
                'Your lost item has been found! Please collect it from Student Care office.'
            ))
            
        else:  # returned
            # Mark item as returned and clear notification
            cursor.execute('''
                UPDATE lost_item SET status = ? WHERE id = ?
            ''', (status, item_id))
            
            cursor.execute('''
                UPDATE student_notification 
                SET is_read = 1 
                WHERE type = 'lost_item' AND 
                student_id = (
                    SELECT student_id FROM lost_item WHERE id = ?
                )
            ''', (item_id,))
        
        db.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if session['role'] == 'student':
        db = get_db()
        cursor = db.cursor()
        
        # Get student info
        cursor.execute('''
            SELECT * FROM student WHERE user_id = ?
        ''', (session['user_id'],))
        student = cursor.fetchone()
        
        if not student:
            flash('Student record not found')
            return redirect(url_for('logout'))
        
        # Get club memberships
        cursor.execute('''
            SELECT 
                club_member.role,
                club.id as club_id,
                club.name as club_name
            FROM club_member 
            JOIN club ON club_member.club_id = club.id
            WHERE club_member.student_id = ?
        ''', (student['id'],))
        club_memberships = cursor.fetchall()
        
        # Get recent print requests
        cursor.execute('''
            SELECT * FROM print_request 
            WHERE student_id = ? 
            ORDER BY created_at DESC LIMIT 5
        ''', (student['id'],))
        print_requests = cursor.fetchall()
        
        # Get recent lost items
        cursor.execute('''
            SELECT lost_item.*, student_notification.message as notification
            FROM lost_item 
            LEFT JOIN student_notification ON 
                student_notification.student_id = lost_item.student_id AND 
                student_notification.type = 'lost_item' AND 
                student_notification.is_read = 0
            WHERE lost_item.student_id = ?
            ORDER BY lost_item.created_at DESC LIMIT 3
        ''', (student['id'],))
        lost_items = cursor.fetchall()
        
        # Get recent leave applications
        cursor.execute('''
            SELECT 
                leave_application.*,
                class_teacher.name as teacher_name,
                hod.name as hod_name
            FROM leave_application 
            JOIN student ON student.id = leave_application.student_id
            LEFT JOIN class_teacher ON class_teacher.department = student.department
            LEFT JOIN hod ON hod.department = student.department
            WHERE student.user_id = ?
            ORDER BY created_at DESC LIMIT 3
        ''', (session['user_id'],))
        leave_applications = cursor.fetchall()
        
        # Get recent events and their approval status
        cursor.execute('''
            SELECT 
                event.*,
                club.id as club_id,
                club.name as club_name
            FROM event
            JOIN club ON club.id = event.club_id
            JOIN club_member ON club_member.club_id = club.id
            JOIN student ON student.id = club_member.student_id
            WHERE student.user_id = ?
            ORDER BY event.created_at DESC LIMIT 3
        ''', (session['user_id'],))
        events = cursor.fetchall()
        
        db.close()
        return render_template('student_dashboard.html',
                             student=student,
                             club_memberships=club_memberships,
                             print_requests=print_requests,
                             lost_items=lost_items,
                             leave_applications=leave_applications,
                             events=events)
    
    elif session['role'] == 'coordinator':
        db = get_db()
        cursor = db.cursor()
        
        # Get coordinator's clubs with stats
        clubs = cursor.execute('''
            SELECT 
                club.*,
                COUNT(DISTINCT club_member.id) as member_count,
                COUNT(DISTINCT CASE WHEN event.coordinator_approval = 'pending' 
                    THEN event.id END) as pending_events
            FROM club
            LEFT JOIN club_member ON club_member.club_id = club.id
            LEFT JOIN event ON event.club_id = club.id
            WHERE club.coordinator_id = ?
            GROUP BY club.id
        ''', (session['user_id'],)).fetchall()
        
        # Get pending events for approval
        events = cursor.execute('''
            SELECT 
                event.*,
                club.name as club_name,
                venue.name as venue_name
            FROM event
            JOIN club ON club.id = event.club_id
            LEFT JOIN venue ON venue.id = event.venue_id
            WHERE club.coordinator_id = ?
            AND event.coordinator_approval = 'pending'
            ORDER BY event.event_date ASC
        ''', (session['user_id'],)).fetchall()
        
        db.close()
        return render_template('coordinator_dashboard.html',
                             clubs=clubs,
                             events=events)
    
    elif session['role'] == 'principal':
        db = get_db()
        cursor = db.cursor()
        
        # Get events pending principal approval
        events = cursor.execute('''
            SELECT 
                event.*,
                club.name as club_name,
                venue.name as venue_name
            FROM event
            JOIN club ON club.id = event.club_id
            LEFT JOIN venue ON venue.id = event.venue_id
            WHERE coordinator_approval = 'approved'
            AND principal_approval = 'pending'
            ORDER BY event.event_date ASC
        ''').fetchall()
        
        db.close()
        return render_template('principal_dashboard.html', events=events)
    
    elif session['role'] == 'class_teacher':
        db = get_db()
        cursor = db.cursor()
        
        # Get teacher info
        cursor.execute('''
            SELECT * FROM class_teacher WHERE user_id = ?
        ''', (session['user_id'],))
        teacher = cursor.fetchone()
        
        # Get pending leave applications
        cursor.execute('''
            SELECT 
                leave_application.*,
                student.name as student_name,
                student.roll_number,
                student.department
            FROM leave_application
            JOIN student ON student.id = leave_application.student_id
            WHERE student.department = ?
            AND class_teacher_status = 'pending'
            ORDER BY leave_application.created_at DESC
        ''', (teacher['department'],))
        leave_applications = cursor.fetchall()
        
        db.close()
        return render_template('teacher_dashboard.html',
                             teacher=teacher,
                             leave_applications=leave_applications)
                             
    elif session['role'] == 'hod':
        db = get_db()
        cursor = db.cursor()
        
        # Get pending leave applications that were approved by class teacher
        leave_applications = cursor.execute('''
            SELECT 
                leave_application.*,
                student.name as student_name,
                student.roll_number,
                student.department
            FROM leave_application
            JOIN student ON student.id = leave_application.student_id
            WHERE class_teacher_status = 'approved'
            AND hod_status = 'pending'
            ORDER BY leave_application.created_at DESC
        ''').fetchall()
        
        db.close()
        return render_template('hod_dashboard.html',
                             leave_applications=leave_applications)
    
    elif session['role'] == 'warden':
        db = get_db()
        cursor = db.cursor()
        
        # Get pending leave applications for hostellers that were approved by HOD
        leave_applications = cursor.execute('''
            SELECT 
                leave_application.*,
                student.name as student_name,
                student.roll_number,
                student.department
            FROM leave_application
            JOIN student ON student.id = leave_application.student_id
            WHERE student.student_type = 'hosteller'
            AND class_teacher_status = 'approved'
            AND hod_status = 'approved'
            AND warden_status = 'pending'
            ORDER BY leave_application.created_at DESC
        ''').fetchall()
        
        db.close()
        return render_template('warden_dashboard.html',
                             leave_applications=leave_applications)
    
    # For other roles, redirect to home
    flash('Welcome ' + session['role'])
    return redirect(url_for('home'))

@app.route('/club/event/create', methods=['GET', 'POST'])
def create_club_event():
    if 'user_id' not in session:
        flash('Please login first')
        return redirect(url_for('login'))
        
    db = get_db()
    cursor = db.cursor()
    
    # Check if user is a club member with permission to create events
    club_role = cursor.execute('''
        SELECT club_member.role, club.* 
        FROM club_member 
        JOIN club ON club_member.club_id = club.id
        JOIN student ON student.id = club_member.student_id
        WHERE student.user_id = ? 
        AND club_member.role IN ('president', 'secretary')
    ''', (session['user_id'],)).fetchone()
    
    if not club_role:
        flash('You do not have permission to create events')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        try:
            # Get form data
            event_date = request.form['event_date']
            start_time = request.form['start_time']
            end_time = request.form['end_time']
            venue_id = request.form['venue_id']
            
            # Check venue availability
            available = cursor.execute('''
                SELECT 1 FROM venue 
                WHERE id = ? 
                AND id NOT IN (
                    SELECT venue_id 
                    FROM venue_booking 
                    WHERE booking_date = ? 
                    AND (
                        (start_time <= ? AND end_time >= ?) OR
                        (start_time <= ? AND end_time >= ?) OR
                        (start_time >= ? AND end_time <= ?)
                    )
                    AND status != 'cancelled'
                )
            ''', (venue_id, event_date, start_time, start_time, 
                  end_time, end_time, start_time, end_time)).fetchone()
            
            if not available:
                flash('Venue not available for selected time')
                return redirect(request.url)
            
            # Create event
            cursor.execute('''
                INSERT INTO event (
                    club_id, name, description, expected_participants,
                    event_date, start_time, end_time, venue_id,
                    needs_transport, transport_details,
                    needs_food, food_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                club_role['id'],  # club_id
                request.form['name'],
                request.form['description'],
                request.form['participants'],
                event_date,
                start_time,
                end_time,
                venue_id,
                'transport' in request.form,
                request.form.get('transport_details'),
                'food' in request.form,
                request.form.get('food_details')
            ))
            
            event_id = cursor.lastrowid
            
            # Book venue
            cursor.execute('''
                INSERT INTO venue_booking (
                    venue_id, event_id, booking_date,
                    start_time, end_time
                ) VALUES (?, ?, ?, ?, ?)
            ''', (venue_id, event_id, event_date, start_time, end_time))
            
            db.commit()
            flash('Event created successfully')
            return redirect(url_for('club_events', club_id=club_role['id']))
            
        except Exception as e:
            db.rollback()
            flash(f'Error creating event: {str(e)}')
            return redirect(request.url)
    
    # Get available venues
    venues = cursor.execute('SELECT * FROM venue').fetchall()
    db.close()
    
    return render_template('create_club_event.html',
                         club=club_role,
                         venues=venues)

@app.route('/clubs')
def list_clubs():
    if 'user_id' not in session:
        flash('Please login first')
        return redirect(url_for('login'))
        
    db = get_db()
    cursor = db.cursor()
    
    # Get all clubs with their coordinators and presidents
    clubs = cursor.execute('''
        SELECT 
            club.*,
            coordinator.email as coordinator_email,
            student.name as president_name,
            student.roll_number as president_roll
        FROM club
        JOIN user coordinator ON coordinator.id = club.coordinator_id
        LEFT JOIN club_member ON club_member.club_id = club.id AND club_member.role = 'president'
        LEFT JOIN student ON student.id = club_member.student_id
        ORDER BY club.name
    ''').fetchall()
    
    db.close()
    return render_template('clubs.html', clubs=clubs)

@app.route('/club/join', methods=['POST'])
def join_club():
    if 'user_id' not in session or session['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    club_id = data.get('club_id')
    
    if not club_id:
        return jsonify({'error': 'Club ID required'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get student ID
        student = cursor.execute('''
            SELECT id FROM student WHERE user_id = ?
        ''', (session['user_id'],)).fetchone()
        
        # Check if already a member
        existing = cursor.execute('''
            SELECT 1 FROM club_member 
            WHERE club_id = ? AND student_id = ?
        ''', (club_id, student['id'])).fetchone()
        
        if existing:
            return jsonify({'error': 'Already a member'}), 400
        
        # Join as regular member
        cursor.execute('''
            INSERT INTO club_member (club_id, student_id, role)
            VALUES (?, ?, 'member')
        ''', (club_id, student['id']))
        
        db.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/club/<int:club_id>/events')
def club_events(club_id):
    if 'user_id' not in session:
        flash('Please login first')
        return redirect(url_for('login'))
        
    db = get_db()
    cursor = db.cursor()
    
    # Get club details
    club = cursor.execute('''
        SELECT 
            club.*,
            user.email as coordinator_email
        FROM club
        JOIN user ON user.id = club.coordinator_id
        WHERE club.id = ?
    ''', (club_id,)).fetchone()
    
    if not club:
        flash('Club not found')
        return redirect(url_for('list_clubs'))
    
    # Get club's events
    events = cursor.execute('''
        SELECT 
            event.*,
            venue.name as venue_name,
            venue.capacity as venue_capacity
        FROM event
        LEFT JOIN venue ON venue.id = event.venue_id
        WHERE event.club_id = ?
        ORDER BY event.event_date DESC
    ''', (club_id,)).fetchall()
    
    # Check if user is a member of this club
    is_member = False
    member_role = None
    if session['role'] == 'student':
        member = cursor.execute('''
            SELECT club_member.role
            FROM club_member
            JOIN student ON student.id = club_member.student_id
            WHERE club_member.club_id = ? AND student.user_id = ?
        ''', (club_id, session['user_id'])).fetchone()
        if member:
            is_member = True
            member_role = member['role']
    
    db.close()
    return render_template('club_events.html',
                         club=club,
                         events=events,
                         is_member=is_member,
                         member_role=member_role)

@app.route('/event/<int:event_id>/coordinator-approval', methods=['POST'])
def coordinator_approval(event_id):
    if 'user_id' not in session or session['role'] != 'coordinator':
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
        
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify this coordinator is assigned to this event's club
        is_coordinator = cursor.execute('''
            SELECT 1 FROM club 
            JOIN event ON event.club_id = club.id
            WHERE event.id = ? AND club.coordinator_id = ?
        ''', (event_id, session['user_id'])).fetchone()
        
        if not is_coordinator:
            return jsonify({'error': 'Not authorized for this club'}), 403
            
        # Update event status
        cursor.execute('''
            UPDATE event 
            SET coordinator_approval = ?,
                principal_approval = CASE 
                    WHEN ? = 'approved' THEN 'pending'
                    ELSE NULL
                END
            WHERE id = ?
        ''', (status, status, event_id))
        
        db.commit()
        
        # If approved, notify principal
        if status == 'approved':
            # TODO: Add notification for principal
            pass
            
        return jsonify({'success': True})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/club/<int:club_id>/members')
def club_members(club_id):
    if 'user_id' not in session:
        flash('Please login first')
        return redirect(url_for('login'))
        
    db = get_db()
    cursor = db.cursor()
    
    # Get club details
    club = cursor.execute('''
        SELECT 
            club.*,
            user.email as coordinator_email
        FROM club
        JOIN user ON user.id = club.coordinator_id
        WHERE club.id = ?
    ''', (club_id,)).fetchone()
    
    if not club:
        flash('Club not found')
        return redirect(url_for('list_clubs'))
    
    # Verify if current user is coordinator of this club
    if session['role'] == 'coordinator':
        is_coordinator = club['coordinator_id'] == session['user_id']
        if not is_coordinator:
            flash('You are not the coordinator of this club')
            return redirect(url_for('dashboard'))
    
    # Get all members with their roles
    members = cursor.execute('''
        SELECT 
            student.name,
            student.roll_number,
            student.department,
            club_member.role,
            club_member.joined_at
        FROM club_member
        JOIN student ON student.id = club_member.student_id
        WHERE club_member.club_id = ?
        ORDER BY 
            CASE club_member.role
                WHEN 'president' THEN 1
                WHEN 'secretary' THEN 2
                WHEN 'member' THEN 3
            END,
            student.name
    ''', (club_id,)).fetchall()
    
    db.close()
    return render_template('club_members.html',
                         club=club,
                         members=members)

@app.route('/event/<int:event_id>/principal-approval', methods=['POST'])
def principal_approval(event_id):
    if 'user_id' not in session or session['role'] != 'principal':
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
        
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get event details first
        event = cursor.execute('''
            SELECT needs_transport, needs_food
            FROM event WHERE id = ?
        ''', (event_id,)).fetchone()
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
            
        # Update event status based on requirements
        if status == 'approved':
            # If no special requirements, mark as approved
            if not event['needs_transport'] and not event['needs_food']:
                cursor.execute('''
                    UPDATE event 
                    SET principal_approval = ?,
                        status = 'approved'
                    WHERE id = ?
                ''', (status, event_id))
            else:
                # If special requirements exist, set to pending and update approvals
                cursor.execute('''
                    UPDATE event 
                    SET principal_approval = ?,
                        transport_approval = CASE 
                            WHEN needs_transport THEN 'pending'
                            ELSE NULL
                        END,
                        food_approval = CASE 
                            WHEN needs_food THEN 'pending'
                            ELSE NULL
                        END
                    WHERE id = ?
                ''', (status, event_id))
        else:
            # If rejected, simply update principal approval and status
            cursor.execute('''
                UPDATE event 
                SET principal_approval = ?,
                    status = 'rejected'
                WHERE id = ?
            ''', (status, event_id))
        
        if status == 'approved':
            # Get event details for notifications
            event = cursor.execute('''
                SELECT 
                    event.*,
                    club.name as club_name
                FROM event
                JOIN club ON club.id = event.club_id
                WHERE event.id = ?
            ''', (event_id,)).fetchone()
            
            # Notify transport department if needed
            if event['needs_transport']:
                cursor.execute('''
                    INSERT INTO notification (
                        user_id, title, message, type
                    ) VALUES (
                        (SELECT id FROM user WHERE role = 'transport'),
                        ?,
                        ?,
                        'transport_request'
                    )
                ''', (
                    f"New transport request for {event['club_name']}",
                    f"Event: {event['name']}\nDate: {event['event_date']}\nDetails: {event['transport_details']}"
                ))
            
            # Notify food department if needed
            if event['needs_food']:
                cursor.execute('''
                    INSERT INTO notification (
                        user_id, title, message, type
                    ) VALUES (
                        (SELECT id FROM user WHERE role = 'food'),
                        ?,
                        ?,
                        'food_request'
                    )
                ''', (
                    f"New food request for {event['club_name']}",
                    f"Event: {event['name']}\nDate: {event['event_date']}\nDetails: {event['food_details']}"
                ))
        
        db.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/cab-share')
def cab_share():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Please login as a student')
        return redirect(url_for('login'))

    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get student info
        student = cursor.execute('''
            SELECT * FROM student WHERE user_id = ?
        ''', (session['user_id'],)).fetchone()
        
        if not student:
            return redirect(url_for('dashboard'))
            
        return render_template('cab_share.html', student=student)
        
    except Exception as e:
        # Instead of showing error, just redirect
        return redirect(url_for('dashboard'))
    finally:
        db.close()

@app.route('/cab-share/requests')
def cab_share_requests():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Please login as a student')
        return redirect(url_for('login'))
        
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get active ride requests
        cursor.execute('''
            SELECT r.*, s.name as student_name
            FROM ride_requests r
            JOIN student s ON s.id = r.student_id
            WHERE r.status = 'active' 
            AND datetime(r.departure_time) > datetime('now')
            ORDER BY r.departure_time ASC
        ''')
        ride_requests = cursor.fetchall()
        
        # Convert string to datetime object
        formatted_rides = []
        for ride in ride_requests:
            ride = dict(ride)
            try:
                # Handle different datetime formats
                if 'T' in ride['departure_time']:
                    # Format: 2025-02-28T23:31
                    ride['departure_time'] = datetime.strptime(ride['departure_time'], '%Y-%m-%dT%H:%M')
                else:
                    # Format: 2025-02-28 23:31:00
                    ride['departure_time'] = datetime.strptime(ride['departure_time'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # If conversion fails, keep original string
                pass
            formatted_rides.append(ride)
            
        return render_template('cab_share_requests.html', 
                             ride_requests=formatted_rides)
    finally:
        db.close()

@app.route('/api/rides', methods=['POST'])
def create_ride():
    if 'user_id' not in session or session['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        data = request.json
        db = get_db()
        cursor = db.cursor()
        
        # Get student ID
        student = cursor.execute('''
            SELECT id FROM student WHERE user_id = ?
        ''', (session['user_id'],)).fetchone()
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
            
        # Insert ride request
        cursor.execute('''
            INSERT INTO ride_requests (
                student_id, name, phone, pickup_lat, pickup_lng,
                drop_lat, drop_lng, pickup_address, drop_address,
                departure_time, gender_preference, additional_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            student['id'],
            data['name'],
            data['phone'],
            data['pickupLocation']['coordinates'][0],
            data['pickupLocation']['coordinates'][1],
            data['dropLocation']['coordinates'][0],
            data['dropLocation']['coordinates'][1],
            data['pickupLocation']['address'],
            data['dropLocation']['address'],
            data['departureTime'],
            data.get('genderPreference'),
            data.get('additionalNotes')
        ))
        
        ride_id = cursor.lastrowid
        db.commit()

        # Find matching rides
        data['id'] = ride_id
        matches = find_matches(data)
        
        return jsonify({
            'success': True,
            'ride_id': ride_id,
            'matches': matches,
            'redirect_url': url_for('cab_share_requests')
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

def format_datetime(dt_str):
    """Format datetime string for display"""
    try:
        if 'T' in dt_str:
            dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M')
        else:
            dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%d %b %Y, %I:%M %p')
    except:
        return dt_str

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points on earth"""
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

def find_matches(ride_request):
    """Find matching rides within proximity"""
    try:
        db = get_db()
        cursor = db.cursor()

        # Get departure time window (±30 minutes)
        departure_time = datetime.strptime(
            ride_request.get('departureTime', ride_request.get('departure_time')), 
            '%Y-%m-%dT%H:%M'
        )
        time_window_start = (departure_time - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M')
        time_window_end = (departure_time + timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M')

        # Get coordinates based on request format
        if 'pickupLocation' in ride_request:
            pickup_lat = float(ride_request['pickupLocation']['coordinates'][0])
            pickup_lng = float(ride_request['pickupLocation']['coordinates'][1])
            drop_lat = float(ride_request['dropLocation']['coordinates'][0])
            drop_lng = float(ride_request['dropLocation']['coordinates'][1])
        else:
            pickup_lat = float(ride_request['pickup_lat'])
            pickup_lng = float(ride_request['pickup_lng'])
            drop_lat = float(ride_request['drop_lat'])
            drop_lng = float(ride_request['drop_lng'])

        cursor.execute('''
            WITH distances AS (
                SELECT 
                    r.*,
                    s.name as student_name,
                    (
                        6371 * acos(
                            cos(radians(?)) * cos(radians(pickup_lat)) *
                            cos(radians(pickup_lng) - radians(?)) +
                            sin(radians(?)) * sin(radians(pickup_lat))
                        )
                    ) as pickup_distance,
                    (
                        6371 * acos(
                            cos(radians(?)) * cos(radians(drop_lat)) *
                            cos(radians(drop_lng) - radians(?)) +
                            sin(radians(?)) * sin(radians(drop_lat))
                        )
                    ) as drop_distance
                FROM ride_requests r
                JOIN student s ON s.id = r.student_id
                WHERE r.status = 'active'
                AND r.matched_with IS NULL
                AND r.departure_time BETWEEN ? AND ?
                AND r.id != ?
            )
            SELECT *
            FROM distances
            WHERE pickup_distance <= 5  -- 5km radius for pickup
            AND drop_distance <= 10     -- 10km radius for drop
            AND (
                -- Check if routes are in same direction
                (drop_lat - pickup_lat) * (? - ?) > 0
                OR
                (drop_lng - pickup_lng) * (? - ?) > 0
            )
            ORDER BY (pickup_distance + drop_distance)
            LIMIT 5
        ''', (
            pickup_lat, pickup_lng, pickup_lat,
            drop_lat, drop_lng, drop_lat,
            time_window_start, time_window_end,
            ride_request.get('id', 0),
            drop_lat, pickup_lat,
            drop_lng, pickup_lng
        ))

        matches = []
        for row in cursor.fetchall():
            match = dict(row)
            matches.append({
                'ride_id': match['id'],
                'name': match['student_name'],
                'phone': match['phone'],
                'pickup': match['pickup_address'],
                'drop': match['drop_address'],
                'departure_time': format_datetime(match['departure_time']),
                'gender_preference': match['gender_preference'],
                'pickup_distance': round(match['pickup_distance'], 2),
                'drop_distance': round(match['drop_distance'], 2),
                'coordinates': {
                    'pickup': {'lat': match['pickup_lat'], 'lng': match['pickup_lng']},
                    'drop': {'lat': match['drop_lat'], 'lng': match['drop_lng']}
                }
            })

        return matches
    except Exception as e:
        print(f"Error finding matches: {e}")
        return []
    finally:
        db.close()

@app.route('/food')
def food_index():
    """Food ordering landing page"""
    if 'user_id' in session:
        if session['role'] == 'food':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('food_dashboard'))
    return redirect(url_for('login'))

@app.route('/food/dashboard')
@login_required
def food_dashboard():
    """Student food dashboard"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT DISTINCT u.* 
            FROM user u
            WHERE u.role = "food"
        ''')
        cafes = cursor.fetchall()
        return render_template('food/dashboard.html', 
                             cafes=cafes,
                             active_page='food')
    finally:
        db.close()

@app.route('/food/cafe/<int:cafe_id>')
@login_required
def cafe_menu(cafe_id):
    """View cafe menu"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get cafe details
        cursor.execute('SELECT * FROM user WHERE id = ?', (cafe_id,))
        cafe = cursor.fetchone()
        
        # Get unique menu items
        cursor.execute('''
            SELECT DISTINCT id, name, description, price, image_url 
            FROM menu_items 
            WHERE cafe_id = ? AND available = 1
            ORDER BY category, name
        ''', (cafe_id,))
        menu_items = cursor.fetchall()
        
        return render_template('food/cafe_menu.html',
                             cafe=cafe,
                             menu_items=menu_items)
    finally:
        db.close()

@app.route('/food/orders')
@login_required
def my_food_orders():
    """View my food orders"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT o.*, u.cafe_name,
                   GROUP_CONCAT(mi.name || ' (x' || oi.quantity || ')') as items
            FROM orders o
            JOIN users u ON o.cafe_id = u.id
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE o.user_id = ?
            GROUP BY o.id
            ORDER BY o.created_at DESC
        ''', (session['user_id'],))
        orders = cursor.fetchall()
        return render_template('food/my_orders.html', 
                             orders=orders,
                             active_page='food_orders')
    finally:
        db.close()

@app.route('/food/place-order', methods=['POST'])
@login_required
def place_food_order():
    """Place a new food order"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            db = get_db()
            cursor = db.cursor()
            
            # Generate order ID
            order_id = f"FOOD{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create order
            cursor.execute('''
                INSERT INTO orders (order_id, user_id, cafe_id, total_amount)
                VALUES (?, ?, ?, ?)
            ''', (order_id, session['user_id'], data['cafe_id'], data['total']))
            
            order_db_id = cursor.lastrowid
            
            # Add order items
            for item in data['items']:
                cursor.execute('''
                    INSERT INTO order_items (order_id, menu_item_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                ''', (order_db_id, item['id'], item['quantity'], item['price']))
            
            db.commit()
            return jsonify({'success': True, 'order_id': order_id})
        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'error': str(e)})
        finally:
            db.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    init_db()  # Create tables
    init_sample_data()  # Uncomment this line for the first run
    app.run(debug=True,port=5001) 