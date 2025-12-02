const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

let authToken: string | null = null;

function buildHeaders(init?: HeadersInit, body?: BodyInit | null) {
  const headers = new Headers(init);
  if (!(body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (authToken) {
    headers.set('Authorization', `Bearer ${authToken}`);
  }
  return headers;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { body } = options;
  const headers = buildHeaders(options.headers, body ?? null);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const text = await response.text();
  if (!response.ok) {
    const message = text || `Request failed with status ${response.status}`;
    throw new Error(message);
  }
  return text ? (JSON.parse(text) as T) : ({} as T);
}

function get<T>(path: string, options: RequestInit = {}) {
  return request<T>(path, { ...options, method: 'GET' });
}

function post<T>(path: string, body?: unknown, options: RequestInit = {}) {
  return request<T>(path, {
    ...options,
    method: 'POST',
    body: body instanceof FormData ? body : JSON.stringify(body ?? {}),
  });
}

export const httpClient = {
  get,
  post,
  setToken(token: string | null) {
    authToken = token;
  },
  baseUrl: API_BASE_URL,
};
