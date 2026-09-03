export interface RequestType {
  request_type_id: string;
  code: string;
  name: string;
  description?: string | null;
  active: boolean;
}

export type MatchingStatus =
  | "MATCHED"
  | "REVIEW_REQUIRED"
  | "NO_MATCH"
  | "MULTIPLE_MATCHES";

export type MatchingLevel =
  | "STREET_NUMBER"
  | "STREET"
  | "DISTRICT"
  | "MUNICIPALITY"
  | "COUNTY"
  | "STATE"
  | "POSTAL_CODE";

export interface MatchingResult {
  building_id: string;
  request_type_id: string;
  authority_id: string | null;
  matching_level: MatchingLevel | null;
  matching_status: MatchingStatus;
  matching_confidence: number;
  reason: string;
  alternative_authorities: string[];
  jurisdiction_id: string | null;
  request_item_id: string;
}

export interface MatchingResponse {
  request_id: string;
  building_id: string;
  results: MatchingResult[];
  timestamp: string;
}

export interface GeneratedDocumentInfo {
  request_item_id: string;
  request_type_id: string;
  authority_id: string;
  filename: string;
  filepath: string;
  aktenzeichen: string | null;
}

export interface DocumentGenerationResponse {
  request_id: string;
  documents: GeneratedDocumentInfo[];
  failed: { request_item_id: string; request_type_id: string; reason: string }[];
  timestamp: string;
}
