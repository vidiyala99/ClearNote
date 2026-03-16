import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ClerkProvider } from "@clerk/clerk-react";

import Landing from "./routes/Landing";
import Dashboard from "./routes/Dashboard";
import NewVisit from "./routes/NewVisit";
import SignInPage from "./routes/SignInPage";
import SignUpPage from "./routes/SignUpPage";
import ProtectedRoute from "./components/ProtectedRoute";

// Load clerk key safely without crashing hard early
const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || "pk_test_sample";


function App() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/sign-in/*" element={<SignInPage />} />
          <Route path="/sign-up/*" element={<SignUpPage />} />
          
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/visits/new" element={
            <ProtectedRoute>
              <NewVisit />
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
    </ClerkProvider>
  )
}

export default App
