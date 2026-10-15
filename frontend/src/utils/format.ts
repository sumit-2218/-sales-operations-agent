export const fmtDate = (iso: string | null | undefined) => (iso ? new Date(iso).toLocaleString() : "—");
export const fmtNum = (n: number | null | undefined) => (n == null ? "—" : n.toLocaleString());
export const label = (s: string | null | undefined) => (s ? s.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase()) : "—");
export const splitList = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);
export const emptyToNull = (s: string) => (s.trim() === "" ? null : s.trim());
export const numOrNull = (s: string) => (s.trim() === "" ? null : Number(s));
