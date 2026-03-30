import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import WebShowcase from "../pages/WebShowcase";

vi.mock("../apiClient", () => ({
  apiFetch: vi.fn(),
  projectName: (p) => p?.name || "Untitled",
}));

import { apiFetch } from "../apiClient";

const SAMPLE_SHOWCASE = {
  projects: [
    {
      id: 1,
      name: "Alpha Project",
      project_type: "code",
      description: "A showcase project",
      importance_score: 9.0,
      languages: ["Python"],
      skills: ["Django"],
      file_count: 10,
      lines_of_code: 500,
      is_featured: true,
      evolution: [{ label: "Initial commit", date: "2024-01-01" }],
    },
    {
      id: 2,
      name: "Beta Project",
      project_type: "data",
      description: "A data project",
      importance_score: 7.5,
      languages: ["R"],
      skills: [],
      file_count: 5,
      lines_of_code: 200,
      is_featured: false,
      evolution: [],
    },
  ],
};

function setupMocks({ showcase = SAMPLE_SHOWCASE } = {}) {
  apiFetch.mockImplementation((url) => {
    if (url === "/portfolio/showcase") return Promise.resolve(showcase);
    return Promise.reject(new Error("Unmatched: " + url));
  });
}

function renderWebShowcase() {
  return render(
    <MemoryRouter>
      <WebShowcase />
    </MemoryRouter>
  );
}

beforeEach(() => vi.clearAllMocks());

describe("WebShowcase - loading state", () => {
  it("shows spinner while loading", () => {
    apiFetch.mockReturnValue(new Promise(() => {}));
    renderWebShowcase();
    expect(document.querySelector(".spinner")).toBeTruthy();
  });
});

describe("WebShowcase - rendering", () => {
  beforeEach(() => setupMocks());

  it("renders Web Portfolio Showcase heading", async () => {
    renderWebShowcase();
    await waitFor(() => expect(screen.getByText("Web Portfolio Showcase")).toBeTruthy());
  });

  it("renders project cards", async () => {
    renderWebShowcase();
    await waitFor(() => expect(screen.getByText("Alpha Project")).toBeTruthy());
  });

  it("renders all projects", async () => {
    renderWebShowcase();
    await waitFor(() => {
      expect(screen.getByText("Alpha Project")).toBeTruthy();
      expect(screen.getByText("Beta Project")).toBeTruthy();
    });
  });

  it("renders rank numbers", async () => {
    renderWebShowcase();
    await waitFor(() => expect(screen.getByText("#1")).toBeTruthy());
  });

  it("renders Featured tag for featured projects", async () => {
    renderWebShowcase();
    await waitFor(() => expect(screen.getByText("Featured")).toBeTruthy());
  });

  it("renders project description", async () => {
    renderWebShowcase();
    await waitFor(() => expect(screen.getByText("A showcase project")).toBeTruthy());
  });

  it("renders language tags", async () => {
    renderWebShowcase();
    await waitFor(() => expect(screen.getByText("Python")).toBeTruthy());
  });

  it("renders evolution timeline", async () => {
    renderWebShowcase();
    await waitFor(() => expect(screen.getByText("Initial commit")).toBeTruthy());
  });
});

describe("WebShowcase - empty state", () => {
  it("shows empty state when no projects", async () => {
    setupMocks({ showcase: { projects: [] } });
    renderWebShowcase();
    await waitFor(() =>
      expect(screen.getByText(/No projects yet/i)).toBeTruthy()
    );
  });
});

describe("WebShowcase - error state", () => {
  it("shows error message on fetch failure", async () => {
    apiFetch.mockRejectedValue(new Error("Network error"));
    renderWebShowcase();
    await waitFor(() =>
      expect(screen.getByText(/Network error/i)).toBeTruthy()
    );
  });
});

describe("WebShowcase - API calls", () => {
  beforeEach(() => setupMocks());

  it("calls /portfolio/showcase endpoint on mount", async () => {
    renderWebShowcase();
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith("/portfolio/showcase")
    );
  });
});