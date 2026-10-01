import { useState } from "react";
import { Loader2, Save, Trash2 } from "lucide-react";
import { api } from "../../services/api";
import { useToast, errorMessage } from "../common/Toast";
import { Button } from "../common/Button";
import type { User, UserSelfUpdateInput } from "../../types/user";

function toForm(u: User): UserSelfUpdateInput {
  return {
    email: u.email,
    full_name: u.full_name,
    phone: u.phone,
    function: u.function,
    street: u.street,
    house_number: u.house_number,
    postal_code: u.postal_code,
    city: u.city,
  };
}

interface MyAccountProps {
  user: User;
  onUpdated: () => void;
  onDeleted: () => void;
}

export function MyAccount({ user, onUpdated, onDeleted }: MyAccountProps) {
  const { showToast } = useToast();
  const [form, setForm] = useState<UserSelfUpdateInput>(toForm(user));
  const [password, setPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const patch: UserSelfUpdateInput = { ...form };
      if (password) patch.password = password;
      await api.updateMyAccount(patch);
      showToast("success", "Account aktualisiert.");
      setPassword("");
      onUpdated();
    } catch (error) {
      showToast("error", errorMessage(error, "Account konnte nicht aktualisiert werden."));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Deinen Account wirklich unwiderruflich löschen?")) return;
    setDeleting(true);
    try {
      await api.deleteMyAccount();
      onDeleted();
    } catch (error) {
      showToast("error", errorMessage(error, "Account konnte nicht gelöscht werden."));
      setDeleting(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-6 py-8">
      <div>
        <h2 className="font-display text-lg font-semibold text-ink">Mein Account</h2>
        <p className="mt-1 text-sm text-ink-faint">
          Diese Angaben erscheinen automatisch im Kopf- und Signaturbereich generierter Anschreiben.
        </p>
      </div>

      <div className="rounded-lg border border-line bg-surface p-5 shadow-sm">
        <div className="grid grid-cols-2 gap-3">
          <input
            value={form.full_name ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
            placeholder="Name"
            className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
          />
          <input
            type="email"
            value={form.email ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            placeholder="E-Mail"
            className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
          />
          <input
            value={form.phone ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
            placeholder="Telefon"
            className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
          />
          <input
            value={form.function ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, function: e.target.value }))}
            placeholder="Funktion"
            className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
          />
          <input
            value={form.street ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, street: e.target.value }))}
            placeholder="Straße"
            className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
          />
          <input
            value={form.house_number ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, house_number: e.target.value }))}
            placeholder="Hausnummer"
            className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
          />
          <input
            value={form.postal_code ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, postal_code: e.target.value }))}
            placeholder="PLZ"
            className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
          />
          <input
            value={form.city ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))}
            placeholder="Ort"
            className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Neues Passwort (leer = unverändert)"
            className="col-span-2 rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
          />
        </div>
        <div className="mt-4 flex justify-end">
          <Button onClick={handleSave} disabled={saving}>
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            Speichern
          </Button>
        </div>
      </div>

      <div className="rounded-lg border border-status-conflict/30 bg-status-conflictBg/30 p-5">
        <h3 className="text-sm font-semibold text-status-conflict">Account löschen</h3>
        <p className="mt-1 text-xs text-ink-soft">
          Löscht deinen Account unwiderruflich. Diese Aktion kann nicht rückgängig gemacht werden.
        </p>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="mt-3 inline-flex items-center gap-1.5 rounded border border-status-conflict/40 px-3 py-1.5 text-xs font-medium text-status-conflict hover:bg-status-conflictBg disabled:opacity-50"
        >
          {deleting ? <Loader2 size={12} className="animate-spin" /> : <Trash2 size={12} />}
          Account unwiderruflich löschen
        </button>
      </div>
    </div>
  );
}
