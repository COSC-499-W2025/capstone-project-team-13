import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, act, waitFor } from "@testing-library/react";
import Toast, { toast } from "../components/Toast";

function renderToast() {
  return render(<Toast />);
}

beforeEach(() => vi.clearAllMocks());

describe("Toast - rendering", () => {
  it("renders without crashing", () => {
    renderToast();
    expect(document.querySelector(".toast-container")).toBeTruthy();
  });

  it("shows no toasts initially", () => {
    renderToast();
    expect(document.querySelectorAll(".toast-item").length).toBe(0);
  });
});

describe("Toast - showing messages", () => {
  it("shows a toast message when toast() is called", async () => {
    renderToast();
    act(() => toast("Hello world", "ok", 5000));
    await waitFor(() => expect(screen.getByText("Hello world")).toBeTruthy());
  });

  it("shows toast with ok type class", async () => {
    renderToast();
    act(() => toast("Success message", "ok", 5000));
    await waitFor(() => {
      expect(document.querySelector(".toast-ok")).toBeTruthy();
    });
  });

  it("shows toast with error type class", async () => {
    renderToast();
    act(() => toast("Error message", "err", 5000));
    await waitFor(() => {
      expect(document.querySelector(".toast-err")).toBeTruthy();
    });
  });

  it("shows toast with warn type class", async () => {
    renderToast();
    act(() => toast("Warning message", "warn", 5000));
    await waitFor(() => {
      expect(document.querySelector(".toast-warn")).toBeTruthy();
    });
  });

  it("shows multiple toasts at once", async () => {
    renderToast();
    act(() => {
      toast("First", "ok", 5000);
      toast("Second", "ok", 5000);
    });
    await waitFor(() => {
      expect(screen.getByText("First")).toBeTruthy();
      expect(screen.getByText("Second")).toBeTruthy();
    });
  });
});

describe("Toast - accessibility", () => {
  it("has aria-live attribute for screen readers", () => {
    renderToast();
    expect(document.querySelector("[aria-live='polite']")).toBeTruthy();
  });
});