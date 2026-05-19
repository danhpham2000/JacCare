export type IntakePayload = {
  zip_code: string;
  insurance_status: string;
  insurance_provider: string;
  insurance_plan: string;
  member_id: string;
  budget: number;
  language: string;
  transport_mode: string;
  care_need: string;
  urgency: string;
  household: string;
};

export type AppUser = {
  id: number;
  full_name: string;
  email: string;
  created_at: string;
  profile: IntakePayload;
};

export type AuthResponse = {
  token: string;
  user: AppUser;
};

export type ClinicOption = {
  id: string;
  name: string;
  address: string;
  estimated_cost: string;
  distance: string;
  latitude: number;
  longitude: number;
  score: number;
  accepts_uninsured: boolean;
  sliding_scale: boolean;
  languages: string[];
  phone: string;
  website: string;
  last_updated?: string;
  reason: string;
  insurance_verification?: InsuranceCheck;
  score_breakdown: Record<string, number>;
  transportation?: TransportRoute;
};

export type InsuranceCheck = {
  status: string;
  message: string;
  member_id_check: {
    status: string;
    message: string;
  };
};

export type TransportRoute = {
  id: string;
  name: string;
  estimated_time: string;
  estimated_cost: number;
  accessibility: string;
  route_summary: string;
};

export type CityService = {
  id: string;
  name: string;
  category: string;
  description: string;
  eligibility: string;
  documents_required: string[];
  phone: string;
  match_score: number;
  eligibility_note: string;
};

export type PharmacyOption = {
  id: string;
  name: string;
  discount_available: boolean;
  generic_support: boolean;
  distance: string;
  latitude: number;
  longitude: number;
  score: number;
  phone: string;
  website: string;
};

export type GraphData = {
  nodes: Array<{ id: string; label: string; type: string; score?: number; detail?: string; latitude?: number; longitude?: number }>;
  edges: Array<{ source: string; target: string; label: string; weight?: number }>;
};

export type LocalizedPlan = {
  summary: string;
  safety_message: string;
  steps: string[];
  call_script: string;
  documents_needed: string[];
  disclaimer: string;
};

export type RuntimeConfig = {
  mapkit_token: string | null;
  neo4j: {
    enabled: boolean;
    connected: boolean;
    database?: string;
    error?: string;
  };
};

export type LiveEligibilitySource = {
  title: string;
  url: string;
  snippet: string;
};

export type LiveEligibility = {
  available: boolean;
  summary: string;
  sources: LiveEligibilitySource[];
  query?: string;
  error?: string;
};

export type CarePlan = {
  user: IntakePayload & { user_id: string; latitude: number; longitude: number };
  safety: {
    safety_level: string;
    message: string;
    red_flags: string[];
  };
  summary: string;
  translated_summary: string;
  insurance_verification: {
    recommended: InsuranceCheck;
    backup: InsuranceCheck;
  };
  recommended_clinic: ClinicOption;
  backup_clinic: ClinicOption;
  top_options: ClinicOption[];
  documents_needed: string[];
  city_services: CityService[];
  pharmacy_options: PharmacyOption[];
  prescription_savings: PharmacyOption;
  transportation: TransportRoute;
  call_script: string;
  translated_call_script: string;
  steps: string[];
  disclaimer: string;
  translations: Record<string, LocalizedPlan>;
  live_eligibility: LiveEligibility;
  graph: GraphData;
  run_id: number;
};

export type HistoryItem = {
  id: number;
  summary: string;
  recommended_clinic: string | null;
  backup_clinic: string | null;
  payload_json: string;
  created_at: string;
};
