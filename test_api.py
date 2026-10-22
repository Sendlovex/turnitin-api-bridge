import requests

API_URL = "http://127.0.0.1:8000"

def test_health():
    print("[*] Testing /api/health...")
    res = requests.get(f"{API_URL}/api/health")
    print("Health Status:", res.status_code, res.json())

def test_list_files():
    print("[*] Testing /api/files (all instructor submissions)...")
    res = requests.get(f"{API_URL}/api/files")
    data = res.json()
    print(f"Total Papers in Account: {data.get('count')}")
    if data.get("files"):
        latest = data["files"][0]
        print(f"Latest Paper: '{latest['title']}' | AI Score: {latest['ai_score']}% | Link: {latest['report_url']}")

def test_check_text(sample_text: str):
    print("\n[*] Testing /api/check-text (submitting text directly)...")
    payload = {
        "text": sample_text,
        "title": "API_Essay_Test.docx",
        "author": "Student Tester"
    }
    res = requests.post(f"{API_URL}/api/check-text", json=payload)
    print("AI Check Result:", res.status_code, res.json())

if __name__ == "__main__":
    print("========================================")
    print("  Testing Turnitin AI Detection Bridge  ")
    print("========================================")
    try:
        test_health()
        test_list_files()
    except requests.exceptions.ConnectionError:
        print("[!] Server not running yet. Start it with: python main.py")
