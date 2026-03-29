import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Analysis from "../pages/Analysis";

vi.mock("../apiClient", () => ({
  apiFetch: vi.fn(),
  projectName: (p) => p?.custom_description || p?.name || "Untitled",
}));

import { apiFetch } from "../apiClient";

const SAMPLE_PROJECTS = [
  { id: 1, name: "Alpha", project_type: "code" },
  { id: 2, name: "Beta", project_type: "data" },
];

function setupMocks() {
  apiFetch.mockImplementation((url, opts) => {
    if (url === "/projects") return Promise.resolve(SAMPLE_PROJECTS);
    if (url === "/projects/compute-importance") return Promise.resolve({ updated: 2, scores: [] });
    if (url === "/projects/rank") return Promise.resolve({ selected: [], summary: "No results" });
    if (url.includes("/analyze")) return Promise.resolve({ results: { overview: "Test overview" } });
    if (url === "/projects/analyze/batch") return Promise.resolve({ analyzed: 2, results: [] });
    if (url === "/projects/timeline") return Promise.resolve([]);
    if (url.includes("/portfolio/")) return Promise.resolve({});
    return Promise.reject(new Error("Unmatched: " + url));
  });
}

function renderAnalysis() {
  return render(
    <MemoryRouter>
      <Analysis />
    </MemoryRouter>
  );
}

// Helper: click a tab button by matching the an-tab class
function clickTab(label) {
  const tabs = screen.getAllByRole("button").filter(b => b.className.includes("an-tab") && b.textContent.includes(label));
  fireEvent.click(tabs[0]);
}

beforeEach(() => vi.clearAllMocks());

describe("Analysis - rendering", () => {
  beforeEach(() => setupMocks());

  it("renders the Analysis heading", async () => {
    renderAnalysis();
    await waitFor(() => expect(screen.getByText("Analysis")).toBeTruthy());
  });

  it("renders Score & Rank tab button", async () => {
    renderAnalysis();
    await waitFor(() => {
      const tabs = screen.getAllByRole("button").filter(b => b.className.includes("an-tab") && b.textContent.includes("Score"));
      expect(tabs.length).toBeGreaterThan(0);
    });
  });

  it("renders AI Analysis tab button", async () => {
    renderAnalysis();
    await waitFor(() => {
      const tabs = screen.getAllByRole("button").filter(b => b.className.includes("an-tab") && b.textContent.includes("AI"));
      expect(tabs.length).toBeGreaterThan(0);
    });
  });

  it("renders Timeline tab button", async () => {
    renderAnalysis();
    await waitFor(() => {
      const tabs = screen.getAllByRole("button").filter(b => b.className.includes("an-tab") && b.textContent.includes("Timeline"));
      expect(tabs.length).toBeGreaterThan(0);
    });
  });

  it("renders Roles tab button", async () => {
    renderAnalysis();
    await waitFor(() => {
      const tabs = screen.getAllByRole("button").filter(b => b.className.includes("an-tab") && b.textContent.includes("Roles"));
      expect(tabs.length).toBeGreaterThan(0);
    });
  });
});

describe("Analysis - Score tab", () => {
  beforeEach(() => setupMocks());

  it("renders Compute All Scores button by default", async () => {
    renderAnalysis();
    await waitFor(() => expect(screen.getByText("Compute All Scores")).toBeTruthy());
  });

  it("renders Run AI Ranking button", async () => {
    renderAnalysis();
    await waitFor(() => expect(screen.getByText("Run AI Ranking")).toBeTruthy());
  });

  it("calls compute-importance endpoint on button click", async () => {
    renderAnalysis();
    await waitFor(() => screen.getByText("Compute All Scores"));
    fireEvent.click(screen.getByText("Compute All Scores"));
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        "/projects/compute-importance",
        expect.objectContaining({ method: "POST" })
      )
    );
  });

  it("shows success message after computing scores", async () => {
    renderAnalysis();
    await waitFor(() => screen.getByText("Compute All Scores"));
    fireEvent.click(screen.getByText("Compute All Scores"));
    await waitFor(() => expect(screen.getByText(/Updated importance scores/i)).toBeTruthy());
  });
});

describe("Analysis - AI tab", () => {
  beforeEach(() => setupMocks());

  it("switches to AI Analysis tab", async () => {
    renderAnalysis();
    await waitFor(() => screen.getAllByRole("button"));
    clickTab("AI");
    await waitFor(() => expect(screen.getByText("Analyze Single Project")).toBeTruthy());
  });

  it("renders project dropdown in AI tab", async () => {
    renderAnalysis();
    await waitFor(() => screen.getAllByRole("button"));
    clickTab("AI");
    await waitFor(() => expect(screen.getByText("Alpha")).toBeTruthy());
  });

  it("Analyze button is disabled when no project selected", async () => {
    renderAnalysis();
    await waitFor(() => screen.getAllByRole("button"));
    clickTab("AI");
    await waitFor(() => screen.getByText("Analyze"));
    expect(screen.getByText("Analyze").closest("button").disabled).toBe(true);
  });

  it("renders Batch Analyze button", async () => {
    renderAnalysis();
    await waitFor(() => screen.getAllByRole("button"));
    clickTab("AI");
    await waitFor(() => {
      const btns = screen.getAllByRole("button").filter(b => b.textContent.includes("Batch Analyze"));
      expect(btns.length).toBeGreaterThan(0);
    });
  });
});

describe("Analysis - Timeline tab", () => {
  beforeEach(() => setupMocks());

  it("switches to Timeline tab and shows empty state", async () => {
    renderAnalysis();
    await waitFor(() => screen.getAllByRole("button"));
    clickTab("Timeline");
    await waitFor(() => expect(screen.getByText(/No projects found/i)).toBeTruthy());
  });
});

describe("Analysis - Roles tab", () => {
  beforeEach(() => setupMocks());

  it("switches to Roles tab", async () => {
    renderAnalysis();
    await waitFor(() => screen.getAllByRole("button"));
    clickTab("Roles");
    await waitFor(() => expect(screen.getByText("Assign Role to Project")).toBeTruthy());
  });

  it("Assign Role button is disabled when no project or role selected", async () => {
    renderAnalysis();
    await waitFor(() => screen.getAllByRole("button"));
    clickTab("Roles");
    await waitFor(() => screen.getByText("Assign Role"));
    expect(screen.getByText("Assign Role").closest("button").disabled).toBe(true);
  });
});

describe("Analysis - API calls", () => {
  beforeEach(() => setupMocks());

  it("calls /projects on mount", async () => {
    renderAnalysis();
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/projects"));
  });
});