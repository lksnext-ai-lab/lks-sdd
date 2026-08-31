import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import { isAuthenticationConfigured } from "./auth";
import "./index.css";

type Item = { id: string; label: string };
type TokenProvider = () => Promise<string>;

export function App({ tokenProvider }: { tokenProvider?: TokenProvider }) {
  const [items, setItems] = useState<Item[]>([]);
  const [label, setLabel] = useState("");
  const [status, setStatus] = useState(tokenProvider ? "Cargando datos reales" : "Scaffold listo");

  const request = useCallback(async (path: string, init?: RequestInit) => {
    if (!tokenProvider) throw new Error("OIDC is not active");
    const token = await tokenProvider();
    const response = await fetch(path, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...(init?.headers ?? {}),
      },
    });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response;
  }, [tokenProvider]);

  const loadItems = useCallback(async () => {
    if (!tokenProvider) return;
    const response = await request("/api/v1/items");
    setItems(await response.json() as Item[]);
    setStatus("API y PostgreSQL conectados");
  }, [request, tokenProvider]);

  useEffect(() => { void loadItems(); }, [loadItems]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!label.trim()) return;
    await request("/api/v1/items", {
      method: "POST",
      headers: { "X-Correlation-ID": "fullstack-gate-correlation" },
      body: JSON.stringify({ label: label.trim() }),
    });
    setLabel("");
    await loadItems();
  }

  return (
    <main>
      <p className="eyebrow">LKS-SDD · Codex · perfil H0</p>
      <h1>Aplicación de referencia preparada para un incremento vertical</h1>
      <p>
        Este fixture de certificación separa los checks de componente del recorrido
        compuesto React, FastAPI, PostgreSQL e identidad controlada.
      </p>
      <dl>
        <div>
          <dt>Identidad</dt>
          <dd>{isAuthenticationConfigured ? "OIDC configurado" : "OIDC pendiente de entorno"}</dd>
        </div>
        <div>
          <dt>Estado</dt>
          <dd>{status}</dd>
        </div>
      </dl>
      {tokenProvider ? (
        <section aria-labelledby="items-heading">
          <h2 id="items-heading">Elementos persistidos</h2>
          <form onSubmit={submit}>
            <label htmlFor="item-label">Etiqueta</label>
            <input id="item-label" value={label} onChange={(event) => setLabel(event.target.value)} />
            <button type="submit">Guardar elemento</button>
          </form>
          <ul>{items.map((item) => <li key={item.id}>{item.label}</li>)}</ul>
        </section>
      ) : null}
    </main>
  );
}
