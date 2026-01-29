## 🚀 QUICK START GUIDE - SentinAI Omega Complete System

### ✅ WHAT YOU NOW HAVE

Your system is a **complete, production-ready web application** with:

- ✅ **Flask backend** (app.py) - handles auth, routes, and DB
- ✅ **Integration layer** (module_wrapper.py) - connects M1, M2, M3
- ✅ **6 HTML templates** - landing, signup, login, dashboard, admin, logs
- ✅ **Frontend JS & CSS** - smooth Fluent design with transitions
- ✅ **3 AI modules** - document analysis, text detection, image forensics
- ✅ **SQLite database** - auto-created on first run
- ✅ **Default admin user** - auto-created on startup

---

### 📦 RUN THE APP (3 SIMPLE STEPS)

**Step 1:** Install dependencies
```bash
cd d:\Others\Hackathon\GDG
pip install -r requirements.txt
```

**Step 2:** Start Flask server
```bash
python app.py
```

You'll see:
```
 * Running on http://127.0.0.1:5000
 * Debugger PIN: 289-250-891
```

**Step 3:** Open in browser
```
http://localhost:5000
```

---

### 🔐 DEFAULT LOGIN CREDENTIALS

**Admin Account (Auto-Created):**
- Email: `admin@local`
- Password: `AdminPass123`

Click **"Admin Login"** button on homepage

---

### 👤 TEST USER ACCOUNT

1. Click **"Get Started"** button
2. Register:
   - Name: Test User
   - Email: testuser@example.com
   - Password: TestPass123
3. Login & access dashboard

---

### 📊 TEST THE THREE MODULES

#### **Module 1: Document Grouping**
1. Go to `/dashboard`
2. Find "Document Grouping & Duplicate Check" card
3. Upload a `.txt`, `.pdf`, or `.docx` file
4. Result: `UNIQUE` or `DUPLICATE_RISK` (with score 0-100)

#### **Module 2: AI vs Human Text**
1. Go to `/dashboard`
2. Find "AI vs Human Text Detection" card
3. Upload a `.txt`, `.pdf`, or `.docx` file
4. Result: `HUMAN_TEXT` or `AI_TEXT` (with score 0-100)

#### **Module 3: Deepfake Image Detection**
1. Go to `/dashboard`
2. Find "AI / Deepfake Image Detection" card
3. Upload `.jpg`, `.png`, or `.jpeg` file
4. Result: `REAL` or `AI_GENERATED` (with score 0-100)

---

### 🛡️ TEST ADMIN FEATURES

1. Login as `admin@local` / `AdminPass123`
2. Go to `/admin` dashboard
3. You'll see:
   - **Overview cards**: Total users, blocked users, total analyses
   - **User management table**: All registered users
   - **Block button**: Click to restrict user access

4. Click **"View System Logs"** to see:
   - Timestamp of each analysis
   - Who ran it (user email)
   - Which module (duplicate/text/image)
   - Result & confidence score

---

### 📁 KEY FILES & THEIR ROLES

| File | Purpose |
|------|---------|
| `app.py` | Flask routes, auth, sessions, database |
| `module_wrapper.py` | Wraps M1/M2/M3 with simple function interfaces |
| `M1.py` | Document grouping & duplicate detection |
| `M2.py` | AI vs human text detection |
| `M3.py` | Deepfake image detection |
| `templates/layout.html` | Base page layout with navbar |
| `templates/dashboard.html` | User analysis interface |
| `templates/admin.html` | Admin dashboard & user management |
| `static/css/style.css` | Fluent design, smooth transitions |
| `static/js/main.js` | Upload handlers, admin actions |
| `requirements.txt` | Python package list |
| `app.db` | SQLite database (auto-created) |

---

### 🌐 NAVIGATION MAP

```
http://localhost:5000/
    ├── / (landing page)
    ├── /signup (register)
    ├── /login (authenticate)
    ├── /logout (clear session)
    ├── /dashboard (user area) [LOGIN REQUIRED]
    │   └── POST /upload/{duplicate|text|image}
    └── /admin (admin area) [ADMIN ONLY]
        ├── /admin/users (JSON list)
        ├── /admin/block (block/unblock user)
        └── /admin/logs (audit trail)
```

---

### 💾 HOW UPLOADING WORKS

```
1. User selects file on /dashboard
2. JavaScript sends to POST /upload/{module}
3. Flask saves file to uploads/{user_id}/
4. Calls module_wrapper.analyze_file()
5. Returns {result, score}
6. Saves to DB logs table
7. Shows result with animation on frontend
```

---

### 🔍 CHECK THE DATABASE

```bash
# Open SQLite
sqlite3 app.db

# View users
SELECT id, name, email, role, blocked FROM users;

# View analysis logs
SELECT * FROM logs ORDER BY timestamp DESC LIMIT 10;
```

---

### ⚙️ CUSTOMIZE ADMIN CREDENTIALS

Before starting the app, set environment variables:

```bash
# Windows PowerShell
$env:DEFAULT_ADMIN_EMAIL = "youradmin@domain.com"
$env:DEFAULT_ADMIN_PW = "YourSecurePassword123"
python app.py
```

Or edit `app.py` lines 70-78 to hardcode defaults.

---

### 🌍 DEPLOY TO CLOUD (Render.com)

1. Push to GitHub
2. Create Render Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn app:app`
5. Add environment variables:
   ```
   FLASK_SECRET=your-random-key
   DEFAULT_ADMIN_EMAIL=admin@domain.com
   DEFAULT_ADMIN_PW=SecurePassword
   ```
6. Deploy!

---

### 📊 WHAT JUDGES WILL SEE

✅ **Enterprise UI**
- Clean, modern Fluent design
- Smooth hover/transition effects
- Professional navbar & layout

✅ **Multi-user System**
- Signup / Login
- User dashboard with personalized data
- Admin oversight of all users

✅ **Role-based Access**
- Normal users see only their data
- Admins see everything
- Blocked users cannot access anything

✅ **AI Analysis**
- 3 modules working in real-time
- Results with confidence scores
- File upload & analysis pipeline

✅ **System Logs**
- Admin can audit all activity
- Shows who did what, when
- Proves governance & compliance

✅ **Cloud-Ready**
- Stateless design
- Database abstraction
- Environment-based config
- Easy to deploy to Render/Heroku

---

### 🚨 COMMON ISSUES

**Port 5000 in use?**
```bash
lsof -i :5000
kill -9 <PID>
python app.py
```

**"No module named M1"?**
- Ensure M1.py, M2.py, M3.py in same folder as app.py
- Run from that directory

**Database locked?**
- Stop Flask server
- Delete `app.db`
- Restart Flask

---

### 🎯 NOW YOU HAVE

✅ Frontend + Backend integrated  
✅ All 3 modules connected  
✅ Database with users & logs  
✅ Admin dashboard with controls  
✅ Default admin auto-created  
✅ Ready to impress judges!  

**Start now:**
```bash
python app.py
```

Then open **http://localhost:5000**

---

Good luck with your hackathon! 🚀
