import os
import uuid
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from edu_turnitin_client import EduTurnitinClient

load_dotenv()

app = FastAPI(
    title="Turnitin AI Detection API Bridge",
    description="REST API proxy bridging edu-turnitin.com instructor account to external web applications.",
    version="1.0.0"
)

# Enable CORS for web apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = EduTurnitinClient()

class TextCheckRequest(BaseModel):
    text: str
    title: Optional[str] = None
    author: Optional[str] = "Student"

@app.get("/")
def root():
    return {
        "service": "Turnitin AI Detection API Bridge",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/api/health")
def health_check():
    try:
        client.ensure_authenticated()
        return {
            "status": "healthy",
            "authenticated": client.is_authenticated,
            "account_user": client.username
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }

@app.get("/api/files")
def list_files():
    """
    List all papers submitted under this instructor account with their AI scores.
    """
    try:
        files = client.get_file_list()
        return {"count": len(files), "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/check-file")
async def check_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None)
):
    """
    Upload a document (.pdf, .docx, .txt) and return immediate AI detection and similarity analysis.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    filename = file.filename or f"Doc_{uuid.uuid4().hex[:8]}.docx"
    try:
        result = client.upload_and_check(
            file_bytes=file_bytes,
            filename=filename
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Check failed: {str(e)}")

@app.post("/api/check-text")
def check_text(req: TextCheckRequest):
    """
    Submit raw text to Turnitin and return AI detection analysis.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    doc_title = req.title or f"Paper_{uuid.uuid4().hex[:8]}"
    filename = f"{doc_title}.docx" if not doc_title.endswith((".docx", ".txt", ".pdf")) else doc_title
    file_bytes = req.text.encode("utf-8")

    try:
        result = client.upload_and_check(
            file_bytes=file_bytes,
            filename=filename,
            text_content=req.text
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Check failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
    print(f"Starting Turnitin API Bridge on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False)
