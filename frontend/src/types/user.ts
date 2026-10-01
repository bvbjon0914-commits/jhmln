export interface User {
  user_id: string;
  email: string;
  full_name: string;
  phone: string;
  function: string;
  street: string;
  house_number: string;
  postal_code: string;
  city: string;
  is_main: boolean;
  active: boolean;
  status: "pending" | "active" | "rejected";
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
  last_login_at?: string | null;
}

export interface UserCreateInput {
  email: string;
  password: string;
  full_name: string;
  phone: string;
  function: string;
  street: string;
  house_number: string;
  postal_code: string;
  city: string;
  is_main?: boolean;
  active?: boolean;
}

export interface UserRegisterInput {
  email: string;
  password: string;
  full_name: string;
  phone: string;
  function: string;
  street: string;
  house_number: string;
  postal_code: string;
  city: string;
}

export interface UserUpdateInput {
  email?: string;
  full_name?: string;
  phone?: string;
  function?: string;
  street?: string;
  house_number?: string;
  postal_code?: string;
  city?: string;
  is_main?: boolean;
  active?: boolean;
  password?: string;
}

/** Selbstbearbeitung des eigenen Accounts - bewusst ohne is_main/active/status,
 * die eigene Rolle/Freigabe kann niemand selbst ändern. */
export interface UserSelfUpdateInput {
  email?: string;
  full_name?: string;
  phone?: string;
  function?: string;
  street?: string;
  house_number?: string;
  postal_code?: string;
  city?: string;
  password?: string;
}
