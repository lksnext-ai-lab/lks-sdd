import {
  BrowserCacheLocation,
  PublicClientApplication,
  type AccountInfo,
  type Configuration,
} from "@azure/msal-browser";

export type AuthEnvironment = {
  VITE_ENTRA_TENANT_ID?: string;
  VITE_ENTRA_CLIENT_ID?: string;
  VITE_ENTRA_REDIRECT_URI?: string;
  VITE_ENTRA_POST_LOGOUT_URI?: string;
  VITE_ENTRA_API_SCOPE?: string;
};

export type ResolvedAuthConfiguration = {
  tenantId: string;
  loginScopes: string[];
  msal: Configuration;
};

export type AuthController = {
  username(): string | null;
  signIn(): Promise<void>;
  signOut(): Promise<void>;
  acquireApiToken(): Promise<string>;
};

const TENANT_ID_PATTERN =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

function required(value: string | undefined, label: string): string {
  if (!value?.trim()) throw new Error(`Missing ${label}`);
  return value.trim();
}

export function authConfiguration(
  environment: AuthEnvironment,
): ResolvedAuthConfiguration {
  const tenantId = required(environment.VITE_ENTRA_TENANT_ID, "tenant ID");
  if (!TENANT_ID_PATTERN.test(tenantId)) {
    throw new Error(
      "Microsoft Entra authority must use a canonical tenant-specific ID",
    );
  }
  const clientId = required(environment.VITE_ENTRA_CLIENT_ID, "SPA client ID");
  const redirectUri = required(
    environment.VITE_ENTRA_REDIRECT_URI,
    "redirect URI",
  );
  const postLogoutRedirectUri = required(
    environment.VITE_ENTRA_POST_LOGOUT_URI,
    "post-logout URI",
  );
  const apiScope = required(
    environment.VITE_ENTRA_API_SCOPE,
    "delegated API scope",
  );
  return {
    tenantId,
    loginScopes: [apiScope],
    msal: {
      auth: {
        clientId,
        authority: `https://login.microsoftonline.com/${tenantId}`,
        redirectUri,
        postLogoutRedirectUri,
      },
      cache: {
        cacheLocation: BrowserCacheLocation.SessionStorage,
      },
    },
  };
}

export async function bootstrapAuthentication(
  environment: AuthEnvironment,
): Promise<AuthController> {
  const configuration = authConfiguration(environment);
  const client = new PublicClientApplication(configuration.msal);
  await client.initialize();
  const redirect = await client.handleRedirectPromise();
  if (redirect?.account) client.setActiveAccount(redirect.account);
  if (!client.getActiveAccount())
    client.setActiveAccount(client.getAllAccounts()[0] ?? null);

  function account(): AccountInfo | null {
    return client.getActiveAccount();
  }

  return {
    username: () => account()?.username ?? null,
    signIn: async () => {
      await client.loginRedirect({ scopes: configuration.loginScopes });
    },
    signOut: async () => {
      await client.logoutRedirect({ account: account() ?? undefined });
    },
    acquireApiToken: async () => {
      const current = account();
      if (!current) throw new Error("No active Microsoft Entra account");
      const response = await client.acquireTokenSilent({
        account: current,
        scopes: configuration.loginScopes,
      });
      return response.accessToken;
    },
  };
}
