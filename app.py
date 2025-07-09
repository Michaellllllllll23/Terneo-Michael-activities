from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
mysql = MySQL(app)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or session['user_role'] != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        
        hashed_password = generate_password_hash(password)
        
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (%s, %s, %s, %s)
            """, (username, email, hashed_password, full_name))
            mysql.connection.commit()
            cur.close()
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'danger')
    
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/students')
@login_required
def list_students():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT s.*, u.username as added_by_username 
        FROM students s
        LEFT JOIN users u ON s.added_by = u.username
        ORDER BY s.last_name, s.first_name
    """)
    students = cur.fetchall()
    cur.close()
    return render_template('students/list.html', students=students)

@app.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        # First verify the user exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE id = %s", (session['user_id'],))
        user = cur.fetchone()
        
        if not user:
            cur.close()
            flash('Invalid user session. Please log in again.', 'danger')
            return redirect(url_for('login'))
        
        student_data = {
            'student_id': request.form['student_id'],
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form['email'],
            'phone': request.form.get('phone', ''),
            'address': request.form.get('address', ''),
            'date_of_birth': request.form.get('date_of_birth'),
            'gender': request.form.get('gender'),
            'enrollment_date': request.form.get('enrollment_date', ''),
            'program': request.form.get('program', ''),
            'added_by': session['user_id']
        }
        
        try:
            cur.execute("""
                INSERT INTO students (
                    student_id, first_name, last_name, email, phone, address,
                    date_of_birth, gender, enrollment_date, program, added_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tuple(student_data.values()))
            mysql.connection.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('list_students'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error adding student: {str(e)}', 'danger')
        finally:
            cur.close()
    
    return render_template('students/add.html')

@app.route('/students/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    cur = mysql.connection.cursor()
    try:
        if request.method == 'POST':
            student_data = {
                'student_id': request.form['student_id'],
                'first_name': request.form['first_name'],
                'last_name': request.form['last_name'],
                'email': request.form['email'],
                'phone': request.form.get('phone', ''),
                'address': request.form.get('address', ''),
                'date_of_birth': request.form.get('date_of_birth'),
                'gender': request.form.get('gender'),
                'enrollment_date': request.form.get('enrollment_date'),
                'program': request.form.get('program', ''),
                'id': id
            }
            
            cur.execute("""
                UPDATE students SET
                    student_id = %s,
                    first_name = %s,
                    last_name = %s,
                    email = %s,
                    phone = %s,
                    address = %s,
                    date_of_birth = %s,
                    gender = %s,
                    enrollment_date = %s,
                    program = %s
                WHERE id = %s
            """, tuple(student_data.values()))
            mysql.connection.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('list_students'))
        
        # GET request
        cur.execute("SELECT * FROM students WHERE id = %s", (id,))
        student = cur.fetchone()
        
        if not student:
            flash('Student not found!', 'danger')
            return redirect(url_for('list_students'))
        
        return render_template('students/edit.html', student=student)
    
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error updating student: {str(e)}', 'danger')
        return redirect(url_for('list_students'))
    finally:
        cur.close()

@app.route('/students/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_student(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM students WHERE id = %s", (id,))
        student = cur.fetchone()
        
        if not student:
            flash('Student not found!', 'danger')
            return redirect(url_for('list_students'))
        
        if request.method == 'POST':
            cur.execute("DELETE FROM students WHERE id = %s", (id,))
            mysql.connection.commit()
            flash('Student deleted successfully!', 'success')
            return redirect(url_for('list_students'))
        
        return render_template('students/delete.html', student=student)
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error deleting student: {str(e)}', 'danger')
        return redirect(url_for('list_students'))
    finally:
        cur.close()

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('change_password'))
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT password_hash FROM users WHERE id = %s", (session['user_id'],))
            user = cur.fetchone()
            
            if user and check_password_hash(user['password_hash'], current_password):
                hashed_password = generate_password_hash(new_password)
                cur.execute("UPDATE users SET password_hash = %s WHERE id = %s", 
                           (hashed_password, session['user_id']))
                mysql.connection.commit()
                flash('Password changed successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Current password is incorrect', 'danger')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error changing password: {str(e)}', 'danger')
        finally:
            cur.close()
    
    return render_template('auth/change_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)