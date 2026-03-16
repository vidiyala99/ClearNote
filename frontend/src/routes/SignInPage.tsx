import { SignIn } from "@clerk/clerk-react";

export default function SignInPage() {
    return (
        <div className="flex items-center justify-center min-h-screen bg-slate-100">
            <SignIn path="/sign-in" routing="path" signUpUrl="/sign-up" />
        </div>
    )
}
