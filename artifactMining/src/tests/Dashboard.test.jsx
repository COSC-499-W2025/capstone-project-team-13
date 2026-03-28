import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Dashboard from "../pages/Dashboard";

vi.mock("../apiClient", () => ({
  apiFetch: vi.fn(),
  projectName: (p) => p?.custom_description || p?.name || "Untitled",
}));

import { apiFetch } from "../apiClient";

const SAMPLE_PROJECTS = [
  { id: 1, name: "Alpha", project_type: "code", importance_score: 9.5, languages: ["Python"], file_count: 5, total_size_bytes: 1024 },
  { id: 2, name: "Beta", project_type: "data", importance_score: 7.0, languages: ["R"], file_count: 3, total_size_bytes: 512 },
];

const SAMPLE_SKILLS = {
  skills: [
    { name: "Python", count: 3 },
    { name: "React", count: 2 },
  ],
};

const SAMPLE_PORTFOLIO = {
  projects: [{ id: 1 }, { id: 2 }],
};

function setupMocks({ projects = SAMPLE_PROJECTS, skills = SAMPLE_SKILLS, portfolio = SAMPLE_PORTFOLIO } = {}) {
  apiFetch.mockImplementation((url) => {
    if (url === "/projects") return Promise.resolve(projects);
    if (url === "/skills/") return Promise.resolve(skills);
    if (url === "/portfolio") return Promise.resolve(portfolio);
    return Promise.reject(new Error("Unmatched URL: " + url));
  });
}

function renderDashboard() {
  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>
  );
}

beforeEach(() => vi.clearAllMocks());

describe("Dashboard - loading state", () => {
  it("shows spinner while loading", () => {
    apiFetch.mockReturnValue(new Promise(() => {}));
    renderDashboard();
    expect(document.querySelector(".spinner")).toBeTruthy();
  });
});

describe("Dashboard - stat cards", () => {
  beforeEach(() => setupMocks());

  it("renders the Dashboard heading", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText("Dashboard")).toBeTruthy());
  });

  it("displays Projects stat label", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText("Projects")).toBeTruthy());
  });

  it("displays Skills stat label", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText("Skills")).toBeTruthy());
  });

  it("shows Upload Project button", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText("+ Upload Project")).toBeTruthy());
  });
});

describe("Dashboard - top projects", () => {
  beforeEach(() => setupMocks());

  it("renders top project names", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText("Alpha")).toBeTruthy());
  });

  it("renders View All button", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText(/View All/i)).toBeTruthy());
  });

  it("renders project type tags", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText("code")).toBeTruthy());
  });
});

describe("Dashboard - skills section", () => {
  beforeEach(() => setupMocks());

  it("renders top skill chips", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText("Python")).toBeTruthy());
  });

  it("renders All Skills button", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText(/All Skills/i)).toBeTruthy());
  });
});

describe("Dashboard - portfolio card", () => {
  beforeEach(() => setupMocks());

  it("shows portfolio project count when portfolio exists", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText(/2 project\(s\) in your portfolio/i)).toBeTruthy());
  });

  it("renders Open Portfolio button", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText(/Open Portfolio/i)).toBeTruthy());
  });
});

describe("Dashboard - empty states", () => {
  it("shows no projects message when projects list is empty", async () => {
    setupMocks({ projects: [], skills: { skills: [] }, portfolio: null });
    renderDashboard();
    await waitFor(() => expect(screen.getByText(/No projects yet/i)).toBeTruthy());
  });

  it("shows no skills message when skills list is empty", async () => {
    setupMocks({ projects: [], skills: { skills: [] }, portfolio: null });
    renderDashboard();
    await waitFor(() => expect(screen.getByText(/No skills detected yet/i)).toBeTruthy());
  });

  it("shows generate portfolio message when portfolio is null", async () => {
    setupMocks({ portfolio: null });
    renderDashboard();
    await waitFor(() => expect(screen.getByText(/Generate your portfolio/i)).toBeTruthy());
  });
});

describe("Dashboard - API calls", () => {
  beforeEach(() => setupMocks());

  it("calls /projects endpoint", async () => {
    renderDashboard();
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/projects"));
  });

  it("calls /skills/ endpoint", async () => {
    renderDashboard();
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/skills/"));
  });

  it("calls /portfolio endpoint", async () => {
    renderDashboard();
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/portfolio"));
  });
});