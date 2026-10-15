import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ImportPage from "../pages/ImportPage";
import { api } from "../services/api";
import { axiosError, renderApp } from "./utils";

vi.mock("../services/api", () => ({ TOKEN_KEY: "soa_token", download: vi.fn(), api: { previewImport: vi.fn(), confirmImport: vi.fn(), me: vi.fn() } }));
const file = () => new File(["company_name\nAcme\n"], "leads.csv", { type: "text/csv" });
const preview = { headers: ["company_name"], mapping: { company_name: "company_name" }, fields: ["company_name", "email"], total_rows: 2, valid_count: 1, invalid_count: 1, duplicate_count: 0,
  rows: [{ row_number: 2, status: "valid", errors: [], data: { company_name: "Acme", email: null, employee_count: null }, duplicate_of: null },
         { row_number: 3, status: "invalid", errors: ["company_name is required."], data: { company_name: null, email: null, employee_count: null }, duplicate_of: null }] };

describe("ImportPage", () => {
  it("shows valid/invalid counts and row errors after upload", async () => {
    vi.mocked(api.previewImport).mockResolvedValue(preview as never);
    renderApp(<ImportPage />);
    await userEvent.upload(screen.getByLabelText("CSV file"), file());
    expect(await screen.findByText(/1 valid/)).toBeInTheDocument();
    expect(screen.getByText(/1 invalid/)).toBeInTheDocument();
    expect(screen.getByText("company_name is required.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Import 1 lead" })).toBeEnabled();
  });
  it("shows server-side file errors", async () => {
    vi.mocked(api.previewImport).mockRejectedValue(axiosError(422, "The file is empty."));
    renderApp(<ImportPage />);
    await userEvent.upload(screen.getByLabelText("CSV file"), file());
    expect(await screen.findByRole("alert")).toHaveTextContent("The file is empty.");
  });
  it("confirms and shows the summary", async () => {
    vi.mocked(api.previewImport).mockResolvedValue(preview as never);
    vi.mocked(api.confirmImport).mockResolvedValue({ imported: 1, skipped_invalid: 1, skipped_duplicates: 0, excluded_by_user: 0 });
    renderApp(<ImportPage />);
    await userEvent.upload(screen.getByLabelText("CSV file"), file());
    await userEvent.click(await screen.findByRole("button", { name: "Import 1 lead" }));
    expect(await screen.findByText("Import complete")).toBeInTheDocument();
    expect(api.confirmImport).toHaveBeenCalledTimes(1);
  });
});
