import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

import {
  mockApiPost,
  makeApiResponse,
} from "../helpers/mock-api";
import type { TriageResponse } from "@/types/api";

let capturedOnAudioReady: ((blob: Blob) => void) | null = null;

vi.mock("@/components/ui/VoiceRecorder", () => ({
  VoiceRecorder: ({ onAudioReady }: { onAudioReady: (blob: Blob) => void }) => {
    capturedOnAudioReady = onAudioReady;
    return null;
  },
}));

import TriagePage from "@/pages/TriagePage";

const sampleTriageResponse: TriageResponse = {
  session_id: "test-session-12345678",
  is_emergency: false,
  urgency: "ROUTINE",
  recommended_facility: {
    facility_id: "BHU-001",
    name: "Test BHU",
    facility_type: "BHU",
    address: "123 Test Street",
    distance_km: 2.5,
    services_available: ["General care"],
    emergency_capable: false,
    phone_number: "+92-300-1234567",
  },
  medicine_status: {
    facility_id: "BHU-001",
    medicines_checked: ["Paracetamol", "Amoxicillin"],
    medicines_available: ["Paracetamol"],
    medicines_unavailable: ["Amoxicillin"],
    last_updated: "2026-09-04T10:00:00Z",
  },
  patient_message_urdu: "براہ کرم قریبی صحت مرکز تشریف لائیں۔",
  audio_url: null,
  reasoning_trace: "Symptoms consistent with routine care.",
};

describe("TriagePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the symptom input form with label and submit button", () => {
    render(
      <MemoryRouter>
        <TriagePage />
      </MemoryRouter>,
    );
    expect(screen.getByText("Describe your symptoms")).toBeInTheDocument();
    expect(screen.getByLabelText(/symptom description/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /analyse symptoms/i }),
    ).toBeInTheDocument();
  });

  it("submit button is disabled when input is empty", () => {
    render(
      <MemoryRouter>
        <TriagePage />
      </MemoryRouter>,
    );
    const button = screen.getByRole("button", { name: /analyse symptoms/i });
    expect(button).toBeDisabled();
  });

  it("submit button is disabled during pending request", async () => {
    mockApiPost.mockImplementation(
      () => new Promise(() => {}),
    );
    render(
      <MemoryRouter>
        <TriagePage />
      </MemoryRouter>,
    );
    const input = screen.getByLabelText(/symptom description/i);
    await userEvent.type(input, "fever and cough");
    const button = screen.getByRole("button", { name: /analyse symptoms/i });
    fireEvent.click(button);
    expect(button).toBeDisabled();
    expect(screen.getByText(/analysing symptoms/i)).toBeInTheDocument();
  });

  it("on successful API response, renders the Urdu response text", async () => {
    mockApiPost.mockResolvedValue(makeApiResponse(sampleTriageResponse));
    render(
      <MemoryRouter>
        <TriagePage />
      </MemoryRouter>,
    );
    const input = screen.getByLabelText(/symptom description/i);
    await userEvent.type(input, "fever");
    fireEvent.click(screen.getByRole("button", { name: /analyse symptoms/i }));
    await waitFor(() => {
      expect(
        screen.getByText("براہ کرم قریبی صحت مرکز تشریف لائیں۔"),
      ).toBeInTheDocument();
    });
  });

  it("on emergency response, renders emergency alert with role=alert", async () => {
    const emergencyResponse: TriageResponse = {
      ...sampleTriageResponse,
      is_emergency: true,
      urgency: "EMERGENCY",
    };
    mockApiPost.mockResolvedValue(makeApiResponse(emergencyResponse));
    render(
      <MemoryRouter>
        <TriagePage />
      </MemoryRouter>,
    );
    const input = screen.getByLabelText(/symptom description/i);
    await userEvent.type(input, "chest pain");
    fireEvent.click(screen.getByRole("button", { name: /analyse symptoms/i }));
    await waitFor(() => {
      const alert = screen.getByRole("alert");
      expect(alert).toHaveTextContent(/emergency/i);
    });
  });

  it("on response with recommended_facility, renders facility name and address", async () => {
    mockApiPost.mockResolvedValue(makeApiResponse(sampleTriageResponse));
    render(
      <MemoryRouter>
        <TriagePage />
      </MemoryRouter>,
    );
    const input = screen.getByLabelText(/symptom description/i);
    await userEvent.type(input, "fever");
    fireEvent.click(screen.getByRole("button", { name: /analyse symptoms/i }));
    await waitFor(() => {
      expect(screen.getByText("Test BHU")).toBeInTheDocument();
      expect(screen.getByText("123 Test Street")).toBeInTheDocument();
    });
  });

  it("on response with audio_url, renders an audio element", async () => {
    const responseWithAudio: TriageResponse = {
      ...sampleTriageResponse,
      audio_url: "https://example.com/audio.mp3",
    };
    mockApiPost.mockResolvedValue(makeApiResponse(responseWithAudio));
    render(
      <MemoryRouter>
        <TriagePage />
      </MemoryRouter>,
    );
    const input = screen.getByLabelText(/symptom description/i);
    await userEvent.type(input, "fever");
    fireEvent.click(screen.getByRole("button", { name: /analyse symptoms/i }));
    await waitFor(() => {
      const audio = screen.getByLabelText(/urdu audio response/i);
      expect(audio).toBeInTheDocument();
      expect(audio.tagName).toBe("AUDIO");
    });
  });

  it("on API error, renders error message with role=alert", async () => {
    mockApiPost.mockRejectedValue(new Error("Network error"));
    render(
      <MemoryRouter>
        <TriagePage />
      </MemoryRouter>,
    );
    const input = screen.getByLabelText(/symptom description/i);
    await userEvent.type(input, "fever");
    fireEvent.click(screen.getByRole("button", { name: /analyse symptoms/i }));
    await waitFor(() => {
      const error = screen.getByRole("alert");
      expect(error).toHaveTextContent(/unable to reach/i);
    });
  });

  it("sends patient_message field (not message) in the POST body", async () => {
    mockApiPost.mockResolvedValue(makeApiResponse(sampleTriageResponse));
    render(
      <MemoryRouter>
        <TriagePage />
      </MemoryRouter>,
    );
    const input = screen.getByLabelText(/symptom description/i);
    await userEvent.type(input, "headache");
    fireEvent.click(screen.getByRole("button", { name: /analyse symptoms/i }));
    await waitFor(() => {
      expect(mockApiPost).toHaveBeenCalledWith("/triage", {
        patient_message: "headache",
      });
    });
  });

  it("on voice recording completion, transcribes audio via /transcribe and appends text to input", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, data: { text: "sar dard hai" }, error: null }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <MemoryRouter>
        <TriagePage />
      </MemoryRouter>,
    );

    expect(capturedOnAudioReady).not.toBeNull();
    const blob = new Blob(["audio"], { type: "audio/webm" });
    await capturedOnAudioReady!(blob);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });

    const [url, options] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/transcribe");
    expect(options.method).toBe("POST");

    await waitFor(() => {
      const input = screen.getByLabelText(/symptom description/i) as HTMLTextAreaElement;
      expect(input.value).toContain("sar dard hai");
    });

    vi.unstubAllGlobals();
  });
});
