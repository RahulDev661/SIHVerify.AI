// Central place for talking to the VERIDEX FastAPI backend.
//
// Set VITE_API_BASE_URL in a .env file at the project root to point at a
// different host (e.g. a deployed backend). Falls back to local dev.
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const TOKEN_KEY = "borderguardToken";
const USER_KEY = "borderguardUser";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

function saveSession(data) {
  localStorage.setItem(TOKEN_KEY, data.accessToken);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Registers a new officer account, then stores the session (token + user).
 *
 * @param {{name: string, email: string, officerId: string, password: string}} form
 */
export async function registerUser(form) {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(form),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Registration failed");
  }

  saveSession(data);
  return data.user;
}

/**
 * Logs an officer in and stores the session (token + user).
 *
 * @param {string} email
 * @param {string} password
 */
export async function loginUser(email, password) {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Login failed");
  }

  saveSession(data);
  return data.user;
}

/**
 * Fetches the current officer's profile using the stored bearer token.
 * Useful to validate that a stored token is still valid.
 */
export async function fetchCurrentUser() {
  const token = getToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Session expired");
  }

  return data;
}

/**
 * Runs the full passport verification pipeline (OCR + MRZ validation +
 * document check + optional face match).
 *
 * @param {File} passportImage - required
 * @param {File|null} selfieImage - optional, enables face-match
 */
export async function verifyPassport(passportImage, selfieImage) {
  const formData = new FormData();
  formData.append("passport_image", passportImage);

  if (selfieImage) {
    formData.append("selfie_image", selfieImage);
  }

  const token = getToken();

  const response = await fetch(`${API_BASE_URL}/api/v1/passport/verify`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Verification failed");
  }

  return data;
}

/**
 * Lists past screenings, most recent first.
 */
export async function getHistory(limit = 50) {
  const token = getToken();

  const response = await fetch(
    `${API_BASE_URL}/api/v1/passport/history?limit=${limit}`,
    { headers: token ? { Authorization: `Bearer ${token}` } : {} }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Could not load history");
  }

  return data;
}

/**
 * Fetches the full stored result for one past screening.
 */
export async function getHistoryDetail(historyId) {
  const token = getToken();

  const response = await fetch(
    `${API_BASE_URL}/api/v1/passport/history/${historyId}`,
    { headers: token ? { Authorization: `Bearer ${token}` } : {} }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Record not found");
  }

  return data;
}
