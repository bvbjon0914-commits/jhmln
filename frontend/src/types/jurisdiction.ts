export interface Jurisdiction {
  jurisdiction_id: string;
  request_type_id: string;
  authority_id: string;
  country: string;
  state?: string | null;
  ags?: string | null;
  municipality?: string | null;
  district?: string | null;
  postal_code?: string | null;
  street?: string | null;
  house_number?: string | null;
  priority: number;
  matching_level?: string | null;
  active: boolean;
  notes?: string | null;
}

export interface JurisdictionUpdateInput {
  ags?: string | null;
  municipality?: string | null;
  priority?: number;
  matching_level?: string | null;
  active?: boolean;
  notes?: string | null;
}
