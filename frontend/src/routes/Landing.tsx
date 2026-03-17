import { Link } from "react-router-dom";
import { Mic, ShieldCheck, ChevronRight, Activity, Zap } from "lucide-react";

const features = [
  {
    icon: Mic,
    title: "One-tap Recording",
    description:
      "Record clinical visits with a single tap. Informed patient consent is captured automatically before each session begins.",
    iconBg: "bg-red-50",
    iconColor: "text-red-500",
    hoverBorder: "hover:border-red-200",
  },
  {
    icon: Zap,
    title: "AI Transcription",
    description:
      "Recordings are automatically transcribed and structured into clear, readable medical summaries — ready in minutes.",
    iconBg: "bg-cyan-50",
    iconColor: "text-cyan-600",
    hoverBorder: "hover:border-cyan-200",
  },
  {
    icon: ShieldCheck,
    title: "Secure & Compliant",
    description:
      "All recordings are encrypted in transit and at rest. Built with healthcare compliance as a foundational principle.",
    iconBg: "bg-emerald-50",
    iconColor: "text-emerald-600",
    hoverBorder: "hover:border-emerald-200",
  },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-white font-body">

      {/* ── Sticky Nav ── */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-100">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-600 flex items-center justify-center" aria-hidden="true">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <span className="font-heading font-bold text-slate-900 text-lg tracking-tight">ClearNote</span>
          </div>
          <nav className="flex items-center gap-2" aria-label="Main navigation">
            <Link
              to="/sign-in"
              className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-cyan-600 transition-colors duration-150 rounded-md"
            >
              Sign In
            </Link>
            <Link
              to="/sign-up"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-cyan-600 text-white text-sm font-semibold rounded-lg hover:bg-cyan-700 transition-colors duration-150 cursor-pointer"
            >
              Get Started <ChevronRight className="w-4 h-4" aria-hidden="true" />
            </Link>
          </nav>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="relative bg-gradient-to-br from-cyan-700 via-cyan-600 to-teal-800 overflow-hidden">
        {/* decorative blobs */}
        <div
          className="absolute -top-32 -right-32 w-[560px] h-[560px] rounded-full bg-white/5 pointer-events-none"
          aria-hidden="true"
        />
        <div
          className="absolute -bottom-24 -left-24 w-[380px] h-[380px] rounded-full bg-teal-900/25 pointer-events-none"
          aria-hidden="true"
        />
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-white/[0.03] pointer-events-none"
          aria-hidden="true"
        />

        <div className="relative max-w-6xl mx-auto px-6 pt-28 pb-36 text-center">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/15 text-cyan-50 text-sm font-medium mb-8 border border-white/20 backdrop-blur-sm">
            <ShieldCheck className="w-4 h-4" aria-hidden="true" />
            Built for clinical documentation
          </div>

          <h1 className="font-heading text-5xl md:text-6xl lg:text-7xl font-extrabold text-white leading-[1.1] max-w-4xl mx-auto mb-6 tracking-tight">
            Dictate. Transcribe.{" "}
            <span className="text-cyan-200">Document with confidence.</span>
          </h1>

          <p className="text-lg md:text-xl text-cyan-100/80 max-w-2xl mx-auto leading-relaxed mb-10">
            ClearNote turns your clinical visit recordings into structured medical summaries —
            so you can focus on your patients, not paperwork.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/sign-up"
              className="inline-flex items-center gap-2 px-8 py-3.5 bg-white text-cyan-700 font-bold rounded-xl hover:bg-cyan-50 transition-colors duration-150 text-base shadow-xl shadow-cyan-900/20 cursor-pointer"
            >
              Start for Free <ChevronRight className="w-5 h-5" aria-hidden="true" />
            </Link>
            <Link
              to="/sign-in"
              className="inline-flex items-center gap-2 px-8 py-3.5 bg-transparent text-white font-semibold rounded-xl border border-white/30 hover:bg-white/10 transition-colors duration-150 text-base cursor-pointer"
            >
              Sign In
            </Link>
          </div>
        </div>

        {/* wave divider */}
        <div className="absolute bottom-0 left-0 right-0" aria-hidden="true">
          <svg viewBox="0 0 1440 72" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full block">
            <path
              d="M0 72L80 60C160 48 320 24 480 16C640 8 800 16 960 24C1120 32 1280 40 1360 44L1440 48V72H1360C1280 72 1120 72 960 72C800 72 640 72 480 72C320 72 160 72 80 72H0Z"
              fill="white"
            />
          </svg>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="text-center mb-14">
          <h2 className="font-heading text-3xl md:text-4xl font-bold text-slate-900 mb-4 tracking-tight">
            Everything you need to document smarter
          </h2>
          <p className="text-slate-500 max-w-xl mx-auto text-lg">
            Streamline your clinical documentation workflow from first word to final note.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((f) => (
            <div
              key={f.title}
              className={`bg-white rounded-2xl p-8 border border-slate-100 hover:shadow-xl hover:shadow-slate-200/60 transition-all duration-200 ${f.hoverBorder}`}
            >
              <div
                className={`w-12 h-12 rounded-xl ${f.iconBg} flex items-center justify-center mb-6`}
                aria-hidden="true"
              >
                <f.icon className={`w-6 h-6 ${f.iconColor}`} />
              </div>
              <h3 className="font-heading font-semibold text-slate-900 text-xl mb-3">{f.title}</h3>
              <p className="text-slate-500 text-sm leading-relaxed">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA Banner ── */}
      <section className="max-w-6xl mx-auto px-6 pb-28">
        <div className="relative bg-gradient-to-r from-cyan-600 to-teal-700 rounded-3xl p-14 text-center overflow-hidden">
          <div
            className="absolute -top-16 -right-16 w-64 h-64 rounded-full bg-white/5 pointer-events-none"
            aria-hidden="true"
          />
          <h2 className="font-heading text-3xl md:text-4xl font-bold text-white mb-4 tracking-tight relative">
            Ready to streamline your documentation?
          </h2>
          <p className="text-cyan-100 mb-8 max-w-lg mx-auto relative">
            Join clinicians who save hours every week with automated transcription and AI-generated summaries.
          </p>
          <Link
            to="/sign-up"
            className="inline-flex items-center gap-2 px-8 py-3.5 bg-white text-cyan-700 font-bold rounded-xl hover:bg-cyan-50 transition-colors duration-150 shadow-lg cursor-pointer relative"
          >
            Get Started Free <ChevronRight className="w-5 h-5" aria-hidden="true" />
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-slate-100 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-cyan-600 flex items-center justify-center" aria-hidden="true">
              <Activity className="w-3 h-3 text-white" />
            </div>
            <span className="font-heading font-semibold text-slate-900 text-sm">ClearNote</span>
          </div>
          <p className="text-slate-400 text-sm">© 2025 ClearNote. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
