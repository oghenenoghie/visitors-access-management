"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { QRCodeSVG } from "qrcode.react";

type AuthResult = {
  status?: string;
  challenge_token?: string;
  otpauth_uri?: string;
  secret?: string;
  recovery_codes?: string[];
  detail?: string;
  non_field_errors?: string[];
};

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [challenge, setChallenge] = useState<string | null>(null);
  const [setup, setSetup] = useState(false);
  const [setupUri, setSetupUri] = useState<string | null>(null);
  const [setupSecret, setSetupSecret] = useState<string | null>(null);
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [setupComplete, setSetupComplete] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function post(path: string, body: unknown): Promise<AuthResult> {
    const response = await fetch("/api/bff/" + path, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({})) as AuthResult;
    if (!response.ok) throw new Error(data.detail || data.non_field_errors?.[0] || "Unable to sign in.");
    return data;
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = challenge
        ? await post(setup ? "auth/2fa/confirm/" : "auth/2fa/verify/", { challenge_token: challenge, code })
        : await post("auth/login/", { email, password });

      if (data.status === "two_factor_required" || data.status === "two_factor_setup_required") {
        setChallenge(data.challenge_token || null);
        setSetup(data.status === "two_factor_setup_required");
        if (data.status === "two_factor_setup_required") {
          const enrolment = await post("auth/2fa/setup/", { challenge_token: data.challenge_token });
          setSetupUri(enrolment.otpauth_uri || null);
          setSetupSecret(enrolment.secret || null);
        }
        return;
      }
      if (data.status !== "authenticated") throw new Error("Unexpected authentication response.");
      if (setup) {
        setRecoveryCodes(data.recovery_codes || []);
        setSetupComplete(true);
        return;
      }
      router.replace("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  if (setupComplete) {
    return <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "white", padding: 24 }}>
      <section style={{ width: "100%", maxWidth: 520 }}>
        <p className="eyebrow">TWO-FACTOR SECURITY ENABLED</p>
        <h1 style={{ fontSize: 30, letterSpacing: "-.04em" }}>Save your recovery codes</h1>
        <p className="page-subtitle">These codes are shown only once. Store them somewhere secure and separate from your authenticator device. Each code can be used once if you lose access to your authenticator.</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, padding: 18, margin: "22px 0", background: "#f4f6f8", borderRadius: 12 }}>
          {recoveryCodes.map(code => <code key={code} style={{ fontSize: 15, fontWeight: 700, letterSpacing: ".08em" }}>{code}</code>)}
        </div>
        <button type="button" className="primary-btn" style={{ width: "100%", padding: 13 }} onClick={() => void navigator.clipboard.writeText(recoveryCodes.join("\\n"))}>Copy recovery codes</button>
        <button type="button" className="primary-btn" style={{ width: "100%", padding: 13, marginTop: 10 }} onClick={() => router.replace("/")}>I have saved my codes — continue</button>
      </section>
    </main>;
  }

  return <main style={{ minHeight: "100vh", display: "grid", gridTemplateColumns: "1fr 1fr", background: "white" }}>
    <section style={{ background: "var(--navy)", color: "white", padding: "8vw", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
      <div className="brand"><span className="brand-mark">EA</span><span>Estate Access</span></div>
      <div>
        <p style={{ color: "#9db8d5", fontSize: 11, letterSpacing: ".15em", fontWeight: 700 }}>ESTATE OPERATIONS</p>
        <h1 style={{ fontSize: 42, lineHeight: 1.12, letterSpacing: "-.04em", maxWidth: 460 }}>A clearer view of every gate.</h1>
        <p style={{ color: "#c2d0df", lineHeight: 1.7, maxWidth: 400 }}>Manage residents, monitor visitor movements and maintain a trusted record of estate access.</p>
      </div>
      <small style={{ color: "#8ea2bb" }}>Secure estate management workspace</small>
    </section>
    <section style={{ display: "grid", placeItems: "center", padding: 28 }}>
      <form onSubmit={submit} style={{ width: "100%", maxWidth: 390 }}>
        <p className="eyebrow">ADMINISTRATOR PORTAL</p>
        <h2 style={{ fontSize: 27, letterSpacing: "-.04em", margin: "8px 0" }}>{challenge ? "Authenticator verification" : "Welcome back"}</h2>
        <p className="page-subtitle" style={{ marginBottom: 28 }}>{challenge ? "Enter the current code from your authenticator app." : "Sign in with your authorised estate account."}</p>
        {!challenge ? <>
          <label className="eyebrow">Email address</label>
          <input className="input" style={{ margin: "8px 0 18px" }} type="email" required value={email} onChange={e => setEmail(e.target.value)} autoComplete="username" />
          <label className="eyebrow">Password</label>
          <input className="input" style={{ margin: "8px 0 18px" }} type="password" required value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" />
        </> : <>
          <label className="eyebrow">Authenticator code</label>
          <input className="input" style={{ margin: "8px 0 16px", letterSpacing: ".2em" }} inputMode="numeric" maxLength={32} required value={code} onChange={e => setCode(e.target.value)} autoComplete="one-time-code" />
          {setup && setupUri && setupSecret && <div style={{ margin: "8px 0 18px", padding: 16, border: "1px solid #e2e8f0", borderRadius: 12 }}>
            <p className="eyebrow" style={{ marginBottom: 12 }}>SCAN WITH YOUR AUTHENTICATOR APP</p>
            <div style={{ display: "grid", placeItems: "center", padding: 12, background: "white" }}>
              <QRCodeSVG value={setupUri} size={196} level="M" includeMargin aria-label="Authenticator enrollment QR code" />
            </div>
            <p className="page-subtitle" style={{ marginTop: 12 }}>Or enter this setup key manually:</p>
            <code style={{ display: "block", padding: 10, background: "#f4f6f8", borderRadius: 8, overflowWrap: "anywhere" }}>{setupSecret}</code>
            <p className="page-subtitle" style={{ marginTop: 10, fontSize: 11 }}>The QR code is generated in this browser. The setup secret is not sent to a third-party QR service.</p>
          </div>}
        </>}
        {error && <p className="error" style={{ marginBottom: 14 }}>{error}</p>}
        <button className="primary-btn" style={{ width: "100%", padding: 13 }} disabled={busy}>{busy ? "Please wait…" : challenge ? "Verify and continue" : "Sign in securely"}</button>
        {challenge && <button type="button" className="primary-btn" style={{ width: "100%", marginTop: 10, background: "#64748b" }} onClick={() => { setChallenge(null); setCode(""); setSetupUri(null); setSetupSecret(null); }}>Use another account</button>}
        <p className="page-subtitle" style={{ marginTop: 24, fontSize: 11 }}>Two-factor authentication is required for dashboard access.</p>
      </form>
    </section>
  </main>;
}
