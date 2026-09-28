import { useEffect, useState } from "react";
import { Pencil, Trash2, Check, X, Loader2, Ban, CheckCircle2, Plus } from "lucide-react";
import { api } from "../../services/api";
import { useToast, errorMessage } from "../common/Toast";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import type { User, UserCreateInput, UserUpdateInput } from "../../types/user";

const EMPTY_CREATE_FORM: UserCreateInput = {
  email: "",
  password: "",
  full_name: "",
  phone: "",
  function: "",
  street: "",
  house_number: "",
  postal_code: "",
  city: "",
  is_main: false,
};

export function UsersAdmin() {
  const { showToast } = useToast();
  const [showInactive, setShowInactive] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<UserUpdateInput>({});
  const [saving, setSaving] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<UserCreateInput>(EMPTY_CREATE_FORM);
  const [creating, setCreating] = useState(false);

  const load = () => {
    setLoading(true);
    api
      .listUsersPaged({ active_only: !showInactive })
      .then((res) => setUsers(res.items))
      .catch((error) => showToast("error", errorMessage(error, "Nutzer konnten nicht geladen werden.")))
      .finally(() => setLoading(false));
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(load, [showInactive]);

  const startEdit = (u: User) => {
    setEditingId(u.user_id);
    setEditForm({
      email: u.email,
      full_name: u.full_name,
      phone: u.phone,
      function: u.function,
      street: u.street,
      house_number: u.house_number,
      postal_code: u.postal_code,
      city: u.city,
      is_main: u.is_main,
    });
  };

  const saveEdit = async (userId: string) => {
    setSaving(true);
    try {
      await api.updateUser(userId, editForm);
      showToast("success", "Nutzer aktualisiert.");
      setEditingId(null);
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Nutzer konnte nicht aktualisiert werden."));
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (u: User) => {
    try {
      await api.updateUser(u.user_id, { active: !u.active });
      showToast("success", u.active ? "Nutzer deaktiviert." : "Nutzer aktiviert.");
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Status konnte nicht geändert werden."));
    }
  };

  const handleDelete = async (u: User) => {
    if (!window.confirm(`"${u.full_name}" wirklich löschen?`)) return;
    try {
      await api.deleteUser(u.user_id);
      showToast("success", "Nutzer gelöscht.");
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Nutzer konnte nicht gelöscht werden."));
    }
  };

  const createFormComplete =
    createForm.email && createForm.password && createForm.full_name && createForm.phone &&
    createForm.function && createForm.street && createForm.house_number && createForm.postal_code &&
    createForm.city;

  const handleCreate = async () => {
    setCreating(true);
    try {
      await api.createUser(createForm);
      showToast("success", "Nutzer angelegt.");
      setShowCreateModal(false);
      setCreateForm(EMPTY_CREATE_FORM);
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Nutzer konnte nicht angelegt werden."));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-1.5 whitespace-nowrap text-xs text-ink-soft">
          <input type="checkbox" checked={showInactive} onChange={(e) => setShowInactive(e.target.checked)} />
          auch inaktive anzeigen
        </label>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus size={14} />
          Neuen Nutzer anlegen
        </Button>
      </div>

      <div className="overflow-hidden rounded-lg border border-line bg-surface shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-sm">
            <thead>
              <tr className="border-b border-line bg-paper/50 text-left text-[11px] uppercase tracking-wide text-ink-faint">
                <th className="px-4 py-2.5 font-medium">Name</th>
                <th className="px-4 py-2.5 font-medium">E-Mail</th>
                <th className="px-4 py-2.5 font-medium">Telefon</th>
                <th className="px-4 py-2.5 font-medium">Funktion</th>
                <th className="px-4 py-2.5 font-medium">Rolle</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="w-28 px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-ink-faint">
                    <Loader2 size={16} className="mx-auto animate-spin" />
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-ink-faint">
                    Keine Nutzer gefunden.
                  </td>
                </tr>
              ) : (
                users.map((u) =>
                  editingId === u.user_id ? (
                    <tr key={u.user_id} className="border-b border-line bg-paper/30 last:border-0">
                      <td colSpan={7} className="px-4 py-3">
                        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                          <input
                            value={editForm.full_name ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, full_name: e.target.value }))}
                            placeholder="Name"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.email ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, email: e.target.value }))}
                            placeholder="E-Mail"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.phone ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, phone: e.target.value }))}
                            placeholder="Telefon"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.function ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, function: e.target.value }))}
                            placeholder="Funktion"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.street ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, street: e.target.value }))}
                            placeholder="Straße"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.house_number ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, house_number: e.target.value }))}
                            placeholder="Nr."
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.postal_code ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, postal_code: e.target.value }))}
                            placeholder="PLZ"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.city ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, city: e.target.value }))}
                            placeholder="Ort"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            type="password"
                            value={editForm.password ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, password: e.target.value }))}
                            placeholder="Neues Passwort (leer = unverändert)"
                            className="col-span-2 rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <label className="flex items-center gap-1.5 text-xs text-ink-soft">
                            <input
                              type="checkbox"
                              checked={editForm.is_main ?? false}
                              onChange={(e) => setEditForm((f) => ({ ...f, is_main: e.target.checked }))}
                            />
                            Haupt-Account
                          </label>
                        </div>
                        <div className="mt-2 flex gap-2">
                          <button
                            onClick={() => saveEdit(u.user_id)}
                            disabled={saving}
                            className="inline-flex items-center gap-1 rounded bg-brand px-2.5 py-1.5 text-xs font-medium text-white hover:bg-brand-dark disabled:opacity-50"
                          >
                            {saving ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
                            Speichern
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="inline-flex items-center gap-1 rounded border border-line px-2.5 py-1.5 text-xs font-medium text-ink-soft hover:border-ink-faint"
                          >
                            <X size={12} />
                            Abbrechen
                          </button>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    <tr key={u.user_id} className="border-b border-line last:border-0 hover:bg-paper/30">
                      <td className="px-4 py-2.5 text-ink">{u.full_name}</td>
                      <td className="px-4 py-2.5 text-ink-soft">{u.email}</td>
                      <td className="px-4 py-2.5 text-ink-soft">{u.phone}</td>
                      <td className="px-4 py-2.5 text-ink-soft">{u.function}</td>
                      <td className="px-4 py-2.5">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                            u.is_main ? "bg-brand-light text-brand" : "bg-status-neutralBg text-status-neutral"
                          }`}
                        >
                          {u.is_main ? "Haupt-Account" : "Standard"}
                        </span>
                      </td>
                      <td className="px-4 py-2.5">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                            u.active
                              ? "bg-status-matchedBg text-status-matched"
                              : "bg-status-neutralBg text-status-neutral"
                          }`}
                        >
                          {u.active ? "Aktiv" : "Inaktiv"}
                        </span>
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => toggleActive(u)}
                            className="rounded p-1.5 text-ink-faint hover:bg-brand-light/50 hover:text-brand"
                            aria-label={u.active ? "Deaktivieren" : "Aktivieren"}
                            title={u.active ? "Deaktivieren" : "Aktivieren"}
                          >
                            {u.active ? <Ban size={14} /> : <CheckCircle2 size={14} />}
                          </button>
                          <button
                            onClick={() => startEdit(u)}
                            className="rounded p-1.5 text-ink-faint hover:bg-brand-light/50 hover:text-brand"
                            aria-label="Bearbeiten"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(u)}
                            className="rounded p-1.5 text-ink-faint hover:bg-status-conflictBg hover:text-status-conflict"
                            aria-label="Löschen"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                )
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showCreateModal && (
        <Modal title="Neuen Nutzer anlegen" onClose={() => setShowCreateModal(false)}>
          <div className="grid grid-cols-2 gap-3">
            <input
              value={createForm.full_name}
              onChange={(e) => setCreateForm((f) => ({ ...f, full_name: e.target.value }))}
              placeholder="Name *"
              className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
            />
            <input
              type="email"
              value={createForm.email}
              onChange={(e) => setCreateForm((f) => ({ ...f, email: e.target.value }))}
              placeholder="E-Mail *"
              className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
            />
            <input
              value={createForm.phone}
              onChange={(e) => setCreateForm((f) => ({ ...f, phone: e.target.value }))}
              placeholder="Telefon *"
              className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
            />
            <input
              value={createForm.function}
              onChange={(e) => setCreateForm((f) => ({ ...f, function: e.target.value }))}
              placeholder="Funktion *"
              className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
            />
            <input
              value={createForm.street}
              onChange={(e) => setCreateForm((f) => ({ ...f, street: e.target.value }))}
              placeholder="Straße *"
              className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
            />
            <input
              value={createForm.house_number}
              onChange={(e) => setCreateForm((f) => ({ ...f, house_number: e.target.value }))}
              placeholder="Hausnummer *"
              className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
            />
            <input
              value={createForm.postal_code}
              onChange={(e) => setCreateForm((f) => ({ ...f, postal_code: e.target.value }))}
              placeholder="PLZ *"
              className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
            />
            <input
              value={createForm.city}
              onChange={(e) => setCreateForm((f) => ({ ...f, city: e.target.value }))}
              placeholder="Ort *"
              className="rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
            />
            <input
              type="password"
              value={createForm.password}
              onChange={(e) => setCreateForm((f) => ({ ...f, password: e.target.value }))}
              placeholder="Passwort *"
              className="col-span-2 rounded border border-line px-2.5 py-2 text-sm focus:border-brand focus:outline-none"
            />
            <label className="col-span-2 flex items-center gap-1.5 text-xs text-ink-soft">
              <input
                type="checkbox"
                checked={createForm.is_main ?? false}
                onChange={(e) => setCreateForm((f) => ({ ...f, is_main: e.target.checked }))}
              />
              Haupt-Account (Verwaltungsrechte)
            </label>
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowCreateModal(false)}>
              Abbrechen
            </Button>
            <Button onClick={handleCreate} disabled={!createFormComplete || creating}>
              {creating && <Loader2 size={14} className="animate-spin" />}
              Anlegen
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}
