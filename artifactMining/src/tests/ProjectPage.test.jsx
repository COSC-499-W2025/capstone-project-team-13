import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ProjectPage from "../pages/ProjectPage";

vi.mock("../apiClient", () => ({
  apiFetch: vi.fn(),
  projectName: (p) => p?.custom_description || p?.name || "Untitled",
}));

import { apiFetch } from "../apiClient";

const SAMPLE_PROJECT = {
  id: 1,
  name: "Alpha Project",
  project_type: "code",
  description: "A sample project",
  ai_description: "AI generated description",
  languages: ["Python", "JavaScript"],
  file_count: 10,
  lines_of_code: 500,
  importance_score: 8.5,
  is_featured: false,
  user_role: "Lead Developer",
  date_created: "2024-01-01T00:00:00",
  date_modified: "2024-06-01T00:00:00",
};

function setupMocks({ project = SAMPLE_PROJECT } = {}) {
  apiFetch.mockImplementation((url, opts) => {
    if (url === `/projects/1`) return Promise.resolve(project);
    if (url === `/projects/1/contributors`) return Promise.resolve([]);
    if (url === `/user/github-username`) return Promise.resolve({ github_username: null });
    if (url === `/configuration/current-configuration`)
      return Promise.resolve({ consent: { ai_consent_granted: true, basic_consent_granted: true }, ai_settings: { ai_enabled: true } });
    if (url.includes("/analyze")) return Promise.resolve({ results: { overview: "Analysis done" } });
    if (url === `/projects/1` && opts?.method === "PATCH") return Promise.resolve(project);
    if (url === `/projects/1` && opts?.method === "DELETE") return Promise.resolve({});
    return Promise.reject(new Error("Unmatched: " + url));
  });
}

function renderProjectPage(id = "1") {
  return render(
    <MemoryRouter initialEntries={[`/projects/${id}`]}>
      <Routes>
        <Route path="/projects/:projectId" element={<ProjectPage />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => vi.clearAllMocks());

describe("ProjectPage - loading state", () => {
  it("shows spinner while loading", () => {
    apiFetch.mockReturnValue(new Promise(() => {}));
    renderProjectPage();
    expect(document.querySelector(".spinner")).toBeTruthy();
  });
});

describe("ProjectPage - rendering", () => {
  beforeEach(() => setupMocks());

  it("renders project name", async () => {
    renderProjectPage();
    await waitFor(() => expect(screen.getByText("Alpha Project")).toBeTruthy());
  });

  it("renders project type tag", async () => {
    renderProjectPage();
    await waitFor(() => expect(screen.getByText("code")).toBeTruthy());
  });

  it("renders AI description", async () => {
    renderProjectPage();
    await waitFor(() => {
      expect(document.body.innerHTML).toContain("AI generated description");
    });
  });

  it("renders language tags", async () => {
    renderProjectPage();
    await waitFor(() => expect(screen.getByText("Python")).toBeTruthy());
  });

  it("renders file count", async () => {
    renderProjectPage();
    await waitFor(() => expect(screen.getByText(/10/)).toBeTruthy());
  });

  it("renders Edit button", async () => {
    renderProjectPage();
    await waitFor(() => expect(screen.getByText(/Edit/i)).toBeTruthy());
  });

  it("renders importance score", async () => {
    renderProjectPage();
    await waitFor(() => expect(screen.getByText(/8.5/)).toBeTruthy());
  });
});

describe("ProjectPage - editing", () => {
  beforeEach(() => setupMocks());

  it("shows edit form when Edit is clicked", async () => {
    renderProjectPage();
    await waitFor(() => screen.getByText(/Edit/i));
    fireEvent.click(screen.getByText(/Edit/i));
    await waitFor(() => {
      expect(screen.getAllByText(/Save/i).length).toBeGreaterThan(0);
    });
  });

  it("shows Cancel button in edit mode", async () => {
    renderProjectPage();
    await waitFor(() => screen.getByText(/Edit/i));
    fireEvent.click(screen.getByText(/Edit/i));
    await waitFor(() => expect(screen.getByText(/Cancel/i)).toBeTruthy());
  });

  it("exits edit mode on Cancel click", async () => {
    renderProjectPage();
    await waitFor(() => screen.getByText(/Edit/i));
    fireEvent.click(screen.getByText(/Edit/i));
    await waitFor(() => screen.getByText(/Cancel/i));
    fireEvent.click(screen.getByText(/Cancel/i));
    await waitFor(() => expect(screen.queryByText(/Edit/i)).toBeTruthy());
  });
});

describe("ProjectPage - AI analysis", () => {
  beforeEach(() => setupMocks());

  it("renders Run Analysis button", async () => {
    renderProjectPage();
    await waitFor(() => {
      const btns = screen.getAllByText(/Run Analysis/i).filter(el => el.tagName === "BUTTON" || el.closest("button"));
      expect(btns.length).toBeGreaterThan(0);
    });
  });

  it("calls analyze endpoint when Run Analysis is clicked", async () => {
    renderProjectPage();
    await waitFor(() => {
      const btns = screen.getAllByText(/Run Analysis/i).filter(el => {
        const btn = el.tagName === "BUTTON" ? el : el.closest("button");
        return btn && !btn.disabled;
      });
      expect(btns.length).toBeGreaterThan(0);
    });
    const btn = screen.getAllByText(/Run Analysis/i).find(el => {
      const b = el.tagName === "BUTTON" ? el : el.closest("button");
      return b && !b.disabled;
    });
    fireEvent.click(btn.tagName === "BUTTON" ? btn : btn.closest("button"));
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        "/projects/1/analyze",
        expect.objectContaining({ method: "POST" })
      )
    );
  });
});

describe("ProjectPage - error state", () => {
  it("shows not found message when project fetch fails", async () => {
    apiFetch.mockRejectedValue(new Error("Not found"));
    renderProjectPage();
    await waitFor(() => expect(screen.getByText(/not found/i)).toBeTruthy());
  });
});

describe("ProjectPage - API calls", () => {
  beforeEach(() => setupMocks());

  it("calls /projects/1 on mount", async () => {
    renderProjectPage();
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/projects/1"));
  });
});