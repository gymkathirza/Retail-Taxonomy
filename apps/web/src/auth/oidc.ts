// OIDC (OAuth2 Authorization Code + PKCE) helper — Phase 2.
// Active when VITE_OIDC_AUTHORITY + VITE_OIDC_CLIENT_ID are set (Compose defaults
// point at local Keycloak). Social buttons use Keycloak identity-provider hints
// (kc_idp_hint); Google/GitHub only succeed after real OAuth app credentials are
// configured in Keycloak (see README).
import { User, UserManager, WebStorageStateStore } from "oidc-client-ts";
import { setBearerToken, clearBearerToken } from "../api/client";

const env = import.meta.env as unknown as Record<string, string | undefined>;
const authority = env.VITE_OIDC_AUTHORITY;
const clientId = env.VITE_OIDC_CLIENT_ID;
const scope = env.VITE_OIDC_SCOPE || "openid";
const redirectUri =
  env.VITE_OIDC_REDIRECT_URI || `${window.location.origin}/callback`;

export type SocialIdp = "google" | "github";

export function isOidcConfigured(): boolean {
  return Boolean(authority && clientId);
}

let manager: UserManager | null = null;

function getManager(): UserManager {
  if (!manager) {
    manager = new UserManager({
      authority: authority as string,
      client_id: clientId as string,
      redirect_uri: redirectUri,
      post_logout_redirect_uri: window.location.origin,
      response_type: "code",
      scope,
      userStore: new WebStorageStateStore({ store: window.sessionStorage }),
      automaticSilentRenew: true,
    });
  }
  return manager;
}

function applyUser(user: User | null): User | null {
  if (user && !user.expired && user.access_token) {
    setBearerToken(user.access_token);
    return user;
  }
  clearBearerToken();
  return null;
}

// Load any existing SSO session (e.g. after a page refresh) and prime the
// Bearer token used by the API client. Returns the active user, if any.
export async function initOidc(): Promise<User | null> {
  if (!isOidcConfigured()) return null;
  try {
    const user = await getManager().getUser();
    return applyUser(user);
  } catch {
    return null;
  }
}

/** Start OIDC login. Pass google|github to skip Keycloak's picker (kc_idp_hint). */
export async function loginWithSso(idp?: SocialIdp): Promise<void> {
  const args = idp
    ? { extraQueryParams: { kc_idp_hint: idp } }
    : undefined;
  await getManager().signinRedirect(args);
}

export async function completeSsoLogin(): Promise<void> {
  const user = await getManager().signinRedirectCallback();
  applyUser(user);
}

export async function logoutSso(): Promise<void> {
  clearBearerToken();
  if (!isOidcConfigured() || !manager) return;
  try {
    await manager.removeUser();
  } catch {
    /* ignore */
  }
}

export function hasSsoSession(): boolean {
  // Synchronous best-effort check for initial render; initOidc() confirms.
  if (!isOidcConfigured()) return false;
  const key = `oidc.user:${authority}:${clientId}`;
  return Boolean(window.sessionStorage.getItem(key));
}
