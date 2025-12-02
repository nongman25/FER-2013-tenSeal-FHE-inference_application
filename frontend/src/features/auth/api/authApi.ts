import { httpClient } from '../../../lib/http/client';
import { Token, UserCreate, UserLogin, UserProfile } from '../../../types';

export const authApi = {
  register(payload: UserCreate) {
    return httpClient.post<UserProfile>('/auth/register', payload);
  },
  login(payload: UserLogin) {
    return httpClient.post<Token>('/auth/login', payload);
  },
};
