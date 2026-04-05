import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import Dashboard from "./Dashboard";

const mockUseAuth = vi.fn();

vi.mock("@clerk/clerk-react", () => ({
  useAuth: () => mockUseAuth(),
  UserButton: () => <div>User menu</div>,
}));

vi.mock("../hooks/useWebSocket", () => ({
  useWebSocket: vi.fn(),
}));

describe("Dashboard", () => {
  it("shows a sign-up CTA instead of the new visit action for guests", async () => {
    mockUseAuth.mockReturnValue({
      isSignedIn: false,
      getToken: vi.fn(),
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByRole("link", { name: "Sign up to create visits" })
      ).toBeInTheDocument();
    });

    expect(
      screen.queryByRole("link", { name: "+ New Visit" })
    ).not.toBeInTheDocument();
  });
});
