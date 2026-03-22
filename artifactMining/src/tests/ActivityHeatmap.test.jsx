import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ActivityHeatmap from "../pages/ActivityHeatmap";

vi.mock("../apiClient", () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from "../apiClient";

const NOW_YEAR = new Date().getFullYear();

const PROJECT_A = {
  id: 1,
  name: "Alpha",
  date_created: `${NOW_YEAR}-01-15T00:00:00`,
  date_modified: `${NOW_YEAR}-03-20T00:00:00`,
};
const PROJECT_B = {
  id: 2,
  name: "Beta",
  date_created: `${NOW_YEAR}-06-01T00:00:00`,
  date_modified: `${NOW_YEAR}-06-01T00:00:00`,
};

beforeEach(() => vi.clearAllMocks());

describe("ActivityHeatmap", () => {
  it("shows loading text initially", () => {
    apiFetch.mockReturnValue(new Promise(() => {}));
    render(<ActivityHeatmap />);
    expect(screen.getByText(/loading activity heatmap/i)).toBeTruthy();
  });

  it("renders the heatmap container after fetch", async () => {
    apiFetch.mockResolvedValue([PROJECT_A]);
    render(<ActivityHeatmap />);
    await waitFor(() => {
      expect(screen.getByTestId("activity-heatmap")).toBeTruthy();
    });
  });

  it("shows error message on fetch failure", async () => {
    apiFetch.mockRejectedValue(new Error("Server error"));
    render(<ActivityHeatmap />);
    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeTruthy();
    });
  });

  it("renders heatmap cells", async () => {
    apiFetch.mockResolvedValue([PROJECT_A, PROJECT_B]);
    render(<ActivityHeatmap />);
    await waitFor(() => {
      const cells = screen.getAllByTestId("heatmap-cell");
      expect(cells.length).toBeGreaterThan(0);
    });
  });

  it("displays current year by default", async () => {
    apiFetch.mockResolvedValue([]);
    render(<ActivityHeatmap />);
    await waitFor(() => {
      expect(screen.getByText(String(NOW_YEAR))).toBeTruthy();
    });
  });

  it("navigates to previous year on prev button click", async () => {
    apiFetch.mockResolvedValue([]);
    render(<ActivityHeatmap />);
    await waitFor(() => screen.getByTestId("prev-year"));
    fireEvent.click(screen.getByTestId("prev-year"));
    await waitFor(() => {
      expect(screen.getByText(String(NOW_YEAR - 1))).toBeTruthy();
    });
  });

  it("disables next-year button when already at current year", async () => {
    apiFetch.mockResolvedValue([]);
    render(<ActivityHeatmap />);
    await waitFor(() => screen.getByTestId("next-year"));
    expect(screen.getByTestId("next-year").disabled).toBe(true);
  });

  it("next-year button enables after going back a year", async () => {
    apiFetch.mockResolvedValue([]);
    render(<ActivityHeatmap />);
    await waitFor(() => screen.getByTestId("prev-year"));
    fireEvent.click(screen.getByTestId("prev-year"));
    await waitFor(() => {
      expect(screen.getByTestId("next-year").disabled).toBe(false);
    });
  });

  it("marks days with activity data-count > 0", async () => {
    apiFetch.mockResolvedValue([PROJECT_A]);
    render(<ActivityHeatmap />);
    await waitFor(() => {
      const cells = screen.getAllByTestId("heatmap-cell");
      const active = cells.filter(c => Number(c.dataset.count) > 0);
      expect(active.length).toBeGreaterThan(0);
    });
  });

  it("shows active days count in summary", async () => {
    apiFetch.mockResolvedValue([PROJECT_A]);
    render(<ActivityHeatmap />);
    await waitFor(() => {
      // Summary line contains "active day(s)"
      expect(screen.getByText(/active day/i)).toBeTruthy();
    });
  });

  it("calls /projects endpoint", async () => {
    apiFetch.mockResolvedValue([]);
    render(<ActivityHeatmap />);
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/projects"));
  });
});
