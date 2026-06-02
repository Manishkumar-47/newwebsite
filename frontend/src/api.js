const API_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = typeof payload === "object" ? payload.detail || "Request failed" : payload;
    throw new Error(message);
  }
  return payload;
}

export async function uploadPdf(file) {
  const formData = new FormData();
  formData.append("file", file);
  return parseResponse(
    await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
    }),
  );
}

export async function getReport(reportId) {
  return parseResponse(await fetch(`${API_BASE}/report/${reportId}`));
}

export function reportDownloadUrl(reportId, format) {
  return `${API_BASE}/report/${reportId}/download/${format}`;
}

export { API_BASE };

