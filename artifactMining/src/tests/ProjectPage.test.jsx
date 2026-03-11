import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi, describe, test, expect, beforeEach, afterEach } from "vitest";
import ProjectPage from "../pages/ProjectPage";

const mockFetch = vi.fn();
global.fetch = mockFetch;

function renderWithRouter(projectId = "1") {
  return render(
    <MemoryRouter initialEntries={[`/projects/${projectId}`]}>
      <Routes>
        <Route path="/projects/:projectId" element={<ProjectPage />} />
      </Routes>
    </MemoryRouter>
  );
}

const baseProject = {
  id: 1,
  name: "Test Project",
  project_type: "code",
  description: "A sample project",
  ai_description: null,
  skills: ["python", "fastapi"],
  languages: ["Python"],
  frameworks: [],
  tags: [],
  file_count: 10,
  lines_of_code: 500,
  word_count: 0,
  total_size_bytes: 1024,
  date_scanned: "2025-01-01T00:00:00",
};

function setupFetchMocks({ aiConsent = false, project = baseProject } = {}) {
  mockFetch.mockImplementation((url) => {
    if (url.includes("ai-consent-status")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ granted: aiConsent }),
      });
    }
    if (url.includes("/projects/") && !url.includes("/analyze")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(project),
      });
    }
    if (url.includes("/analyze")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            message: "AI analysis complete",
            ai_description: "An AI-generated description.",
            project: { ...project, ai_description: "An AI-generated description." },
          }),
      });
    }
    return Promise.reject(new Error("Unexpected URL: " + url));
  });
}

describe("ProjectPage - no AI consent", () => {
  beforeEach(() => setupFetchMocks({ aiConsent: false }));
  afterEach(() => mockFetch.mockReset());

  test("renders project name", async () => {
    renderWithRouter();
    await waitFor(() => screen.getByText("Test Project"));
    expect(screen.getByText("Test Project")).toBeInTheDocument();
  });

  test("shows description text when no ai_description", async () => {
    renderWithRouter();
    await waitFor(() => screen.getByText("A sample project"));
  });

  test("does not show Generate AI Description button", async () => {
    renderWithRouter();
    await waitFor(() => screen.getByText("Test Project"));
    expect(screen.queryByText(/Generate AI Description/i)).not.toBeInTheDocument();
  });

  test("shows Settings link hint", async () => {
    renderWithRouter();
    await waitFor(() => screen.getByText(/Enable AI consent/i));
  });
});

describe("ProjectPage - with AI consent", () => {
  beforeEach(() => setupFetchMocks({ aiConsent: true }));
  afterEach(() => mockFetch.mockReset());

  test("shows Generate AI Description button", async () => {
    renderWithRouter();
    await waitFor(() => screen.getByText(/Generate AI Description/i));
  });

  test("clicking Generate calls analyze endpoint and updates description", async () => {
    renderWithRouter();
    const btn = await waitFor(() => screen.getByText(/Generate AI Description/i));
    fireEvent.click(btn);
    await waitFor(() => screen.getByText("An AI-generated description."));
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/analyze"),
      expect.objectContaining({ method: "POST" })
    );
  });
});

describe("ProjectPage - with existing ai_description", () => {
  beforeEach(() =>
    setupFetchMocks({
      aiConsent: true,
      project: { ...baseProject, ai_description: "Existing AI description." },
    })
  );
  afterEach(() => mockFetch.mockReset());

  test("shows existing ai_description in AI block", async () => {
    renderWithRouter();
    await waitFor(() => screen.getByText("Existing AI description."));
    expect(screen.getByText("AI")).toBeInTheDocument();
  });

  test("shows Regenerate button instead of Generate", async () => {
    renderWithRouter();
    await waitFor(() => screen.getByText(/Regenerate AI Description/i));
  });
});