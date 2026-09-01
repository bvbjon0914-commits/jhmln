import { useEffect, useState } from "react";
import { Loader2, ShieldCheck, ShieldOff } from "lucide-react";
import { api } from "../../services/api";
import { useToast, errorMessage } from "../common/Toast";
import { useAuth } from "../auth/AuthContext";

export function SettingsAdmin() {
  const { showToast } = useToast();
  const { refresh } = useAuth();
  const [loginRequired, setLoginRequired] = useState<boolean | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .authStatus()
      .then((s) => setLoginRequired(s.login_required))
      .catch((error) => showToast("error", errorMessage(error, "Status konnte nicht geladen werden.")));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggle = async () => {
    if (loginRequired === null) return;
    setSaving(true);
    try {
      const result = await api.setLoginRequired(!loginRequired);
      setLoginRequired(result.login_required);
      showToast(
        "success",
        result.login_required ? "Login-Pflicht aktiviert." : "Login-Pflicht deaktiviert – die Seite ist jetzt für alle offen."
      );
      refresh();
    } catch (error) {
      showToast("error", errorMessage(error, "Konnte nicht geändert werden."));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-lg space-y-4">
      <div className="rounded-lg border border-line bg-surface p-5 shadow-sm">
        <div className="flex items-start gap-3">
          <div
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md ${
              loginRequired ? "bg-status-matchedBg text-status-matched" : "bg-status-neutralBg text-status-neutral"
            }`}
          >
            {loginRequired ? <ShieldCheck size={18} /> : <ShieldOff size={18} />}
          </div>
          <div className="flex-1">
            <div className="text-sm font-medium text-ink">Login-Pflicht</div>
            <p className="mt-0.5 text-xs text-ink-soft">
              Wenn deaktiviert, ist die Seite für jeden im Netzwerk ohne Passwort erreichbar. Nur
              der Haupt-Account kann das hier ändern.
            </p>
          </div>
        </div>
        <button
          onClick={toggle}
          disabled={loginRequired === null || saving}
          className={`mt-4 inline-flex items-center gap-2 rounded px-4 py-2.5 text-sm font-medium shadow-sm transition-all disabled:opacity-40 ${
            loginRequired
              ? "border border-line bg-surface text-ink-soft hover:border-status-conflict/40 hover:text-status-conflict"
              : "bg-brand text-white hover:bg-brand-dark hover:shadow-md"
          }`}
        >
          {saving && <Loader2 size={14} className="animate-spin" />}
          {loginRequired ? "Login-Pflicht deaktivieren" : "Login-Pflicht aktivieren"}
        </button>
      </div>
    </div>
  );
}
