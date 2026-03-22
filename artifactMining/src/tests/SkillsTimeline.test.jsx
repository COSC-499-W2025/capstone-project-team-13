import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import SkillsTimeline from "../pages/SkillsTimeline";

// Mock apiFetch
vi.mock("../apiClient", () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from "../apiClient";

const SKILL_A = {
  name: "Python",
  first_seen: "2022-01-01",
  last_seen: "2024-06-01",
  project_count: 3,
  projects: [],
};
const SKILL_B = {
  name: "React",
  first_seen: "2023-03-01",
  last_seen: "2024-01-01",
  project_count: 1,
  projects: [],
};

beforeEach(() => vi.clearAllMocks());

describe("SkillsTimeline", () => {
  it("shows loading text initially", () => {
    apiFetch.mockReturnValue(new Promise(() => {})); // never resolves
    render(<SkillsTimeline />);
    expect(screen.getByText(/loading skills timeline/i)).toBeTruthy();
  });

  it("renders skill rows after fetch", async () => {
    apiFetch.mockResolvedValue({ skills: [SKILL_A, SKILL_B] });
    render(<SkillsTimeline />);
    await waitFor(() => {
      expect(screen.getAllByTestId("skill-row").length).toBe(2);
    });
  });

  it("renders the timeline container", async () => {
    apiFetch.mockResolvedValue({ skills: [SKILL_A] });
    render(<SkillsTimeline />);
    await waitFor(() => {
      expect(screen.getByTestId("skills-timeline")).toBeTruthy();
    });
  });

  it("shows error message on fetch failure", async () => {
    apiFetch.mockRejectedValue(new Error("Network error"));
    render(<SkillsTimeline />);
    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeTruthy();
    });
  });

  it("shows empty state when no skills have dates", async () => {
    const noDate = { name: "Go", first_seen: null, last_seen: null, project_count: 1, projects: [] };
    apiFetch.mockResolvedValue({ skills: [noDate] });
    render(<SkillsTimeline />);
    await waitFor(() => {
      expect(screen.getByText(/no skills match/i)).toBeTruthy();
    });
  });

  it("filter input narrows visible skills", async () => {
    apiFetch.mockResolvedValue({ skills: [SKILL_A, SKILL_B] });
    render(<SkillsTimeline />);
    await waitFor(() => screen.getAllByTestId("skill-row"));

    fireEvent.change(screen.getByTestId("filter-input"), { target: { value: "Python" } });
    await waitFor(() => {
      expect(screen.getAllByTestId("skill-row").length).toBe(1);
    });
  });

  it("minProjects filter hides skills below threshold", async () => {
    apiFetch.mockResolvedValue({ skills: [SKILL_A, SKILL_B] }); // B has count 1
    render(<SkillsTimeline />);
    await waitFor(() => screen.getAllByTestId("skill-row"));

    fireEvent.change(screen.getByTestId("min-projects-select"), { target: { value: "2" } });
    await waitFor(() => {
      // Only Python (count 3) remains
      expect(screen.getAllByTestId("skill-row").length).toBe(1);
    });
  });

  it("calls /skills/timeline endpoint", async () => {
    apiFetch.mockResolvedValue({ skills: [] });
    render(<SkillsTimeline />);
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/skills/timeline"));
  });

  it("renders project count badge for each skill", async () => {
    apiFetch.mockResolvedValue({ skills: [SKILL_A] });
    render(<SkillsTimeline />);
    await waitFor(() => {
      expect(screen.getByText("×3")).toBeTruthy();
    });
  });

  it("shows summary count text", async () => {
    apiFetch.mockResolvedValue({ skills: [SKILL_A, SKILL_B] });
    render(<SkillsTimeline />);
    await waitFor(() => {
      expect(screen.getByText(/showing 2 skills/i)).toBeTruthy();
    });
  });
});
