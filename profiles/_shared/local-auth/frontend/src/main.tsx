import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { api, login, logout, onSessionEnded } from "./auth";
import "./style.css";

type Item = {id: string; label: string};

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [message, setMessage] = useState("");
  const [items, setItems] = useState<Item[]>([]);
  const [busy, setBusy] = useState(false);
  const sessionGeneration = useRef(0);
  useEffect(() => onSessionEnded(() => { sessionGeneration.current += 1; setAuthenticated(false); setItems([]); }), []);
  async function load() {
    const epoch = sessionGeneration.current;
    const response = await api("/records");
    if (!response.ok) throw new Error("Unable to read records");
    const records = await response.json();
    if (epoch !== sessionGeneration.current) return;
    setItems(records);
    setAuthenticated(true);
  }
  useEffect(() => { let disposed = false; const epoch = sessionGeneration.current;
    api("/records").then(async response => { if (response.ok) { const records = await response.json(); if (!disposed && epoch === sessionGeneration.current) { setItems(records); setAuthenticated(true); } } }).catch(() => {});
    return () => { disposed = true; };
  }, []);
  return <main><header><p className="eyebrow">LKS-SDD · ISOLATED REFERENCE</p><h1>Private workspace</h1><p>Local identity, live permissions and PostgreSQL persistence.</p></header>
    <p role="status" aria-live="polite">{message}</p>
    {!authenticated ? <form aria-label="Sign in" onSubmit={async event => {
      event.preventDefault(); const form = event.currentTarget; const values = new FormData(form); setBusy(true); setMessage("");
      try { await login(String(values.get("username")), String(values.get("password")), String(values.get("organization"))); form.reset(); await load(); }
      catch (error) { setMessage(error instanceof Error ? error.message : "Unable to sign in"); }
      finally { setBusy(false); }
    }}>
      <h2>Sign in</h2><label>Username<input name="username" autoComplete="username" required maxLength={120}/></label>
      <label>Password<input name="password" type="password" autoComplete="current-password" required maxLength={128}/></label>
      <label>Organization<input name="organization" required placeholder="Organization identifier"/></label>
      <button disabled={busy}>Sign in</button>
    </form> : <section aria-label="Workspace"><div className="section-heading"><h2>Records</h2><button disabled={busy} onClick={async () => { setBusy(true); const confirmed = await logout(); setMessage(confirmed ? "Signed out; server session revoked" : "Signed out locally. Server revocation could not be confirmed."); setBusy(false); }}>Sign out</button></div>
      <form aria-label="Create record" onSubmit={async event => { event.preventDefault(); const form = event.currentTarget; const label = String(new FormData(form).get("label")); setBusy(true);
        try { const response = await api("/records", {method: "POST", body: JSON.stringify({label})}); if (!response.ok) throw new Error("Save failed"); form.reset(); await load(); setMessage("Record saved"); }
        catch { setMessage("Save could not be confirmed. Check the connection before retrying."); } finally { setBusy(false); }
      }}><label>Record label<input name="label" required maxLength={160}/></label><button disabled={busy}>Save record</button></form>
      <ul>{items.map(item => <li key={item.id} data-record-id={item.id}>{item.label}</li>)}</ul>
    </section>}
    <footer>Development and CI only · No public registration · Contact an administrator for account recovery.</footer>
  </main>;
}

createRoot(document.getElementById("root")!).render(<App/>);
