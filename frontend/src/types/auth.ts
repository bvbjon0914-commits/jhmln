import type { User } from "./user";

export interface AuthStatus {
  login_required: boolean;
  logged_in: boolean;
  is_main: boolean;
  user?: User | null;
}
