import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import NotFound from "../pages/NotFound";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

function renderNotFound() {
  return render(
    <MemoryRouter>
      <NotFound />
    </MemoryRouter>
  );
}

describe("NotFound - rendering", () => {
  it("renders 404 code", () => {
    renderNotFound();
    expect(screen.getByText("404")).toBeTruthy();
  });

  it("renders page not found title", () => {
    renderNotFound();
    expect(screen.getByText("Page not found")).toBeTruthy();
  });

  it("renders descriptive message", () => {
    renderNotFound();
    expect(screen.getByText(/doesn't exist or was moved/i)).toBeTruthy();
  });

  it("renders Go to Dashboard button", () => {
    renderNotFound();
    expect(screen.getByText("Go to Dashboard")).toBeTruthy();
  });

  it("renders Go Back button", () => {
    renderNotFound();
    expect(screen.getByText("Go Back")).toBeTruthy();
  });
});

describe("NotFound - navigation", () => {
  it("navigates to dashboard on Go to Dashboard click", () => {
    renderNotFound();
    fireEvent.click(screen.getByText("Go to Dashboard"));
    expect(mockNavigate).toHaveBeenCalledWith("/");
  });

  it("navigates back on Go Back click", () => {
    renderNotFound();
    fireEvent.click(screen.getByText("Go Back"));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });
});