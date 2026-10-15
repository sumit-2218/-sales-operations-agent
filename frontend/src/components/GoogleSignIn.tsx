import { useEffect, useRef, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { apiErrorMessage } from "../utils/errors";

declare global { interface Window { google?: any; } }

export default function GoogleSignIn() {
  const host = useRef<HTMLDivElement>(null);
  const { signInGoogle } = useAuth();
  const [error, setError] = useState("");
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;
  useEffect(() => {
    if (!clientId || !host.current) return;
    let cancelled = false;
    const render = () => {
      if (cancelled || !host.current || !window.google?.accounts?.id) return;
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response: { credential: string }) => {
          setError("");
          try { await signInGoogle(response.credential); window.location.assign("/"); }
          catch (e) { setError(apiErrorMessage(e)); }
        },
      });
      host.current.innerHTML = "";
      window.google.accounts.id.renderButton(host.current, { theme: "outline", size: "large", shape: "rectangular", text: "continue_with", width: 320 });
    };
    if (window.google?.accounts?.id) render();
    else {
      const existing = document.querySelector<HTMLScriptElement>('script[data-google-identity="true"]');
      const script = existing ?? document.createElement("script");
      if (!existing) { script.src = "https://accounts.google.com/gsi/client"; script.async = true; script.defer = true; script.dataset.googleIdentity = "true"; document.head.appendChild(script); }
      script.addEventListener("load", render);
      return () => { cancelled = true; script.removeEventListener("load", render); };
    }
    return () => { cancelled = true; };
  }, [clientId]);
  if (!clientId) return <p className="text-xs text-slate-500">Google sign-in is not configured yet. Add VITE_GOOGLE_CLIENT_ID to frontend/.env.</p>;
  return <div className="space-y-2"><div className="flex justify-center" ref={host} /><p role="alert" className="text-sm text-rose-700">{error}</p></div>;
}
