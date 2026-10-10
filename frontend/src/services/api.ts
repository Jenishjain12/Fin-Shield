import type {
  AdvertisementDetail,
  AlertItem,
  CampaignDetail,
  CampaignSummary,
  DashboardSummary,
  Note,
  PaginatedAds,
  Relationship,
  ReviewStatus,
} from "../types/api";
import { ApiError } from "../types/api";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, init);
  } catch {
    throw new ApiError(0, "FIN-SHIELD backend is unavailable. Start the API on port 8000.");
  }
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string | Array<{ msg: string }> };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* use default */
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),
  dashboard: () => request<DashboardSummary>("/api/dashboard/summary"),
  ads: (params: Record<string, string | number | undefined>) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== "") query.set(key, String(value));
    });
    return request<PaginatedAds>(`/api/ads?${query.toString()}`);
  },
  ad: (id: string) => request<AdvertisementDetail>(`/api/ads/${id}`),
  relationships: (id: string) => request<Relationship[]>(`/api/ads/${id}/relationships`),
  analyze: (form: FormData) =>
    request<AdvertisementDetail>("/api/analyze", { method: "POST", body: form }),
  campaigns: () => request<CampaignSummary[]>("/api/campaigns"),
  campaign: (id: string) => request<CampaignDetail>(`/api/campaigns/${id}`),
  alerts: () => request<AlertItem[]>("/api/alerts"),
  markAlert: (id: string, is_read: boolean) =>
    request<AlertItem>(`/api/alerts/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_read }),
    }),
  updateReview: (id: string, review_status: ReviewStatus) =>
    request<AdvertisementDetail>(`/api/ads/${id}/review`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review_status }),
    }),
  addNote: (id: string, content: string) =>
    request<Note>(`/api/ads/${id}/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    }),
};
