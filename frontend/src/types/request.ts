export interface RequestItemRecord {
  request_item_id: string;
  request_type_id: string;
  authority_id: string | null;
  matching_status: string;
  document_status: string;
}

export interface RequestRecord {
  request_id: string;
  building_id: string;
  created_at: string;
  status: string;
  completion_status: { total: number; completed: number; failed: number; pending: number };
  items: RequestItemRecord[];
  building: { street: string; house_number: string; city: string } | null;
}
