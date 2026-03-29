import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Deletion from "../pages/Deletion";

vi.mock("../apiClient", () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from "../apiClient";

const SAMPLE_PROJECTS = [
  { id: 1, name: "Alpha", project_type: "code", ai_description: "An AI desc" },
  { id: 2, name: "Beta", project_type: "data", ai_description: null },
];

function setupMocks() {
  apiFetch.mockImplementation((url, opts) => {
    if (url === "/projects") return Promise.resolve(SAMPLE_PROJECTS);
    if (url.includes("/ai-insights")) return Promise.resolve({});
    if (url === "/projects/ai-insights/all") return Promise.resolve({});
    if (url === "/projects/shared-files") return Promise.resolve([]);
    if (url === "/projects/cache-stats") return Promise.resolve({ total_cache_files: 5, total_cache_size_bytes: 2048 });
    if (url === "/projects/cache") return Promise.resolve({});
    if (url.match(/\/projects\/\d+$/)) return Promise.resolve({});
    return Promise.reject(new Error("Unmatched: " + url));
  });
}

function renderDeletion() {
  return render(
    <MemoryRouter>
      <Deletion />
    </MemoryRouter>
  );
}

// Helper: click a del-tab button by label text
function clickDelTab(label) {
  const tabs = screen.getAllByRole("button").filter(b => b.className.includes("del-tab") && b.textContent.includes(label));
  fireEvent.click(tabs[0]);
}

beforeEach(() => vi.clearAllMocks());

describe("Deletion - rendering", () => {
  beforeEach(() => setupMocks());

  it("renders Deletion Manager heading", async () => {
    renderDeletion();
    await waitFor(() => expect(screen.getByText("Deletion Manager")).toBeTruthy());
  });

  it("renders Delete Projects tab button", async () => {
    renderDeletion();
    await waitFor(() => {
      const tabs = screen.getAllByRole("button").filter(b => b.className.includes("del-tab") && b.textContent.includes("Delete"));
      expect(tabs.length).toBeGreaterThan(0);
    });
  });

  it("renders AI Insights tab button", async () => {
    renderDeletion();
    await waitFor(() => {
      const tabs = screen.getAllByRole("button").filter(b => b.className.includes("del-tab") && b.textContent.includes("AI"));
      expect(tabs.length).toBeGreaterThan(0);
    });
  });

  it("renders Cache tab button", async () => {
    renderDeletion();
    await waitFor(() => {
      const tabs = screen.getAllByRole("button").filter(b => b.className.includes("del-tab") && b.textContent.includes("Cache"));
      expect(tabs.length).toBeGreaterThan(0);
    });
  });

  it("renders project list", async () => {
    renderDeletion();
    await waitFor(() => expect(screen.getByText("Alpha")).toBeTruthy());
  });
});

describe("Deletion - project selection", () => {
  beforeEach(() => setupMocks());

  it("renders Select All button", async () => {
    renderDeletion();
    await waitFor(() => expect(screen.getByText("All")).toBeTruthy());
  });

  it("renders Clear Selection button", async () => {
    renderDeletion();
    await waitFor(() => expect(screen.getByText("None")).toBeTruthy());
  });

  it("selects a project on row click", async () => {
    renderDeletion();
    await waitFor(() => screen.getByText("Alpha"));
    fireEvent.click(screen.getByText("Alpha").closest(".del-proj-row"));
    await waitFor(() => {
      const checkbox = screen.getAllByRole("checkbox")[0];
      expect(checkbox.checked).toBe(true);
    });
  });

  it("selects all projects on All button click", async () => {
    renderDeletion();
    await waitFor(() => screen.getByText("All"));
    fireEvent.click(screen.getByText("All"));
    await waitFor(() => {
      const checkboxes = screen.getAllByRole("checkbox");
      expect(checkboxes.every(cb => cb.checked)).toBe(true);
    });
  });

  it("clears selection on None button click", async () => {
    renderDeletion();
    await waitFor(() => screen.getByText("All"));
    fireEvent.click(screen.getByText("All"));
    fireEvent.click(screen.getByText("None"));
    await waitFor(() => {
      const checkboxes = screen.getAllByRole("checkbox");
      expect(checkboxes.every(cb => !cb.checked)).toBe(true);
    });
  });
});

describe("Deletion - delete button state", () => {
  beforeEach(() => setupMocks());

  it("Delete button is disabled when no projects selected", async () => {
    renderDeletion();
    await waitFor(() => screen.getByText(/Delete 0 Projects/i));
    expect(screen.getByText(/Delete 0 Projects/i).closest("button").disabled).toBe(true);
  });
});

describe("Deletion - shared files", () => {
  beforeEach(() => setupMocks());

  it("renders Load Report button", async () => {
    renderDeletion();
    await waitFor(() => expect(screen.getByText("Load Report")).toBeTruthy());
  });

  it("calls shared-files endpoint on Load Report click", async () => {
    renderDeletion();
    await waitFor(() => screen.getByText("Load Report"));
    fireEvent.click(screen.getByText("Load Report"));
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith("/projects/shared-files")
    );
  });

  it("shows no shared files message after loading", async () => {
    renderDeletion();
    await waitFor(() => screen.getByText("Load Report"));
    fireEvent.click(screen.getByText("Load Report"));
    await waitFor(() => expect(screen.getByText(/No shared files detected/i)).toBeTruthy());
  });
});

describe("Deletion - AI Insights tab", () => {
  beforeEach(() => setupMocks());

  it("switches to AI Insights tab", async () => {
    renderDeletion();
    await waitFor(() => screen.getAllByRole("button"));
    clickDelTab("AI");
    await waitFor(() => expect(screen.getByText("Delete All AI Insights")).toBeTruthy());
  });

  it("shows has AI tag for projects with ai_description", async () => {
    renderDeletion();
    await waitFor(() => screen.getAllByRole("button"));
    clickDelTab("AI");
    await waitFor(() => expect(screen.getByText("has AI")).toBeTruthy());
  });
});

describe("Deletion - Cache tab", () => {
  beforeEach(() => setupMocks());

  it("switches to Cache tab", async () => {
    renderDeletion();
    await waitFor(() => screen.getAllByRole("button"));
    clickDelTab("Cache");
    await waitFor(() => expect(screen.getByText("Cache Statistics")).toBeTruthy());
  });

  it("renders Load Stats button in Cache tab", async () => {
    renderDeletion();
    await waitFor(() => screen.getAllByRole("button"));
    clickDelTab("Cache");
    await waitFor(() => expect(screen.getByText("Load Stats")).toBeTruthy());
  });

  it("calls cache-stats endpoint on Load Stats click", async () => {
    renderDeletion();
    await waitFor(() => screen.getAllByRole("button"));
    clickDelTab("Cache");
    await waitFor(() => screen.getByText("Load Stats"));
    fireEvent.click(screen.getByText("Load Stats"));
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith("/projects/cache-stats")
    );
  });
});

describe("Deletion - API calls", () => {
  beforeEach(() => setupMocks());

  it("calls /projects on mount", async () => {
    renderDeletion();
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/projects"));
  });
});