export interface Building {
  building_id: string;
  street: string;
  house_number: string;
  postal_code: string | null;
  city: string;
  district?: string | null;
  state?: string | null;
  ags?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  property_name?: string | null;
  internal_reference?: string | null;
  notes?: string | null;
}

export interface BuildingCreateInput {
  street: string;
  house_number: string;
  postal_code?: string | null;
  city: string;
  district?: string | null;
  state?: string | null;
  ags?: string | null;
  property_name?: string | null;
  internal_reference?: string | null;
  notes?: string | null;
}

export interface BuildingUpdateInput {
  street?: string;
  house_number?: string;
  postal_code?: string | null;
  city?: string;
  district?: string | null;
  state?: string | null;
  ags?: string | null;
  property_name?: string | null;
  internal_reference?: string | null;
  notes?: string | null;
}

export interface GeoCandidate {
  ags: string;
  ags_kreis: string;
  state_name: string;
  county_name: string | null;
  municipality_name: string;
  municipality_type: string | null;
  postal_code: string | null;
}

export interface GeoResolveResponse {
  status: "MATCHED" | "AMBIGUOUS" | "NOT_FOUND";
  query: { city: string; state?: string | null };
  candidates: GeoCandidate[];
}
