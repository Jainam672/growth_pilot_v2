const API_BASE = "http://localhost:8000";

// ─── Path resolver: works from both /pages/ and root ────────
function _authPage(page) {
  const inPages = window.location.pathname.includes("/pages/");
  return inPages ? page : "pages/" + page;
}

// ─── Core request helper ─────────────────────────────────────
async function request(method, endpoint, body = null) {
  const token = localStorage.getItem("gp_token");
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const opts = { method, headers };
  if (body && method !== "GET") opts.body = JSON.stringify(body);

  let res;
  try {
    res = await fetch(API_BASE + endpoint, opts);
  } catch (err) {
    throw new Error("Cannot connect to server. Make sure the backend is running on port 8000.");
  }

  if (res.status === 401) {
    if (endpoint !== "/auth/login" && endpoint !== "/auth/register") {
      localStorage.clear();
      window.location.href = _authPage("login.html");
      return;
    }
  }
  if (res.status === 204) return null;

  let data;
  try { data = await res.json(); } catch { data = {}; }
  if (!res.ok) {
    let msg = "Request failed (" + res.status + ")";
    if (data.detail) {
      if (typeof data.detail === "string") msg = data.detail;
      else if (Array.isArray(data.detail)) msg = data.detail.map(e => e.msg).join(", ");
      else msg = JSON.stringify(data.detail);
    }
    throw new Error(msg);
  }
  return data;
}

// ─── API methods ─────────────────────────────────────────────
const api = {
  register:    (name, email, password, language, age, city, profession, exp, interest, income, birthdate, state, country, mobile, gender, usage_purpose) =>
                 request("POST", "/auth/register", { 
                   name, email, password, language: language || "en",
                   age: parseInt(age) || null, city, profession,
                   experience_level: exp || "beginner", business_interest: interest,
                   income, birthdate, state, country, mobile_number: mobile, gender, usage_purpose
                 }),
  login:       (email, password) =>
                 request("POST", "/auth/login", { email, password }),
  getMe:       ()        => request("GET",  "/me"),
  createIdea:  (data)    => request("POST", "/idea/",          data),
  listIdeas:   ()        => request("GET",  "/idea/"),
  getIdea:     (id)      => request("GET",  "/idea/" + id),
  deleteIdea:  (id)      => request("DELETE", "/idea/" + id),
  analyzeIdea: (idea_id) => request("POST", "/ai/analyze",     { idea_id }),
  getResult:   (idea_id) => request("GET",  "/ai/result/" + idea_id),
  getDashboard:()        => request("GET",  "/dashboard/stats"),
  getSettings: ()        => request("GET",  "/settings/"),
  saveSettings:(data)    => request("PUT",  "/settings/",      data),
  sendChat:    (messages, idea_context) => request("POST", "/chat/message",  { messages, idea_context }),
};

// ─── Auth helpers ─────────────────────────────────────────────
function saveAuth(token, userId, name, email) {
  localStorage.setItem("gp_token", token);
  localStorage.setItem("gp_user_id", String(userId));
  localStorage.setItem("gp_name", name);
  localStorage.setItem("gp_email", email);
}
function getUser() {
  return {
    id:    localStorage.getItem("gp_user_id"),
    name:  localStorage.getItem("gp_name")  || "Entrepreneur",
    email: localStorage.getItem("gp_email") || ""
  };
}
function isLoggedIn() { return !!localStorage.getItem("gp_token"); }
function requireAuth() {
  if (!isLoggedIn()) window.location.href = _authPage("login.html");
}
function logout() {
  localStorage.clear();
  window.location.href = _authPage("login.html");
}

// ─── Utility helpers ──────────────────────────────────────────
function timeAgo(d) {
  const days = Math.floor((Date.now() - new Date(d).getTime()) / 86400000);
  if (!days) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return days + " days ago";
  if (days < 14) return "1 week ago";
  return Math.floor(days / 7) + " weeks ago";
}
function parseList(v) {
  if (Array.isArray(v)) return v;
  if (!v) return [];
  try { const p = JSON.parse(v); return Array.isArray(p) ? p : []; } catch { return []; }
}
function formatBudget(val) {
  const n = parseInt(val) || 0;
  if (n >= 100000) return "₹" + (n / 100000).toFixed(n % 100000 === 0 ? 0 : 1) + "L";
  if (n >= 1000)   return "₹" + Math.round(n / 1000) + "K";
  return "₹" + n;
}
function catClass(c) {
  if (!c) return "other"; c = c.toLowerCase();
  if (c.includes("food")||c.includes("bev")||c.includes("chai")) return "food";
  if (c.includes("tech")||c.includes("soft")||c.includes("app")) return "tech";
  if (c.includes("edu")||c.includes("train")) return "edu";
  return "other";
}
function catEmoji(c) {
  if (!c) return "💼"; c = c.toLowerCase();
  if (c.includes("food")||c.includes("bev")||c.includes("chai")) return "🍽️";
  if (c.includes("tech")||c.includes("soft")||c.includes("app")) return "💻";
  if (c.includes("edu")) return "📚";
  if (c.includes("health")) return "💊";
  if (c.includes("fashion")) return "👗";
  if (c.includes("retail")||c.includes("ecomm")) return "🛍️";
  if (c.includes("agri")) return "🌾";
  if (c.includes("travel")||c.includes("tourism")) return "✈️";
  return "💼";
}
