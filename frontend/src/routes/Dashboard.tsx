import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { UserButton, useAuth } from "@clerk/clerk-react";
import { api, setAuthToken } from "../lib/api";
import { useWebSocket } from "../hooks/useWebSocket";

const mockVisits = [
  { id: "1", title: "Cardiology Consultation", doctor: "Dr. Smith", date: "2026-03-16", status: "ready", duration: "12:45" },
  { id: "2", title: "Annual Physical Exam", doctor: "Dr. Jones", date: "2026-03-14", status: "ready", duration: "08:30" },
  { id: "3", title: "Follow-up - Hypertension", doctor: "Dr. Smith", date: "2026-03-12", status: "processing", duration: "15:10" },
  { id: "4", title: "Pediatric Wellness Check", doctor: "Dr. Lee", date: "2026-03-10", status: "ready", duration: "10:15" },
  { id: "5", title: "Dermatology Screening", doctor: "Dr. Davis", date: "2026-03-08", status: "ready", duration: "06:45" },
  { id: "6", title: "Orthopedic Initial Assessment", doctor: "Dr. Wilson", date: "2026-03-05", status: "failed", duration: "18:20" },
];

export default function Dashboard() {
  const { isSignedIn, getToken } = useAuth();
  const [visits, setVisits] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // 1. Fetch real visits or fallback to demo data
  useEffect(() => {
    const fetchVisits = async () => {
      if (isSignedIn) {
        try {
          const token = await getToken();
          setAuthToken(token);
          const response = await api.get("/visits");
          
          setVisits(response.data.length ? response.data : mockVisits);
        } catch (error) {
          console.error("Failed to fetch visits:", error);
          setVisits(mockVisits); // fallback on error
        }
      } else {
        setVisits(mockVisits); // guest mode fallback
      }
      setLoading(false);
    };

    fetchVisits();
  }, [isSignedIn, getToken]);

  // 2. Real-time updates via WebSocket
  useWebSocket((data) => {
    if (data.type === "visit_ready") {
      setVisits((prev) =>
        prev.map((visit) =>
          visit.id === data.visit_id ? { ...visit, status: "ready" } : visit
        )
      );
    }
  });

  return (
    <div className="min-h-screen bg-slate-50 font-body">
      <nav className="flex justify-between items-center px-6 py-4 bg-white border-b shadow-sm">
        <h1 className="text-xl font-bold font-heading text-slate-800">ClearNote</h1>
        <div className="flex gap-4 items-center">
          <Link to="/visits/new" className="px-4 py-2 text-sm text-white bg-cyan-600 rounded-md hover:bg-cyan-700 transition shadow-sm">+ New Visit</Link>
          {isSignedIn ? (
            <UserButton afterSignOutUrl="/" />
          ) : (
            <div className="w-8 h-8 rounded-full bg-slate-300 text-slate-600 flex items-center justify-center text-xs font-bold border border-slate-200">G</div>
          )}
        </div>
      </nav>

      <main className="p-8 max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold font-heading text-slate-900 border-b-2 border-cyan-500 pb-1">Recent Visits</h2>
          {!isSignedIn && <span className="text-xs px-2 py-0.5 rounded-full bg-slate-200 text-slate-600 font-medium tracking-wide">Demo Mode</span>}
        </div>

        {loading ? (
             <div className="text-center py-20 text-slate-400">Loading your visits...</div>
        ) : (
             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
               {visits.map((visit) => (
                 <Link to={`/visits/${visit.id}`} key={visit.id} className="block p-5 bg-white rounded-xl border border-slate-100 shadow-sm hover:shadow-md hover:border-cyan-200 hover:translate-y-[-1px] transition-all cursor-pointer">
                   <div className="flex justify-between items-start">
                     <h3 className="font-semibold text-slate-800 text-base">{visit.title || "Untitled Visit"}</h3>
                     <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${visit.status === 'ready' ? 'bg-emerald-100 text-emerald-800' : visit.status === 'failed' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800 animate-pulse'}`}>
                       {visit.status === 'ready' ? 'Ready' : visit.status === 'failed' ? 'Failed' : 'Processing'}
                     </span>
                   </div>
                   <p className="text-sm text-slate-500 mt-1">{visit.doctor_name || visit.doctor || "No doctor assigned"}</p>
                   
                   <div className="flex justify-between items-center mt-6 pt-4 border-t border-slate-100 text-xs text-slate-400">
                     <div className="flex items-center gap-1.5">
                         <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-slate-300"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                         <span>{visit.visit_date || new Date().toLocaleDateString()}</span>
                     </div>
                     <div className="flex items-center gap-1">
                         <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-slate-300"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/><polyline points="12 6 12 12 16 14"/></svg>
                         <span>{visit.duration || "10:00"}</span>
                     </div>
                   </div>
                 </Link>
               ))}
             </div>
        )}
      </main>
    </div>
  )
}
