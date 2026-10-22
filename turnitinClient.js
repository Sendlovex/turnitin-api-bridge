/**
 * Turnitin AI Detection API Bridge Client
 * Drop this file into your frontend project (React, Next.js, Vue, Vite, or Vanilla JS)
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_TURNITIN_API_URL 
  || process.env.VITE_TURNITIN_API_URL 
  || "https://turnitin-api-bridge.onrender.com"; // Replace with your actual Render URL

/**
 * Check raw text for AI-generated content
 * @param {string} text - Essay or document content
 * @param {string} title - Optional title (defaults to Paper.docx)
 * @param {string} author - Optional author name
 */
export async function checkText(text, title = "Submission.docx", author = "Student") {
  const response = await fetch(`${API_BASE_URL}/api/check-text`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text, title, author }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server responded with ${response.status}`);
  }

  return await response.json();
}

/**
 * Check an uploaded document file (.docx, .pdf, .txt)
 * @param {File|Blob} file - Uploaded File object from an <input type="file">
 * @param {string} title - Optional custom title
 */
export async function checkFile(file, title = null) {
  const formData = new FormData();
  formData.append("file", file);
  if (title) {
    formData.append("title", title);
  }

  const response = await fetch(`${API_BASE_URL}/api/check-file`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server responded with ${response.status}`);
  }

  return await response.json();
}

/**
 * Check if the API bridge is online and Turnitin session is authenticated
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return await response.json();
  } catch (err) {
    return { status: "offline", error: err.message };
  }
}

/**
 * Fetch all papers processed under this instructor account
 */
export async function getFileList() {
  const response = await fetch(`${API_BASE_URL}/api/files`);
  if (!response.ok) {
    throw new Error(`Failed to fetch file list: ${response.status}`);
  }
  return await response.json();
}
