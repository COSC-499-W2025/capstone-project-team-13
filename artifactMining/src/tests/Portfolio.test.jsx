import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi, describe, test, expect, beforeEach, afterEach } from "vitest";
import Portfolio from "../pages/Portfolio";

const mockFetch = vi.fn();
global.fetch = mockFetch;

const sampleProjects = [
  {
    id: 1,
    name: "Alpha Project",
    project_type: "code",
    description: "A regular description",
    ai_description: null,
    languages: ["Python"],
    file_count: 10,
    lines_of_code: 300,
  },
];

function setupFetchMocks({ aiConsent = false, projects = sampleProjects } = {}) {
  mockFetch.mockImplementation((url, opts) => {
    if (url.includes("ai-consent-status")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ granted: aiConsent }),
      });
    }
    if (url.includes("/portfolio/generate")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ projects, summary: "Good portfolio", stats: {} }),
      });
    }
    if (url.includes("/analyze")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            ai_description: "AI-powered description for the project.",
          }),
      });
    }
    return Promise.reject(new Error("Unmatched URL: " + url));
  });
}

function renderPortfolio() {
  return render(
    <MemoryRouter>
      <Portfolio />
    </MemoryRouter>
  );
}

describe("Portfolio - no AI consent", () => {
  beforeEach(() => setupFetchMocks({ aiConsent: false }));
  afterEach(() => mockFetch.mockReset());

  test("renders project cards", async () => {
    renderPortfolio();
    await waitFor(() => screen.getByText("Alpha Project"));
  });

  test("does not show Generate AI Descriptions button", async () => {
    renderPortfolio();
    await waitFor(() => screen.getByText("Alpha Project"));
    expect(screen.queryByText(/Generate AI Descriptions/i)).not.toBeInTheDocument();
  });

  test("shows settings hint", async () => {
    renderPortfolio();
    await waitFor(() => screen.getByText(/Enable AI consent/i));
  });
});

describe("Portfolio - with AI consent", () => {
  beforeEach(() => setupFetchMocks({ aiConsent: true }));
  afterEach(() => mockFetch.mockReset());

  test("shows Generate AI Descriptions button", async () => {
    renderPortfolio();
    await waitFor(() => screen.getByText(/Generate AI Descriptions/i));
  });

  test("clicking button calls analyze and updates descriptions", async () => {
    renderPortfolio();
    const btn = await waitFor(() => screen.getByText(/Generate AI Descriptions/i));
    fireEvent.click(btn);
    await waitFor(() => screen.getByText("AI-powered description for the project."));
  });
});

describe("Portfolio - projects with existing ai_description", () => {
  const projectsWithAi = [
    { ...sampleProjects[0], ai_description: "Pre-existing AI description." },
  ];

  beforeEach(() => setupFetchMocks({ aiConsent: true, projects: projectsWithAi }));
  afterEach(() => mockFetch.mockReset());

  test("displays existing ai_description in card", async () => {
    renderPortfolio();
    await waitFor(() => screen.getByText("Pre-existing AI description."));
    expect(screen.getByText("AI")).toBeInTheDocument();
  });
});