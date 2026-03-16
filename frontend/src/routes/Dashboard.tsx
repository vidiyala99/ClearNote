import { Link } from "react-router-dom";
import { UserButton } from "@clerk/clerk-react";

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="flex justify-between p-4 bg-white border-b shadow-sm">
        <h1 className="text-xl font-bold">ClearNote Dashboard</h1>
        <div className="flex gap-4 items-center">
            <Link to="/visits/new" className="px-3 py-1.5 text-white bg-blue-600 rounded-md hover:bg-blue-700">New Visit</Link>
            <UserButton afterSignOutUrl="/" />
        </div>
      </nav>
      <main className="p-8">
        <p className="text-slate-600">Your recent visits will appear here.</p>
      </main>
    </div>
  )
}
