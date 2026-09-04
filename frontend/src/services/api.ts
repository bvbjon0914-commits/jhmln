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
import type { Case, CaseListItem, CaseDetail } from "../types/case";
import type { InboundEmailEntry, AktenzeichenLookupResult } from "../types/mailbox";

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

  async previewImport(file: File, sheet?: string): Promise<ImportPreview> {
    const form = new FormData();
    form.append("file", file);
    if (sheet) form.append("sheet", sheet);
    const { data } = await client.post<ImportPreview>("/import/preview", form);
    return data;
  },

  async importBuildings(file: File, mapping: Record<string, string>, sheet?: string): Promise<ImportSummary> {
    const form = new FormData();
    form.append("file", file);
    form.append("mapping", JSON.stringify(mapping));
    if (sheet) form.append("sheet", sheet);
    const { data } = await client.post<ImportSummary>("/import/buildings", form);
    return data;
  },

  async importAuthorities(
    file: File,
    mapping: Record<string, string>,
    fillGaps = false,
    sheet?: string
  ): Promise<ImportSummary> {
    const form = new FormData();
    form.append("file", file);
    form.append("mapping", JSON.stringify(mapping));
    form.append("fill_gaps", String(fillGaps));
    if (sheet) form.append("sheet", sheet);
    const { data } = await client.post<ImportSummary>("/import/authorities", form);
    return data;
  },

  async importJurisdictions(
    file: File,
    mapping: Record<string, string>,
    requestTypeId: string,
    sheet?: string
  ): Promise<ImportSummary> {
    const form = new FormData();
    form.append("file", file);
    form.append("mapping", JSON.stringify(mapping));
    form.append("request_type_id", requestTypeId);
    if (sheet) form.append("sheet", sheet);
    const { data } = await client.post<ImportSummary>("/import/jurisdictions", form);
    return data;
  },

  // ========== Verwaltung: Gebäude ==========

  async listBuildingsPaged(params: {
    search?: string;
    state?: string;
    ags?: string;
    missing_ags?: boolean;
    duplicate_only?: boolean;
    review_required_only?: boolean;
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
    state?: string;
    has_email?: boolean;
    duplicate_only?: boolean;
    unverified_only?: boolean;
    without_jurisdiction_only?: boolean;
    without_address_only?: boolean;
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
    state?: string;
    municipality?: string;
    district?: string;
    duplicate_only?: boolean;
    orphaned_only?: boolean;
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
    status?: string;
    date_from?: string;
    date_to?: string;
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

  async clearBadGeocoding(): Promise<{ deleted: number }> {
    const { data } = await client.post<{ deleted: number }>("/data-quality/clear-bad-geocoding");
    return data;
  },

  async mergeDuplicateAuthorities(): Promise<{ merged_groups: number; removed: number; needs_review: number }> {
    const { data } = await client.post<{ merged_groups: number; removed: number; needs_review: number }>(
      "/data-quality/merge-duplicate-authorities"
    );
    return data;
  },

  async deleteReviewRequiredBuildings(): Promise<{ deleted: number; skipped: number }> {
    const { data } = await client.post<{ deleted: number; skipped: number }>(
      "/data-quality/delete-review-required-buildings"
    );
    return data;
  },

  async mergeDuplicateJurisdictions(): Promise<{ merged_groups: number; removed: number; needs_review: number }> {
    const { data } = await client.post<{ merged_groups: number; removed: number; needs_review: number }>(
      "/data-quality/merge-duplicate-jurisdictions"
    );
    return data;
  },

  async mergeDuplicateBuildings(): Promise<{ merged_groups: number; removed: number; needs_review: number }> {
    const { data } = await client.post<{ merged_groups: number; removed: number; needs_review: number }>(
      "/data-quality/merge-duplicate-buildings"
    );
    return data;
  },

  // ========== Aufträge (Cases) ==========

  async listCasesPaged(params: {
    search?: string;
    limit: number;
    offset: number;
  }): Promise<Paged<CaseListItem>> {
    const { data, headers } = await client.get<CaseListItem[]>("/cases", { params });
    return paged(data, headers);
  },

  async createCase(input: { name: string; notes?: string | null }): Promise<Case> {
    const { data } = await client.post<Case>("/cases", input);
    return data;
  },

  async getCase(caseId: string): Promise<CaseDetail> {
    const { data } = await client.get<CaseDetail>(`/cases/${caseId}`);
    return data;
  },

  async updateCase(
    caseId: string,
    patch: { name?: string; notes?: string | null; status?: "OPEN" | "CLOSED" }
  ): Promise<Case> {
    const { data } = await client.put<Case>(`/cases/${caseId}`, patch);
    return data;
  },

  async deleteCase(caseId: string): Promise<void> {
    await client.delete(`/cases/${caseId}`);
  },

  async addBuildingToCase(caseId: string, buildingId: string): Promise<void> {
    await client.post(`/cases/${caseId}/buildings`, { building_id: buildingId });
  },

  async removeBuildingFromCase(caseId: string, buildingId: string): Promise<void> {
    await client.delete(`/cases/${caseId}/buildings/${buildingId}`);
  },

  async linkRequestToCase(caseId: string, requestId: string): Promise<void> {
    await client.post(`/cases/${caseId}/link-request`, { request_id: requestId });
  },

  async sendBundle(
    caseId: string,
    requestItemIds: string[]
  ): Promise<{ sent: number; dry_run: boolean; mailgun_message_id: string | null }> {
    const { data } = await client.post(`/cases/${caseId}/send-bundle`, {
      request_item_ids: requestItemIds,
    });
    return data;
  },

  async markItemSent(requestItemId: string): Promise<void> {
    await client.put(`/matching/items/${requestItemId}/mark-sent`);
  },

  async uploadItemResponse(requestItemId: string, file: File): Promise<void> {
    const form = new FormData();
    form.append("file", file);
    await client.post(`/matching/items/${requestItemId}/upload-response`, form);
  },

  async markItemReviewed(requestItemId: string): Promise<void> {
    await client.put(`/matching/items/${requestItemId}/mark-reviewed`);
  },

  itemResponseDownloadUrl(requestItemId: string): string {
    return `/api/matching/items/${requestItemId}/response-download`;
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

  // ========== Postfach (Phase 6: eingehende Antworten) ==========

  async listPendingInboundEmails(): Promise<InboundEmailEntry[]> {
    const { data } = await client.get<InboundEmailEntry[]>("/mailbox/inbound/pending");
    return data;
  },

  inboundAttachmentDownloadUrl(attachmentId: number): string {
    return `/api/mailbox/inbound/attachments/${attachmentId}/download`;
  },

  async lookupAktenzeichen(query: string): Promise<AktenzeichenLookupResult[]> {
    const { data } = await client.get<AktenzeichenLookupResult[]>("/mailbox/lookup-aktenzeichen", {
      params: { q: query },
    });
    return data;
  },

  async assignInboundEmail(
    inboundId: number,
    requestItemId: string,
    attachmentId?: number
  ): Promise<void> {
    await client.post(`/mailbox/inbound/${inboundId}/assign`, {
      request_item_id: requestItemId,
      attachment_id: attachmentId,
    });
  },
};
