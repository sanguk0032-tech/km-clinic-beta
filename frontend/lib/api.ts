const API_BASE = 'http://127.0.0.1:8000/api';

export type MetricDefinition = {
  id: number;
  key: string;
  name: string;
  input_type: 'scale' | 'choice';
  min_value: number | null;
  max_value: number | null;
};

export type DailyEntry = {
  id: number;
  date: string;
  note: string;
  metric_values: Array<{
    metric_key: string;
    value_int: number | null;
    value_text: string;
  }>;
};

function getToken() {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem('access_token') || '';
}

async function request(path: string, options: RequestInit = {}) {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: token ? `Bearer ${token}` : '',
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    throw new Error(`API Error ${res.status}`);
  }

  return res.json();
}

export async function login(username: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) throw new Error('로그인 실패');
  return res.json();
}

export const fetchMetrics = () => request('/metrics/') as Promise<MetricDefinition[]>;
export const fetchTodayEntry = () => request('/entries/today/') as Promise<DailyEntry>;

export const upsertEntry = (payload: {
  date: string;
  note: string;
  values: Array<{ metric_key: string; value_int?: number | null; value_text?: string }>;
}) => request('/entries/upsert/', { method: 'POST', body: JSON.stringify(payload) });

export const fetchTrend = (days: number, metricKey: string) =>
  request(`/entries/trend/?days=${days}&metric_key=${metricKey}`) as Promise<{
    metric_key: string;
    days: number;
    points: Array<{ date: string; value: number | string }>;
  }>;
