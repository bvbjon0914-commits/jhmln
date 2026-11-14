import { useEffect, useState } from "react";
import { api } from "../../services/api";
import type { EmailContact, EmailContactInput } from "../../types/authority";
import type { RequestType } from "../../types/matching";
import { useToast, errorMessage } from "../common/Toast";

const empty: EmailContactInput = {
  request_type_id: "", value: "", source_url: "", verified: false, preferred: false, active: true,
};

export function AuthorityEmailContacts({ authorityId }: { authorityId: string }) {
  const { showToast } = useToast();
  const [contacts, setContacts] = useState<EmailContact[]>([]);
  const [types, setTypes] = useState<RequestType[]>([]);
  const [form, setForm] = useState<EmailContactInput>(empty);
  const [editingId, setEditingId] = useState<number>();
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let current = true;
    Promise.all([api.listEmailContacts(authorityId), api.listRequestTypes()])
      .then(([rows, requestTypes]) => { if (current) { setContacts(rows); setTypes(requestTypes); } })
      .catch((error) => { if (current) showToast("error", errorMessage(error, "Fachkontakte konnten nicht geladen werden.")); });
    return () => { current = false; };
  }, [authorityId, showToast]);

  const save = async () => {
    setSaving(true);
    try {
      await api.saveEmailContact(authorityId, form, editingId);
      setContacts(await api.listEmailContacts(authorityId));
      setEditingId(undefined);
      setForm(empty);
      showToast("success", "Fachkontakt gespeichert.");
    } catch (error) {
      showToast("error", errorMessage(error, "Fachkontakt konnte nicht gespeichert werden."));
    } finally { setSaving(false); }
  };

  const input = "rounded border border-line bg-surface px-2 py-1.5 text-sm";
  return (
    <section className="mt-4 border-t border-line pt-3">
      <h4 className="mb-1 text-sm font-medium">E-Mail-Kontakte je Auskunftsart</h4>
      <p className="mb-3 text-xs text-ink-soft">Prüfe auf der amtlichen Leistungsseite, ob die Adresse für diese Auskunft vorgesehen ist. Nur geprüfte Kontakte mit Quellenlink werden für den E-Mail-Versand verwendet.</p>
      <ul className="mb-3 space-y-1 text-xs">
        {contacts.map((c) => (
          <li key={c.id} className="flex flex-wrap items-center gap-2">
            <span>{types.find((t) => t.request_type_id === c.request_type_id)?.name ?? c.request_type_id}: {c.value}</span>
            <span className="text-ink-faint">{c.active ? "Aktiv" : "Inaktiv"} · {c.last_verified_at ? `Zuletzt geprüft: ${new Date(c.last_verified_at).toLocaleDateString("de-DE")}` : "Ungeprüft"}</span>
            <button type="button" className="text-brand hover:underline" onClick={() => {
              setEditingId(c.id);
              setForm({ request_type_id: c.request_type_id, value: c.value, source_url: c.source_url ?? "", preferred: c.preferred, active: c.active, verified: false });
            }}>Bearbeiten</button>
          </li>
        ))}
      </ul>
      <div className="grid gap-2 sm:grid-cols-3">
        <select aria-label="Auskunftsart des Fachkontakts" className={input} value={form.request_type_id} onChange={(e) => setForm({ ...form, request_type_id: e.target.value, verified: false })}>
          <option value="">Auskunftsart wählen</option>
          {types.map((t) => <option key={t.request_type_id} value={t.request_type_id}>{t.name}</option>)}
        </select>
        <input aria-label="E-Mail des Fachkontakts" type="email" placeholder="E-Mail-Adresse" className={input} value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value, verified: false })} />
        <input aria-label="Amtliche Quelle des Fachkontakts" type="url" placeholder="Amtliche Quellen-URL" className={input} value={form.source_url ?? ""} onChange={(e) => setForm({ ...form, source_url: e.target.value, verified: false })} />
      </div>
      <div className="my-2 flex flex-wrap gap-3 text-xs">
        <label><input type="checkbox" checked={form.verified} onChange={(e) => setForm({ ...form, verified: e.target.checked })} /> Kontakt für diese Auskunft anhand der Quelle geprüft</label>
        <label><input type="checkbox" checked={form.preferred} onChange={(e) => setForm({ ...form, preferred: e.target.checked })} /> Bevorzugter Kontakt</label>
        <label><input type="checkbox" checked={form.active} onChange={(e) => setForm({ ...form, active: e.target.checked })} /> Aktiv</label>
      </div>
      <button type="button" disabled={saving || !form.request_type_id || !form.value || (form.verified && !form.source_url)} onClick={() => void save()} className="rounded bg-brand px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50">
        {saving ? "Wird gespeichert…" : editingId === undefined ? "Fachkontakt hinzufügen" : "Fachkontakt speichern"}
      </button>
      {editingId !== undefined && <button type="button" onClick={() => { setEditingId(undefined); setForm(empty); }} className="ml-3 text-xs text-ink-soft">Abbrechen</button>}
    </section>
  );
}
