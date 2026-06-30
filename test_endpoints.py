import requests
import sys

BASE_URL = "http://localhost:8000"

def test_module1():
    print("Testing Module 1 (Document Analysis)...")
    url = f"{BASE_URL}/api/module1/analyze"
    
    # We will upload student_A.txt and student_B.txt
    files = [
        ('files', ('student_A.txt', open('Module-1/sample_assignments/student_A.txt', 'rb'), 'text/plain')),
        ('files', ('student_B.txt', open('Module-1/sample_assignments/student_B.txt', 'rb'), 'text/plain'))
    ]
    
    try:
        response = requests.post(url, files=files)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("[SUCCESS] Module 1 Test Passed!")
                print(f"Files analyzed: {data['files_analyzed']}")
                print(f"Verdicts: {list(data['verdicts'].keys())}")
            else:
                print("[FAIL] Module 1 Failed: API returned success=False")
                print(data)
        else:
            print(f"[FAIL] Module 1 Failed with Status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[FAIL] Module 1 Exception: {e}")

def test_module2():
    print("\nTesting Module 2 (Image Classification)...")
    url = f"{BASE_URL}/api/module2/classify"
    
    # We will upload ai_watch.jpg
    files = {
        'image': ('ai_watch.jpg', open('Module-2/independent_test/ai_watch.jpg', 'rb'), 'image/jpeg')
    }
    
    try:
        response = requests.post(url, files=files)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("[SUCCESS] Module 2 Test Passed!")
                print(f"Detected Category: {data['detected_category']}")
                print(f"Verdict: {data['result']['verdict']}")
                print(f"Confidence: {data['result']['confidence']}")
                if data['result'].get('error'):
                    print(f"Error: {data['result']['error']}")
                print(f"Full Data: {data['result']}")
            else:
                print("[FAIL] Module 2 Failed: API returned success=False")
                print(data)
        else:
            print(f"[FAIL] Module 2 Failed with Status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[FAIL] Module 2 Exception: {e}")

if __name__ == "__main__":
    test_module1()
    test_module2()
