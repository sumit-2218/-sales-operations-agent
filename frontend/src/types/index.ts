export type Role = "admin" | "manager" | "sales_rep";
export interface User { id: number; name: string; email: string; role: Role; is_active: boolean; created_at: string }
export interface Page<T> { items: T[]; total: number; page: number; page_size: number }
export type LeadStatus = "new" | "qualified" | "contacted" | "interested" | "meeting_scheduled" | "follow_up_required" | "converted" | "unqualified";
export interface Lead {
  id: number; company_name: string; contact_name: string | null; email: string | null; job_title: string | null;
  industry: string | null; employee_count: number | null; location: string | null; website: string | null;
  annual_revenue: number | null; description: string | null; source: string | null; owner_id: number | null;
  status: LeadStatus; qualification_category: string | null; score: number | null; notes: string | null;
  created_at: string; updated_at: string;
}
export interface Factor { name: string; status: "match" | "partial" | "mismatch" | "missing"; earned: number; max_points: number; detail: string }
export interface Breakdown { score: number; category: string; factors: Factor[]; evaluable_weight_pct: number; exclusion_reasons: string[] }
export interface AiExplanation {
  summary: string; positive_factors: string[]; negative_factors: string[]; missing_information: string[];
  recommended_next_steps: string[]; data_limitations: string[];
}
export interface Analysis {
  id: number; lead_id: number; icp_id: number | null; score: number; category: string; breakdown: Breakdown;
  ai_status: "not_requested" | "completed" | "failed"; ai_explanation: AiExplanation | null; ai_error: string | null;
  model_name: string | null; created_at: string;
}
export interface IcpConfig {
  target_industries: string[]; excluded_industries: string[]; min_employees: number | null; max_employees: number | null;
  target_locations: string[]; min_revenue: number | null; max_revenue: number | null; keywords: string[];
  excluded_keywords: string[]; weights: Record<string, number>; strong_threshold: number; potential_threshold: number;
  min_evaluable_weight_pct: number;
}
export interface Icp { id: number; name: string; owner_id: number; is_active: boolean; config: IcpConfig; explanations: string[] }
export interface Draft {
  id: number; lead_id: number; parent_id: number | null; channel: string; tone: string; length: string; objective: string;
  subject: string | null; body: string; personalization_note: string | null; status: string; model_name: string | null;
  created_at: string; review_notice: string;
}
export interface FollowUp {
  id: number; lead_id: number; assigned_user_id: number | null; title: string; description: string | null; due_at: string;
  priority: "low" | "medium" | "high"; status: "open" | "completed" | "cancelled"; completed_at: string | null; is_overdue: boolean;
}
export interface Activity { id: number; actor_email: string | null; action: string; entity_type: string; lead_id: number | null; meta: Record<string, unknown> | null; created_at: string }
export interface Summary {
  total_leads: number; new_imported_leads: number; qualified_leads: number; review_required_leads: number; unqualified_leads: number;
  unscored_leads: number; by_category: Record<string, number>; by_status: Record<string, number>; outreach_drafts: number;
  pending_follow_ups: number; overdue_follow_ups: number;
  upcoming_follow_ups: { id: number; title: string; lead_id: number; company_name: string; due_at: string; priority: string; is_overdue: boolean }[];
}
export interface ImportRow { row_number: number; status: "valid" | "invalid" | "duplicate"; errors: string[]; data: Record<string, string | number | null>; duplicate_of: string | null }
export interface ImportPreview {
  headers: string[]; mapping: Record<string, string | null>; fields: string[]; total_rows: number; valid_count: number;
  invalid_count: number; duplicate_count: number; rows: ImportRow[];
}
export const STATUSES: LeadStatus[] = ["new", "qualified", "contacted", "interested", "meeting_scheduled", "follow_up_required", "converted", "unqualified"];
