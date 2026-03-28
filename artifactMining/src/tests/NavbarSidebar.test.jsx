import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";

// ─── Navbar Tests ──────────────────────────────────────────────────────────────

function renderNavbar(initialPath = "/") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Navbar />
    </MemoryRouter>
  );
}

describe("Navbar - rendering", () => {
  it("renders the brand link", () => {
    renderNavbar();
    expect(screen.getByText(/Digital Artifact Mining/i)).toBeTruthy();
  });

  it("renders Projects nav link", () => {
    renderNavbar();
    expect(screen.getByText("Projects")).toBeTruthy();
  });

  it("renders Skills nav link", () => {
    renderNavbar();
    expect(screen.getByText("Skills")).toBeTruthy();
  });

  it("renders Portfolio nav link", () => {
    renderNavbar();
    expect(screen.getByText("Portfolio")).toBeTruthy();
  });

  it("renders Resume nav link", () => {
    renderNavbar();
    expect(screen.getByText("Resume")).toBeTruthy();
  });

  it("renders Tools dropdown trigger", () => {
    renderNavbar();
    expect(screen.getByText(/Tools/i)).toBeTruthy();
  });

  it("renders Profile link", () => {
    renderNavbar();
    expect(screen.getByText("Profile")).toBeTruthy();
  });
});

describe("Navbar - active states", () => {
  it("marks brand as active on dashboard route", () => {
    renderNavbar("/");
    const brand = screen.getByText(/Digital Artifact Mining/i);
    expect(brand.className).toContain("active");
  });

  it("marks Projects as active on /projects route", () => {
    renderNavbar("/projects");
    const link = screen.getByText("Projects");
    expect(link.className).toContain("active");
  });

  it("marks Skills as active on /skills route", () => {
    renderNavbar("/skills");
    const link = screen.getByText("Skills");
    expect(link.className).toContain("active");
  });

  it("marks Profile as active on /settings route", () => {
    renderNavbar("/settings");
    const link = screen.getByText("Profile");
    expect(link.className).toContain("active");
  });

  it("marks Projects as active on /upload route", () => {
    renderNavbar("/upload");
    const link = screen.getByText("Projects");
    expect(link.className).toContain("active");
  });
});

describe("Navbar - Tools dropdown", () => {
  it("dropdown menu is hidden by default", () => {
    renderNavbar();
    expect(screen.queryByText("Evidence")).not.toBeInTheDocument();
    expect(screen.queryByText("Analysis")).not.toBeInTheDocument();
  });

  it("opens dropdown on Tools click", async () => {
    renderNavbar();
    fireEvent.click(screen.getByText(/Tools/i));
    await waitFor(() => {
      expect(screen.getByText("Evidence")).toBeTruthy();
      expect(screen.getByText("Analysis")).toBeTruthy();
    });
  });

  it("closes dropdown when clicking the navbar container", async () => {
    const { container } = renderNavbar();
    fireEvent.click(screen.getByText(/Tools/i));
    await waitFor(() => screen.getByText("Evidence"));
    // Click the nav element itself (which has the onClick close handler)
    fireEvent.click(container.querySelector("nav.navbar"));
    await waitFor(() =>
      expect(screen.queryByText("Evidence")).not.toBeInTheDocument()
    );
  });

  it("Tools button has aria-expanded false by default", () => {
    renderNavbar();
    const btn = screen.getByRole("button", { name: /Tools/i });
    expect(btn.getAttribute("aria-expanded")).toBe("false");
  });

  it("Tools button has aria-expanded true when open", async () => {
    renderNavbar();
    const btn = screen.getByRole("button", { name: /Tools/i });
    fireEvent.click(btn);
    await waitFor(() =>
      expect(btn.getAttribute("aria-expanded")).toBe("true")
    );
  });
});

// ─── Sidebar Tests ─────────────────────────────────────────────────────────────

function renderSidebar() {
  return render(
    <MemoryRouter>
      <Sidebar />
    </MemoryRouter>
  );
}

describe("Sidebar - rendering", () => {
  it("renders the Resume Analyzer heading", () => {
    renderSidebar();
    expect(screen.getByText("Resume Analyzer")).toBeTruthy();
  });

  it("renders Dashboard link", () => {
    renderSidebar();
    expect(screen.getByText("Dashboard")).toBeTruthy();
  });

  it("renders Upload Resume link", () => {
    renderSidebar();
    expect(screen.getByText("Upload Resume")).toBeTruthy();
  });

  it("renders View Resumes link", () => {
    renderSidebar();
    expect(screen.getByText("View Resumes")).toBeTruthy();
  });

  it("renders Settings link", () => {
    renderSidebar();
    expect(screen.getByText("Settings")).toBeTruthy();
  });

  it("Dashboard link points to /", () => {
    renderSidebar();
    const link = screen.getByText("Dashboard").closest("a");
    expect(link.getAttribute("href")).toBe("/");
  });

  it("Upload Resume link points to /upload", () => {
    renderSidebar();
    const link = screen.getByText("Upload Resume").closest("a");
    expect(link.getAttribute("href")).toBe("/upload");
  });
});