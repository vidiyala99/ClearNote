import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50">
      <h1 className="text-4xl font-bold text-slate-900">Welcome to ClearNote</h1>
      <p className="mt-4 text-slate-600">Dictate and transcribe clinical visits with confidence.</p>
      <div className="flex gap-4 mt-8">
        <Link to="/sign-in" className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700">Get Started</Link>
      </div>
    </div>
  )
}
