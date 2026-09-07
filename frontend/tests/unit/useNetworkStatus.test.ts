import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

import { useNetworkStatus } from "@/hooks/useNetworkStatus";

describe("useNetworkStatus", () => {
  const originalNavigator = global.navigator;

  beforeEach(() => {
    vi.stubGlobal("navigator", {
      ...originalNavigator,
      onLine: true,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns isOnline=true when navigator.onLine is true", () => {
    (navigator as Navigator & { onLine: boolean }).onLine = true;
    const { result } = renderHook(() => useNetworkStatus());
    expect(result.current.isOnline).toBe(true);
  });

  it("returns isOnline=false when navigator.onLine is false", () => {
    (navigator as Navigator & { onLine: boolean }).onLine = false;
    const { result } = renderHook(() => useNetworkStatus());
    expect(result.current.isOnline).toBe(false);
  });

  it("updates to false when 'offline' event fires", () => {
    (navigator as Navigator & { onLine: boolean }).onLine = true;
    const { result } = renderHook(() => useNetworkStatus());
    expect(result.current.isOnline).toBe(true);

    act(() => {
      window.dispatchEvent(new Event("offline"));
    });
    expect(result.current.isOnline).toBe(false);
  });

  it("updates to true when 'online' event fires", () => {
    (navigator as Navigator & { onLine: boolean }).onLine = false;
    const { result } = renderHook(() => useNetworkStatus());
    expect(result.current.isOnline).toBe(false);

    act(() => {
      window.dispatchEvent(new Event("online"));
    });
    expect(result.current.isOnline).toBe(true);
  });

  it("removes event listeners on unmount", () => {
    const addSpy = vi.spyOn(window, "addEventListener");
    const removeSpy = vi.spyOn(window, "removeEventListener");

    const { unmount } = renderHook(() => useNetworkStatus());
    expect(addSpy).toHaveBeenCalledWith("online", expect.any(Function));
    expect(addSpy).toHaveBeenCalledWith("offline", expect.any(Function));

    unmount();

    expect(removeSpy).toHaveBeenCalledWith("online", expect.any(Function));
    expect(removeSpy).toHaveBeenCalledWith("offline", expect.any(Function));

    addSpy.mockRestore();
    removeSpy.mockRestore();
  });
});
