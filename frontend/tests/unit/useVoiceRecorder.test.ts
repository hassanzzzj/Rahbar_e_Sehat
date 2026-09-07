import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

import { useVoiceRecorder } from "@/hooks/useVoiceRecorder";

type StopCallback = (() => void) | null;
type DataCallback = ((event: { data: Blob }) => void) | null;

class MockMediaRecorder {
  static instances: MockMediaRecorder[] = [];
  state = "inactive";
  ondataavailable: DataCallback = null;
  onstop: StopCallback = null;
  mimeType: string;

  constructor(_stream: MediaStream, options?: { mimeType?: string }) {
    this.mimeType = options?.mimeType ?? "";
    MockMediaRecorder.instances.push(this);
  }

  start(_interval?: number) {
    this.state = "recording";
  }

  stop() {
    this.state = "inactive";
    if (this.ondataavailable) {
      this.ondataavailable({ data: new Blob(["fake-audio-chunk"], { type: this.mimeType }) });
    }
    if (this.onstop) {
      this.onstop();
    }
  }

  static isTypeSupported = vi.fn((_mime: string) => true);
  static reset() {
    MockMediaRecorder.instances = [];
    MockMediaRecorder.isTypeSupported.mockReturnValue(true);
  }
}

const mockGetUserMedia = vi.fn();

describe("useVoiceRecorder", () => {
  beforeEach(() => {
    MockMediaRecorder.reset();
    mockGetUserMedia.mockReset();
    mockGetUserMedia.mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }],
    });

    vi.stubGlobal("MediaRecorder", MockMediaRecorder);
    Object.defineProperty(navigator, "mediaDevices", {
      value: { getUserMedia: mockGetUserMedia },
      configurable: true,
      writable: true,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("starts with isRecording=false and no audio blob", () => {
    const { result } = renderHook(() => useVoiceRecorder());
    expect(result.current.isRecording).toBe(false);
    expect(result.current.audioBlob).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isSupported).toBe(true);
  });

  it("sets isRecording=true after startRecording", async () => {
    const { result } = renderHook(() => useVoiceRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.isRecording).toBe(true);
    expect(mockGetUserMedia).toHaveBeenCalledWith({ audio: true });
    expect(MockMediaRecorder.instances).toHaveLength(1);
  });

  it("produces an audio blob after stopRecording", async () => {
    const { result } = renderHook(() => useVoiceRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    act(() => {
      result.current.stopRecording();
    });

    expect(result.current.isRecording).toBe(false);
    expect(result.current.audioBlob).toBeInstanceOf(Blob);
  });

  it("stops all tracks on the media stream when recording stops", async () => {
    const stopTrack = vi.fn();
    mockGetUserMedia.mockResolvedValue({
      getTracks: () => [{ stop: stopTrack }],
    });

    const { result } = renderHook(() => useVoiceRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    act(() => {
      result.current.stopRecording();
    });

    expect(stopTrack).toHaveBeenCalledTimes(1);
  });

  it("sets error when getUserMedia fails", async () => {
    mockGetUserMedia.mockRejectedValue(new Error("Permission denied"));

    const { result } = renderHook(() => useVoiceRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.isRecording).toBe(false);
    expect(result.current.error).toBe("Permission denied");
    expect(result.current.audioBlob).toBeNull();
  });

  it("prefers audio/webm;codecs=opus when supported", async () => {
    MockMediaRecorder.isTypeSupported.mockReturnValue(true);

    const { result } = renderHook(() => useVoiceRecorder());
    await act(async () => {
      await result.current.startRecording();
    });

    expect(MockMediaRecorder.isTypeSupported).toHaveBeenCalledWith(
      "audio/webm;codecs=opus",
    );
  });

  it("reports isSupported=false when MediaRecorder is undefined", () => {
    vi.stubGlobal("MediaRecorder", undefined);

    const { result } = renderHook(() => useVoiceRecorder());
    expect(result.current.isSupported).toBe(false);
  });

  it("sets error when startRecording is called on unsupported browser", async () => {
    vi.stubGlobal("MediaRecorder", undefined);

    const { result } = renderHook(() => useVoiceRecorder());
    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.error).toMatch(/not supported/i);
    expect(result.current.isRecording).toBe(false);
  });
});
