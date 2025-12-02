export interface Token {
  access_token: string;
  token_type: string;
}

export interface UserCreate {
  user_id: string;
  password: string;
  email?: string;
}

export interface UserLogin {
  user_id: string;
  password: string;
}

export interface UserProfile {
  user_id: string;
  email?: string | null;
}
