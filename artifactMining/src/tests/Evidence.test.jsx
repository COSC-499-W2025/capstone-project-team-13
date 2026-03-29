import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Evidence from "../pages/Evidence";

vi.mock("../apiClient", () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from "../apiClient";

const SAMPLE_PROJECTS = [
  { id: 1, name: "Alpha", project_type: "code" },
  { id: 2, name: "Beta", project_type: "data" },
];

const SAMPLE_EVIDENCE = {
  test_coverage: 85,
  code_quality: "A",
  manual_metrics: { Users: { value: "1000", description: "Active users" } },
  feedback: [{ text: "Great work", source: "Client", rating: 5 }],
  achievements: [{ description: "Won hackathon", date: "2024-01-01" }],
  readme_badges: [],
};

function setupMocks({ evidence = SAMPLE_EVIDENCE } = {}) {
  apiFetch.mockImplementation((url, opts) => {
    if (url === "/projects") return Promise.resolve(SAMPLE_PROJECTS);
    if (url.match(/\/evidence\/\d+$/) && (!opts || opts.method !== "DELETE"))
      return Promise.resolve(evidence);
    if (url.includes("/evidence/") && url.includes("/extract"))
      return Promise.resolve({});
    if (url.includes("/evidence/") && url.includes("/metric"))
      return Promise.resolve({});
    if (url.includes("/evidence/") && url.includes("/feedback"))
      return Promise.resolve({});
    if (url.includes("/evidence/") && url.includes("/achievement"))
      return Promise.resolve({});
    if (url.match(/\/evidence\/\d+$/) && opts?.method === "DELETE")
      return Promise.resolve({});
    return Promise.reject(new Error("Unmatched: " + url));
  });
}

function renderEvidence() {
  return render(
    <MemoryRouter>
      <Evidence />
    </MemoryRouter>
  );
}

function clickEvTab(label) {
  const tabs = screen.getAllByRole("button").filter(
    b => b.className.includes("ev-tab") && b.textContent.includes(label)
  );
  fireEvent.click(tabs[0]);
}

beforeEach(() => vi.clearAllMocks());

describe("Evidence - rendering", () => {
  beforeEach(() => setupMocks());

  it("renders Evidence Manager heading", async () => {
    renderEvidence();
    await waitFor(() => expect(screen.getByText("Evidence Manager")).toBeTruthy());
  });

  it("renders project list", async () => {
    renderEvidence();
    await waitFor(() => expect(screen.getByText("Alpha")).toBeTruthy());
  });

  it("shows select prompt before project is chosen", async () => {
    renderEvidence();
    await waitFor(() =>
      expect(screen.getByText(/Select a project to manage evidence/i)).toBeTruthy()
    );
  });
});

describe("Evidence - project selection", () => {
  beforeEach(() => setupMocks());

  it("loads evidence when a project is clicked", async () => {
    renderEvidence();
    await waitFor(() => screen.getByText("Alpha"));
    fireEvent.click(screen.getByText("Alpha").closest(".ev-proj-row"));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/evidence/1"));
  });

  it("renders evidence tabs after project selected", async () => {
    renderEvidence();
    await waitFor(() => screen.getByText("Alpha"));
    fireEvent.click(screen.getByText("Alpha").closest(".ev-proj-row"));
    await waitFor(() => {
      const tabs = screen.getAllByRole("button").filter(b => b.className.includes("ev-tab") && b.textContent === "View");
      expect(tabs.length).toBeGreaterThan(0);
    });
  });

  it("shows test coverage after loading evidence", async () => {
    renderEvidence();
    await waitFor(() => screen.getByText("Alpha"));
    fireEvent.click(screen.getByText("Alpha").closest(".ev-proj-row"));
    await waitFor(() => expect(screen.getByText("85%")).toBeTruthy());
  });

  it("shows feedback text in view tab", async () => {
    renderEvidence();
    await waitFor(() => screen.getByText("Alpha"));
    fireEvent.click(screen.getByText("Alpha").closest(".ev-proj-row"));
    await waitFor(() => expect(screen.getByText(/Great work/i)).toBeTruthy());
  });

  it("shows achievement in view tab", async () => {
    renderEvidence();
    await waitFor(() => screen.getByText("Alpha"));
    fireEvent.click(screen.getByText("Alpha").closest(".ev-proj-row"));
    await waitFor(() => expect(screen.getByText(/Won hackathon/i)).toBeTruthy());
  });
});

describe("Evidence - tab switching", () => {
  beforeEach(() => setupMocks());

  async function selectProject() {
    renderEvidence();
    await waitFor(() => screen.getByText("Alpha"));
    fireEvent.click(screen.getByText("Alpha").closest(".ev-proj-row"));
    await waitFor(() =>
      screen.getAllByRole("button").filter(b => b.className.includes("ev-tab")).length > 0
    );
  }

  it("switches to Metric tab", async () => {
    await selectProject();
    clickEvTab("Metric");
    await waitFor(() => expect(screen.getByText("Add Manual Metric")).toBeTruthy());
  });

  it("switches to Feedback tab", async () => {
    await selectProject();
    const feedbackTab = screen.getAllByRole("button").find(
      b => b.className.includes("ev-tab") && b.textContent.trim() === "+ Feedback"
    );
    fireEvent.click(feedbackTab);
    await waitFor(() => {
      // Use getAllByText since "Add Feedback" appears in both h3 and button
      expect(screen.getAllByText(/Add Feedback/i).length).toBeGreaterThan(0);
    });
  });

  it("switches to Achievement tab", async () => {
    await selectProject();
    const achieveTab = screen.getAllByRole("button").find(
      b => b.className.includes("ev-tab") && b.textContent.trim() === "+ Achievement"
    );
    fireEvent.click(achieveTab);
    await waitFor(() => {
      // Use getAllByText since "Add Achievement" appears in both h3 and button
      expect(screen.getAllByText(/Add Achievement/i).length).toBeGreaterThan(0);
    });
  });
});

describe("Evidence - form validation", () => {
  beforeEach(() => setupMocks());

  async function goToMetricTab() {
    renderEvidence();
    await waitFor(() => screen.getByText("Alpha"));
    fireEvent.click(screen.getByText("Alpha").closest(".ev-proj-row"));
    await waitFor(() =>
      screen.getAllByRole("button").filter(b => b.className.includes("ev-tab")).length > 0
    );
    clickEvTab("Metric");
    await waitFor(() => screen.getByText("Add Manual Metric"));
  }

  it("shows error when adding metric without required fields", async () => {
    await goToMetricTab();
    fireEvent.click(screen.getByText("Add Metric"));
    await waitFor(() =>
      expect(screen.getByText(/Name and value required/i)).toBeTruthy()
    );
  });
});

describe("Evidence - empty state", () => {
  it("shows no evidence message when evidence is empty", async () => {
    setupMocks({ evidence: {} });
    renderEvidence();
    await waitFor(() => screen.getByText("Alpha"));
    fireEvent.click(screen.getByText("Alpha").closest(".ev-proj-row"));
    await waitFor(() =>
      expect(screen.getByText(/No evidence yet/i)).toBeTruthy()
    );
  });
});

describe("Evidence - API calls", () => {
  beforeEach(() => setupMocks());

  it("calls /projects on mount", async () => {
    renderEvidence();
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/projects"));
  });
});