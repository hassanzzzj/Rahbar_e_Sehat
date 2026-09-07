import { vi } from "vitest";
import type { APIResponse } from "@/types/api";

export const mockApiGet = vi.fn();
export const mockApiPost = vi.fn();

vi.mock("@/lib/api-client", () => ({
  API_BASE_URL: "http://localhost:8000/api/v1",
  api: {
    get: mockApiGet,
    post: mockApiPost,
  },
  ApiClientError: class ApiClientError extends Error {
    code: string;
    status: number;
    constructor(code: string, message: string, status: number) {
      super(message);
      this.name = "ApiClientError";
      this.code = code;
      this.status = status;
    }
  },
}));

export function makeApiResponse<T>(data: T): APIResponse<T> {
  return { success: true, data, error: null };
}

export function makeApiError(
  code: string,
  message: string,
): APIResponse<null> {
  return {
    success: false,
    data: null,
    error: { code, message },
  };
}
