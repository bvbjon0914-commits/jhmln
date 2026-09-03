export interface ImportPreview {
  total_rows: number;
  columns: string[];
  preview_rows: Record<string, unknown>[];
}

export type ImportRowStatus = "IMPORTED" | "UPDATED" | "DUPLICATE" | "NEEDS_REVIEW" | "ERROR";

export interface ImportRowResult {
  row_index: number;
  status: ImportRowStatus;
  message: string;
}

export interface ImportSummary {
  total_rows: number;
  imported: number;
  duplicates: number;
  needs_review: number;
  errors: number;
  updated: number;
  details: ImportRowResult[];
}

export type ImportKind = "authorities" | "jurisdictions" | "buildings";

export interface FieldSpec {
  key: string;
  label: string;
  required: boolean;
}

export const BUILDING_FIELDS: FieldSpec[] = [
  { key: "street", label: "Straße", required: true },
  { key: "house_number", label: "Hausnummer", required: true },
  { key: "city", label: "Ort", required: true },
  { key: "postal_code", label: "PLZ", required: false },
  { key: "district", label: "Stadtteil", required: false },
  { key: "state", label: "Bundesland", required: false },
  { key: "ags", label: "AGS-Schlüssel", required: false },
  { key: "property_name", label: "Objektname", required: false },
  { key: "internal_reference", label: "Interne Referenz", required: false },
  { key: "notes", label: "Notizen", required: false },
];

export const AUTHORITY_FIELDS: FieldSpec[] = [
  { key: "authority_name", label: "Behördenname", required: true },
  { key: "department_name", label: "Abteilung", required: false },
  { key: "city", label: "Ort", required: false },
  { key: "street", label: "Straße", required: false },
  { key: "house_number", label: "Hausnummer", required: false },
  { key: "postal_code", label: "PLZ", required: false },
  { key: "state", label: "Bundesland", required: false },
  { key: "email", label: "E-Mail", required: false },
  { key: "phone", label: "Telefon", required: false },
  { key: "website", label: "Website", required: false },
  { key: "source", label: "Quelle", required: false },
];

export const JURISDICTION_FIELDS: FieldSpec[] = [
  { key: "authority_name", label: "Behördenname", required: true },
  { key: "ags", label: "AGS-Schlüssel", required: true },
  { key: "city", label: "Ort", required: false },
  { key: "department_name", label: "Abteilung", required: false },
  { key: "street", label: "Straße", required: false },
  { key: "house_number", label: "Hausnummer", required: false },
  { key: "postal_code", label: "PLZ", required: false },
  { key: "state", label: "Bundesland", required: false },
  { key: "email", label: "E-Mail", required: false },
  { key: "phone", label: "Telefon", required: false },
  { key: "website", label: "Website", required: false },
  { key: "municipality", label: "Gemeindename", required: false },
  { key: "priority", label: "Priorität", required: false },
  { key: "matching_level", label: "Matching-Level", required: false },
  { key: "source", label: "Quelle", required: false },
  { key: "notes", label: "Notizen", required: false },
];

// Zusätzliche, von den sichtbaren Feld-Labels abweichende Spaltennamen, die
// trotzdem eindeutig demselben Feld zugeordnet werden sollen – insbesondere
// die Spaltenüberschriften des eigenen "Als Excel exportieren"-Features
// (Datenqualität-Tab), damit eine ausgefüllte Export-Datei beim Reimport
// automatisch korrekt zugeordnet wird, ohne dass jedes Feld manuell per
// Dropdown ausgewählt werden muss.
const FIELD_ALIASES: Record<string, string[]> = {
  authority_name: ["Behörde", "Behördenname", "Name", "Amt"],
  department_name: ["Abteilung"],
  city: ["Ort", "Stadt"],
  street: ["Straße", "Strasse"],
  house_number: ["Hausnummer", "Nr", "Nr."],
  postal_code: ["PLZ", "Postleitzahl"],
  state: ["Bundesland"],
  email: ["E-Mail", "Email", "Mail"],
  phone: ["Telefon", "Tel"],
  website: ["Website", "Web"],
  source: ["Quelle"],
  ags: ["AGS-Schlüssel", "AGS", "Amtlicher Gemeindeschlüssel"],
  district: ["Stadtteil"],
  property_name: ["Objektname"],
  internal_reference: ["Interne Referenz"],
  notes: ["Notizen"],
  municipality: ["Gemeindename"],
  priority: ["Priorität"],
  matching_level: ["Matching-Level"],
};

/**
 * Ordnet Datei-Spalten automatisch den bekannten Feldern zu, sofern der
 * Spaltenname (Groß-/Kleinschreibung und Leerzeichen ignoriert) dem
 * Feld-Label, -Key oder einem hinterlegten Alias entspricht. Jede Spalte
 * wird höchstens einem Feld zugeordnet. Restliche Felder bleiben leer und
 * können weiterhin manuell per Dropdown gesetzt werden.
 */
export function autoMapColumns(fields: FieldSpec[], columns: string[]): Record<string, string> {
  const normalize = (s: string) => s.trim().toLowerCase();
  const remaining = [...columns];
  const mapping: Record<string, string> = {};

  for (const field of fields) {
    const candidates = [field.label, field.key, ...(FIELD_ALIASES[field.key] || [])].map(normalize);
    const matchIndex = remaining.findIndex((col) => candidates.includes(normalize(col)));
    if (matchIndex !== -1) {
      mapping[field.key] = remaining[matchIndex];
      remaining.splice(matchIndex, 1);
    }
  }
  return mapping;
}
