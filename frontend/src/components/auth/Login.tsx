import { useState } from "react";
import { Loader2, Lock } from "lucide-react";
import { api } from "../../services/api";
import { errorMessage } from "../common/Toast";

export function Login({ onSuccess }: { onSuccess: () => void }) {
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) return;
    setLoading(true);
    setError(null);
    try {
      await api.login(password);
      onSuccess();
    } catch (err) {
      setError(errorMessage(err, "Anmeldung fehlgeschlagen."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-6">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-lg border border-line bg-surface p-6 shadow-sm"
      >
        <div className="mb-6 flex flex-col items-center text-center">
          <img src="/brand/logo-full.png" alt="Civeloq" className="h-24 w-auto" />
          <p className="mt-3 text-xs text-ink-faint">Bitte anmelden, um fortzufahren.</p>
        </div>

        <label className="mb-1.5 block text-xs font-medium text-ink-soft">Passwort</label>
        <div className="relative">
          <Lock size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
          <input
            type="password"
            autoFocus
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-line bg-surface py-2.5 pl-9 pr-4 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>

        {error && <p className="mt-2 text-xs text-status-conflict">{error}</p>}

        <button
          type="submit"
          disabled={loading || !password}
          className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded bg-brand px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-brand-dark hover:shadow-md disabled:opacity-40 disabled:shadow-none"
        >
          {loading && <Loader2 size={14} className="animate-spin" />}
          Anmelden
        </button>
      </form>
    </div>
  );
}
