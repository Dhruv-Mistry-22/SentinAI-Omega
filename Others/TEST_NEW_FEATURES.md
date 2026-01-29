# Testing Guide - M1 Multiple Files & Progress Messages (Updated Message 10)

## ✅ What's Been Fixed

### 1. **M1 Now Accepts Multiple Documents (Folder Logic)**
- **Before**: Only accepted single .txt/.pdf/.docx file
- **After**: Accepts 2+ documents at once, compares them for duplicates
- **How**: Upload as folder by selecting multiple files in file picker

### 2. **Real Progress Messages Now Display**
- **Before**: Clicking "Analyze" showed nothing until result
- **After**: Shows "⏳ Processing..." with:
  - Module name (DUPLICATE, TEXT ANALYSIS, IMAGE DETECTION)
  - File count and file names
  - Status: "Analyzing with AI models..."
  - Spinner animation

### 3. **Email Reports Sent Automatically**
- **Before**: No confirmation user got email
- **After**: Shows "✉️ Email report sent" after analysis
- **Also**: Admin can see all emails sent in Logs

---

## 🧪 Step-by-Step Testing

### **TEST 1: Sign Up & Login**

1. Go to **http://localhost:5000**
2. Click **"Get Started"** button
3. Fill signup form:
   - Name: `Test User`
   - Email: `test@gmail.com` (or your real email for email testing)
   - Password: `Test123!`
   - Click **Sign Up**
4. You'll be redirected to **Login**
5. Enter email/password and click **Login**
6. You should see **Dashboard** with 3 modules

**Expected**: Dashboard loads with M1, M2, M3 cards visible

---

### **TEST 2: M1 - Multiple Document Upload (NEW)**

**Purpose**: Test M1 with 2-3 documents to verify duplicate detection

#### Step A: Create Test Documents
1. Create 2-3 text files:
   - `doc1.txt`: 
     ```
     This is a document about artificial intelligence.
     AI is transforming the world.
     Machine learning is a key technology.
     ```
   - `doc2.txt`:
     ```
     Artificial intelligence is changing society.
     AI and machine learning are important.
     The future is powered by AI.
     ```
   - `doc3.txt`:
     ```
     Cats are animals. Dogs are also animals.
     Birds can fly. Fish live in water.
     ```

2. **Save all 3 files locally** (e.g., in `Downloads` folder)

#### Step B: Upload to M1
1. On Dashboard, find **Module 1: Document Grouping** card
2. Click **"Choose Files"** button in M1 card
3. Select **ALL 3 files** (Ctrl+Click to multi-select)
4. Click **Open**
5. Files should show as selected
6. Click **Analyze** button

#### Step C: Verify Progress Message
**Watch carefully for:**
- ✅ Loading spinner appears
- ✅ Message shows: `"⏳ Processing... Module: DUPLICATE, Files: 3 (doc1.txt, doc2.txt, doc3.txt)"`
- ✅ After 3-5 seconds, result appears

#### Step D: Check Results
**Expected Result:**
- **Status**: "HAS_DUPLICATES" or similar (since doc1 & doc2 are similar)
- **Confidence**: 65-75% (similarity score)
- **Message**: Shows which documents are grouped together
- **Progress Bar**: Shows confidence as colored bar

**Screenshot moment**: Capture the result showing multiple files analyzed

---

### **TEST 3: M2 - Single Text File (Verify Still Works)**

1. Create `sample_text.txt`:
   ```
   This is a sample text for AI authenticity analysis.
   It might be written by human or AI.
   ```

2. On Dashboard, find **Module 2: Text Authenticity**
3. Click **"Choose File"** (should only allow 1 file now)
4. Select `sample_text.txt`
5. Click **Analyze**

#### Expected:
- ✅ Loading message: `"Module: TEXT ANALYSIS, Files: 1"`
- ✅ Result shows: "HUMAN_WRITTEN" or "AI_GENERATED" with score
- ✅ Progress bar shows confidence

---

### **TEST 4: M3 - Multiple Images (NEW)**

1. Download 2-3 sample images (or use any images on your PC):
   - Can be `.jpg`, `.png`, `.bmp`
   - Can be photos, AI-generated, or mixed

2. On Dashboard, find **Module 3: Deepfake Detection**
3. Click **"Choose Images"** button
4. Select **2-3 images** (Ctrl+Click to multi-select)
5. Click **Open**
6. Click **Analyze**

#### Expected:
- ✅ Loading message: `"Module: IMAGE DETECTION, Files: 3 (image1.jpg, image2.jpg, image3.jpg)"`
- ✅ After 5-10 seconds, result shows
- ✅ Result shows: "REAL" or "AI_GENERATED"
- ✅ Score aggregated from all images
- ✅ Progress bar displays

---

### **TEST 5: Email Report Confirmation**

#### Setup (One-time):
1. After each analysis, you should see: **"✉️ Email report sent"** message below results
2. Check your email inbox (might be in Spam)

#### Check Email Contains:
- ✅ Subject line with module name and result
- ✅ Timestamp of analysis
- ✅ Files analyzed (with file names)
- ✅ Confidence score
- ✅ Detailed message

**Example Email Subject**: `"SentinAI Omega: Document Analysis - HAS_DUPLICATES (74%)`

---

### **TEST 6: Admin Dashboard - Verify Logs**

1. Go to **http://localhost:5000/admin**
2. Login with:
   - Email: `admin@local`
   - Password: `AdminPass123`

3. Click **"View Logs"** button
4. You should see all analyses with:
   - User email
   - Module (duplicate/text/image)
   - Result
   - Confidence score
   - Timestamp

#### Expected Log Entries:
After running all tests above, you should see 3-4 log entries (M1, M2, M3)

**Example Log**:
```
Time: 2026-01-11 08:05:32
User: test@gmail.com
Module: duplicate
Result: HAS_DUPLICATES
Score: 74%
File: doc1.txt, doc2.txt, doc3.txt
```

---

### **TEST 7: User Blocking Feature**

1. In Admin dashboard, click **"View Users"**
2. Click **Block** button next to "Test User"
3. Logout and try to login as Test User
4. You should see: **"Your account has been blocked"** message

#### Expected:
- ✅ Blocked user cannot access dashboard
- ✅ Blocked user sees blocked.html page
- ✅ Admin can see "blocked: 1" in admin stats

---

## 🔍 Troubleshooting

### Issue: "Nothing happens when I click Analyze"
**Fix:**
1. Open **DevTools** (F12 in Chrome)
2. Click **Console** tab
3. Try analyze again
4. Look for any red error messages
5. Post the error in console

### Issue: "Progress message doesn't show"
**Fix:**
1. Check if file was selected (should show filename)
2. Wait 2-3 seconds (first run downloads AI models)
3. Check DevTools Network tab to see if request was sent

### Issue: "Email not received"
**Fix:**
1. Check Spam/Junk folder
2. Verify email address was typed correctly in signup
3. Check if Flask console shows `[EMAIL] ✓` message

### Issue: "M1 only takes one file"
**Fix (already done, but verify):**
1. Click "Choose Files" button (not "Choose File")
2. Use **Ctrl+Click** to select multiple files
3. All selected files should show in file input

---

## 📊 Expected Console Output (Flask Terminal)

When you run an analysis, Flask terminal should show:

```
[M1] Starting analysis on 3 document(s)
[M1] Reading 3 files...
[M1] ✓ Loaded: doc1.txt
[M1] ✓ Loaded: doc2.txt
[M1] ✓ Loaded: doc3.txt
[M1] Building similarity matrix...
[M1] Grouping documents...
[M1] Result: HAS_DUPLICATES (74%)
[EMAIL] Sending report to test@gmail.com...
[EMAIL] ✓ Report sent successfully
```

---

## ✨ Key Improvements in Message 10

| Feature | Before | After |
|---------|--------|-------|
| M1 Input | Single file only | Multiple files (folder) |
| Progress | Silent (no feedback) | Shows spinner + status |
| File Count | Not shown | Displays "Files: 3 (doc1, doc2, doc3)" |
| Email | Optional | Automatic + confirmation shown |
| Results | Basic | Shows progress bar + confidence |
| Logs | Not detailed | Shows all files in analysis |

---

## 🎯 Ready for Hackathon?

After passing all 7 tests, your system is ready:
- ✅ Multiple documents analyzed (M1)
- ✅ Real-time feedback to users (Progress messages)
- ✅ Automatic email reports
- ✅ Admin monitoring & user blocking
- ✅ Beautiful Fluent UI with animations

---

## 📝 Notes

- **First run** of each module takes 10-30 seconds (downloads AI models)
- **Subsequent runs** are fast (2-5 seconds) - models cached
- **Large files** (>10MB) may take longer
- **Email testing**: Use your real email to receive reports
- **Admin Email**: `admin@local` (no real mailbox, used for admin features only)

---

Good luck with hackathon! 🚀
