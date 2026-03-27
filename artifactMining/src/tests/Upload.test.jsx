import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Upload from "../pages/Upload";

vi.mock("../apiClient", () => ({
  apiFetch: vi.fn(),
  apiUpload: vi.fn(),
}));

import { apiFetch, apiUpload } from "../apiClient";

function setupConsentMock({ basicConsent = true } = {}) {
  apiFetch.mockImplementation((url) => {
    if (url === "/configuration/current-configuration") {
      return Promise.resolve({ consent: { basic_consent_granted: basicConsent } });
    }
    if (url === "/projects") {
      return Promise.resolve([
        { id: 1, name: "Project One", custom_description: "" },
      ]);
    }
    if (url.includes("/consent/")) return Promise.resolve({});
    return Promise.reject(new Error("Unmatched URL: " + url));
  });
}

function renderUpload() {
  return render(
    <MemoryRouter>
      <Upload />
    </MemoryRouter>
  );
}

beforeEach(() => vi.clearAllMocks());
afterEach(() => vi.clearAllMocks());

describe("Upload - consent warning", () => {
  it("shows consent warning when basic consent is not granted", async () => {
    setupConsentMock({ basicConsent: false });
    renderUpload();
    await waitFor(() =>
      expect(screen.getByText(/File access consent is required/i)).toBeTruthy()
    );
  });

  it("does not show consent warning when consent is granted", async () => {
    setupConsentMock({ basicConsent: true });
    renderUpload();
    await waitFor(() => screen.getByText("Upload Project"));
    expect(screen.queryByText(/File access consent is required before uploading/i)).not.toBeInTheDocument();
  });
});

describe("Upload - tab switching", () => {
  beforeEach(() => setupConsentMock());

  it("renders New Project tab by default", async () => {
    renderUpload();
    await waitFor(() => expect(screen.getByText("New Project")).toBeTruthy());
  });

  it("renders Add to Existing tab", async () => {
    renderUpload();
    await waitFor(() => expect(screen.getByText("Add to Existing")).toBeTruthy());
  });

  it("switches to incremental tab on click", async () => {
    renderUpload();
    await waitFor(() => screen.getByText("Add to Existing"));
    fireEvent.click(screen.getByText("Add to Existing"));
    await waitFor(() => expect(screen.getByText(/Drop additional files here/i)).toBeTruthy());
  });
});

describe("Upload - drop zone", () => {
  beforeEach(() => setupConsentMock());

  it("renders drop zone with upload prompt", async () => {
    renderUpload();
    await waitFor(() => expect(screen.getByText(/Drag & drop a file here/i)).toBeTruthy());
  });

  it("Upload & Analyze button is disabled when no file selected", async () => {
    renderUpload();
    await waitFor(() => screen.getByText("Upload & Analyze"));
    expect(screen.getByText("Upload & Analyze").closest("button").disabled).toBe(true);
  });
});

describe("Upload - consent buttons", () => {
  beforeEach(() => setupConsentMock());

  it("renders Grant File Access button", async () => {
    renderUpload();
    await waitFor(() => expect(screen.getByText("Grant File Access")).toBeTruthy());
  });

  it("renders Revoke File Access button", async () => {
    renderUpload();
    await waitFor(() => expect(screen.getByText("Revoke File Access")).toBeTruthy());
  });

  it("renders Grant AI Consent button", async () => {
    renderUpload();
    await waitFor(() => expect(screen.getByText("Grant AI Consent")).toBeTruthy());
  });

  it("calls grant consent API when Grant File Access is clicked", async () => {
    apiFetch.mockImplementation((url) => {
      if (url === "/configuration/current-configuration")
        return Promise.resolve({ consent: { basic_consent_granted: true } });
      if (url.includes("/consent/")) return Promise.resolve({});
      return Promise.reject(new Error("Unmatched: " + url));
    });
    renderUpload();
    await waitFor(() => screen.getByText("Grant File Access"));
    fireEvent.click(screen.getByText("Grant File Access"));
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        "/consent/basic-consent-grant",
        expect.objectContaining({ method: "POST" })
      )
    );
  });
});

describe("Upload - accepted file types", () => {
  beforeEach(() => setupConsentMock());

  it("shows .zip in accepted file types", async () => {
    renderUpload();
    await waitFor(() => expect(screen.getByText(".zip")).toBeTruthy());
  });

  it("shows .py in accepted file types", async () => {
    renderUpload();
    await waitFor(() => expect(screen.getByText(".py")).toBeTruthy());
  });
});

describe("Upload - upload error when no consent", () => {
  it("shows error status when uploading without consent", async () => {
    setupConsentMock({ basicConsent: false });
    renderUpload();
    await waitFor(() => screen.getByText("Upload & Analyze"));
    fireEvent.click(screen.getByText("Upload & Analyze"));
    await waitFor(() =>
      expect(screen.getByText(/File access consent is required/i)).toBeTruthy()
    );
  });
});

describe("Upload - successful upload", () => {
  it("shows success message after upload", async () => {
    setupConsentMock({ basicConsent: true });
    apiUpload.mockResolvedValue({ status: "ok" });
    renderUpload();

    await waitFor(() => screen.getByText(/Drag & drop a file here/i));

    const file = new File(["content"], "project.zip", { type: "application/zip" });
    const input = document.querySelector("input[type='file']");
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => screen.getByText("Upload & Analyze"));
    fireEvent.click(screen.getByText("Upload & Analyze"));

    await waitFor(() =>
      expect(screen.getByText(/Uploaded and analyzed!/i)).toBeTruthy()
    );
  });
});