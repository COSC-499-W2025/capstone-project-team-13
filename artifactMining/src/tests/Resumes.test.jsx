import React from "react";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi, describe, test, expect, beforeEach, afterEach } from "vitest";
import Resumes from "../pages/Resumes";

const mockFetch = vi.fn();
global.fetch = mockFetch;

const sampleResume = {
  name: "Jane Doe",
  role: "Software Developer",
  contact: "jane@example.com",
  education: [
    { degree: "BSc Computer Science", institution: "UBCO", dates: "2021–2025" },
  ],
  awards: ["Dean's List 2024"],
  skills_by_level: {
    Expert: ["Python", "FastAPI"],
    Proficient: ["JavaScript"],
    Familiar: [],
  },
  projects: [
    {
      name: "Capstone",
      header: "Python · FastAPI",
      bullets: ["Built REST API with 10 endpoints", "Achieved 90% test coverage"],
      ats_score: 82,
    },
  ],
};

function setupFetchMocks({ aiConsent = false, resume = sampleResume } = {}) {
  mockFetch.mockImplementation((url, opts) => {
    if (url.includes("ai-consent-status")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ granted: aiConsent }),
      });
    }
    if (url.includes("/resume/generate")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ resume, message: "Resume generated" }),
      });
    }
    if (url.includes("/resume/") && (!opts || opts.method !== "POST")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ resume }),
      });
    }
    if (url.includes("/edit")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ resume }),
      });
    }
    return Promise.reject(new Error("Unmatched URL: " + url));
  });
}

function renderResumes() {
  return render(
    <MemoryRouter>
      <Resumes />
    </MemoryRouter>
  );
}

describe("Resumes - renders resume content", () => {
  beforeEach(() => setupFetchMocks());
  afterEach(() => mockFetch.mockReset());

  test("shows user name", async () => {
    renderResumes();
    await waitFor(() => screen.getByText("Jane Doe"));
  });

  test("shows Education and Awards section", async () => {
    renderResumes();
    await waitFor(() => screen.getByText("Education and Awards"));
  });

  test("shows education entry", async () => {
    renderResumes();
    await waitFor(() => screen.getByText("BSc Computer Science"));
  });

  test("shows skills section", async () => {
    renderResumes();
    await waitFor(() => screen.getByText("Skills"));
    const main = screen.getByRole("main");
    expect(within(main).getByText(/Python, FastAPI/)).toBeInTheDocument();
  });

  test("shows project bullets", async () => {
    renderResumes();
    await waitFor(() => screen.getByText("Built REST API with 10 endpoints"));
  });

  test("shows ATS score", async () => {
    renderResumes();
    await waitFor(() => screen.getByText(/82/));
    expect(screen.getByText(/ATS score/i)).toBeInTheDocument();
  });
});

describe("Resumes - awards management", () => {
  beforeEach(() => setupFetchMocks());
  afterEach(() => mockFetch.mockReset());

  test("pre-populated award from resume is shown in sidebar", async () => {
    renderResumes();
    // Scope to sidebar to avoid matching the duplicate in the resume doc
    const sidebar = await waitFor(() => screen.getByRole("complementary"));
    expect(within(sidebar).getByText("Dean's List 2024")).toBeInTheDocument();
  });

  test("adding an award appends it to the sidebar list", async () => {
    renderResumes();
    const sidebar = await waitFor(() => screen.getByRole("complementary"));
    const input = within(sidebar).getByPlaceholderText(/Add award/i);
    fireEvent.change(input, { target: { value: "Best Project Award" } });
    fireEvent.click(within(sidebar).getByText("+"));
    expect(within(sidebar).getByText("Best Project Award")).toBeInTheDocument();
  });

  test("removing an award removes it from the sidebar list", async () => {
    renderResumes();
    const sidebar = await waitFor(() => screen.getByRole("complementary"));
    const removeBtn = within(sidebar).getByText("×");
    fireEvent.click(removeBtn);
    await waitFor(() =>
      expect(within(sidebar).queryByText("Dean's List 2024")).not.toBeInTheDocument()
    );
  });
});

describe("Resumes - no AI consent hint", () => {
  beforeEach(() => setupFetchMocks({ aiConsent: false }));
  afterEach(() => mockFetch.mockReset());

  test("shows AI consent hint in sidebar", async () => {
    renderResumes();
    await waitFor(() => screen.getByText(/Enable AI consent/i));
  });
});

describe("Resumes - generate button", () => {
  beforeEach(() => setupFetchMocks());
  afterEach(() => mockFetch.mockReset());

  test("clicking Generate calls POST /resume/generate", async () => {
    renderResumes();
    await waitFor(() => screen.getByText("Jane Doe"));
    const btn = screen.getByText(/Generate \/ Refresh/i);
    fireEvent.click(btn);
    await waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/resume/generate"),
        expect.objectContaining({ method: "POST" })
      )
    );
  });
});