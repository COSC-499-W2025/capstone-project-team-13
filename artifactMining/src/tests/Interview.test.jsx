import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Interview from "../pages/Interview";

vi.mock("../apiClient", () => ({
  apiFetch: vi.fn(),
  projectName: (p) => p?.name || "Untitled",
}));

import { apiFetch } from "../apiClient";

const mockFetch = vi.fn();
global.fetch = mockFetch;

const SAMPLE_PROJECTS = [
  { id: 1, name: "Alpha", project_type: "code" },
  { id: 2, name: "Beta", project_type: "data" },
];

const SAMPLE_ANSWERS = [
  {
    question: "Tell me about a challenging project",
    project_name: "Alpha",
    situation: "We had a tight deadline",
    task: "Build a feature",
    action: "I wrote the code",
    result: "We shipped on time",
  },
];

function setupMocks() {
  mockFetch.mockImplementation((url) => {
    if (url.includes("/auth/me"))
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ id: 1 }) });
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });
  apiFetch.mockImplementation((url, opts) => {
    if (url === "/projects") return Promise.resolve(SAMPLE_PROJECTS);
    if (url === "/interview/generate") return Promise.resolve({ answers: SAMPLE_ANSWERS });
    return Promise.reject(new Error("Unmatched: " + url));
  });
}

function renderInterview() {
  return render(
    <MemoryRouter>
      <Interview />
    </MemoryRouter>
  );
}

beforeEach(() => {
  localStorage.setItem("token", "fake-token");
  vi.clearAllMocks();
});

afterEach(() => {
  localStorage.removeItem("token");
  mockFetch.mockReset();
});

describe("Interview - unauthenticated state", () => {
  it("shows sign in prompt when not authenticated", async () => {
    localStorage.removeItem("token");
    mockFetch.mockImplementation((url) => {
      if (url.includes("/auth/me"))
        return Promise.resolve({ ok: false, status: 401, json: () => Promise.resolve({}) });
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    renderInterview();
    await waitFor(() =>
      expect(document.body.innerHTML).toContain("Sign In"), { timeout: 3000 }
    );
  });
});

describe("Interview - authenticated rendering", () => {
  beforeEach(() => setupMocks());

  it("renders Interview Prep heading", async () => {
    renderInterview();
    await waitFor(() => expect(screen.getByText(/Interview Prep/i)).toBeTruthy());
  });

  it("renders role selector", async () => {
    renderInterview();
    await waitFor(() => expect(screen.getByText("Software Engineer")).toBeTruthy());
  });

  it("renders project list", async () => {
    renderInterview();
    await waitFor(() => expect(screen.getByText("Alpha")).toBeTruthy());
  });

  it("renders Generate Answers button", async () => {
    renderInterview();
    await waitFor(() => {
      const btns = screen.getAllByRole("button").filter(b => b.textContent.includes("Generate"));
      expect(btns.length).toBeGreaterThan(0);
    });
  });

  it("calls /projects endpoint on mount", async () => {
    renderInterview();
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/projects"));
  });
});

describe("Interview - project selection", () => {
  beforeEach(() => setupMocks());

  it("all projects are selected by default", async () => {
    renderInterview();
    await waitFor(() => screen.getByText("Alpha"));
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes.every(cb => cb.checked)).toBe(true);
  });

  it("deselects project on click", async () => {
    renderInterview();
    await waitFor(() => screen.getByText("Alpha"));
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);
    await waitFor(() => expect(checkboxes[0].checked).toBe(false));
  });
});

describe("Interview - generating answers", () => {
  beforeEach(() => setupMocks());

  it("calls /interview/generate on Generate click", async () => {
    renderInterview();
    await waitFor(() => screen.getByText("Alpha"));
    const btn = screen.getAllByRole("button").find(b => b.textContent.includes("Generate"));
    fireEvent.click(btn);
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        "/interview/generate",
        expect.objectContaining({ method: "POST" })
      )
    );
  });

  it("shows answers after generation", async () => {
    renderInterview();
    // Wait for projects to load first so selectedIds is populated
    await waitFor(() => screen.getByText("Alpha"));
    const btn = screen.getAllByRole("button").find(b => b.textContent.includes("Generate"));
    fireEvent.click(btn);
    await waitFor(() =>
      expect(document.body.innerHTML).toContain("Tell me about a challenging project"),
      { timeout: 3000 }
    );
  });
});