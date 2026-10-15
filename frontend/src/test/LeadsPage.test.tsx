import { screen } from "@testing-library/react";
import LeadsPage from "../pages/LeadsPage";
import { api } from "../services/api";
import { axiosError, renderApp } from "./utils";

vi.mock("../services/api", () => ({ TOKEN_KEY: "soa_token", download: vi.fn(), api: { leads: vi.fn(), me: vi.fn() } }));

const lead = (id: number, name: string) => ({ id, company_name: name, contact_name: "Lena", email: null, job_title: null, industry: "Software", employee_count: 120, location: "Berlin",
  website: null, annual_revenue: null, description: null, source: "manual", owner_id: 1, status: "new", qualification_category: "strong_match", score: 95, notes: null, created_at: "", updated_at: "" });

describe("LeadsPage", () => {
  it("renders leads from the API", async () => {
    vi.mocked(api.leads).mockResolvedValue({ items: [lead(1, "Acme GmbH"), lead(2, "Beta AG")], total: 2, page: 1, page_size: 20 } as never);
    renderApp(<LeadsPage />, "/leads");
    expect(await screen.findByRole("link", { name: "Acme GmbH" })).toHaveAttribute("href", "/leads/1");
    expect(screen.getByText("Beta AG")).toBeInTheDocument();
    expect(screen.getAllByText("Strong match")).toHaveLength(2);
  });
  it("shows a helpful empty state", async () => {
    vi.mocked(api.leads).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 } as never);
    renderApp(<LeadsPage />, "/leads");
    expect(await screen.findByText("No leads found")).toBeInTheDocument();
  });
  it("shows API errors with a retry button", async () => {
    vi.mocked(api.leads).mockRejectedValue(axiosError(503, "The database is unavailable. Please try again shortly."));
    renderApp(<LeadsPage />, "/leads");
    expect(await screen.findByRole("alert")).toHaveTextContent("database is unavailable");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
