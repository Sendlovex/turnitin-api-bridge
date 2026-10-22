# Turnitin AI Detection API Bridge

High-performance REST API bridge turning `edu-turnitin.com` instructor accounts into an automated AI detection engine for web applications.

---

## 1. Quick Start

### Step 1: Start the Server
Dependencies are already installed and credentials have been verified against `edu-turnitin.com`:
```bash
python main.py
```
The server will boot on `http://localhost:8000`.

### Step 2: Open Interactive API Documentation
Navigate to:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Step 3: Run the Test Client
In another terminal:
```bash
python test_api.py
```

---

## 2. API Endpoints

### `POST /api/check-text`
Submit raw text and get immediate AI detection percentage, word count, and flagged sentences.

**Payload:**
```json
{
  "text": "Artificial intelligence algorithms continue to revolutionize modern technological capabilities...",
  "title": "Essay_1.docx",
  "author": "Student"
}
```

**Response:**
```json
{
  "status": "success",
  "doc_id": "7517",
  "filename": "Essay_1.docx",
  "ai_score": 85,
  "similarity_score": 0,
  "word_count": 640,
  "flagged_segments": 14,
  "flagged_sentences": [
    "Artificial intelligence algorithms continue to revolutionize modern technological capabilities."
  ],
  "report_url": "https://edu-turnitin.com/home/report?id=7517"
}
```

---

### `POST /api/check-file`
Upload `.docx` or `.pdf` file via multipart form data:
```bash
curl -X POST "http://localhost:8000/api/check-file" \
  -F "file=@student_paper.docx"
```

---

### `GET /api/files`
List all documents and their calculated AI scores recorded under this instructor account.

---

### `GET /api/health`
Verify that the instructor account session is online and authenticated.

---

## 3. Web App Frontend Integration (JavaScript / Fetch)

```javascript
async function checkAI(paperText, filename = "Submission.docx") {
  const response = await fetch("http://localhost:8000/api/check-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: paperText,
      title: filename
    })
  });

  const data = await response.json();
  console.log(`AI Detection: ${data.ai_score}%`);
  console.log(`Report URL: ${data.report_url}`);
  return data;
}
```
