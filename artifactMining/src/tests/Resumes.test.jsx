import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Resumes from "../pages/Resumes";

const mockFetch = vi.fn();
global.fetch = mockFetch;

vi.mock("canvas-confetti", () => ({ default: vi.fn() }));
vi.mock("../components/Toast", () => ({ toast: vi.fn() }));

function setupAuthMocks() {
  mockFetch.mockImplementation((url) => {
    if (url.includes("/auth/me")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ id: 1, email: "jane@example.com" }),
      });
    }
    if (url.includes("/consent/ai-consent-status")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ granted: false }) });
    }
    if (url.includes("/education")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ education: [] }) });
    }
    if (url.includes("/work-history")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ work_history: [] }) });
    }
    if (url.includes("/skills/")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ skills: [] }) });
    }
    if (url.includes("/resume")) {
      return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });
}

beforeEach(() => {
  localStorage.setItem("token", "fake-token");
  vi.clearAllMocks();
});

afterEach(() => {
  localStorage.removeItem("token");
  mockFetch.mockReset();
});

function renderResumes() {
  return render(
    <MemoryRouter>
      <Resumes />
    </MemoryRouter>
  );
}

describe("Resumes - authenticated state", () => {
  beforeEach(() => setupAuthMocks());

  it("renders the page without crashing", async () => {
    renderResumes();
    await waitFor(() => expect(document.body).toBeTruthy());
  });

  it("calls /auth/me on mount", async () => {
    renderResumes();
    await waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/auth/me"),
        expect.anything()
      )
    );
  });

  it("calls /resume endpoint after auth", async () => {
    renderResumes();
    await waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/resume"),
        expect.anything()
      )
    );
  });

  it("renders Resume Controls heading when authenticated", async () => {
    renderResumes();
    await waitFor(() => expect(screen.getByText("Resume Controls")).toBeTruthy());
  });

  it("shows empty state when no resume exists", async () => {
    renderResumes();
    await waitFor(() =>
      expect(screen.getByText(/No resume yet/i)).toBeTruthy()
    );
  });

  it("renders bullet count stepper", async () => {
    renderResumes();
    await waitFor(() => expect(screen.getByText("Bullets per project")).toBeTruthy());
  });
});

describe("Resumes - unauthenticated state", () => {
  it("shows sign in prompt when not authenticated", async () => {
    localStorage.removeItem("token");
    mockFetch.mockImplementation((url) => {
      if (url.includes("/auth/me"))
        return Promise.resolve({ ok: false, status: 401, json: () => Promise.resolve({}) });
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    renderResumes();
    await waitFor(() =>
      expect(document.body.innerHTML).toContain("Sign In"), { timeout: 3000 }
    );
  });

  it("shows Resume Builder heading on auth wall", async () => {
    localStorage.removeItem("token");
    mockFetch.mockImplementation((url) => {
      if (url.includes("/auth/me"))
        return Promise.resolve({ ok: false, status: 401, json: () => Promise.resolve({}) });
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    renderResumes();
    await waitFor(() =>
      expect(screen.getByText("Resume Builder")).toBeTruthy(), { timeout: 3000 }
    );
  });
});

describe("Resumes - API calls", () => {
  beforeEach(() => setupAuthMocks());

  it("calls /education endpoint", async () => {
    renderResumes();
    await waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/education"),
        expect.anything()
      )
    );
  });

  it("calls /work-history endpoint", async () => {
    renderResumes();
    await waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/work-history"),
        expect.anything()
      )
    );
  });
});