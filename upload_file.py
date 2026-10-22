import argparse
import os
import sys
import requests

API_URL = "http://127.0.0.1:8000/api/check-file"

def upload_file(file_path: str):
    if not os.path.exists(file_path):
        print(f"[-] File not found: {file_path}")
        sys.exit(1)

    filename = os.path.basename(file_path)
    print(f"[*] Uploading '{filename}' to Turnitin AI Detection Bridge...")

    try:
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/octet-stream")}
            res = requests.post(API_URL, files=files)

        if res.status_code != 200:
            print(f"[-] Error (HTTP {res.status_code}): {res.text}")
            return

        data = res.json()
        print("\n==========================================")
        print("          TURNITIN AI DETECTION           ")
        print("==========================================")
        print(f"  Document ID      : {data.get('doc_id')}")
        print(f"  Filename         : {data.get('filename')}")
        print(f"  AI Score         : {data.get('ai_score')}%")
        print(f"  Similarity Score : {data.get('similarity_score')}%")
        print(f"  Word Count       : {data.get('word_count')}")
        print(f"  Flagged Segments : {data.get('flagged_segments')}")
        print(f"  Report URL       : {data.get('report_url')}")
        print("==========================================")

        flagged = data.get("flagged_sentences", [])
        if flagged:
            print("\nFlagged AI Sentences Preview:")
            for idx, s in enumerate(flagged[:5], 1):
                print(f"  [{idx}] \"{s}\"")

    except requests.exceptions.ConnectionError:
        print("[-] Could not connect to API server. Ensure 'python main.py' is running on http://127.0.0.1:8000")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload a document to Turnitin AI Detection Bridge")
    parser.add_argument("file", help="Path to .docx or .pdf file")
    args = parser.parse_args()

    upload_file(args.file)
