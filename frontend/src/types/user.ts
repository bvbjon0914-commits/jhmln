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
