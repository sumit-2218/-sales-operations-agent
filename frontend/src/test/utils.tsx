import { render } from "@testing-library/react";
import { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { ToastProvider } from "../components/ui";
import { AuthProvider } from "../hooks/useAuth";

export function renderApp(ui: ReactElement, route = "/") {
  return render(<MemoryRouter initialEntries={[route]}><ToastProvider><AuthProvider>{ui}</AuthProvider></ToastProvider></MemoryRouter>);
}

/** Builds an object that axios.isAxiosError() accepts, for testing error handling without a network. */
export function axiosError(status: number | null, detail?: unknown) {
  return Object.assign(new Error("request failed"), { isAxiosError: true, response: status ? { status, data: { detail } } : undefined, config: { url: "/x" } });
}
