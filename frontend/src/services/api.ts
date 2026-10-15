import axios from "axios";
import type { Activity, Analysis, Draft, FollowUp, Icp, IcpConfig, ImportPreview, Lead, Page, Summary, User } from "../types";

export const TOKEN_KEY = "soa_token";
const http = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1", timeout: 240000 });

http.interceptors.request.use((cfg) => {
  const t = localStorage.getItem(TOKEN_KEY);
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});
http.interceptors.response.use(undefined, (err) => {
  if (err?.response?.status === 401 && !String(err.config?.url).includes("/auth/login")) {
    localStorage.removeItem(TOKEN_KEY);
    window.dispatchEvent(new Event("auth:expired"));
  }
  return Promise.reject(err);
});

export type Params = Record<string, string | number | boolean | undefined | null>;
const clean = (p?: Params) => Object.fromEntries(Object.entries(p ?? {}).filter(([, v]) => v !== "" && v != null));
const get = async <T,>(url: string, params?: Params) => (await http.get<T>(url, { params: clean(params) })).data;
const send = async <T,>(m: "post" | "patch", url: string, body?: unknown): Promise<T> =>
  (m === "post" ? await http.post<T>(url, body) : await http.patch<T>(url, body)).data;

export async function download(url: string, filename: string, params?: Params) {
  const res = await http.get(url, { responseType: "blob", params: clean(params) });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(res.data);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

async function importFile<T>(mode: "preview" | "confirm", file: File, extra: Record<string, string>): Promise<T> {
  const f = new FormData();
  f.append("file", file);
  Object.entries(extra).forEach(([k, v]) => f.append(k, v));
  return (await http.post<T>(`/imports/${mode}`, f)).data;
}

export const api = {
  login: (email: string, password: string) => send<{ access_token: string; user: User }>("post", "/auth/login", { email, password }),
  googleLogin: (credential: string) => send<{ access_token: string; user: User }>("post", "/auth/google", { credential }),
  sendDraft: (id: number) => send<{ status: string; to: string; draft_id: number; message: string }>("post", `/outreach/${id}/send`, {}),
  register: (name: string, email: string, password: string) => send<User>("post", "/auth/register", { name, email, password }),
  logout: () => send<void>("post", "/auth/logout"),
  me: () => get<User>("/auth/me"),
  updateMe: (b: { name?: string; current_password?: string; new_password?: string }) => send<User>("patch", "/auth/me", b),

  summary: () => get<Summary>("/dashboard/summary"),
  recentActivity: () => get<Activity[]>("/dashboard/activity"),

  leads: (p: Params) => get<Page<Lead>>("/leads", p),
  lead: (id: number) => get<Lead>(`/leads/${id}`),
  createLead: (b: Partial<Lead>) => send<Lead>("post", "/leads", b),
  updateLead: (id: number, b: Partial<Lead>) => send<Lead>("patch", `/leads/${id}`, b),
  deleteLead: async (id: number) => { await http.delete(`/leads/${id}`); },
  leadActivity: (id: number) => get<Page<Activity>>(`/leads/${id}/activity`, { page_size: 30 }),

  score: (id: number) => send<Analysis>("post", `/leads/${id}/score`, {}),
  analyze: (id: number, analysis_id?: number) => send<Analysis>("post", `/leads/${id}/analyze`, analysis_id ? { analysis_id } : {}),
  analyses: (id: number) => get<Page<Analysis>>(`/leads/${id}/analyses`, { page_size: 20 }),

  drafts: (id: number) => get<Page<Draft>>(`/leads/${id}/outreach`, { page_size: 50 }),
  createDraft: (id: number, b: { channel: string; tone: string; length: string; objective: string }) => send<Draft>("post", `/leads/${id}/outreach`, b),
  editDraft: (id: number, b: { subject?: string | null; body?: string; status?: string }) => send<Draft>("patch", `/outreach/${id}`, b),
  regenerateDraft: (id: number) => send<Draft>("post", `/outreach/${id}/regenerate`, {}),

  followUps: (p: Params) => get<Page<FollowUp>>("/follow-ups", p),
  createFollowUp: (b: { lead_id: number; title: string; description?: string | null; due_at: string; priority: string }) => send<FollowUp>("post", "/follow-ups", b),
  updateFollowUp: (id: number, b: Partial<Pick<FollowUp, "title" | "due_at" | "priority" | "status" | "description">>) => send<FollowUp>("patch", `/follow-ups/${id}`, b),

  icps: () => get<Icp[]>("/icp"),
  defaultIcp: () => get<{ config: IcpConfig; explanations: string[] }>("/icp/default-config"),
  createIcp: (b: { name: string; config: IcpConfig; is_active: boolean }) => send<Icp>("post", "/icp", b),
  updateIcp: (id: number, b: { name?: string; config?: IcpConfig; is_active?: boolean }) => send<Icp>("patch", `/icp/${id}`, b),
  deleteIcp: async (id: number) => { await http.delete(`/icp/${id}`); },

  previewImport: (file: File, mapping?: Record<string, string | null>, corrections?: Record<string, Record<string, string>>) =>
    importFile<ImportPreview>("preview", file, {
      ...(mapping ? { mapping: JSON.stringify(mapping) } : {}), ...(corrections ? { corrections: JSON.stringify(corrections) } : {}) }),
  confirmImport: (file: File, mapping: Record<string, string | null>, corrections: Record<string, Record<string, string>>, exclude: number[]) =>
    importFile<{ imported: number; skipped_invalid: number; skipped_duplicates: number; excluded_by_user: number }>("confirm", file, {
      mapping: JSON.stringify(mapping), corrections: JSON.stringify(corrections), exclude_rows: JSON.stringify(exclude) }),

  adminUsers: () => get<Page<User>>("/admin/users", { page_size: 100 }),
  adminUpdateUser: (id: number, b: { role?: string; is_active?: boolean }) => send<User>("patch", `/admin/users/${id}`, b),
  adminStatus: () => get<{ application: { status: string }; database: { status: string; message: string };
    ai: { reachable: boolean; model_available: boolean; model: string; base_url: string; message: string };
    config: { model: string; ollama_base_url: string; registration_enabled: boolean; max_upload_mb: number } }>("/admin/system-status"),
  adminStats: () => get<Record<string, any>>("/admin/statistics"),
  adminActivity: (p: Params) => get<Page<Activity>>("/admin/activity", p),
};
