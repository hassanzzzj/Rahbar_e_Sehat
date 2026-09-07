import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { VoiceRecorder } from "@/components/ui/VoiceRecorder";
import * as useVoiceRecorderModule from "@/hooks/useVoiceRecorder";

vi.mock("@/hooks/useVoiceRecorder", async () => {
  const actual = await vi.importActual<typeof useVoiceRecorderModule>(
    "@/hooks/useVoiceRecorder",
  );
  return { ...actual, useVoiceRecorder: vi.fn() };
});

const mockedHook = vi.mocked(useVoiceRecorderModule.useVoiceRecorder);

describe("VoiceRecorder", () => {
  beforeEach(() => {
    mockedHook.mockReset();
    mockedHook.mockReturnValue({
      isRecording: false,
      startRecording: vi.fn(),
      stopRecording: vi.fn(),
      audioBlob: null,
      error: null,
      isSupported: true,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the 'Record voice' button when supported", () => {
    render(<VoiceRecorder onAudioReady={() => {}} />);
    expect(
      screen.getByRole("button", { name: /start voice recording/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/voice input/i)).toBeInTheDocument();
  });

  it("calls startRecording when the record button is clicked", () => {
    const startRecording = vi.fn();
    mockedHook.mockReturnValue({
      isRecording: false,
      startRecording,
      stopRecording: vi.fn(),
      audioBlob: null,
      error: null,
      isSupported: true,
    });

    render(<VoiceRecorder onAudioReady={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: /start voice recording/i }));
    expect(startRecording).toHaveBeenCalledTimes(1);
  });

  it("shows 'Stop' button and elapsed timer while recording", () => {
    mockedHook.mockReturnValue({
      isRecording: true,
      startRecording: vi.fn(),
      stopRecording: vi.fn(),
      audioBlob: null,
      error: null,
      isSupported: true,
    });

    render(<VoiceRecorder onAudioReady={() => {}} />);
    expect(screen.getByRole("button", { name: /stop recording/i })).toBeInTheDocument();
    expect(screen.getByText(/recording…/i)).toBeInTheDocument();
    expect(screen.getByText("0:00")).toBeInTheDocument();
  });

  it("calls stopRecording when the stop button is clicked", () => {
    const stopRecording = vi.fn();
    mockedHook.mockReturnValue({
      isRecording: true,
      startRecording: vi.fn(),
      stopRecording,
      audioBlob: null,
      error: null,
      isSupported: true,
    });

    render(<VoiceRecorder onAudioReady={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: /stop recording/i }));
    expect(stopRecording).toHaveBeenCalledTimes(1);
  });

  it("invokes onAudioReady when audioBlob becomes available", async () => {
    const onAudioReady = vi.fn();
    const blob = new Blob(["audio"], { type: "audio/webm" });

    mockedHook.mockReturnValue({
      isRecording: false,
      startRecording: vi.fn(),
      stopRecording: vi.fn(),
      audioBlob: blob,
      error: null,
      isSupported: true,
    });

    render(<VoiceRecorder onAudioReady={onAudioReady} />);

    await waitFor(() => {
      expect(onAudioReady).toHaveBeenCalledWith(blob);
    });
  });

  it("renders error message with role=alert when error is set", () => {
    mockedHook.mockReturnValue({
      isRecording: false,
      startRecording: vi.fn(),
      stopRecording: vi.fn(),
      audioBlob: null,
      error: "Permission denied",
      isSupported: true,
    });

    render(<VoiceRecorder onAudioReady={() => {}} />);
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Permission denied");
  });

  it("renders fallback UI when MediaRecorder is unsupported", () => {
    mockedHook.mockReturnValue({
      isRecording: false,
      startRecording: vi.fn(),
      stopRecording: vi.fn(),
      audioBlob: null,
      error: null,
      isSupported: false,
    });

    render(<VoiceRecorder onAudioReady={() => {}} />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.getByText(/voice recording is not supported/i)).toBeInTheDocument();
  });

  it("disables the button when disabled prop is true", () => {
    render(<VoiceRecorder onAudioReady={() => {}} disabled />);
    expect(
      screen.getByRole("button", { name: /start voice recording/i }),
    ).toBeDisabled();
  });
});
