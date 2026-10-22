import io
import json
import logging
import os
import re
from typing import Dict, Any, Optional, List
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import docx
from pypdf import PdfReader

from algo_port import run_sentence_algo

load_dotenv()

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    try:
        if ext == ".docx":
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([p.text for p in doc.paragraphs if p.text])
        elif ext == ".pdf":
            reader = PdfReader(io.BytesIO(file_bytes))
            pages_text = [page.extract_text() for page in reader.pages if page.extract_text()]
            return "\n".join(pages_text)
        else:
            return file_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Error extracting text from {filename}: {e}")
        return file_bytes.decode("utf-8", errors="ignore")

logger = logging.getLogger("edu_turnitin")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_URL = "https://edu-turnitin.com"
SIGNIN_URL = f"{BASE_URL}/home/signin"
ORIGINALITY_URL = f"{BASE_URL}/home/originality"
UPLOAD_URL = f"{BASE_URL}/home/upload"
REPORT_URL = f"{BASE_URL}/home/report"
UPDATE_SCORE_URL = f"{BASE_URL}/home/update_score.php"

class EduTurnitinClient:
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username or os.getenv("EDU_TURNITIN_USER")
        self.password = password or os.getenv("EDU_TURNITIN_PASS")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": f"{BASE_URL}/home"
        })
        self.is_authenticated = False

    def login(self) -> bool:
        if not self.username or not self.password:
            raise ValueError("Credentials missing. Please set EDU_TURNITIN_USER and EDU_TURNITIN_PASS in .env")

        logger.info(f"Authenticating as {self.username} against {SIGNIN_URL}...")
        self.session.get(f"{BASE_URL}/home")

        payload = {
            "form_type": "login",
            "username": self.username,
            "password": self.password
        }

        res = self.session.post(SIGNIN_URL, data=payload, allow_redirects=True)
        if "Invalid username or password" in res.text:
            self.is_authenticated = False
            logger.error("Authentication failed: Invalid credentials.")
            return False

        if "originality" in res.text or "Dashboard - Turnitin" in res.text or res.url.endswith("/index"):
            self.is_authenticated = True
            logger.info("Successfully authenticated to edu-turnitin.com!")
            return True

        self.is_authenticated = True
        return True

    def ensure_authenticated(self):
        if not self.is_authenticated:
            if not self.login():
                raise PermissionError("Failed to authenticate to edu-turnitin.com")

    def get_file_list(self) -> List[Dict[str, Any]]:
        """
        Retrieves all documents from the 'My Files' (originality) dashboard.
        """
        self.ensure_authenticated()
        res = self.session.get(ORIGINALITY_URL)
        soup = BeautifulSoup(res.text, "html.parser")

        files = []
        for row in soup.find_all("tr", {"data-type": "file"}):
            files.append({
                "doc_id": row.get("data-id"),
                "title": row.get("data-title"),
                "author": row.get("data-author"),
                "ai_score": int(row.get("data-ai", -1)),
                "date_timestamp": row.get("data-date"),
                "report_url": f"{REPORT_URL}?id={row.get('data-id')}"
            })
        return files

    def upload_and_check(
        self,
        file_bytes: bytes,
        filename: str,
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Uploads a document to edu-turnitin, fetches the report metadata,
        calculates the AI score using the portal algorithm, updates the score,
        and returns the complete AI analysis.
        """
        self.ensure_authenticated()

        logger.info(f"Uploading file '{filename}' to {UPLOAD_URL}...")
        files = {
            "file": (filename, file_bytes, "application/octet-stream")
        }
        data = {
            "parent_id": "0"
        }

        upload_headers = {
            "Referer": ORIGINALITY_URL,
            "X-Requested-With": "XMLHttpRequest"
        }

        res = self.session.post(UPLOAD_URL, data=data, files=files, headers=upload_headers)
        logger.info(f"Upload HTTP status: {res.status_code}")

        doc_id = None
        try:
            resp_json = res.json()
            doc_id = resp_json.get("id") or resp_json.get("doc_id")
        except Exception:
            # Fallback regex search
            match = re.search(r'["\']?(?:id|doc_id)["\']?\s*:\s*["\']?(\d+)', res.text)
            if match:
                doc_id = match.group(1)

        if not doc_id:
            # Inspect originality page for newly uploaded row
            file_list = self.get_file_list()
            for f in file_list:
                if f["title"] == filename:
                    doc_id = f["doc_id"]
                    break

        if not doc_id:
            raise RuntimeError(f"Upload failed or doc_id could not be found. Response: {res.text[:300]}")

        logger.info(f"Document uploaded successfully! Assigned doc_id: {doc_id}")

        # Fetch report page to acquire triggers and document metadata
        report_url = f"{REPORT_URL}?id={doc_id}"
        logger.info(f"Fetching report metadata from {report_url}...")
        report_res = self.session.get(report_url)

        # Extract docData JSON
        doc_data = {}
        m = re.search(r'const\s+docData\s*=\s*(\{.*?\});', report_res.text)
        if m:
            try:
                doc_data = json.loads(m.group(1))
            except Exception as e:
                logger.warning(f"Failed to parse docData as strict JSON: {e}")

        triggers = doc_data.get("triggers", [])
        similarity_score = doc_data.get("similarity_score", 0)

        # Extract text content if not passed directly
        content_to_scan = text_content
        if not content_to_scan:
            content_to_scan = extract_text_from_file(file_bytes, filename)

        # Compute AI detection score
        algo_result = run_sentence_algo(content_to_scan, triggers)
        ai_score = algo_result["score"]
        word_count = algo_result["word_count"]

        # Sync score back to backend
        try:
            update_url = f"{UPDATE_SCORE_URL}?doc_id={doc_id}&ai_score={ai_score}&word_count={word_count}"
            self.session.get(update_url)
            logger.info(f"Synchronized score to backend: {ai_score}% (doc_id: {doc_id})")
        except Exception as e:
            logger.warning(f"Failed to sync score to backend: {e}")

        return {
            "status": "success",
            "doc_id": doc_id,
            "filename": filename,
            "ai_score": ai_score,
            "similarity_score": similarity_score,
            "word_count": word_count,
            "flagged_segments": algo_result["flagged_count"],
            "flagged_sentences": algo_result["flagged_sentences"][:10],
            "report_url": report_url
        }
