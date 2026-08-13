import { FormEvent, useState } from "react";
import { setStoredAuth } from "../api/client";
import { isOidcConfigured, loginWithSso } from "../auth/oidc";

type Props = {
  onLoggedIn: () => void;
};

const SOCIAL_DEMO_MSG =
  "Auth required — this is demo only. Google/GitHub OAuth apps are not configured. Use Sign In (Basic) or Keycloak SSO (sso.user / password). See README → Authentication to enable social login.";

export default function Login({ onLoggedIn }: Props) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("password");
  const [error, setError] = useState<string | null>(null);
  const [socialNote, setSocialNote] = useState<string | null>(null);
  const ssoEnabled = isOidcConfigured();

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSocialNote(null);
    setStoredAuth(username, password);
    try {
      const token = btoa(`${username}:${password}`);
      const res = await fetch("/api/v1/zones", {
        headers: { Authorization: `Basic ${token}` },
      });
      if (!res.ok) {
        throw new Error("Invalid username or password");
      }
      onLoggedIn();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function onSocialDemo() {
    setError(null);
    setSocialNote(SOCIAL_DEMO_MSG);
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div className="login-head">
          <div className="brand-logo">RT</div>
          <h1>Retail Taxonomy Console</h1>
          <p>Sign in with demo credentials, or use SSO.</p>
        </div>
        <form className="login-body" onSubmit={onSubmit}>
          <label className="field">
            <span>Username</span>
            <input
              name="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {error ? (
            <p className="login-error" role="alert">
              {error}
            </p>
          ) : null}
          <button type="submit" className="btn btn-primary">
            Sign In
          </button>
          {ssoEnabled ? (
            <>
              <div className="login-divider">or OAuth2 / SSO</div>
              <div className="login-oauth">
                <button
                  type="button"
                  className="btn btn-outline login-sso"
                  onClick={() => {
                    setSocialNote(null);
                    void loginWithSso();
                  }}
                >
                  Sign in with Keycloak (SSO)
                </button>
                <button
                  type="button"
                  className="btn btn-outline login-sso"
                  onClick={onSocialDemo}
                >
                  Sign in with Google
                </button>
                <button
                  type="button"
                  className="btn btn-outline login-sso"
                  onClick={onSocialDemo}
                >
                  Sign in with GitHub
                </button>
              </div>
              {socialNote ? (
                <p className="login-oauth-demo" role="status">
                  {socialNote}
                </p>
              ) : (
                <p className="login-oauth-note">
                  Keycloak SSO works locally (<code>sso.user</code> /{" "}
                  <code>password</code>). Google/GitHub show a demo notice until
                  OAuth apps are configured (README → Authentication).
                </p>
              )}
            </>
          ) : null}
        </form>
      </div>
    </div>
  );
}
