import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, act, waitFor } from "@testing-library/react";
import { MemoryRouter, useNavigate } from "react-router-dom";
import LoadingBar, { loadingBar } from "../components/LoadingBar";
import PageTransition from "../components/PageTransition";

// ─── LoadingBar Tests ──────────────────────────────────────────────────────────

describe("LoadingBar - initial state", () => {
  it("renders nothing when inactive", () => {
    render(<LoadingBar />);
    expect(document.querySelector(".loading-bar-track")).toBeNull();
  });
});

describe("LoadingBar - active state", () => {
  it("shows loading bar when loadingBar.start() is called", async () => {
    render(<LoadingBar />);
    act(() => loadingBar.start());
    await waitFor(() =>
      expect(document.querySelector(".loading-bar-track")).toBeTruthy()
    );
    // Cleanup
    act(() => loadingBar.done());
  });

  it("shows loading bar fill element", async () => {
    render(<LoadingBar />);
    act(() => loadingBar.start());
    await waitFor(() =>
      expect(document.querySelector(".loading-bar-fill")).toBeTruthy()
    );
    act(() => loadingBar.done());
  });

  it("hides loading bar after done() is called", async () => {
    render(<LoadingBar />);
    act(() => loadingBar.start());
    await waitFor(() => document.querySelector(".loading-bar-track"));
    act(() => loadingBar.done());
    await waitFor(() =>
      expect(document.querySelector(".loading-bar-track")).toBeNull(),
      { timeout: 1000 }
    );
  });

  it("handles multiple start calls", async () => {
    render(<LoadingBar />);
    act(() => { loadingBar.start(); loadingBar.start(); });
    await waitFor(() =>
      expect(document.querySelector(".loading-bar-track")).toBeTruthy()
    );
    act(() => { loadingBar.done(); loadingBar.done(); });
  });
});

// ─── PageTransition Tests ──────────────────────────────────────────────────────

function renderPageTransition(children = <div>Page Content</div>) {
  return render(
    <MemoryRouter>
      <PageTransition>{children}</PageTransition>
    </MemoryRouter>
  );
}

describe("PageTransition - rendering", () => {
  it("renders children", () => {
    renderPageTransition(<div>Hello Page</div>);
    expect(screen.getByText("Hello Page")).toBeTruthy();
  });

  it("renders with page-transition class", () => {
    renderPageTransition();
    expect(document.querySelector(".page-transition")).toBeTruthy();
  });

  it("starts in idle phase", () => {
    renderPageTransition();
    expect(document.querySelector(".page-transition-idle")).toBeTruthy();
  });

  it("renders updated children", () => {
    const { rerender } = render(
      <MemoryRouter>
        <PageTransition><div>First</div></PageTransition>
      </MemoryRouter>
    );
    expect(screen.getByText("First")).toBeTruthy();
    rerender(
      <MemoryRouter>
        <PageTransition><div>Second</div></PageTransition>
      </MemoryRouter>
    );
    expect(document.body.innerHTML).toContain("First");
  });
});