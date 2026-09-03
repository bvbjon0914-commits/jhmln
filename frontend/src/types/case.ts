import type { Building } from "./building";

export type CaseStatus = "OPEN" | "CLOSED";

export interface Case {
  case_id: string;
  name: string;
  notes: string | null;
  status: CaseStatus;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface CaseListItem extends Case {
  items_total: number;
  items_done: number;
}

export type CaseItemStatus =
  | "NICHT_BEANTRAGT"
  | "BEREIT_ZUM_SENDEN"
  | "GESENDET"
  | "ANTWORT_ERHALTEN"
  | "GEPRUEFT";

export interface CaseRequestItem {
  request_item_id: string;
  request_id: string;
  building_id: string;
  request_type_id: string;
  request_type_name: string;
  authority_id: string | null;
  authority_name: string | null;
  matching_status: string;
  document_status: string;
  status: CaseItemStatus;
  aktenzeichen: string | null;
  sent_at: string | null;
  response_received_at: string | null;
  response_document_filename: string | null;
  reviewed_at: string | null;
}

export interface CaseDetail extends Case {
  buildings: Building[];
  items: CaseRequestItem[];
}
