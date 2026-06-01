// TypeScript interfaces mirroring the backend Pydantic schemas.

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  user?: User;
}

export interface NearbySchool {
  name: string;
  rating?: number;
  type?: string;
  distance?: number;
}

export interface PropertyNeighborhood {
  id: string;
  property_id: string;
  school_score: number;
  restaurants_count: number;
  commute_time: number;
  walk_score: number;
  crime_score: number;
  nearby_schools: NearbySchool[];
  created_at: string;
}

export interface PropertyAnalysis {
  id: string;
  property_id: string;
  summary: string;
  pros: string[];
  cons: string[];
  investment_score: number;
  risk_score: 'low' | 'med' | 'high' | string;
  buyer_score: number;
  price_evaluation: string;
  estimated_value: number | null;
  created_at: string;
}

export interface Property {
  id: string;
  external_id: string | null;
  address: string;
  city: string;
  state: string;
  zip: string;
  price: number;
  beds: number;
  bathrooms: number;
  sqft: number;
  lot_size: number | null;
  year_built: number | null;
  property_type: string;
  lat: number;
  lng: number;
  description: string;
  photos: string[];
  status: string;
  listed_date: string | null;
  created_at: string;
  updated_at: string;
  neighborhood?: PropertyNeighborhood | null;
  analysis?: PropertyAnalysis | null;
}

export interface SearchResponse {
  results: Property[];
  total: number;
}

export interface ComparablesStats {
  avg_price: number;
  avg_price_per_sqft: number;
  count: number;
  subject_price_per_sqft: number;
}

export interface ComparablesResponse {
  comparables: Property[];
  stats: ComparablesStats;
}

export interface DashboardSummary {
  properties_analyzed: number;
  avg_valuation: number;
  saved_count: number;
  new_opportunities: number;
  recent: Property[];
}

export interface RecommendationsResponse {
  recommendations: Property[];
}

export interface ChatSource {
  property_id: string;
  address: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  properties: Property[];
  sources: ChatSource[];
}

export interface SavedProperty {
  id: string;
  user_id: string;
  property_id: string;
  notes: string | null;
  label: string | null;
  created_at: string;
  property: Property;
}

// Request bodies
export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SavedCreate {
  property_id: string;
  notes?: string | null;
  label?: string | null;
}

export interface SearchParams {
  city?: string;
  state?: string;
  min_price?: number;
  max_price?: number;
  beds?: number;
  baths?: number;
  min_sqft?: number;
  keywords?: string;
  limit?: number;
  offset?: number;
}
