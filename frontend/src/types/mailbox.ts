export interface InboundAttachment {
  id: number;
  inbound_email_id: number;
  filename: string | null;
  content_type: string | null;
  size: number;
}

export interface InboundEmailEntry {
  id: number;
  received_at: string;
  from_address: string | null;
  subject: string | null;
  body_text: string | null;
  matched_request_item_id: string | null;
  auto_matched: boolean;
  attachments: InboundAttachment[];
}

export interface AktenzeichenLookupResult {
  request_item_id: string;
  aktenzeichen: string;
  building_label: string | null;
  authority_name: string | null;
  request_type_name: string;
}
