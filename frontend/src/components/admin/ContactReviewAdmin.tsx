import { useEffect, useRef, useState } from "react";
import { Check, Download, ExternalLink, FileSearch, Loader2, RefreshCw, Upload, X } from "lucide-react";
import { api } from "../../services/api";
import type { ContactReview, ContactReviewImport, ContactReviewPage, ReviewDecision } from "../../types/contactReview";
import type { RequestType } from "../../types/matching";
import { Button } from "../common/Button";
import { errorMessage, useToast } from "../common/Toast";

const labels: Record<string, string> = { PENDING: "Neu", RESEARCH: "Nachrecherche", CONFIRMED: "Bestätigt", REJECTED: "Abgelehnt" };
const reasons: Record<string, string> = {
  DIENSTLEISTUNG_BELEGT: "Auf einer passenden Leistungsseite veröffentlicht",
  PERSOENLICHER_PRUEFKONTAKT: "Persönlicher Ansprechpartner: Zuständigkeit prüfen",
  KEINE_EINDEUTIGE_DIENSTLEISTUNGSBINDUNG: "Zuordnung zur Auskunftsart noch offen",
  AMTLICHE_DOMAIN_NICHT_BESTAETIGT: "Amtliche Herkunft der Website noch prüfen",
  MAILDOMAIN_ALIAS_UNBELEGT: "Abweichende E-Mail-Domain noch prüfen",
  PDF_PRUEFKONTAKT: "Kontakt aus einem PDF: Kontext und Gültigkeit prüfen",
  PORTAL_PRUEFEN: "Einreichungsweg im Portal prüfen",
  SICHTBARER_TEXT: "E-Mail-Adresse aus dem sichtbaren Seitentext",
};
function date(value: string) { return new Date(value).toLocaleString("de-DE"); }
function safeLink(value: string): string | undefined {
  try { const url = new URL(value); return ["http:", "https:"].includes(url.protocol) ? url.href : undefined; } catch { return undefined; }
}

export function ContactReviewAdmin() {
  const { showToast } = useToast();
  const [page, setPage] = useState<ContactReviewPage>({ items: [], total: 0, counts: {} });
  const [status, setStatus] = useState("OPEN");
  const [type, setType] = useState("");
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [reload, setReload] = useState(0);
  const [types, setTypes] = useState<RequestType[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [checked, setChecked] = useState(false);
  const [preferred, setPreferred] = useState(false);
  const [comment, setComment] = useState("");
  const [imported, setImported] = useState<ContactReviewImport | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const selected = page.items.find(p => p.proposal_id === selectedId) ?? page.items[0];

  useEffect(() => { api.listRequestTypes().then(setTypes).catch(() => undefined); }, []);
  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(() => {
      setLoading(true); setError("");
      api.listContactReviews({ status, request_type_id: type || undefined, search, offset })
        .then(result => { if (active) { setPage(result); setSelectedId(""); setChecked(false); setPreferred(false); setComment(""); } })
        .catch(e => { if (active) setError(errorMessage(e, "Kontaktprüfung konnte nicht geladen werden.")); })
        .finally(() => { if (active) setLoading(false); });
    }, 180);
    return () => { active = false; window.clearTimeout(timer); };
  }, [status, type, search, offset, reload]);

  function select(p: ContactReview) { setSelectedId(p.proposal_id); setChecked(false); setPreferred(false); setComment(""); }
  async function upload(file: File) {
    if (file.size > 8 * 1024 * 1024) { showToast("error", "Die Prüfdatei darf höchstens 8 MB groß sein."); return; }
    setBusy(true);
    try { const result = await api.importContactReviews(file); setImported(result); setOffset(0); setReload(n => n + 1); }
    catch (e) { showToast("error", errorMessage(e, "Prüfdatei konnte nicht eingelesen werden.")); }
    finally { setBusy(false); if (fileRef.current) fileRef.current.value = ""; }
  }
  async function decide(decision: ReviewDecision) {
    if (!selected) return;
    setBusy(true);
    try {
      await api.decideContactReview(selected.proposal_id, { decision, version: selected.version, source_checked: checked, preferred, comment });
      showToast("success", decision === "CONFIRM" ? "Kontakt für diese Auskunftsart bestätigt." : decision === "REJECT" ? "Vorschlag abgelehnt." : "Für eine weitere Recherche vorgemerkt.");
      setReload(n => n + 1);
    } catch (e) { showToast("error", errorMessage(e, "Entscheidung konnte nicht gespeichert werden.")); setReload(n => n + 1); }
    finally { setBusy(false); }
  }
  async function exportNeeds() {
    setBusy(true);
    try {
      const blob = await api.exportContactResearch(); const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = "fachkontakte_nachrecherche.xlsx"; a.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) { showToast("error", errorMessage(e, "Nachrecherche konnte nicht exportiert werden.")); }
    finally { setBusy(false); }
  }
  const editable = selected && ["PENDING", "RESEARCH"].includes(selected.status);

  return <div className="space-y-5">
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div><h3 className="font-display text-xl font-semibold text-ink">Fachkontakte prüfen</h3>
        <p className="mt-1 max-w-2xl text-sm text-ink-soft">Vergleiche jeden Vorschlag mit der Quelle und der Auskunftsart. Erst deine Bestätigung gibt den Kontakt frei.</p></div>
      <div className="flex flex-wrap gap-2">
        <input ref={fileRef} type="file" accept=".json,application/json" className="hidden" aria-label="Prüfdatei auswählen" onChange={e => { const file = e.target.files?.[0]; if (file) void upload(file); }} />
        <Button variant="secondary" disabled={busy} onClick={() => fileRef.current?.click()}><Upload size={16} />Prüfdatei laden</Button>
        <Button variant="secondary" disabled={busy || !page.counts.RESEARCH} onClick={() => void exportNeeds()}><Download size={16} />Nachrecherche exportieren</Button>
      </div>
    </div>
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">{Object.entries(labels).map(([key, label]) => <button key={key} onClick={() => { setStatus(key); setOffset(0); }} className={`rounded border p-3 text-left ${status === key ? "border-brand bg-brand-light" : "border-line bg-white"}`}>
      <span className="block text-xs text-ink-soft">{label}</span><span className="mt-1 block text-2xl font-semibold text-ink">{page.counts[key as keyof typeof page.counts] ?? 0}</span>
    </button>)}</div>
    {imported && <div role="status" className="rounded border border-line bg-surface p-4 text-sm text-ink">
      {imported.imported} neue Vorschläge · {imported.duplicates} bereits vorhanden · {imported.needs_review} Eingaben zu klären.
      {!!imported.details.length && <ul className="mt-2 max-h-40 list-disc overflow-auto pl-5">{imported.details.map(d => <li key={d.row}>Eintrag {d.row}: {d.reason}</li>)}</ul>}
    </div>}
    <div className="flex flex-wrap gap-2">
      <input className="min-w-48 flex-1 rounded border border-line bg-white px-3 py-2 text-sm" placeholder="Behörde, Ort oder Kontakt suchen" aria-label="Kontaktvorschläge suchen" value={search} onChange={e => { setSearch(e.target.value); setOffset(0); }} />
      <select aria-label="Auskunftsart filtern" className="rounded border border-line bg-white px-3 py-2 text-sm" value={type} onChange={e => { setType(e.target.value); setOffset(0); }}><option value="">Alle Auskunftsarten</option>{types.map(t => <option key={t.request_type_id} value={t.request_type_id}>{t.name}</option>)}</select>
      <select aria-label="Prüfstatus filtern" className="rounded border border-line bg-white px-3 py-2 text-sm" value={status} onChange={e => { setStatus(e.target.value); setOffset(0); }}><option value="OPEN">Alle offenen</option>{Object.entries(labels).map(([k,v]) => <option key={k} value={k}>{v}</option>)}<option value="ALL">Alle Status</option></select>
      <Button variant="ghost" aria-label="Kontaktprüfung aktualisieren" disabled={busy || loading} onClick={() => setReload(n => n + 1)}><RefreshCw size={16}/></Button>
    </div>
    {error && <div role="alert" className="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>}
    {loading ? <div className="flex items-center gap-2 py-12 text-sm text-ink-soft"><Loader2 size={18} className="animate-spin"/>Kontaktvorschläge werden geladen …</div> : !page.items.length ? <div className="rounded border border-dashed border-line p-10 text-center"><FileSearch className="mx-auto text-brand"/><p className="mt-3 font-medium text-ink">{page.total ? "Auf dieser Seite liegen keine Vorschläge." : "Keine passenden Kontaktvorschläge."}</p><p className="mt-2 text-sm text-ink-soft">Lade die Datei <code>civeloq_pruefung.json</code> aus Bot 2.6 oder passe die Filter an.</p></div> : <div className="grid gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
      <div className="max-h-[800px] space-y-2 overflow-auto" aria-label="Kontaktvorschläge">{page.items.map(p => <button key={p.proposal_id} onClick={() => select(p)} className={`w-full rounded border p-4 text-left ${selected?.proposal_id === p.proposal_id ? "border-brand bg-brand-light" : "border-line bg-white hover:border-brand/40"}`}>
        <span className="block text-xs text-ink-soft">{p.city} · {labels[p.status]}</span><span className="mt-1 block text-sm font-semibold text-ink">{p.request_type_name}</span><span className="mt-1 block break-all text-sm text-brand">{p.value}</span><span className="mt-2 block text-xs text-ink-soft">{p.authority_name}</span>
      </button>)}</div>
      {selected && <div className="min-w-0 space-y-5 rounded border border-line bg-white p-5 md:p-6">
        <div><div className="text-xs font-medium uppercase tracking-wide text-brand">{selected.request_type_name}</div><h4 className="mt-1 font-display text-lg font-semibold text-ink">{selected.authority_name}</h4><p className="mt-1 text-xs text-ink-soft">AGS {selected.ags.join(", ")} · {labels[selected.status]}</p></div>
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded bg-surface p-4"><h5 className="text-xs font-semibold uppercase tracking-wide text-ink-soft">Behördenstammdaten</h5><p className="mt-2 break-all text-sm text-ink">{selected.stock.email || "Keine allgemeine E-Mail vorhanden"}</p><p className="mt-2 text-xs text-ink-soft">{[selected.stock.street, selected.stock.house_number].filter(Boolean).join(" ")}<br/>{selected.stock.postal_code} {selected.stock.city}</p></div>
          <div className="rounded border border-brand/25 bg-brand-light p-4"><h5 className="text-xs font-semibold uppercase tracking-wide text-brand">Vorschlag für diese Auskunftsart</h5><p className="mt-2 break-all font-medium text-ink">{selected.value}</p><p className="mt-2 text-xs text-ink-soft">{selected.channel_type === "EMAIL" ? "E-Mail" : "Online-Portal / Formular"}</p></div>
        </div>
        {!!selected.current_channels.length && <div className="text-sm"><h5 className="font-medium text-ink">Bereits hinterlegte Kontakte dieser Auskunftsart</h5>{selected.current_channels.map(c => <p key={c.id} className="mt-1 break-all text-ink-soft">{c.value} · {c.last_verified_at ? "geprüft" : "ungeprüft"}{c.preferred ? " · bevorzugt" : ""}{!c.active ? " · inaktiv" : ""}</p>)}</div>}
        {!!selected.reasons.length && <div className="rounded bg-surface p-3 text-sm text-ink-soft">{selected.reasons.map((reason,i) => <p key={i}>{reasons[reason] ?? reason}</p>)}</div>}
        <section><div className="flex flex-wrap items-center justify-between gap-2"><h5 className="font-medium text-ink">Quellenbeleg</h5><a className="inline-flex items-center gap-1 text-sm text-brand underline" href={safeLink(selected.source_url)} target="_blank" rel="noopener noreferrer">Quelle öffnen<ExternalLink size={14}/></a></div>
          <p className="mt-2 break-all text-xs text-ink-soft">{selected.source_url}<br/>Abgerufen am {date(selected.observed_at)}</p>
          {selected.evidence.map((e,i) => <blockquote key={i} className="mt-3 border-l-2 border-brand/40 bg-surface px-4 py-3"><p className="whitespace-pre-wrap text-sm text-ink">{e.evidence_quote}</p><footer className="mt-2 text-xs text-ink-faint">{e.locator}</footer></blockquote>)}
        </section>
        {editable && <div className="space-y-3 border-t border-line pt-4">
          <label className="flex items-start gap-2 text-sm text-ink"><input type="checkbox" className="mt-1 accent-brand" checked={checked} onChange={e => setChecked(e.target.checked)}/>Ich habe die Quelle geöffnet und die Zuordnung zu dieser Auskunftsart geprüft.</label>
          <label className="flex items-start gap-2 text-sm text-ink-soft"><input type="checkbox" className="mt-1 accent-brand" checked={preferred} onChange={e => setPreferred(e.target.checked)}/>Diesen Kontakt für diese Auskunftsart bevorzugen.</label>
          <textarea aria-label="Prüfnotiz" className="w-full rounded border border-line px-3 py-2 text-sm" rows={2} maxLength={1000} placeholder="Prüfnotiz (optional)" value={comment} onChange={e => setComment(e.target.value)}/>
          <div className="flex flex-wrap gap-2"><Button disabled={busy || !checked} onClick={() => void decide("CONFIRM")}><Check size={16}/>Bestätigen</Button><Button variant="secondary" disabled={busy} onClick={() => void decide("RESEARCH")}><FileSearch size={16}/>Weitere Recherche</Button><Button variant="ghost" disabled={busy} onClick={() => void decide("REJECT")}><X size={16}/>Ablehnen</Button></div>
          <p className="text-xs text-ink-soft">Weitere Recherche merkt den Fall vor. Über den Export kannst du ihn erneut mit dem Bot bearbeiten.</p>
        </div>}
        {!!selected.history.length && <div className="border-t border-line pt-4"><h5 className="text-sm font-medium text-ink">Prüfverlauf</h5>{selected.history.map(h => <p key={h.version} className="mt-2 text-xs text-ink-soft">{date(h.at)} · {h.actor} · {h.decision === "CONFIRM" ? "Bestätigt" : h.decision === "REJECT" ? "Abgelehnt" : "Weitere Recherche"}{h.comment ? ` · ${h.comment}` : ""}</p>)}</div>}
      </div>}
    </div>}
    <div className="flex items-center justify-between text-sm text-ink-soft"><span>{page.total} passende Vorschläge</span><div className="flex gap-2"><Button variant="ghost" disabled={offset === 0 || loading} onClick={() => setOffset(n => Math.max(0,n-40))}>Zurück</Button><Button variant="ghost" disabled={offset + 40 >= page.total || loading} onClick={() => setOffset(n => n+40)}>Weiter</Button></div></div>
  </div>;
}
