import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import {
  mockApiGet,
  makeApiResponse,
} from "../helpers/mock-api";
import type { AdminStats } from "@/types/api";

import AdminPage from "@/pages/AdminPage";

const sampleStats: AdminStats = {
  total_sessions: 42,
  emergency_cases: 5,
  average_response_time_ms: 1250,
  active_agents: 6,
};

describe("AdminPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows skeleton loading state initially", () => {
    mockApiGet.mockImplementation(() => new Promise(() => {}));
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>,
    );
    const skeleton = screen.getByRole("region", { name: /loading content/i });
    expect(skeleton).toHaveAttribute("aria-busy", "true");
  });

  it("after successful fetch, renders stats values", async () => {
    mockApiGet.mockResolvedValue(makeApiResponse(sampleStats));
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText("42")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument();
      expect(screen.getByText("1250ms")).toBeInTheDocument();
      expect(screen.getByText("6")).toBeInTheDocument();
    });
  });

  it("shows error message on API failure", async () => {
    mockApiGet.mockRejectedValue(new Error("Network error"));
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>,
    );
    await waitFor(() => {
      const error = screen.getByRole("alert");
      expect(error).toHaveTextContent(/unable to load/i);
    });
  });
});
