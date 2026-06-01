import axios, { AxiosInstance } from 'axios';
import { getToken, clearToken } from './auth';
import type {
  User,
  Token,
  Property,
  SearchResponse,
  ComparablesResponse,
  PropertyAnalysis,
  DashboardSummary,
  RecommendationsResponse,
  ChatResponse,
  SavedProperty,
  RegisterRequest,
  LoginRequest,
  SavedCreate,
  SearchParams
} from './types';

const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const api: AxiosInstance = axios.create({ baseURL });

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      clearToken();
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ---- Auth ----
export async function register(body: RegisterRequest): Promise<Token> {
  const { data } = await api.post<Token>('/auth/register', body);
  return data;
}

export async function login(body: LoginRequest): Promise<Token> {
  const { data } = await api.post<Token>('/auth/login', body);
  return data;
}

export async function refresh(): Promise<Token> {
  const { data } = await api.post<Token>('/auth/refresh');
  return data;
}

export async function me(): Promise<User> {
  const { data } = await api.get<User>('/auth/me');
  return data;
}

// ---- Properties ----
export async function searchProperties(params: SearchParams): Promise<SearchResponse> {
  const { data } = await api.get<SearchResponse>('/properties/search', { params });
  return data;
}

export async function getProperty(id: string): Promise<Property> {
  const { data } = await api.get<Property>(`/properties/${id}`);
  return data;
}

export async function getComparables(id: string): Promise<ComparablesResponse> {
  const { data } = await api.get<ComparablesResponse>(`/properties/${id}/comparables`);
  return data;
}

export async function getAnalysis(id: string): Promise<PropertyAnalysis> {
  const { data } = await api.get<PropertyAnalysis>(`/properties/${id}/analysis`);
  return data;
}

export async function generateAnalysis(id: string): Promise<PropertyAnalysis> {
  const { data } = await api.post<PropertyAnalysis>('/properties/analysis', { property_id: id });
  return data;
}

// ---- Dashboard ----
export async function dashboardSummary(): Promise<DashboardSummary> {
  const { data } = await api.get<DashboardSummary>('/dashboard/summary');
  return data;
}

export async function recommendations(): Promise<RecommendationsResponse> {
  const { data } = await api.get<RecommendationsResponse>('/dashboard/recommendations');
  return data;
}

// ---- Chat ----
export async function chatQuery(query: string): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>('/chat/query', { query });
  return data;
}

// ---- Saved ----
export async function listSaved(): Promise<SavedProperty[]> {
  const { data } = await api.get<SavedProperty[]>('/saved');
  return data;
}

export async function addSaved(body: SavedCreate): Promise<SavedProperty> {
  const { data } = await api.post<SavedProperty>('/saved', body);
  return data;
}

export async function deleteSaved(id: string): Promise<{ ok: boolean }> {
  const { data } = await api.delete<{ ok: boolean }>(`/saved/${id}`);
  return data;
}
