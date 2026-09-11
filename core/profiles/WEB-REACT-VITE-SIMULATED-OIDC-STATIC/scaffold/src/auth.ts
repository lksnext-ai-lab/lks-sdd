export type AuthEnvironment = {
  VITE_APP_ENV?: string;
  VITE_SIMULATED_OIDC_ISSUER?: string;
  VITE_OIDC_AUDIENCE?: string;
  VITE_SIMULATED_SUBJECT?: string;
  VITE_SIMULATED_OBJECT_ID?: string;
  VITE_SIMULATED_USERNAME?: string;
};

export type ResolvedAuthConfiguration = {
  environment: string;
  issuer: string;
  audience: string;
  subject: string;
  objectId: string;
  username: string;
  authorizationEndpoint: string;
  tokenEndpoint: string;
};

export type AuthController = {
  username(): string | null;
  signIn(): Promise<void>;
  signOut(): Promise<void>;
  acquireApiToken(): Promise<string>;
};

type Session = { username: string; accessToken: string };
type Dependencies = { fetcher?: typeof fetch; storage?: Storage; webCrypto?: Crypto };

const SESSION_KEY = "lks-sdd.simulated-oidc.session";
const SIMULATED_OIDC_PATH = "/__test__/oidc";
const ALLOWED_NON_PRODUCTION_ENVIRONMENTS = new Set([
  "development",
  "test",
  "ci",
  "integration",
  "verification",
  "acceptance",
  "preproduction",
  "acceptance-preproduction",
]);

function required(value: string | undefined, label: string): string {
  if (!value?.trim()) throw new Error(`Missing ${label}`);
  return value.trim();
}

export function authConfiguration(environment: AuthEnvironment): ResolvedAuthConfiguration {
  const appEnvironment = required(environment.VITE_APP_ENV, "explicit non-production environment").toLowerCase();
  if (!ALLOWED_NON_PRODUCTION_ENVIRONMENTS.has(appEnvironment)) {
    throw new Error("Simulated identity is disabled outside explicit non-production environments");
  }
  const rawIssuer = required(environment.VITE_SIMULATED_OIDC_ISSUER, "simulated OIDC issuer");
  const pathStart = rawIssuer.indexOf("/", rawIssuer.indexOf("://") + 3);
  const rawPath = pathStart >= 0 ? rawIssuer.slice(pathStart) : "";
  if (
    [...rawIssuer].some((character) => {
      const codePoint = character.charCodeAt(0);
      return codePoint <= 32 || codePoint === 127;
    })
    || rawIssuer.includes("\\")
    || rawIssuer.includes("?")
    || rawIssuer.includes("#")
    || rawIssuer.includes("%")
    || ![SIMULATED_OIDC_PATH, `${SIMULATED_OIDC_PATH}/`].includes(rawPath)
  ) {
    throw new Error("Simulated OIDC issuer must use the dedicated test path");
  }
  const parsed = new URL(rawIssuer);
  const hostname = parsed.hostname.toLowerCase();
  const loopback = hostname === "localhost" || hostname === "[::1]" || /^127(?:\.\d{1,3}){3}$/.test(hostname);
  if (
    !["http:", "https:"].includes(parsed.protocol)
    || parsed.username !== ""
    || parsed.password !== ""
    || ![SIMULATED_OIDC_PATH, `${SIMULATED_OIDC_PATH}/`].includes(parsed.pathname)
    || (parsed.protocol === "http:" && !loopback)
  ) {
    throw new Error("Simulated OIDC issuer must be a dedicated loopback HTTP or HTTPS test endpoint");
  }
  const issuer = `${parsed.protocol}//${parsed.host}${SIMULATED_OIDC_PATH}`;
  return {
    environment: appEnvironment,
    issuer,
    audience: required(environment.VITE_OIDC_AUDIENCE ?? "api://lks-sdd-reference-api", "OIDC audience"),
    subject: required(environment.VITE_SIMULATED_SUBJECT ?? "synthetic-user", "synthetic subject"),
    objectId: required(environment.VITE_SIMULATED_OBJECT_ID ?? "synthetic-object-001", "synthetic object ID"),
    username: required(environment.VITE_SIMULATED_USERNAME ?? "synthetic.user@example.invalid", "synthetic username"),
    authorizationEndpoint: `${issuer}/authorize`,
    tokenEndpoint: `${issuer}/token`,
  };
}

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  bytes.forEach((value) => { binary += String.fromCharCode(value); });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export async function pkceChallenge(verifier: string, webCrypto: Crypto = crypto): Promise<string> {
  const digest = await webCrypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
  return base64Url(new Uint8Array(digest));
}

function newVerifier(webCrypto: Crypto): string {
  const bytes = new Uint8Array(48);
  webCrypto.getRandomValues(bytes);
  return base64Url(bytes);
}

async function postJson(fetcher: typeof fetch, url: string, body: object): Promise<Record<string, unknown>> {
  const response = await fetcher(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`Simulated OIDC request failed: ${response.status}`);
  return await response.json() as Record<string, unknown>;
}

export async function bootstrapAuthentication(
  environment: AuthEnvironment,
  dependencies: Dependencies = {},
): Promise<AuthController> {
  const configuration = authConfiguration(environment);
  const fetcher = dependencies.fetcher ?? fetch;
  const storage = dependencies.storage ?? sessionStorage;
  const webCrypto = dependencies.webCrypto ?? crypto;

  function session(): Session | null {
    const value = storage.getItem(SESSION_KEY);
    if (!value) return null;
    const parsed = JSON.parse(value) as Partial<Session>;
    return typeof parsed.username === "string" && typeof parsed.accessToken === "string"
      ? parsed as Session
      : null;
  }

  return {
    username: () => session()?.username ?? null,
    signIn: async () => {
      const verifier = newVerifier(webCrypto);
      const challenge = await pkceChallenge(verifier, webCrypto);
      const authorization = await postJson(fetcher, configuration.authorizationEndpoint, {
        subject: configuration.subject,
        object_id: configuration.objectId,
        username: configuration.username,
        code_challenge: challenge,
        code_challenge_method: "S256",
        scopes: ["api.read"],
        roles: [],
      });
      const token = await postJson(fetcher, configuration.tokenEndpoint, {
        code: required(authorization.code as string | undefined, "authorization code"),
        code_verifier: verifier,
      });
      storage.setItem(SESSION_KEY, JSON.stringify({
        username: configuration.username,
        accessToken: required(token.access_token as string | undefined, "access token"),
      } satisfies Session));
    },
    signOut: async () => { storage.removeItem(SESSION_KEY); },
    acquireApiToken: async () => {
      const current = session();
      if (!current) throw new Error("No active synthetic session");
      return current.accessToken;
    },
  };
}
