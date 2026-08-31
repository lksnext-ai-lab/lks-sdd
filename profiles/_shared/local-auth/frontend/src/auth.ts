/** Credentials exist in memory or in the HttpOnly cookie, never web storage. */
let access: string | null = null;
let refreshInFlight: Promise<void> | null = null;
let generation = 0;
const listeners = new Set<() => void>();
const channel = typeof BroadcastChannel !== "undefined" ? new BroadcastChannel("lks-auth-events") : null;

function clearLocal() {
  generation += 1;
  access = null;
  listeners.forEach(listener => listener());
}
if (channel) channel.onmessage = event => { if (event.data === "logout") clearLocal(); };

export function onSessionEnded(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

async function request(path: string, body: unknown) {
  return fetch(path, {method: "POST", credentials: "include", headers: {"Content-Type": "application/json", "X-CSRF": "1"}, body: JSON.stringify(body), cache: "no-store", signal: AbortSignal.timeout(10000)});
}

async function rotate() {
  const epoch = generation;
  const response = await request("/auth/refresh", {});
  if (!response.ok) { clearLocal(); throw new Error("Please sign in again"); }
  const value = await response.json();
  if (epoch !== generation) throw new Error("Session ended");
  access = value.access_token;
}

export async function refresh() {
  if (!refreshInFlight) {
    // Web Locks serializes refresh across tabs sharing the same Secure cookie.
    // Fail closed on platforms without that primitive instead of racing tokens.
    if (!navigator.locks) throw new Error("This browser does not support safe session renewal");
    refreshInFlight = navigator.locks.request("lks-auth-refresh", rotate).then(() => {}).finally(() => { refreshInFlight = null; });
  }
  return refreshInFlight;
}

export async function login(username: string, password: string, organization: string) {
  const epoch = generation;
  const response = await request("/auth/login", {username, password, organization});
  if (!response.ok) throw new Error(response.status === 429 ? "Please try again later" : "Unable to sign in");
  const value = await response.json();
  if (epoch !== generation) throw new Error("Session ended");
  access = value.access_token;
}

export async function api(path: string, init: RequestInit = {}, retry = true): Promise<Response> {
  if (!path.startsWith("/") || path.startsWith("//")) throw new Error("Same-origin API path required");
  if (!access) await refresh();
  const epoch = generation;
  const response = await fetch(path, {...init, signal: init.signal ? AbortSignal.any([init.signal, AbortSignal.timeout(10000)]) : AbortSignal.timeout(10000), credentials: "include", cache: "no-store", headers: {...init.headers, "Content-Type": "application/json", "X-CSRF": "1", Authorization: `Bearer ${access}`}});
  if (epoch !== generation) throw new Error("Session ended");
  if (response.status === 401 && retry) { await refresh(); return api(path, init, false); }
  if (response.status === 401) clearLocal();
  return response;
}

export async function logout(): Promise<boolean> {
  clearLocal();
  channel?.postMessage("logout");
  try {
    const response = await request("/auth/logout", {});
    return response.ok && (await response.json()).revoked === true;
  } catch { return false; }
}
