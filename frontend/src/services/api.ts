import axios from "axios";
import type {
  Building,
  BuildingCreateInput,
  BuildingUpdateInput,
  GeoResolveResponse,
} from "../types/building";
import type { Authority, AuthorityUpdateInput } from "../types/authority";
import type { Jurisdiction, JurisdictionUpdateInput } from "../types/jurisdiction";
import type { RequestRecord } from "../types/request";
import type {
  RequestType,
  MatchingResponse,
  DocumentGenerationResponse,
} from "../types/matching";
import type { ImportPreview, ImportSummary } from "../types/import";
import type { AuthStatus } from "../types/auth";
import type { DataQualitySummary } from "../types/dataQuality";

const client = axios.create({
  baseURL: "/api",
  withCredentials: true,
  // Verhindert, dass der Browser GET-Antworten (insb. bei Proxy-/Deploy-Übergängen
  // fälschlich gecachte HTML-Fallbacks) heuristisch zwischenspeichert.
  headers: { "Cache-Control": "no-cache" },
});

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler;
}

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && onUnauthorized) {
      onUnauthorized();
    }
    return Promise.reject(error);
  }
);

export interface Paged<T> {
  items: T[];
  total: number;
}

function paged<T>(data: T[], headers: Record<string, unknown>): Paged<T> {
  const totalHeader = headers["x-total-count"];
  const total = typeof totalHeader === "string" ? parseInt(totalHeader, 10) : data.length;
  return { items: data, total: Number.isNaN(total) ? data.length : total };
}

export const api = {
  async searchBuildings(query: string): Promise<Building[]> {
    const { data } = await client.get<Building[]>("/buildings", {
      params: query ? { search: query } : {},
    });
    return data;
  },

  async getBuilding(buildingId: string): Promise<Building> {
    const { data } = await client.get<Building>(`/buildings/${buildingId}`);
    return data;
  },

  async createBuilding(building: BuildingCreateInput): Promise<Building> {
    const { data } = await client.post<Building>("/buildings", building);
    return data;
  },

  async resolveAgs(city: string, state?: string): Promise<GeoResolveResponse> {
    const { data } = await client.get<GeoResolveResponse>("/geo/resolve-ags", {
      params: state ? { city, state } : { city },
    });
    return data;
  },

  async geocodeBuilding(buildingId: string): Promise<{ latitude: number; longitude: number }> {
    const { data } = await client.post<{ latitude: number; longitude: number }>(
      `/geo/geocode-building/${buildingId}`
    );
    return data;
  },

  async getAuthorityLocation(authorityId: string): Promise<{ latitude: number; longitude: number }> {
    const { data } = await client.get<{ latitude: number; longitude: number }>(
      `/geo/authority-location/${authorityId}`
    );
    return data;
  },

  async getAdministrativeUnitArea(
    ags: string
  ): Promise<{ ags: string; municipality_name: string; area_km2: number | null; approx_radius_meters: number | null }> {
    const { data } = await client.get(`/geo/administrative-unit/${ags}`);
    return data;
  },

  async listRequestTypes(): Promise<RequestType[]> {
    const { data } = await client.get<RequestType[]>("/request-types");
    return data;
  },

  async listAuthorities(search?: string): Promise<Authority[]> {
    const { data } = await client.get<Authority[]>("/authorities", {
      params: search ? { search } : {},
    });
    return data;
  },

  async getAuthority(authorityId: string): Promise<Authority> {
    const { data } = await client.get<Authority>(`/authorities/${authorityId}`);
    return data;
  },

  async getAuthorities(authorityIds: string[]): Promise<Authority[]> {
    const uniqueIds = [...new Set(authorityIds)];
    if (uniqueIds.length === 0) return [];
    const { data } = await client.get<Authority[]>("/authorities", {
      params: { ids: uniqueIds.join(",") },
    });
    return data;
  },

  async runMatching(
    buildingId: string,
    requestTypeIds: string[]
  ): Promise<MatchingResponse> {
    const { data } = await client.post<MatchingResponse>("/matching", {
      building_id: buildingId,
      request_type_ids: requestTypeIds,
    });
    return data;
  },

  async assignAuthority(
    requestItemId: string,
    authorityId: string,
    reason: string
  ): Promise<void> {
    await client.put(`/matching/items/${requestItemId}/assign`, {
      authority_id: authorityId,
      reason,
    });
  },

  async generateDocuments(
    requestId: string,
    options?: { retryFailedOnly?: boolean }
  ): Promise<DocumentGenerationResponse> {
    const { data } = await client.post<DocumentGenerationResponse>(
      "/documents/generate",
      { request_id: requestId, retry_failed_only: options?.retryFailedOnly ?? false }
    );
    return data;
  },

  downloadDocumentUrl(requestItemId: string): string {
    return `/api/documents/${requestItemId}/download`;
  },

  downloadAllUrl(requestId: string): string {
    return `/api/documents/request/${requestId}/download-all`;
  },

  downloadAllCombinedUrl(requestIds: string[]): string {
    return `/api/documents/download-all-combined?request_ids=${encodeURIComponent(requestIds.join(","))}`;
  },

  exportResultsCsvUrl(requestIds: string[]): string {
    return `/api/matching/export-csv?request_ids=${encodeURIComponent(requestIds.join(","))}`;
  },

  async previewImport(file: File): Promise<ImportPreview> {
    const form = new FormData();
    form.append("file", file);
    const { data } = await client.post<ImportPreview>("/import/preview", form);
    return data;
  },

  async importBuildings(file: File, mapping: Record<string, string>): Promise<ImportSummary> {
    const form = new FormData();
    form.append("file", file);
    form.append("mapping", JSON.stringify(mapping));
    const { data } = await client.post<ImportSummary>("/import/buildings", form);
    return data;
  },

  async importAuthorities(file: File, mapping: Record<string, string>): Promise<ImportSummary> {
    const form = new FormData();
    form.append("file", file);
    form.append("mapping", JSON.stringify(mapping));
    const { data } = await client.post<ImportSummary>("/import/authorities", form);
    return data;
  },

  async importJurisdictions(
    file: File,
    mapping: Record<string, string>,
    requestTypeId: string
  ): Promise<ImportSummary> {
    const form = new FormData();
    form.append("file", file);
    form.append("mapping", JSON.stringify(mapping));
    form.append("request_type_id", requestTypeId);
    const { data } = await client.post<ImportSummary>("/import/jurisdictions", form);
    return data;
  },

  // ========== Verwaltung: Gebäude ==========

  async listBuildingsPaged(params: {
    search?: string;
    limit: number;
    offset: number;
  }): Promise<Paged<Building>> {
    const { data, headers } = await client.get<Building[]>("/buildings", { params });
    return paged(data, headers);
  },

  async updateBuilding(buildingId: string, patch: BuildingUpdateInput): Promise<Building> {
    const { data } = await client.put<Building>(`/buildings/${buildingId}`, patch);
    return data;
  },

  async deleteBuilding(buildingId: string): Promise<void> {
    await client.delete(`/buildings/${buildingId}`);
  },

  // ========== Verwaltung: Behörden ==========

  async listAuthoritiesPaged(params: {
    search?: string;
    active_only: boolean;
    limit: number;
    offset: number;
  }): Promise<Paged<Authority>> {
    const { data, headers } = await client.get<Authority[]>("/authorities", { params });
    return paged(data, headers);
  },

  async updateAuthority(authorityId: string, patch: AuthorityUpdateInput): Promise<Authority> {
    const { data } = await client.put<Authority>(`/authorities/${authorityId}`, patch);
    return data;
  },

  async deleteAuthority(authorityId: string): Promise<void> {
    await client.delete(`/authorities/${authorityId}`);
  },

  // ========== Verwaltung: Zuständigkeiten ==========

  async listJurisdictionsPaged(params: {
    request_type_id?: string;
    authority_id?: string;
    ags?: string;
    active_only: boolean;
    limit: number;
    offset: number;
  }): Promise<Paged<Jurisdiction>> {
    const { data, headers } = await client.get<Jurisdiction[]>("/jurisdictions", { params });
    return paged(data, headers);
  },

  async updateJurisdiction(
    jurisdictionId: string,
    patch: JurisdictionUpdateInput
  ): Promise<Jurisdiction> {
    const { data } = await client.put<Jurisdiction>(`/jurisdictions/${jurisdictionId}`, patch);
    return data;
  },

  async deleteJurisdiction(jurisdictionId: string): Promise<void> {
    await client.delete(`/jurisdictions/${jurisdictionId}`);
  },

  // ========== Verwaltung: Anfragen ==========

  async listRequestsPaged(params: {
    building_id?: string;
    orphaned_only?: boolean;
    limit: number;
    offset: number;
  }): Promise<Paged<RequestRecord>> {
    const { data, headers } = await client.get<RequestRecord[]>("/requests", { params });
    return paged(data, headers);
  },

  async deleteRequest(requestId: string): Promise<void> {
    await client.delete(`/requests/${requestId}`);
  },

  async purgeOrphanedRequests(): Promise<{ deleted: number }> {
    const { data } = await client.post<{ deleted: number }>("/requests/purge-orphaned");
    return data;
  },

  // ========== Verwaltung: Datenqualität ==========

  async getDataQualitySummary(): Promise<DataQualitySummary> {
    const { data } = await client.get<DataQualitySummary>("/data-quality/summary");
    return data;
  },

  exportDataQualityXlsxUrl(): string {
    return "/api/data-quality/export-xlsx";
  },

  // ========== Auth ==========

  async authStatus(): Promise<AuthStatus> {
    const { data } = await client.get<AuthStatus>("/auth/status");
    return data;
  },

  async login(password: string): Promise<{ is_main: boolean }> {
    const { data } = await client.post<{ is_main: boolean }>("/auth/login", { password });
    return data;
  },

  async logout(): Promise<void> {
    await client.post("/auth/logout");
  },

  async setLoginRequired(enabled: boolean): Promise<{ login_required: boolean }> {
    const { data } = await client.put<{ login_required: boolean }>(
      "/auth/settings/login-required",
      { enabled }
    );
    return data;
  },
};
