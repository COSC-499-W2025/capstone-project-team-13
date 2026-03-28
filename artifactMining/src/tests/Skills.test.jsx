import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Skills from "../pages/Skills";

vi.mock("../apiClient", () => ({
  apiFetch: vi.fn(),
  projectName: (p) => p?.custom_description || p?.name || "Untitled",
}));

import { apiFetch } from "../apiClient";

const SAMPLE_SKILLS = [
  { name: "Python", count: 5, projects: [{ project_id: 1, project_name: "Alpha", project_type: "code" }] },
  { name: "React", count: 2, projects: [{ project_id: 2, project_name: "Beta", project_type: "web" }] },
];

const SAMPLE_ANALYTICS = {
  insights: {
    top_skills: SAMPLE_SKILLS,
    skill_diversity: 0.85,
  },
  raw: { co_occurrence: [] },
};

function setupMocks({ skills = SAMPLE_SKILLS, analytics = SAMPLE_ANALYTICS } = {}) {
  apiFetch.mockImplementation((url) => {
    if (url === "/skills/") return Promise.resolve({ skills });
    if (url === "/analytics/skills") return Promise.resolve(analytics);
    if (url.startsWith("/skills/")) {
      const name = decodeURIComponent(url.replace("/skills/", ""));
      const found = skills.find((s) => s.name === name);
      return Promise.resolve(found
        ? { project_count: found.count, projects: found.projects }
        : { project_count: 0, projects: [] });
    }
    return Promise.reject(new Error("Unmatched URL: " + url));
  });
}

function renderSkills() {
  return render(
    <MemoryRouter>
      <Skills />
    </MemoryRouter>
  );
}

// Click the skill-row div (not the top chip) by finding the skill-name span
function clickSkillRow(name) {
  const allMatches = screen.getAllByText(name);
  const skillNameSpan = allMatches.find(el => el.className === "skill-name");
  fireEvent.click(skillNameSpan.closest(".skill-row"));
}

beforeEach(() => vi.clearAllMocks());

describe("Skills - loading state", () => {
  it("shows spinner while loading", () => {
    apiFetch.mockReturnValue(new Promise(() => {}));
    renderSkills();
    expect(document.querySelector(".spinner")).toBeTruthy();
  });
});

describe("Skills - rendering", () => {
  beforeEach(() => setupMocks());

  it("renders the Skills heading", async () => {
    renderSkills();
    await waitFor(() => expect(screen.getByText("Skills")).toBeTruthy());
  });

  it("renders skill names in the list", async () => {
    renderSkills();
    await waitFor(() => {
      expect(screen.getAllByText("Python").length).toBeGreaterThan(0);
    });
  });

  it("renders correct skill count label", async () => {
    renderSkills();
    await waitFor(() => expect(screen.getByText(/5 projects/i)).toBeTruthy());
  });

  it("renders total skills stat", async () => {
    renderSkills();
    await waitFor(() => expect(screen.getByText("Total Skills")).toBeTruthy());
  });

  it("renders diversity score", async () => {
    renderSkills();
    await waitFor(() => expect(screen.getByText("0.85")).toBeTruthy());
  });
});

describe("Skills - filtering", () => {
  beforeEach(() => setupMocks());

  it("filters skills by input text", async () => {
    renderSkills();
    await waitFor(() => screen.getAllByText("Python"));
    const input = screen.getByPlaceholderText(/Filter skills/i);
    fireEvent.change(input, { target: { value: "Python" } });
    await waitFor(() => {
      // After filtering to Python, React's count label should be gone
      expect(screen.queryByText(/2 projects/i)).not.toBeInTheDocument();
    });
  });
});

describe("Skills - detail panel", () => {
  beforeEach(() => setupMocks());

  it("shows skill detail on row click", async () => {
    renderSkills();
    await waitFor(() => screen.getAllByText("Python"));
    clickSkillRow("Python");
    await waitFor(() => expect(screen.getByText(/Used in 5 project/i)).toBeTruthy());
  });

  it("shows project name in skill detail", async () => {
    renderSkills();
    await waitFor(() => screen.getAllByText("Python"));
    clickSkillRow("Python");
    await waitFor(() => expect(screen.getByText("Alpha")).toBeTruthy());
  });

  it("collapses skill detail on second click", async () => {
    renderSkills();
    await waitFor(() => screen.getAllByText("Python"));
    clickSkillRow("Python");
    await waitFor(() => screen.getByText(/Used in 5 project/i));
    clickSkillRow("Python");
    await waitFor(() =>
      expect(screen.queryByText(/Used in 5 project/i)).not.toBeInTheDocument()
    );
  });
});

describe("Skills - empty state", () => {
  it("shows empty state message when no skills found", async () => {
    apiFetch.mockImplementation((url) => {
      if (url === "/skills/") return Promise.resolve({ skills: [] });
      if (url === "/analytics/skills") return Promise.resolve(null);
      return Promise.reject(new Error("Unmatched"));
    });
    renderSkills();
    await waitFor(() => {
      // Message appears in both alert and empty-state, use getAllByText
      expect(screen.getAllByText(/No skills found/i).length).toBeGreaterThan(0);
    });
  });
});

describe("Skills - API calls", () => {
  beforeEach(() => setupMocks());

  it("calls /skills/ endpoint on mount", async () => {
    renderSkills();
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/skills/"));
  });

  it("calls /analytics/skills endpoint on mount", async () => {
    renderSkills();
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/analytics/skills"));
  });
});