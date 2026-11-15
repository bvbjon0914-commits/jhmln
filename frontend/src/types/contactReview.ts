export type ReviewStatus = "PENDING" | "RESEARCH" | "CONFIRMED" | "REJECTED";
export type ReviewDecision = "CONFIRM" | "REJECT" | "RESEARCH";
export interface ContactReview {
  proposal_id: string;
  authority_id: string;
  authority_name: string;
  city: string;
  request_type_id: string;
  request_type_name: string;
  ags: string[];
  channel_type: "EMAIL" | "PORTAL";
  value: string;
  source_url: string;
  source_sha256: string;
  observed_at: string;
  evidence: { locator: string; evidence_quote: string }[];
  reasons: string[];
  status: ReviewStatus;
  version: number;
  channel_id: number | null;
  stock: { email: string | null; phone: string | null; street: string | null; house_number: string | null; postal_code: string | null; city: string; department_name: string | null };
  current_channels: { id: number; channel_type: string; value: string; active: boolean; preferred: boolean; last_verified_at: string | null }[];
  history: { at: string; actor: string; decision: ReviewDecision; comment: string; version: number }[];
}
export interface ContactReviewPage {
  items: ContactReview[];
  total: number;
  counts: Partial<Record<ReviewStatus, number>>;
}
export interface ContactReviewImport {
  imported: number;
  duplicates: number;
  needs_review: number;
  details: { row: number; reason: string }[];
}
