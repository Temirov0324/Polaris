/* Thin fetch() wrapper for the /api/v1/ backend. Auth tokens live in
   httpOnly cookies, so we never touch them here — just always send
   credentials and let a 401 trigger a single silent refresh + retry. */

const API_BASE = "/api/v1";

async function apiRequest(path, { method = "GET", body, retry = true } = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    credentials: "same-origin",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && retry) {
    const refreshed = await fetch(`${API_BASE}/auth/refresh/`, {
      method: "POST",
      credentials: "same-origin",
    });
    if (refreshed.ok) {
      return apiRequest(path, { method, body, retry: false });
    }
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(payload?.error?.message_uz || "Xatolik yuz berdi");
    error.details = payload?.error;
    error.status = response.status;
    throw error;
  }
  return payload;
}

window.api = {
  get: (path) => apiRequest(path),
  post: (path, body) => apiRequest(path, { method: "POST", body }),
  patch: (path, body) => apiRequest(path, { method: "PATCH", body }),
  delete: (path) => apiRequest(path, { method: "DELETE" }),
};
