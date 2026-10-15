import { apiProblem } from "../utils/errors";
import { axiosError } from "./utils";

describe("apiProblem", () => {
  it("reads string details", () => expect(apiProblem(axiosError(409, "Duplicate lead")).message).toBe("Duplicate lead"));
  it("flattens FastAPI validation arrays", () => {
    const p = apiProblem(axiosError(422, [{ loc: ["body", "email"], msg: "Enter a valid email address" }]));
    expect(p.message).toBe("email: Enter a valid email address");
  });
  it("keeps AI error code and hint", () => {
    const p = apiProblem(axiosError(503, { code: "unavailable", message: "Ollama is not running", hint: "ollama serve" }));
    expect(p).toMatchObject({ code: "unavailable", hint: "ollama serve", status: 503 });
  });
  it("explains network failures", () => expect(apiProblem(axiosError(null)).message).toMatch(/Cannot reach the server/));
});
