import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DraftEditor } from "../components/OutreachPanel";
import { api } from "../services/api";
import { axiosError, renderApp } from "./utils";

vi.mock("../services/api", () => ({ TOKEN_KEY: "soa_token", api: { editDraft: vi.fn(), regenerateDraft: vi.fn(), me: vi.fn() } }));
const draft = { id: 5, lead_id: 1, parent_id: null, channel: "email", tone: "professional", length: "short", objective: "intro", subject: "Hello", body: "Original body text.",
  personalization_note: "Used industry.", status: "draft", model_name: "qwen2.5:3b-instruct", created_at: "2026-01-01T00:00:00Z", review_notice: "AI-generated draft. Review and edit before use; nothing is sent automatically." };

describe("DraftEditor", () => {
  it("labels the draft as requiring human review", () => {
    renderApp(<DraftEditor draft={draft} onChanged={() => {}} />);
    expect(screen.getByText(/Review and edit before use/)).toBeInTheDocument();
  });
  it("saves edits through the API", async () => {
    vi.mocked(api.editDraft).mockResolvedValue({ ...draft, body: "My edit" } as never);
    renderApp(<DraftEditor draft={draft} onChanged={() => {}} />);
    const box = screen.getByLabelText("Message");
    await userEvent.clear(box); await userEvent.type(box, "My edit");
    await userEvent.click(screen.getByRole("button", { name: "Save edits" }));
    await waitFor(() => expect(api.editDraft).toHaveBeenCalledWith(5, { body: "My edit", subject: "Hello" }));
  });
  it("refuses to save an empty body", async () => {
    renderApp(<DraftEditor draft={draft} onChanged={() => {}} />);
    await userEvent.clear(screen.getByLabelText("Message"));
    await userEvent.click(screen.getByRole("button", { name: "Save edits" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("cannot be empty");
    expect(api.editDraft).not.toHaveBeenCalled();
  });
  it("shows AI errors with the hint when regenerating fails", async () => {
    vi.mocked(api.regenerateDraft).mockRejectedValue(axiosError(503, { code: "unavailable", message: "The local AI service (Ollama) is not running.", hint: "Start Ollama." }));
    renderApp(<DraftEditor draft={draft} onChanged={() => {}} />);
    await userEvent.click(screen.getByRole("button", { name: "Regenerate" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Start Ollama.");
  });
});
