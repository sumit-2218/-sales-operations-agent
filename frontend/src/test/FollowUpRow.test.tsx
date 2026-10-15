import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import FollowUpRow from "../components/FollowUpRow";
import { api } from "../services/api";
import { renderApp } from "./utils";

vi.mock("../services/api", () => ({ TOKEN_KEY: "soa_token", api: { updateFollowUp: vi.fn(), me: vi.fn() } }));
const f = { id: 7, lead_id: 3, assigned_user_id: 1, title: "Call Lena", description: null, due_at: "2020-01-01T10:00:00Z", priority: "high" as const, status: "open" as const, completed_at: null, is_overdue: true };

describe("FollowUpRow", () => {
  it("marks overdue tasks and completes them via the API", async () => {
    vi.mocked(api.updateFollowUp).mockResolvedValue({ ...f, status: "completed" } as never);
    const onChanged = vi.fn();
    renderApp(<ul><FollowUpRow f={f} onChanged={onChanged} /></ul>);
    expect(screen.getByText(/overdue/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Complete" }));
    await waitFor(() => expect(api.updateFollowUp).toHaveBeenCalledWith(7, { status: "completed" }));
    await waitFor(() => expect(onChanged).toHaveBeenCalled());
  });
  it("cancels a task", async () => {
    vi.mocked(api.updateFollowUp).mockResolvedValue({ ...f, status: "cancelled" } as never);
    renderApp(<ul><FollowUpRow f={f} onChanged={() => {}} /></ul>);
    await userEvent.click(screen.getByRole("button", { name: "Cancel task" }));
    await waitFor(() => expect(api.updateFollowUp).toHaveBeenCalledWith(7, { status: "cancelled" }));
  });
  it("offers no complete button for finished tasks", () => {
    renderApp(<ul><FollowUpRow f={{ ...f, status: "completed", is_overdue: false }} onChanged={() => {}} /></ul>);
    expect(screen.queryByRole("button", { name: "Complete" })).not.toBeInTheDocument();
  });
});
