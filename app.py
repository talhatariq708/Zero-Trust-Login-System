from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# ------------------- INIT DB -------------------

def init_db():
    with sqlite3.connect("users.db") as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        email TEXT PRIMARY KEY,
                        password TEXT,
                        role TEXT
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS logs (
                        email TEXT,
                        ip TEXT,
                        browser TEXT,
                        timestamp TEXT
                    )''')
        conn.commit()

# ------------------- DEMO EMAIL OTP -------------------

def send_otp(email, otp):
    print(f"\n🔐 [DEMO] OTP for {email} is: {otp}\n")

# ------------------- LOGGING -------------------

def log_user_activity(email, ip, browser):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with sqlite3.connect("users.db", timeout=10) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO logs (email, ip, browser, timestamp) VALUES (?, ?, ?, ?)",
                      (email, ip, browser, timestamp))
            conn.commit()
    except Exception as e:
        print("❌ Log error:", e)

# ------------------- ROUTES -------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with sqlite3.connect("users.db") as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=? AND password=? AND role='admin'", (email, password))
            user = c.fetchone()
        if user:
            session['email'] = email
            session['role'] = 'admin'
            session['otp'] = random.randint(1000, 9999)
            send_otp(email, session['otp'])
            return redirect('/otp')
        else:
            flash("❌ Invalid admin credentials", "error")
    return render_template('admin_login.html')

@app.route('/login', methods=['GET', 'POST'])
def employee_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with sqlite3.connect("users.db") as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=? AND password=? AND role='employee'", (email, password))
            user = c.fetchone()
        if user:
            session['email'] = email
            session['role'] = 'employee'
            session['otp'] = random.randint(1000, 9999)
            send_otp(email, session['otp'])
            return redirect('/otp')
        else:
            flash("❌ Invalid employee credentials", "error")
    return render_template('employee_login.html')

@app.route('/signup/<role>', methods=['GET', 'POST'])
def signup(role):
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with sqlite3.connect("users.db") as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            if c.fetchone():
                flash("⚠️ User already exists.", "error")
                return redirect(f'/signup/{role}')
            c.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", (email, password, role))
            conn.commit()
        session['email'] = email
        session['role'] = role
        session['otp'] = random.randint(1000, 9999)
        send_otp(email, session['otp'])
        return redirect('/otp')
    return render_template('signup.html', role=role)

@app.route('/otp', methods=['GET', 'POST'])
def otp():
    if 'email' not in session:
        return redirect('/')
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if str(entered_otp) == str(session.get('otp')):
            ip = request.remote_addr
            browser = request.headers.get('User-Agent')
            log_user_activity(session['email'], ip, browser)
            if session['role'] == 'admin':
                return redirect('/admin-dashboard')
            else:
                return redirect('/employee-dashboard')
        else:
            flash("❌ Invalid OTP. Please try again.", "error")
    return render_template('otp.html')

@app.route('/resend-otp')
def resend_otp():
    if 'email' in session:
        session['otp'] = random.randint(1000, 9999)
        send_otp(session['email'], session['otp'])
        flash("✅ OTP resent successfully.", "success")
    return redirect('/otp')

@app.route('/admin-dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/')
    return render_template('admin_dashboard.html')

@app.route('/employee-dashboard')
def employee_dashboard():
    if session.get('role') != 'employee':
        return redirect('/')
    return render_template('employee_dashboard.html')

@app.route('/view-logs')
def view_logs():
    if session.get('role') != 'admin':
        return redirect('/')
    try:
        with sqlite3.connect("users.db") as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM logs ORDER BY timestamp DESC")
            logs = c.fetchall()
        return render_template('view_logs.html', logs=logs)
    except Exception as e:
        return f"Error loading logs: {e}"


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ------------------- RUN -------------------

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
