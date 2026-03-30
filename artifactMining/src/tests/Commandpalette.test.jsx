import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import CommandPalette, { openCommandPalette } from "../components/CommandPalette";

vi.mock("../apiClient", () => ({
  apiFetch: vi.fn().mockResolvedValue([]),
  projectName: (p) => p?.name || "Untitled",
}));

function renderCommandPalette() {
  return render(
    <MemoryRouter>
      <CommandPalette />
    </MemoryRouter>
  );
}

beforeEach(() => vi.clearAllMocks());

describe("CommandPalette - closed state", () => {
  it("renders nothing when closed", () => {
    renderCommandPalette();
    expect(document.querySelector(".cp-modal")).toBeNull();
  });
});

describe("CommandPalette - opening", () => {
  it("opens on Ctrl+K keyboard shortcut", async () => {
    renderCommandPalette();
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    await waitFor(() => expect(document.querySelector(".cp-modal")).toBeTruthy());
  });

  it("opens via openCommandPalette() function", async () => {
    renderCommandPalette();
    openCommandPalette();
    await waitFor(() => expect(document.querySelector(".cp-modal")).toBeTruthy());
  });

  it("closes on Escape key", async () => {
    renderCommandPalette();
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    await waitFor(() => document.querySelector(".cp-modal"));
    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() => expect(document.querySelector(".cp-modal")).toBeNull());
  });

  it("closes when clicking backdrop", async () => {
    renderCommandPalette();
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    await waitFor(() => document.querySelector(".cp-backdrop"));
    fireEvent.click(document.querySelector(".cp-backdrop"));
    await waitFor(() => expect(document.querySelector(".cp-modal")).toBeNull());
  });
});

describe("CommandPalette - content", () => {
  it("renders search input when open", async () => {
    renderCommandPalette();
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    await waitFor(() => expect(document.querySelector(".cp-input")).toBeTruthy());
  });

  it("renders navigation commands", async () => {
    renderCommandPalette();
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    await waitFor(() => expect(screen.getByText("Dashboard")).toBeTruthy());
  });

  it("renders Projects nav item", async () => {
    renderCommandPalette();
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    await waitFor(() => expect(screen.getByText("Projects")).toBeTruthy());
  });

  it("renders keyboard shortcut hints in footer", async () => {
    renderCommandPalette();
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    await waitFor(() => expect(document.querySelector(".cp-footer")).toBeTruthy());
  });
});

describe("CommandPalette - search", () => {
  it("filters results based on query", async () => {
    renderCommandPalette();
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    await waitFor(() => document.querySelector(".cp-input"));
    fireEvent.change(document.querySelector(".cp-input"), { target: { value: "Dashboard" } });
    await waitFor(() => expect(screen.getByText("Dashboard")).toBeTruthy());
  });

  it("shows no results message for unmatched query", async () => {
    renderCommandPalette();
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    await waitFor(() => document.querySelector(".cp-input"));
    fireEvent.change(document.querySelector(".cp-input"), { target: { value: "xyzxyzxyz" } });
    await waitFor(() => expect(screen.getByText(/No results/i)).toBeTruthy());
  });
});