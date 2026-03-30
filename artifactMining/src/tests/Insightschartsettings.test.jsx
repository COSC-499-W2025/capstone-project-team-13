import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import InsightsChart from "../components/InsightsChart";
import Settings from "../pages/Settings";

// ─── InsightsChart Tests ───────────────────────────────────────────────────────

function renderInsightsChart() {
  return render(<InsightsChart />);
}

describe("InsightsChart - rendering", () => {
  it("renders Skill Frequency toggle button", () => {
    renderInsightsChart();
    expect(screen.getByText("Skill Frequency")).toBeTruthy();
  });

  it("renders By Project Type toggle button", () => {
    renderInsightsChart();
    expect(screen.getByText("By Project Type")).toBeTruthy();
  });

  it("shows Skill Frequency view by default", () => {
    renderInsightsChart();
    expect(screen.getByText("JavaScript")).toBeTruthy();
    expect(screen.getByText("Python")).toBeTruthy();
  });

  it("shows skill values in bar chart", () => {
    renderInsightsChart();
    expect(screen.getByText("8")).toBeTruthy();
  });

  it("Skill Frequency button has active class by default", () => {
    renderInsightsChart();
    const btn = screen.getByText("Skill Frequency");
    expect(btn.className).toContain("active");
  });
});

describe("InsightsChart - tab switching", () => {
  it("switches to By Project Type view", async () => {
    renderInsightsChart();
    fireEvent.click(screen.getByText("By Project Type"));
    await waitFor(() => expect(screen.getByText("Code")).toBeTruthy());
  });

  it("shows pie chart legend items when switching to project types", async () => {
    renderInsightsChart();
    fireEvent.click(screen.getByText("By Project Type"));
    await waitFor(() => {
      expect(screen.getByText("Text")).toBeTruthy();
      expect(screen.getByText("Media")).toBeTruthy();
    });
  });

  it("shows percentage values in project type view", async () => {
    renderInsightsChart();
    fireEvent.click(screen.getByText("By Project Type"));
    await waitFor(() => expect(screen.getByText("50%")).toBeTruthy());
  });

  it("By Project Type button has active class after click", async () => {
    renderInsightsChart();
    fireEvent.click(screen.getByText("By Project Type"));
    await waitFor(() => {
      const btn = screen.getByText("By Project Type");
      expect(btn.className).toContain("active");
    });
  });

  it("switches back to Skill Frequency view", async () => {
    renderInsightsChart();
    fireEvent.click(screen.getByText("By Project Type"));
    await waitFor(() => screen.getByText("Code"));
    fireEvent.click(screen.getByText("Skill Frequency"));
    await waitFor(() => expect(screen.getByText("JavaScript")).toBeTruthy());
  });
});

// ─── Settings Tests ────────────────────────────────────────────────────────────

const mockFetch = vi.fn();
global.fetch = mockFetch;

function setupSettingsMocks({ basicConsent = false, aiConsent = false } = {}) {
  mockFetch.mockImplementation((url) => {
    if (url.includes("current-configuration")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          consent: { basic_consent_granted: basicConsent, ai_consent_granted: aiConsent },
          privacy_settings: { excluded_folders: [], excluded_file_types: [] },
        }),
      });
    }
    if (url.includes("ai-consent-status") || url.includes("basic-consent-status")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ granted: basicConsent }) });
    }
    if (url.includes("/consent/")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }
    if (url.includes("/auth/me")) {
      return Promise.resolve({ ok: false, status: 401, json: () => Promise.resolve({}) });
    }
    if (url.includes("/privacy/")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ excluded_folders: [], excluded_file_types: [] }) });
    }
    if (url.includes("/user/github-username")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ github_username: "" }) });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });
}

function renderSettings() {
  return render(
    <MemoryRouter>
      <Settings />
    </MemoryRouter>
  );
}

beforeEach(() => vi.clearAllMocks());
afterEach(() => mockFetch.mockReset());

describe("Settings - rendering", () => {
  beforeEach(() => setupSettingsMocks());

  it("renders Settings heading in sidebar", async () => {
    renderSettings();
    await waitFor(() => expect(screen.getByText("Settings")).toBeTruthy());
  });

  it("renders Account Settings nav item", async () => {
    renderSettings();
    await waitFor(() => {
      const navBtns = screen.getAllByText("Account Settings");
      expect(navBtns.length).toBeGreaterThan(0);
    });
  });

  it("renders Consent nav item", async () => {
    renderSettings();
    await waitFor(() => expect(screen.getByText("Consent")).toBeTruthy());
  });

  it("renders Privacy nav item", async () => {
    renderSettings();
    await waitFor(() => expect(screen.getByText("Privacy")).toBeTruthy());
  });

  it("renders Dashboard Settings nav item", async () => {
    renderSettings();
    await waitFor(() => expect(screen.getByText("Dashboard Settings")).toBeTruthy());
  });

  it("renders About nav item", async () => {
    renderSettings();
    await waitFor(() => expect(screen.getByText("About")).toBeTruthy());
  });

  it("renders Dark and Light theme buttons", async () => {
    renderSettings();
    await waitFor(() => {
      expect(screen.getByText("Dark")).toBeTruthy();
      expect(screen.getByText("Light")).toBeTruthy();
    });
  });
});

describe("Settings - section navigation", () => {
  beforeEach(() => setupSettingsMocks());

  it("shows Account Settings section by default", async () => {
    renderSettings();
    await waitFor(() => {
      const matches = screen.getAllByText("Account Settings");
      expect(matches.length).toBeGreaterThan(0);
    });
  });

  it("navigates to Consent section", async () => {
    renderSettings();
    await waitFor(() => screen.getByText("Consent"));
    fireEvent.click(screen.getByText("Consent"));
    await waitFor(() => expect(screen.getByText("Consent Settings")).toBeTruthy());
  });

  it("navigates to Privacy section", async () => {
    renderSettings();
    await waitFor(() => screen.getByText("Privacy"));
    fireEvent.click(screen.getByText("Privacy"));
    await waitFor(() => expect(screen.getByText("Privacy Settings")).toBeTruthy());
  });

  it("navigates to Dashboard Settings section", async () => {
    renderSettings();
    await waitFor(() => screen.getByText("Dashboard Settings"));
    fireEvent.click(screen.getByText("Dashboard Settings"));
    await waitFor(() => expect(screen.getByText(/Display Options/i)).toBeTruthy());
  });

  it("navigates to About section", async () => {
    renderSettings();
    await waitFor(() => screen.getByText("About"));
    fireEvent.click(screen.getByText("About"));
    await waitFor(() => expect(screen.getByText("Digital Artifact Mining")).toBeTruthy());
  });
});

describe("Settings - consent section", () => {
  beforeEach(() => setupSettingsMocks());

  it("renders Grant Consent buttons in consent section", async () => {
    renderSettings();
    await waitFor(() => screen.getByText("Consent"));
    fireEvent.click(screen.getByText("Consent"));
    await waitFor(() => {
      const grantBtns = screen.getAllByText("Grant Consent");
      expect(grantBtns.length).toBeGreaterThan(0);
    });
  });

  it("renders Revoke Consent buttons in consent section", async () => {
    renderSettings();
    await waitFor(() => screen.getByText("Consent"));
    fireEvent.click(screen.getByText("Consent"));
    await waitFor(() => {
      const revokeBtns = screen.getAllByText("Revoke Consent");
      expect(revokeBtns.length).toBeGreaterThan(0);
    });
  });
});

describe("Settings - dashboard section", () => {
  beforeEach(() => setupSettingsMocks());

  it("renders Show emojis checkbox", async () => {
    renderSettings();
    await waitFor(() => screen.getByText("Dashboard Settings"));
    fireEvent.click(screen.getByText("Dashboard Settings"));
    await waitFor(() => expect(screen.getByText("Show emojis")).toBeTruthy());
  });

  it("renders Show daily streak checkbox", async () => {
    renderSettings();
    await waitFor(() => screen.getByText("Dashboard Settings"));
    fireEvent.click(screen.getByText("Dashboard Settings"));
    await waitFor(() => expect(screen.getByText("Show daily streak")).toBeTruthy());
  });

  it("renders Show tip of the day checkbox", async () => {
    renderSettings();
    await waitFor(() => screen.getByText("Dashboard Settings"));
    fireEvent.click(screen.getByText("Dashboard Settings"));
    await waitFor(() => expect(screen.getByText("Show tip of the day")).toBeTruthy());
  });
});