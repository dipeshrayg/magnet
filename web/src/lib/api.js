// In dev, Vite proxies /api to localhost:8000 (vite.config.js). In a static
// deploy (GitHub Pages) there's no proxy, so the deployed backend's origin
// must be baked in at build time via VITE_API_BASE.
const BASE = `${import.meta.env.VITE_API_BASE || ""}/api`;

async function req(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${method} ${path} -> ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  get: (path) => req("GET", path),
  post: (path, body) => req("POST", path, body || {}),
  put: (path, body) => req("PUT", path, body || {}),
};
