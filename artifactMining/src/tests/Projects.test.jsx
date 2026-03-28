import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Projects from "../pages/Projects";

vi.mock("../apiClient", () => ({
  apiFetch: vi.fn(),
  projectName: (p) => p?.custom_description || p?.name || "Untitled",
}));

import { apiFetch } from "../apiClient";

const SAMPLE_PROJECTS = [
  { id: 1, name: "Alpha", project_type: "code", importance_score: 9.0, languages: ["Python"], file_count: 5, total_size_bytes: 2048 },
  { id: 2, name: "Beta", project_type: "data", importance_score: 6.0, languages: ["R"], file_count: 2, total_size_bytes: 512 },
  { id: 3, name: "Gamma", project_type: "code", importance_score: 7.5, languages: ["JavaScript"], file_count: 8, total_size_bytes: 4096 },
];

function renderProjects() {
  return render(
    <MemoryRouter initialEntries={["/projects"]}>
      <Projects />
    </MemoryRouter>
  );
}

beforeEach(() => vi.clearAllMocks());

describe("Projects - loading state", () => {
  it("shows spinner while loading", () => {
    apiFetch.mockReturnValue(new Promise(() => {}));
    renderProjects();
    expect(document.querySelector(".spinner")).toBeTruthy();
  });
});

describe("Projects - rendering", () => {
  beforeEach(() => apiFetch.mockResolvedValue(SAMPLE_PROJECTS));

  it("renders the Projects heading", async () => {
    renderProjects();
    await waitFor(() => expect(screen.getByText("Projects")).toBeTruthy());
  });

  it("renders all project cards", async () => {
    renderProjects();
    await waitFor(() => {
      expect(screen.getByText("Alpha")).toBeTruthy();
      expect(screen.getByText("Beta")).toBeTruthy();
      expect(screen.getByText("Gamma")).toBeTruthy();
    });
  });

  it("renders Upload button", async () => {
    renderProjects();
    await waitFor(() => expect(screen.getByText("+ Upload")).toBeTruthy());
  });

  it("renders project type tags", async () => {
    renderProjects();
    await waitFor(() => expect(screen.getAllByText("code").length).toBeGreaterThan(0));
  });
});

describe("Projects - filtering", () => {
  beforeEach(() => apiFetch.mockResolvedValue(SAMPLE_PROJECTS));

  it("filters projects by search text", async () => {
    renderProjects();
    await waitFor(() => screen.getByText("Alpha"));
    const input = screen.getByPlaceholderText(/Search projects/i);
    fireEvent.change(input, { target: { value: "Alpha" } });
    await waitFor(() => {
      expect(screen.getByText("Alpha")).toBeTruthy();
      expect(screen.queryByText("Beta")).not.toBeInTheDocument();
    });
  });

  it("filters projects by type tab", async () => {
    renderProjects();
    await waitFor(() => screen.getAllByText("data"));
    // Click the tab-btn specifically, not the tag span
    const dataTab = screen.getAllByText("data").find(el => el.className.includes("tab-btn"));
    fireEvent.click(dataTab);
    await waitFor(() => {
      expect(screen.getByText("Beta")).toBeTruthy();
      expect(screen.queryByText("Alpha")).not.toBeInTheDocument();
    });
  });

  it("shows all projects when 'all' filter is selected", async () => {
    renderProjects();
    await waitFor(() => screen.getByText("all"));
    fireEvent.click(screen.getByText("all"));
    await waitFor(() => {
      expect(screen.getByText("Alpha")).toBeTruthy();
      expect(screen.getByText("Beta")).toBeTruthy();
    });
  });
});

describe("Projects - empty state", () => {
  it("shows empty state when no projects found", async () => {
    apiFetch.mockResolvedValue([]);
    renderProjects();
    await waitFor(() =>
      expect(screen.getByText(/No projects found/i)).toBeTruthy()
    );
  });
});

describe("Projects - subtabs", () => {
  beforeEach(() => apiFetch.mockResolvedValue(SAMPLE_PROJECTS));

  it("renders All Projects subtab", async () => {
    renderProjects();
    await waitFor(() => expect(screen.getByText("All Projects")).toBeTruthy());
  });

  it("renders Deletion Manager subtab", async () => {
    renderProjects();
    await waitFor(() => expect(screen.getByText("Deletion Manager")).toBeTruthy());
  });
});

describe("Projects - API calls", () => {
  it("calls /projects endpoint on mount", async () => {
    apiFetch.mockResolvedValue([]);
    renderProjects();
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/projects"));
  });
});