import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import ProtectedRoute from "./ProtectedRoute";

const mockUseAuth = vi.fn();

vi.mock("@clerk/clerk-react", () => ({
  useAuth: () => mockUseAuth(),
}));

describe("ProtectedRoute", () => {
  it("renders children for anonymous users when guest preview is allowed", () => {
    mockUseAuth.mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
      getToken: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute allowGuestPreview>
                <div>Demo dashboard</div>
              </ProtectedRoute>
            }
          />
          <Route path="/sign-in" element={<div>Sign in page</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Demo dashboard")).toBeInTheDocument();
  });

  it("redirects anonymous users to sign in when guest preview is not allowed", () => {
    mockUseAuth.mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
      getToken: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/visits/new"]}>
        <Routes>
          <Route
            path="/visits/new"
            element={
              <ProtectedRoute>
                <div>New visit</div>
              </ProtectedRoute>
            }
          />
          <Route path="/sign-in" element={<div>Sign in page</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Sign in page")).toBeInTheDocument();
  });
});
