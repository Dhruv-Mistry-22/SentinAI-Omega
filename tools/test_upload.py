"""
Simple test script to login and upload multiple files to M1 (/upload/duplicate).
Update EMAIL and PASSWORD to an account that exists in the app, and FILES paths.
"""
import requests
import os
import sys

BASE = "http://127.0.0.1:5000"
EMAIL = "test@example.com"  # replace
PASSWORD = "Test123!"       # replace
FILES = [
    r"d:\\Others\\Hackathon\\GDG\\dataM1\\a.txt",
    r"d:\\Others\\Hackathon\\GDG\\dataM1\\b.txt",
]

s = requests.Session()
# Login
r = s.post(f"{BASE}/login", data={"email": EMAIL, "password": PASSWORD}, allow_redirects=True)
print("Login status code:", r.status_code)
if r.status_code != 200:
    print("Login response snippet:", r.text[:400])

# Verify we are logged in by fetching dashboard
r2 = s.get(f"{BASE}/dashboard")
print("Dashboard fetch status:", r2.status_code)
if "Login" in r2.text and r2.status_code == 200:
    print("It looks like login did not succeed (dashboard returned login page). Check credentials.")

# Prepare files
files = []
for p in FILES:
    if not os.path.exists(p):
        print("Missing test file:", p)
        sys.exit(1)
    files.append(('files', (os.path.basename(p), open(p, 'rb'))))

print('Uploading files:', [f[1][0] for f in files])
resp = s.post(f"{BASE}/upload/duplicate", files=files)
print('Upload status code:', resp.status_code)
try:
    print('Response JSON:', resp.json())
except Exception:
    print('Response text:', resp.text)
