import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

import { useDebounce } from "@/hooks/useDebounce";

describe("useDebounce", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns the initial value immediately", () => {
    const { result } = renderHook(() => useDebounce("hello", 500));
    expect(result.current).toBe("hello");
  });

  it("does not update value before the delay elapses", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "hello", delay: 500 } },
    );

    rerender({ value: "world", delay: 500 });

    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current).toBe("hello");
  });

  it("updates value after the delay elapses", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "hello", delay: 500 } },
    );

    rerender({ value: "world", delay: 500 });

    act(() => {
      vi.advanceTimersByTime(500);
    });
    expect(result.current).toBe("world");
  });

  it("resets the timer on each new value change", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "a", delay: 300 } },
    );

    rerender({ value: "b", delay: 300 });
    act(() => {
      vi.advanceTimersByTime(200);
    });
    rerender({ value: "c", delay: 300 });
    act(() => {
      vi.advanceTimersByTime(200);
    });
    // "b" should NOT have been committed (only 200ms elapsed before change)
    expect(result.current).toBe("a");

    act(() => {
      vi.advanceTimersByTime(100);
    });
    // Now 300ms since last change ("c")
    expect(result.current).toBe("c");
  });

  it("handles zero delay", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "a", delay: 0 } },
    );

    rerender({ value: "b", delay: 0 });
    act(() => {
      vi.advanceTimersByTime(0);
    });
    expect(result.current).toBe("b");
  });
});
