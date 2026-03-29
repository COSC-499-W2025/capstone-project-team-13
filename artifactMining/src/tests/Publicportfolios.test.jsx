import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { PublicPortfoliosList, PublicPortfolioView } from "../pages/PublicPortfolios";

const mockFetch = vi.fn();
global.fetch = mockFetch;

const SAMPLE_PORTFOLIOS = [
  { user_id: 1, display_name: "Jane Doe", project_count: 3, top_skills: ["Python", "React"], summary: "A great developer" },
  { user_id: 2, display_name: "John Smith", project_count: 5, top_skills: ["Java"], summary: "Backend specialist" },
];

const SAMPLE_PORTFOLIO_VIEW = {
  display_name: "Jane Doe",
  summary_text: "A passionate developer",
  projects: [
    { id: 1, name: "Alpha Project", type: "code", description: "A cool project", skills: ["Python"], languages: ["Python"] },
  ],
  stats: { total_projects: 1, total_skills: 3 },
};

function setupListMocks() {
  mockFetch.mockImplementation((url) => {
    if (url.includes("/public/portfolios") && !url.includes("/public/portfolios/")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ portfolios: SAMPLE_PORTFOLIOS }) });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });
}

function setupViewMocks() {
  mockFetch.mockImplementation((url) => {
    if (url.includes("/public/portfolios/1")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(SAMPLE_PORTFOLIO_VIEW) });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });
}

beforeEach(() => vi.clearAllMocks());
afterEach(() => mockFetch.mockReset());

// ─── PublicPortfoliosList Tests ────────────────────────────────────────────────

function renderList() {
  return render(
    <MemoryRouter>
      <PublicPortfoliosList />
    </MemoryRouter>
  );
}

describe("PublicPortfoliosList - rendering", () => {
  beforeEach(() => setupListMocks());

  it("renders Public Portfolios heading", async () => {
    renderList();
    await waitFor(() => expect(screen.getByText("Public Portfolios")).toBeTruthy());
  });

  it("renders portfolio cards", async () => {
    renderList();
    await waitFor(() => expect(screen.getByText("Jane Doe")).toBeTruthy());
  });

  it("renders all portfolios", async () => {
    renderList();
    await waitFor(() => {
      expect(screen.getByText("Jane Doe")).toBeTruthy();
      expect(screen.getByText("John Smith")).toBeTruthy();
    });
  });

  it("renders skill tags", async () => {
    renderList();
    await waitFor(() => expect(screen.getByText("Python")).toBeTruthy());
  });

  it("renders search input", async () => {
    renderList();
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/Search by name/i)).toBeTruthy()
    );
  });
});

describe("PublicPortfoliosList - search", () => {
  beforeEach(() => setupListMocks());

  it("filters portfolios by search text", async () => {
    renderList();
    await waitFor(() => screen.getByText("Jane Doe"));
    fireEvent.change(screen.getByPlaceholderText(/Search by name/i), {
      target: { value: "Jane" },
    });
    await waitFor(() => {
      expect(screen.getByText("Jane Doe")).toBeTruthy();
      expect(screen.queryByText("John Smith")).not.toBeInTheDocument();
    });
  });
});

describe("PublicPortfoliosList - empty state", () => {
  it("shows empty message when no portfolios", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ portfolios: [] }),
    });
    renderList();
    await waitFor(() =>
      expect(screen.getByText(/No public portfolios available yet/i)).toBeTruthy()
    );
  });

  it("shows error message on fetch failure", async () => {
    mockFetch.mockResolvedValue({ ok: false });
    renderList();
    await waitFor(() =>
      expect(screen.getByText(/Could not load/i)).toBeTruthy()
    );
  });
});

// ─── PublicPortfolioView Tests ─────────────────────────────────────────────────

function renderView() {
  return render(
    <MemoryRouter initialEntries={["/public-portfolios/1"]}>
      <Routes>
        <Route path="/public-portfolios/:userId" element={<PublicPortfolioView />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("PublicPortfolioView - rendering", () => {
  beforeEach(() => setupViewMocks());

  it("renders portfolio owner name", async () => {
    renderView();
    await waitFor(() => expect(screen.getByText(/Jane Doe/i)).toBeTruthy());
  });

  it("renders project cards", async () => {
    renderView();
    await waitFor(() => expect(screen.getByText("Alpha Project")).toBeTruthy());
  });

  it("renders summary text", async () => {
    renderView();
    await waitFor(() => expect(screen.getByText("A passionate developer")).toBeTruthy());
  });
});

describe("PublicPortfolioView - error state", () => {
  it("shows not available message on fetch failure", async () => {
    mockFetch.mockResolvedValue({ ok: false });
    renderView();
    await waitFor(() =>
      expect(screen.getByText(/Portfolio Not Available/i)).toBeTruthy()
    );
  });
});