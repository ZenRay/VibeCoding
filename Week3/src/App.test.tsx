import { render, screen } from "@testing-library/react";
import { act } from "react";
import { vi } from "vitest";
import App from "./App";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: vi.fn(),
  isTauri: vi.fn(() => false),
}));
vi.mock("@tauri-apps/api/event", () => ({
  listen: vi.fn(() => Promise.resolve(() => {})),
}));

describe("App", () => {
  it("renders heading", async () => {
    await act(async () => {
      render(<App />);
    });
    expect(screen.getByRole("heading", { name: /scribeflow/i })).toBeInTheDocument();
  });
});
