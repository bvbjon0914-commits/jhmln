import type { ResolvedContact } from "../../types/authority";

export function ContactStatus({ contact }: { contact?: ResolvedContact }) {
  if (!contact) return null;
  const labels: Record<string, string> = {
    VERIFIED: "Geprüfter Fachkontakt",
    UNVERIFIED: "Fachkontakt muss geprüft werden",
    GENERAL_ONLY: "Nur allgemeiner Kontakt – Fachkontakt fehlt",
    CONFLICT: "Mehrere Fachkontakte – Auswahl prüfen",
    MISSING: "Fachkontakt fehlt",
    INACTIVE: "Behörde ist inaktiv",
  };
  return (
    <div className={`mt-1 text-xs ${contact.can_send ? "text-ink-soft" : "text-status-conflict"}`}>
      {labels[contact.status] ?? "Kontakt prüfen"}
      {contact.email && <span> · {contact.email}</span>}
      {!contact.email && contact.fallback_email && <span> · Zentrale: {contact.fallback_email}</span>}
    </div>
  );
}
