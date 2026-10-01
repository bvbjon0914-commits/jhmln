import { useState } from "react";
import { Loader2, CheckCircle2 } from "lucide-react";
import { api } from "../../services/api";
import { errorMessage } from "../common/Toast";
import type { UserRegisterInput } from "../../types/user";

const EMPTY_FORM: UserRegisterInput = {
  email: "",
  password: "",
  full_name: "",
  phone: "",
  function: "",
  street: "",
  house_number: "",
  postal_code: "",
  city: "",
};

export function Register({ onBack }: { onBack: () => void }) {
  const [form, setForm] = useState<UserRegisterInput>(EMPTY_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ status: string; message: string } | null>(null);

  const field = (key: keyof UserRegisterInput) => ({
    value: form[key],
    onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value })),
  });

  const formComplete =
    form.email && form.password && form.full_name && form.phone &&
    form.function && form.street && form.house_number && form.postal_code && form.city;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formComplete) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.register(form);
      setResult(res);
    } catch (err) {
      setError(errorMessage(err, "Registrierung fehlgeschlagen."));
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper px-6">
        <div className="w-full max-w-sm rounded-lg border border-line bg-surface p-6 text-center shadow-sm">
          <CheckCircle2 size={32} className="mx-auto text-status-matched" />
          <p className="mt-3 text-sm text-ink">
            {result.message || "Dein Account wurde angelegt und wartet auf Freigabe durch einen Administrator."}
          </p>
          <button
            onClick={onBack}
            className="mt-4 text-xs font-medium text-brand hover:text-brand-dark"
          >
            Zurück zum Login
          </button>
        </div>
      </div>
    );
  }

  const inputClass =
    "w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand";

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-6 py-10">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md rounded-lg border border-line bg-surface p-6 shadow-sm"
      >
        <div className="mb-5 flex flex-col items-center text-center">
          <img src="/brand/logo-full.png" alt="Civeloq" className="h-20 w-auto" />
          <p className="mt-3 text-xs text-ink-faint">Account beantragen</p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <input {...field("full_name")} placeholder="Name *" className={`col-span-2 ${inputClass}`} />
          <input type="email" {...field("email")} placeholder="E-Mail *" className={`col-span-2 ${inputClass}`} />
          <input {...field("phone")} placeholder="Telefon *" className={inputClass} />
          <input {...field("function")} placeholder="Funktion *" className={inputClass} />
          <input {...field("street")} placeholder="Straße *" className={inputClass} />
          <input {...field("house_number")} placeholder="Hausnummer *" className={inputClass} />
          <input {...field("postal_code")} placeholder="PLZ *" className={inputClass} />
          <input {...field("city")} placeholder="Ort *" className={inputClass} />
          <input
            type="password"
            {...field("password")}
            placeholder="Passwort *"
            className={`col-span-2 ${inputClass}`}
          />
        </div>

        {error && <p className="mt-3 text-xs text-status-conflict">{error}</p>}

        <button
          type="submit"
          disabled={loading || !formComplete}
          className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded bg-brand px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-brand-dark hover:shadow-md disabled:opacity-40 disabled:shadow-none"
        >
          {loading && <Loader2 size={14} className="animate-spin" />}
          Account beantragen
        </button>

        <button
          type="button"
          onClick={onBack}
          className="mt-3 w-full text-center text-xs font-medium text-brand hover:text-brand-dark"
        >
          Zurück zum Login
        </button>
      </form>
    </div>
  );
}
