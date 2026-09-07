import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

import {
  mockApiPost,
  makeApiResponse,
} from "../helpers/mock-api";
import type { FacilitySearchResult } from "@/types/api";

import FacilitiesPage from "@/pages/FacilitiesPage";

const sampleSearchResult: FacilitySearchResult = {
  facilities: [
    {
      facility_id: "BHU-001",
      name: "Test BHU",
      facility_type: "BHU",
      address: "123 Test Street",
      distance_km: 2.5,
      services_available: ["General care", "Vaccination"],
      emergency_capable: false,
      phone_number: "+92-300-1234567",
    },
    {
      facility_id: "DHQ-001",
      name: "District Hospital",
      facility_type: "DHQ",
      address: "456 Main Road",
      distance_km: 8.3,
      services_available: ["Emergency", "Surgery"],
      emergency_capable: true,
    },
  ],
  total_count: 2,
  search_radius_km: 50,
};

describe("FacilitiesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders location input fields and search button", () => {
    render(
      <MemoryRouter>
        <FacilitiesPage />
      </MemoryRouter>,
    );
    expect(screen.getByLabelText(/latitude/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/longitude/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /^search$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /use my gps location/i }),
    ).toBeInTheDocument();
  });

  it("calls POST /facilities/search with correct lat/lng when search is triggered", async () => {
    mockApiPost.mockResolvedValue(makeApiResponse(sampleSearchResult));
    render(
      <MemoryRouter>
        <FacilitiesPage />
      </MemoryRouter>,
    );
    const latInput = screen.getByLabelText(/latitude/i);
    const lngInput = screen.getByLabelText(/longitude/i);
    await userEvent.clear(latInput);
    await userEvent.type(latInput, "33.6844");
    await userEvent.clear(lngInput);
    await userEvent.type(lngInput, "73.0479");
    fireEvent.click(screen.getByRole("button", { name: /^search$/i }));
    await waitFor(() => {
      expect(mockApiPost).toHaveBeenCalledWith("/facilities/search", {
        latitude: 33.6844,
        longitude: 73.0479,
        max_distance_km: 50,
      });
    });
  });

  it("renders facility cards with name, address, distance, and emergency status", async () => {
    mockApiPost.mockResolvedValue(makeApiResponse(sampleSearchResult));
    render(
      <MemoryRouter>
        <FacilitiesPage />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /^search$/i }));
    await waitFor(() => {
      expect(screen.getByText("Test BHU")).toBeInTheDocument();
      expect(screen.getByText("123 Test Street")).toBeInTheDocument();
      expect(screen.getByText(/2.5 km/)).toBeInTheDocument();
      expect(screen.getByText("BHU")).toBeInTheDocument();
      expect(screen.getByText("District Hospital")).toBeInTheDocument();
      expect(screen.getByText("Emergency", { selector: "span" })).toBeInTheDocument();
    });
  });

  it("shows error message with role=alert on API failure", async () => {
    mockApiPost.mockRejectedValue(new Error("Network error"));
    render(
      <MemoryRouter>
        <FacilitiesPage />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /^search$/i }));
    await waitFor(() => {
      const error = screen.getByRole("alert");
      expect(error).toHaveTextContent(/unable to search/i);
    });
  });

  it("uses facility_id as React key (no duplicate key warnings)", async () => {
    mockApiPost.mockResolvedValue(makeApiResponse(sampleSearchResult));
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <MemoryRouter>
        <FacilitiesPage />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /^search$/i }));
    await waitFor(() => {
      expect(screen.getByText("Test BHU")).toBeInTheDocument();
    });
    expect(consoleSpy).not.toHaveBeenCalledWith(
      expect.stringContaining("duplicate key"),
    );
    consoleSpy.mockRestore();
  });
});
