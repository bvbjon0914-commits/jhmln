export interface AuthorityRef {
  authority_id: string;
  authority_name: string;
  city: string | null;
}

export interface DataQualityGroup {
  count: number;
  items: AuthorityRef[];
}

export interface DataQualitySummary {
  total_authorities: number;
  authorities_without_email: DataQualityGroup;
  authorities_without_jurisdiction: DataQualityGroup;
  authorities_without_address: DataQualityGroup;
}
