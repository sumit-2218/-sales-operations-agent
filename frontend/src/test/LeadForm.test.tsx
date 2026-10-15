import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LeadFormPage, { validateLead } from "../pages/LeadFormPage";
import { api } from "../services/api";
import { renderApp } from "./utils";

vi.mock("../services/api", () => ({ TOKEN_KEY: "soa_token", api: { createLead: vi.fn(), me: vi.fn() } }));
const blank = { company_name: "", contact_name: "", email: "", job_title: "", industry: "", employee_count: "", location: "", website: "", annual_revenue: "", description: "", notes: "" };

describe("lead form validation", () => {
  it("requires only the company name", () => expect(validateLead({ ...blank, company_name: "X" })).toEqual({}));
  it("flags bad email and negative/non-numeric numbers", () => {
    expect(validateLead({ ...blank, company_name: "X", email: "nope", employee_count: "-3", annual_revenue: "abc" })).toEqual({
      email: "Enter a valid email address", employee_count: "Enter a whole number (0 or more)", annual_revenue: "Enter a whole number (0 or more)" });
  });
  it("blocks submit and shows messages", async () => {
    renderApp(<LeadFormPage />, "/leads/new");
    await userEvent.click(screen.getByRole("button", { name: "Save lead" }));
    expect(await screen.findByText("Company name is required")).toBeInTheDocument();
    expect(api.createLead).not.toHaveBeenCalled();
  });
});
