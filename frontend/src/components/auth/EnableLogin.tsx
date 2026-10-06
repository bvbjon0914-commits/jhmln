import { useState } from "react";
import { ChevronDown, ChevronRight, Loader2, Lock, Mail } from "lucide-react";
import { api } from "../../services/api";
import { useToast, errorMessage } from "../common/Toast";
import { Button } from "../common/Button";

/**
 * Wird gezeigt, solange der Login-Zwang global ausgeschaltet ist: ohne
 * Login-Screen und ohne Haupt-Session gäbe es sonst keinen Weg, ihn aus der
 * Oberfläche wieder einzuschalten. Autorisierung per Haupt-Passwort (oder
 * Haupt-Account mit E-Mail + Passwort).
 */
export function EnableLogin({ onEnabled }: { onEnabled: () => void }) {
  const { showToast } = useToast();
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [showEmail, setShowEmail] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password || loading) return;
    setLoading(true);
    setError(null);
    try {
      await api.enableLoginRequired(password, email.trim() || undefined);
      showToast("success", "Login-Pflicht ist wieder aktiv.");
      onEnabled();
    } catch (err) {
      setError(errorMessage(err, "Aktivierung fehlgeschlagen."));
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full rounded-lg border border-line bg-surface py-2.5 pl-9 pr-4 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand";

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-6">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-lg border border-line bg-surface p-6 shadow-sm"
      >
        <h1 className="text-lg font-semibold text-ink">Login-Pflicht aktivieren</h1>
        <p className="mb-5 mt-2 text-sm text-ink-soft">
          Der Login ist derzeit deaktiviert, alle können die Anwendung ohne Anmeldung nutzen. Mit dem
          Haupt-Passwort schaltest du die Login-Pflicht wieder ein.
        </p>

        <label htmlFor="enable-login-password" className="mb-1.5 block text-xs font-medium text-ink-soft">
          Haupt-Passwort
        </label>
        <div className="relative">
          <Lock size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
          <input
            id="enable-login-password"
            type="password"
            autoFocus
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClass}
          />
        </div>

        <button
          type="button"
          onClick={() => setShowEmail((v) => !v)}
          aria-expanded={showEmail}
          className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-brand hover:text-brand-dark"
        >
          {showEmail ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
          Mit Haupt-Account statt Haupt-Passwort
        </button>

        {showEmail && (
          <div className="mt-2">
            <label htmlFor="enable-login-email" className="mb-1.5 block text-xs font-medium text-ink-soft">
              E-Mail (nur bei Haupt-Account statt Haupt-Passwort)
            </label>
            <div className="relative">
              <Mail size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
              <input
                id="enable-login-email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputClass}
              />
            </div>
            <p className="mt-1.5 text-xs text-ink-faint">
              Bei Angabe einer E-Mail wird das Feld oben als Passwort dieses Accounts geprüft.
            </p>
          </div>
        )}

        {error && <p className="mt-3 text-xs text-status-conflict">{error}</p>}

        <Button type="submit" disabled={loading || !password} className="mt-4 w-full">
          {loading && <Loader2 size={14} className="animate-spin" />}
          Login-Pflicht aktivieren
        </Button>
      </form>
    </div>
  );
}
