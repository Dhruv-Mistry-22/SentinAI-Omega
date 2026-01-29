from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import datetime
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'app.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-key')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user',
        blocked INTEGER DEFAULT 0,
        last_active TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        module TEXT,
        result TEXT,
        score INTEGER,
        filename TEXT,
        timestamp TEXT
    )
    ''')
    conn.commit()
    conn.close()


init_db()


def create_default_admin():
    """Create a default admin user if none exists. Password and email can be overridden
    with environment variables DEFAULT_ADMIN_EMAIL and DEFAULT_ADMIN_PW."""
    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE role='admin' LIMIT 1").fetchone()
    if existing:
        conn.close()
        return
    admin_email = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@local')
    admin_pw = os.environ.get('DEFAULT_ADMIN_PW', 'AdminPass123')
    admin_name = os.environ.get('DEFAULT_ADMIN_NAME', 'admin')
    try:
        pw_hash = generate_password_hash(admin_pw)
        conn.execute('INSERT INTO users (name,email,password,role,last_active,blocked) VALUES (?,?,?,?,?,?)',
                     (admin_name, admin_email, pw_hash, 'admin', datetime.datetime.utcnow().isoformat(), 0))
        conn.commit()
    except Exception:
        # ignore if insertion fails for any reason
        pass
    conn.close()


create_default_admin()


def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()
    conn.close()
    return user


def login_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        if user['blocked']:
            return render_template('blocked.html')
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or user['role'] != 'admin':
            return redirect(url_for('login'))
        return fn(*args, **kwargs)

    return wrapper


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')
        pw_hash = generate_password_hash(password)
        conn = get_db()
        try:
            conn.execute('INSERT INTO users (name,email,password,role,last_active) VALUES (?,?,?,?,?)',
                         (name, email, pw_hash, role, datetime.datetime.utcnow().isoformat()))
            conn.commit()
        except Exception:
            conn.close()
            return render_template('signup.html', error='Email already registered')
        conn.close()
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if not user or not check_password_hash(user['password'], password):
            conn.close()
            return render_template('login.html', error='Invalid credentials')
        if user['blocked']:
            conn.close()
            return render_template('blocked.html')
        # update last_active
        conn.execute('UPDATE users SET last_active = ? WHERE id = ?', (datetime.datetime.utcnow().isoformat(), user['id']))
        conn.commit()
        conn.close()
        session['user_id'] = user['id']
        session['role'] = user['role']
        if user['role'] == 'admin':
            return redirect(url_for('admin'))
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()
    conn = get_db()
    logs = conn.execute('SELECT * FROM logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10', (user['id'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', user=user, logs=logs)


@app.route('/admin')
@admin_required
def admin():
    conn = get_db()
    users = conn.execute('SELECT * FROM users').fetchall()
    total = conn.execute('SELECT COUNT(*) as c FROM users').fetchone()['c']
    blocked = conn.execute('SELECT COUNT(*) as c FROM users WHERE blocked=1').fetchone()['c']
    analyses = conn.execute('SELECT COUNT(*) as c FROM logs').fetchone()['c']
    conn.close()
    return render_template('admin.html', users=users, total=total, blocked=blocked, analyses=analyses)


@app.route('/admin/users', methods=['GET'])
@admin_required
def admin_users():
    conn = get_db()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])


@app.route('/admin/block', methods=['POST'])
@admin_required
def admin_block():
    uid = request.form.get('user_id')
    action = request.form.get('action')
    conn = get_db()
    if action == 'block':
        conn.execute('UPDATE users SET blocked=1 WHERE id=?', (uid,))
    else:
        conn.execute('UPDATE users SET blocked=0 WHERE id=?', (uid,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@app.route('/admin/logs')
@admin_required
def admin_logs():
    conn = get_db()
    logs = conn.execute('SELECT logs.*, users.email as user_email FROM logs LEFT JOIN users ON logs.user_id=users.id ORDER BY timestamp DESC LIMIT 200').fetchall()
    conn.close()
    return render_template('logs.html', logs=logs)


@app.route('/upload/<module>', methods=['POST'])
@login_required
def upload(module):
    user = current_user()
    
    # Handle multiple files for M1 and M3, single file for M2
    if module in ['duplicate', 'image']:
        # Multiple files allowed
        if 'files' not in request.files:
            return jsonify({'error': 'no files', 'status': 'failed'}), 400
        files = request.files.getlist('files')
        if not files or len(files) == 0:
            return jsonify({'error': 'no files selected', 'status': 'failed'}), 400
    else:
        # Single file for M2
        if 'file' not in request.files:
            return jsonify({'error': 'no file', 'status': 'failed'}), 400
        files = [request.files['file']]
    
    # Validate files
    saved_paths = []
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(user['id']))
    os.makedirs(user_folder, exist_ok=True)
    
    for f in files:
        if f.filename == '':
            continue
        
        filename = secure_filename(f.filename)
        dest = os.path.join(user_folder, filename)
        f.save(dest)
        saved_paths.append(dest)
        print(f"[UPLOAD] Saved: {dest}")
    
    if not saved_paths:
        return jsonify({'error': 'no valid files', 'status': 'failed'}), 400
    
    print(f"\n[UPLOAD] Starting {module} analysis on {len(saved_paths)} file(s)")
    print(f"[UPLOAD] Files: {[os.path.basename(p) for p in saved_paths]}")
    
    # Run actual analysis
    if module == 'duplicate':
        # M1 takes multiple files
        ret = run_m1_analysis(saved_paths, user['id'])
    elif module == 'text':
        # M2 takes single file
        ret = run_analysis(saved_paths[0], module, user['id'])
    elif module == 'image':
        # M3 takes multiple image files
        ret = run_m3_analysis(saved_paths, user['id'])
    else:
        return jsonify({'error': 'unknown module', 'status': 'failed'}), 400
    
    # Save to database
    conn = get_db()
    for path in saved_paths:
        filename = os.path.basename(path)
        # store result/score from ret if available
        if isinstance(ret, (list, tuple)) and len(ret) >= 3:
            rres, rscore = ret[0], ret[1]
        else:
            rres, rscore = 'ERROR', 0
        conn.execute('INSERT INTO logs (user_id,module,result,score,filename,timestamp) VALUES (?,?,?,?,?,?)',
                     (user['id'], module, rres, rscore, filename, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    # Normalize ret
    if isinstance(ret, (list, tuple)) and len(ret) >= 3:
        result, score, message = ret[0], ret[1], ret[2]
        emailed = bool(ret[3]) if len(ret) > 3 else False
    else:
        result, score, message = 'ERROR', 0, 'Analysis failed'
        emailed = False

    print(f"[UPLOAD] Analysis complete: {result} ({score}%)\n")

    return jsonify({
        'result': result,
        'score': score,
        'message': message,
        'emailed': emailed,
        'status': 'success' if result != 'ERROR' else 'failed',
        'files': len(saved_paths)
    })

def run_analysis(filepath: str, module: str, user_id: int):
    """Run the actual M1/M2/M3 analysis on uploaded file and send email report."""
    try:
        from module_wrapper import analyze_file, send_report_email
        
        print(f"[APP] Running analysis for user {user_id}: {filepath}")
        result, score, message = analyze_file(filepath, module)
        
        # Get user email for reporting
        conn = get_db()
        user = conn.execute('SELECT email FROM users WHERE id = ?', (user_id,)).fetchone()
        user_email = user['email'] if user else None
        conn.close()
        
        emailed = False
        # Send email if analysis was successful
        if user_email and result != "ERROR":
            subject = f"SentinAI Analysis Report - {module.upper()}"
            body = f"""
Analysis Complete

Module: {module.upper()}
Result: {result}
Confidence: {score}%
Message: {message}
Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
SentinAI Omega - Enterprise AI Detection System
"""
            print(f"[APP] Sending email to {user_email}")
            try:
                emailed = send_report_email(user_email, subject, body)
            except Exception as e:
                print(f"[APP] Warning: send_report_email failed: {e}")

        return result, score, message, emailed
    except Exception as e:
        print(f"[APP] Analysis error: {e}")
        traceback.print_exc()
        return "ERROR", 0, str(e), False


def run_m1_analysis(filepaths: list, user_id: int):
    """Run M1 analysis on multiple document files."""
    try:
        from module_wrapper import analyze_document_m1, send_report_email
        
        print(f"[APP-M1] Running analysis for user {user_id} on {len(filepaths)} files")
        result, score, message = analyze_document_m1(filepaths)
        
        # Get user email
        conn = get_db()
        user = conn.execute('SELECT email FROM users WHERE id = ?', (user_id,)).fetchone()
        user_email = user['email'] if user else None
        conn.close()
        
        # Send email
        emailed = False
        if user_email and result != "ERROR":
            subject = f"SentinAI Document Analysis Report - {result}"
            body = f"""
Document Grouping & Duplicate Detection Complete

Module: DOCUMENT_GROUPING
Result: {result}
Confidence: {score}%
Details: {message}
Files Analyzed: {len(filepaths)}
Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
SentinAI Omega - Enterprise AI Detection System
"""
            print(f"[APP-M1] Sending email to {user_email}")
            # Try to create a PDF report and attach it
            try:
                from fpdf import FPDF
                import tempfile

                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("Arial", size=12)
                for line in body.splitlines():
                    pdf.multi_cell(0, 8, line)

                tf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                tf_path = tf.name
                tf.close()
                pdf.output(tf_path)
                try:
                    emailed = send_report_email(user_email, subject, body, tf_path)
                finally:
                    try:
                        os.remove(tf_path)
                    except Exception:
                        pass
            except Exception as e:
                print(f"[APP-M1] Warning: PDF generation failed: {e}")
                try:
                    emailed = send_report_email(user_email, subject, body)
                except Exception as e:
                    print(f"[APP-M1] Warning: send_report_email failed: {e}")

        return result, score, message, emailed
    except Exception as e:
        print(f"[APP-M1] Error: {e}")
        traceback.print_exc()
        return "ERROR", 0, str(e), False


def run_m3_analysis(filepaths: list, user_id: int):
    """Run M3 analysis on multiple image files."""
    try:
        from module_wrapper import analyze_image_m3, send_report_email
        
        print(f"[APP-M3] Running analysis for user {user_id} on {len(filepaths)} image(s)")
        
        # Analyze each image and aggregate results
        results = []
        total_score = 0
        
        for filepath in filepaths:
            result, score, msg = analyze_image_m3(filepath)
            results.append({'file': os.path.basename(filepath), 'result': result, 'score': score})
            total_score += score
        
        # Aggregate: if any is AI_GENERATED, mark overall as AI_GENERATED
        ai_count = sum(1 for r in results if r['result'] == 'AI_GENERATED')
        overall_result = "AI_GENERATED" if ai_count > 0 else "REAL"
        overall_score = int(total_score / len(results)) if results else 0
        
        message = f"Analyzed {len(results)} image(s). {ai_count} AI-generated, {len(results)-ai_count} real"
        
        # Get user email
        conn = get_db()
        user = conn.execute('SELECT email FROM users WHERE id = ?', (user_id,)).fetchone()
        user_email = user['email'] if user else None
        conn.close()
        
        # Send email
        emailed = False
        if user_email and overall_result != "ERROR":
            subject = f"SentinAI Image Analysis Report - {overall_result}"
            details = "\n".join([f"  • {r['file']}: {r['result']} ({r['score']}%)" for r in results])
            body = f"""
Image Deepfake Detection Analysis Complete

Module: IMAGE_DEEPFAKE_DETECTION
Overall Result: {overall_result}
Average Confidence: {overall_score}%
Message: {message}

Individual Results:
{details}

Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
SentinAI Omega - Enterprise AI Detection System
"""
            print(f"[APP-M3] Sending email to {user_email}")
            # Try to create a PDF report with details and attach it
            try:
                from fpdf import FPDF
                import tempfile

                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 8, body)
                pdf.ln(6)
                pdf.set_font("Arial", size=11)
                pdf.cell(0, 6, 'Individual Results:', ln=1)
                for r in results:
                    pdf.multi_cell(0, 6, f" - {r['file']}: {r['result']} ({r['score']}%)")

                tf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                tf_path = tf.name
                tf.close()
                pdf.output(tf_path)
                try:
                    emailed = send_report_email(user_email, subject, body, tf_path)
                finally:
                    try:
                        os.remove(tf_path)
                    except Exception:
                        pass
            except Exception as e:
                print(f"[APP-M3] Warning: PDF generation failed: {e}")
                try:
                    emailed = send_report_email(user_email, subject, body)
                except Exception as e:
                    print(f"[APP-M3] Warning: send_report_email failed: {e}")

        return overall_result, overall_score, message, emailed
    except Exception as e:
        print(f"[APP-M3] Error: {e}")
        traceback.print_exc()
        return "ERROR", 0, str(e), False


@app.route('/static/<path:pth>')
def static_proxy(pth):
    return send_from_directory('static', pth)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
