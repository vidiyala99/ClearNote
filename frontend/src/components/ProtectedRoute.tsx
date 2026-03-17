import { useAuth } from "@clerk/clerk-react";
import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api, setAuthToken } from "../lib/api";


export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const { isSignedIn, isLoaded, getToken } = useAuth();
    const [verified, setVerified] = useState(false);
    const [verifying, setVerifying] = useState(true);

    useEffect(() => {
        async function verifyUser() {
            if (!isSignedIn) {
                setVerifying(false);
                return;
            }
            try {
                const token = await getToken();
                setAuthToken(token);
                // Calls /users/me specifically to sync credentials
                await api.get("/users/me");
                setVerified(true);
            } catch (err) {
                setVerified(false);
                setAuthToken(null);
            } finally {
                setVerifying(false);
            }
        }
        verifyUser();
    }, [isSignedIn, getToken]);

    if (!isLoaded || verifying) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-slate-50 font-body" aria-live="polite" aria-label="Checking authorization">
                <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 rounded-full border-2 border-cyan-600 border-t-transparent animate-spin" aria-hidden="true" />
                    <p className="text-sm text-slate-500">Checking authorization…</p>
                </div>
            </div>
        )
    }

    // Bypass redirect for local layout testing
    // if (!isSignedIn || !verified) {
    //     return <Navigate to="/sign-in" replace />;
    // }

    return <>{children}</>;
}
