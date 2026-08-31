/** Component tests explicitly use HTTP doubles; they certify no composition. */
import { afterEach, expect, it, vi } from "vitest";
import { login, api, logout } from "./auth";

afterEach(() => vi.unstubAllGlobals());
it("keeps credentials out of web storage and adds the in-memory bearer", async () => {
  const setLocal = vi.spyOn(Storage.prototype, "setItem");
  const fetcher = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({access_token: "synthetic-component-token"})))
    .mockResolvedValueOnce(new Response("[]"));
  vi.stubGlobal("fetch", fetcher);
  await login("synthetic", "synthetic-password", "synthetic-org");
  await api("/records");
  expect(setLocal).not.toHaveBeenCalled();
  expect(fetcher.mock.calls[1][1].headers.Authorization).toBe("Bearer synthetic-component-token");
  setLocal.mockRestore();
});
it("does not claim remote revocation while offline", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  expect(await logout()).toBe(false);
});
it("rejects an in-flight API response after logout", async () => {
  let finish: (response: Response) => void = () => {};
  const fetcher = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({access_token: "synthetic-component-token"})))
    .mockImplementationOnce(() => new Promise<Response>(resolve => { finish = resolve; }))
    .mockResolvedValueOnce(new Response(JSON.stringify({revoked: true})));
  vi.stubGlobal("fetch", fetcher);
  await login("synthetic", "synthetic-password", "synthetic-org");
  const pending = api("/records");
  await logout();
  finish(new Response("[]"));
  await expect(pending).rejects.toThrow("Session ended");
});
it("never sends credentials to an external origin", async () => {
  const fetcher = vi.fn(); vi.stubGlobal("fetch", fetcher);
  await expect(api("https://untrusted.invalid/records")).rejects.toThrow("Same-origin");
  await expect(api("//untrusted.invalid/records")).rejects.toThrow("Same-origin");
  await expect(api(String.raw`/\untrusted.invalid/records`)).rejects.toThrow("Same-origin");
  await expect(api("/\t/untrusted.invalid/records")).rejects.toThrow("Same-origin");
  expect(fetcher).not.toHaveBeenCalled();
});
