import { SignIn } from "@clerk/clerk-react";
import { Link } from "react-router-dom";
import { Activity, Mic, FileText, ShieldCheck } from "lucide-react";

const brandPoints = [
  { icon: Mic,         text: "One-tap recording with patient consent built-in" },
  { icon: FileText,    text: "Automatic AI transcription & medical summaries" },
  { icon: ShieldCheck, text: "Secure, HIPAA-ready infrastructure" },
];

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex font-body">

      {/* ── Left branding panel ── */}
      <div className="hidden lg:flex lg:w-[44%] xl:w-5/12 bg-gradient-to-br from-cyan-700 to-teal-800 flex-col justify-between p-12 flex-shrink-0 relative overflow-hidden">
        {/* decorative circles */}
        <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full bg-white/5 pointer-events-none" aria-hidden="true" />
        <div className="absolute -bottom-16 -left-16 w-60 h-60 rounded-full bg-teal-900/30 pointer-events-none" aria-hidden="true" />

        <div className="relative flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center" aria-hidden="true">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <span className="font-heading font-bold text-white text-xl tracking-tight">ClearNote</span>
        </div>

        <div className="relative">
          <h2 className="font-heading text-3xl font-bold text-white leading-snug mb-8 tracking-tight">
            Clinical documentation,<br />made effortless.
          </h2>
          <ul className="space-y-5" aria-label="Product features">
            {brandPoints.map((item) => (
              <li key={item.text} className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center flex-shrink-0 mt-0.5" aria-hidden="true">
                  <item.icon className="w-4 h-4 text-white" />
                </div>
                <p className="text-white/75 text-sm leading-relaxed">{item.text}</p>
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-white/30 text-xs">© 2025 ClearNote. All rights reserved.</p>
      </div>

      {/* ── Right Clerk panel ── */}
      <div className="flex-1 flex flex-col items-center justify-center gap-5 p-8">
        <SignIn path="/sign-in" routing="path" signUpUrl="/sign-up" />
        <Link
          to="/dashboard"
          className="text-sm font-medium text-cyan-700 hover:text-cyan-800 transition-colors duration-150"
        >
          Preview the demo dashboard instead
        </Link>
      </div>
    </div>
  );
}
