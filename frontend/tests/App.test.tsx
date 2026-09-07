import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import App from "../src/App";

vi.mock("../src/pages/HomePage", () => ({
  default: () => <div>HomePage mock</div>,
}));
vi.mock("../src/pages/TriagePage", () => ({
  default: () => <div>TriagePage mock</div>,
}));
vi.mock("../src/pages/FacilitiesPage", () => ({
  default: () => <div>FacilitiesPage mock</div>,
}));
vi.mock("../src/pages/AdminPage", () => ({
  default: () => <div>AdminPage mock</div>,
}));
vi.mock("../src/pages/NotFoundPage", () => ({
  default: () => <div>NotFoundPage mock</div>,
}));

describe("App smoke test", () => {
  it("renders the site header with brand name", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByText("Rahbar-e-Sehat")).toBeInTheDocument();
  });

  it("renders the non-diagnostic disclaimer in the footer", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );
    expect(
      screen.getByText(/Not a diagnostic tool/i),
    ).toBeInTheDocument();
  });
});
