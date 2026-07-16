/* Xeer AI — client API partagé (auth + fetch). */
const XeerAPI = (() => {
  const TOKEN_KEY = "xeer_token";
  const USER_KEY = "xeer_user";

  const getToken = () => localStorage.getItem(TOKEN_KEY);
  const getUser = () => {
    try { return JSON.parse(localStorage.getItem(USER_KEY) || "null"); }
    catch { return null; }
  };
  const setSession = (token, user) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  };
  const setUser = (user) => localStorage.setItem(USER_KEY, JSON.stringify(user));
  const clearSession = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  };

  async function request(path, { method = "GET", body = null, auth = true } = {}) {
    const headers = { "Content-Type": "application/json" };
    const token = getToken();
    if (auth && token) headers["Authorization"] = `Bearer ${token}`;

    const resp = await fetch(path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null,
    });

    let data = null;
    try { data = await resp.json(); } catch { /* réponse vide */ }

    if (!resp.ok) {
      const detail = data && data.detail
        ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail))
        : `Erreur ${resp.status}`;
      const err = new Error(detail);
      err.status = resp.status;
      throw err;
    }
    return data;
  }

  async function refreshUser() {
    const user = await request("/api/auth/me");
    setUser(user);
    return user;
  }

  return { request, getToken, getUser, setSession, setUser, clearSession, refreshUser };
})();
