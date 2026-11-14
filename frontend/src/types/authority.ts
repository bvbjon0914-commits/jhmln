export interface Authority {
  authority_id: string;
  authority_name: string;
  department_name?: string | null;
  street?: string | null;
  house_number?: string | null;
  postal_code?: string | null;
  city?: string | null;
  state?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  active: boolean;
}

export interface AuthorityUpdateInput {
  authority_name?: string;
  department_name?: string | null;
  street?: string | null;
  house_number?: string | null;
  postal_code?: string | null;
  city?: string | null;
  state?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  active?: boolean;
}
export interface ResolvedContact {
  email: string | null;
  status: string;
  can_send: boolean;
  source_url: string | null;
  channel_id: number | null;
  fallback_email: string | null;
}

export interface EmailContactInput {
  request_type_id: string;
  value: string;
  source_url: string | null;
  verified: boolean;
  preferred: boolean;
  active: boolean;
}

export interface EmailContact extends Omit<EmailContactInput, "verified"> {
  id: number;
  last_verified_at: string | null;
}
