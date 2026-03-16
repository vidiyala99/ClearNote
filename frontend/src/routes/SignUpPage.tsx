import { SignUp } from "@clerk/clerk-react";

export default function SignUpPage() {
    return (
        <div className="flex items-center justify-center min-h-screen bg-slate-100">
            <SignUp path="/sign-up" routing="path" signInUrl="/sign-in" />
        </div>
    )
}
