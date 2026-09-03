export interface AuthorityRef {
  authority_id: string;
  authority_name: string;
  city: string | null;
}

export interface BuildingRef {
  building_id: string;
  street: string | null;
  house_number: string | null;
  postal_code: string | null;
  city: string | null;
}

export interface DataQualityGroup {
  count: number;
  items: AuthorityRef[];
}

export interface DuplicateAuthorityGroup extends DataQualityGroup {
  needs_review_count: number;
}

export interface BuildingsReviewRequiredGroup {
  count: number;
  items: BuildingRef[];
  needs_review_count: number;
}

export interface DataQualitySummary {
  total_authorities: number;
  authorities_without_email: DataQualityGroup;
  authorities_without_jurisdiction: DataQualityGroup;
  authorities_without_address: DataQualityGroup;
  duplicate_authorities: DuplicateAuthorityGroup;
  buildings_review_required: BuildingsReviewRequiredGroup;
}
