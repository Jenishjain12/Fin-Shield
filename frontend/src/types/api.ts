export type RiskCategory = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type ReviewStatus = "unreviewed" | "under_review" | "escalated" | "closed";

export interface Entity {
  id: string;
  entity_type: string;
  raw_value: string;
  normalized_value: string;
  source_text: string;
  extraction_method: string;
  confidence: number;
}

export interface Signal {
  id: string;
  signal_type: string;
  title: string;
  explanation: string;
  evidence: string;
  contribution: number;
  recommendation?: string;
}

export interface Anomaly {
  id: string;
  anomaly_type: string;
  title: string;
  explanation: string;
  evidence: string;
  severity: string;
}

export interface Note {
  id: string;
  content: string;
  created_at: string;
}

export interface Relationship {
  id: string;
  source_ad_id: string;
  target_ad_id: string;
  relationship_type: string;
  evidence: string;
  explanation: string;
  similarity_score: number | null;
}

export interface AdvertisementSummary {
  id: string;
  is_seed: boolean;
  text: string;
  source: string | null;
  source_url: string | null;
  analysis_status: string;
  review_status: ReviewStatus;
  risk_score: number;
  risk_category: RiskCategory;
  created_at: string;
  entity_count: number;
  related_count: number;
}

export interface AdvertisementDetail extends AdvertisementSummary {
  image_filename: string | null;
  ocr_text: string | null;
  ocr_status: string;
  limitations: string | null;
  recommendation: string | null;
  analyzed_at: string | null;
  missing_data_warnings?: string[];
  entities: Entity[];
  signals: Signal[];
  anomalies?: Anomaly[];
  notes: Note[];
  relationships: Relationship[];
}

export interface AlertItem {
  id: string;
  alert_type: string;
  severity: string;
  advertisement_id: string | null;
  campaign_id: string | null;
  reason: string;
  is_read: boolean;
  created_at: string;
}

export interface CampaignSummary {
  id: string;
  label: string;
  member_count: number;
  high_risk_count: number;
  max_risk_score: number;
  member_ids: string[];
}

export interface CampaignDetail extends CampaignSummary {
  advertisements: AdvertisementSummary[];
  relationships: Relationship[];
}

export interface DashboardSummary {
  total_advertisements: number;
  potentially_suspicious: number;
  high_risk: number;
  relationship_count: number;
  seed_advertisement_count: number;
  risk_distribution: Record<string, number>;
  recent_advertisements: AdvertisementSummary[];
  recent_alerts: AlertItem[];
  campaign_activity: CampaignSummary[];
}

export interface PaginatedAds {
  items: AdvertisementSummary[];
  total: number;
  page: number;
  page_size: number;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}
