import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi, describe, test, expect, beforeEach, afterEach } from "vitest";
import SkillsTimeline from "../pages/SkillsTimeline";

const mockFetch = vi.fn();
global.fetch = mockFetch;

const sampleSkills = [
  {
    name: "Python",
    first_seen: "2023-01-01",
    last_seen: "2024-06-01",
    project_count: 2,
    projects: [
      {
        project_id: 1,
        project_name: "Project A",
        project_type: "code",
        first_activity_date: "2023-01-01",
        last_activity_date: "2023-06-01",
        duration_days: 151,
      },
      {
        project_id: 2,
        project_name: "Project B",
        project_type: "code",
        first_activity_date: "2024-01-01",
        last_activity_date: "2024-06-01",
        duration_days: 152,
      },
    ],
  },
  {
    name: "React",
    first_seen: "2024-01-01",
    last_seen: "2024-09-01",
    project_count: 1,
    projects: [
      {
        project_id: 2,
        project_name: "Project B",
        project_type: "code",
        first_activity_date: "2024-01-01",
        last_activity_date: "2024-09-01",
        duration_days: 244,
      },
    ],
  },
];

function setupFetchMocks({ skills = sampleSkills, ok = true } = {}) {
  mockFetch.mockImplementation((url) => {
    if (url.includes("/skills/timeline")) {
      return Promise.resolve({
        ok,
        json: () => Promise.resolve({ skills }),
      });
    }
    return Promise.reject(new Error("Unmatched URL: " + url));
  });
}

function renderSkillsTimeline() {
  return render(
    <MemoryRouter>
      <SkillsTimeline />
    </MemoryRouter>
  );
}

describe("SkillsTimeline", () => {
  afterEach(() => mockFetch.mockReset());

  test("shows loading state initially", () => {
    setupFetchMocks();
    renderSkillsTimeline();
    expect(screen.getByText(/loading skills/i)).toBeInTheDocument();
  });

  test("renders skill names after loading", async () => {
    setupFetchMocks();
    renderSkillsTimeline();
    await waitFor(() => screen.getByText("Python"));
    expect(screen.getByText("React")).toBeInTheDocument();
  });

  test("shows empty message when no skills returned", async () => {
    setupFetchMocks({ skills: [] });
    renderSkillsTimeline();
    await waitFor(() =>
      screen.getByText(/no skills found/i)
    );
  });

  test("shows error message on failed fetch", async () => {
    setupFetchMocks({ ok: false });
    renderSkillsTimeline();
    await waitFor(() =>
      screen.getByText(/failed to load skills/i)
    );
  });

  test("shows project count for each skill", async () => {
    setupFetchMocks();
    renderSkillsTimeline();
    await waitFor(() => screen.getByText("Python"));
    expect(screen.getByText(/2 projects/i)).toBeInTheDocument();
    expect(screen.getByText(/1 project/i)).toBeInTheDocument();
  });
});