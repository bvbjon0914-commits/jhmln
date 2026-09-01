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
