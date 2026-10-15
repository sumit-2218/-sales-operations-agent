import axios from "axios";

export interface ApiProblem { message: string; hint?: string; code?: string; status?: number }

/** Turns any thrown value (FastAPI validation arrays, AI error objects, network failures) into readable text. */
export function apiProblem(err: unknown): ApiProblem {
  if (axios.isAxiosError(err)) {
    if (!err.response) return { message: "Cannot reach the server. Check that the backend is running.", code: "network" };
    const { status, data } = err.response;
    const d = data?.detail;
    if (typeof d === "string") return { message: d, status };
    if (Array.isArray(d)) {
      const msg = d.map((e: { loc?: (string | number)[]; msg: string }) =>
        `${(e.loc ?? []).filter((x) => x !== "body").join(".")}: ${e.msg}`).join("; ");
      return { message: msg || "Invalid input", status };
    }
    if (d && typeof d === "object" && "message" in d) return { message: d.message, hint: d.hint, code: d.code, status };
    return { message: `Request failed (HTTP ${status})`, status };
  }
  return { message: err instanceof Error ? err.message : "Something went wrong" };
}
export const apiErrorMessage = (err: unknown) => apiProblem(err).message;
