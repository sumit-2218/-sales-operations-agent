import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LoginPage from "../pages/LoginPage";
import { api } from "../services/api";
import { axiosError, renderApp } from "./utils";

vi.mock("../services/api", () => ({ TOKEN_KEY: "soa_token", api: { login: vi.fn(), me: vi.fn(), logout: vi.fn() } }));

beforeEach(() => { vi.clearAllMocks(); localStorage.clear(); });

describe("LoginPage", () => {
  it("validates empty and malformed input without calling the API", async () => {
    renderApp(<LoginPage />);
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByText("Email is required")).toBeInTheDocument();
    expect(screen.getByText("Password is required")).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Email"), "not-an-email");
    await userEvent.type(screen.getByLabelText("Password"), "x");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByText("Enter a valid email address")).toBeInTheDocument();
    expect(api.login).not.toHaveBeenCalled();
  });
  it("shows the server's error for bad credentials", async () => {
    vi.mocked(api.login).mockRejectedValue(axiosError(401, "Incorrect email or password"));
    renderApp(<LoginPage />);
    await userEvent.type(screen.getByLabelText("Email"), "a@b.co");
    await userEvent.type(screen.getByLabelText("Password"), "wrongpass");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Incorrect email or password");
  });
  it("stores the token on success", async () => {
    vi.mocked(api.login).mockResolvedValue({ access_token: "tok", user: { id: 1, name: "A", email: "a@b.co", role: "sales_rep", is_active: true, created_at: "" } });
    renderApp(<LoginPage />);
    await userEvent.type(screen.getByLabelText("Email"), "a@b.co");
    await userEvent.type(screen.getByLabelText("Password"), "Password123");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(localStorage.getItem("soa_token")).toBe("tok"));
  });
});
