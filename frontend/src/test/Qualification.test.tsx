import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import QualificationPanel from "../components/QualificationPanel";
import { api } from "../services/api";
import { axiosError, renderApp } from "./utils";

vi.mock("../services/api", () => ({ TOKEN_KEY: "soa_token", api: { analyses: vi.fn(), score: vi.fn(), analyze: vi.fn(), me: vi.fn() } }));
const analysis = { id: 9, lead_id: 1, icp_id: null, score: 72, category: "potential_match", ai_status: "not_requested", ai_explanation: null, ai_error: null, model_name: null, created_at: "2026-01-01T00:00:00Z",
  breakdown: { score: 72, category: "potential_match", evaluable_weight_pct: 90, exclusion_reasons: [], factors: [
    { name: "industry", status: "match", earned: 30, max_points: 30, detail: "Industry 'Software' is a target industry" },
    { name: "revenue", status: "missing", earned: 0, max_points: 10, detail: "Revenue not provided" }] } };

describe("QualificationPanel", () => {
  it("shows the deterministic breakdown and treats missing data separately", async () => {
    vi.mocked(api.analyses).mockResolvedValue({ items: [analysis], total: 1, page: 1, page_size: 20 } as never);
    renderApp(<QualificationPanel leadId={1} onChanged={() => {}} />);
    expect(await screen.findByText("Industry 'Software' is a target industry")).toBeInTheDocument();
    expect(screen.getByText("Missing")).toBeInTheDocument();
    expect(screen.getByText(/not counted as a mismatch/)).toBeInTheDocument();
  });
  it("reports an unavailable AI service without losing the score", async () => {
    vi.mocked(api.analyses).mockResolvedValue({ items: [analysis], total: 1, page: 1, page_size: 20 } as never);
    vi.mocked(api.analyze).mockRejectedValue(axiosError(503, { code: "unavailable", message: "The local AI service (Ollama) is not running.", hint: "Run ollama serve" }));
    renderApp(<QualificationPanel leadId={1} onChanged={() => {}} />);
    await userEvent.click(await screen.findByRole("button", { name: "Generate AI explanation" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Run ollama serve");
    expect(screen.getByText(/Score/)).toBeInTheDocument();
  });
});
