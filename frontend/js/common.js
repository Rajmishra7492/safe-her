const API_BASE = "http://127.0.0.1:5000";

function getToken() {
  return localStorage.getItem("token") || "";
}

function getUser() {
  try { return JSON.parse(localStorage.getItem("user") || "null"); }
  catch { return null; }
}

function saveAuth(token, user) {
  localStorage.setItem("token", token);
  localStorage.setItem("user", JSON.stringify(user));
}

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  window.location.href = "login.html";
}

function requireAuth() {
  if (!getToken()) window.location.href = "login.html";
}

function mediaUrl(path) {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}

async function api(path, options = {}) {
  const headers = options.headers || {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

function setMsg(el, text, isErr = false) {
  el.textContent = text;
  el.style.color = isErr ? "#ef4444" : "#10b981";
}

function navHtml() {
  const user = getUser();
  const isAdmin = !!(user && (user.is_admin || user.role === "admin"));
  const adminLink = isAdmin ? '<a class="btn btn-outline" href="admin.html">Admin</a>' : '';
  return `
    <div class="nav">
      <div class="brand">SafeHer</div>
      <div class="links">
        <a class="btn btn-outline" href="dashboard.html">Dashboard</a>
        <a class="btn btn-outline" href="sos.html">SOS</a>
        <a class="btn btn-outline" href="contacts.html">Contacts</a>
        <a class="btn btn-outline" href="report.html">Report</a>
        <a class="btn btn-outline" href="alerts.html">Alerts</a>
        ${adminLink}
        <button class="btn btn-danger" onclick="logout()">Logout</button>
      </div>
    </div>
  `;
}
