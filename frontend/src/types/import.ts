export interface ImportPreview {
  total_rows: number;
  columns: string[];
  preview_rows: Record<string, unknown>[];
}

export type ImportRowStatus = "IMPORTED" | "DUPLICATE" | "NEEDS_REVIEW" | "ERROR";

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
  details: ImportRowResult[];
}

export type ImportKind = "authorities" | "jurisdictions";

export interface FieldSpec {
  key: string;
  label: string;
  required: boolean;
}

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
