import { useState, useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Loader2, FileText, ClipboardList, AlertCircle, Calendar, User, Printer } from "lucide-react";
import { api } from "../lib/api";

export default function VisitDetail() {
  const { id } = useParams();
  const [visit, setVisit] = useState<any>(null);
  const [transcript, setTranscript] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Using Promise.all, setting fallbacks to null for not-ready AI rows
        const [visitRes, transRes, summRes] = await Promise.all([
            api.get(`/visits/${id}`),
            api.get(`/visits/${id}/transcript`).catch(() => ({ data: null })),
            api.get(`/visits/${id}/summary`).catch(() => ({ data: null }))
        ]);
        
        setVisit(visitRes.data);
        setTranscript(transRes.data);
        setSummary(summRes.data);
      } catch (err: any) {
         console.error("Failed to load visit details:", err);
         setError("Failed to load visit details. Please return into Dashboard.");
      } finally {
         setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Analyzing visit summaries...</span>
        </div>
      </div>
    );
  }

  if (error || !visit) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <AlertCircle className="w-12 h-12 text-red-500 mb-2" />
        <p className="text-slate-800 font-semibold">{error || "Visit not found"}</p>
        <Link to="/dashboard" className="mt-4 text-cyan-600 hover:underline flex items-center gap-1.5 text-sm">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 font-body">
      <style>{`
        @media print {
          header, nav, .bg-white.border-b.px-6.py-4, .print-hide { display: none !important; }
          main { display: block !important; grid-template-columns: 1fr !important; height: auto !important; margin: 0 !important; padding: 0 !important; }
          .overflow-y-auto { overflow: visible !important; height: auto !important; }
          .bg-white { border: none !important; box-shadow: none !important; }
          div { page-break-inside: avoid; }
        }
      `}</style>

      {/* ── Header ── */}
      <header className="sticky top-0 z-40 bg-white border-b border-slate-100 shadow-sm print:hidden">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-cyan-600 transition-colors cursor-pointer back-link">
              <ArrowLeft className="w-4 h-4" />
              Dashboard
            </Link>
            <div className="h-4 w-px bg-slate-200" />
            <h1 className="font-heading font-bold text-slate-900 text-lg tracking-tight">{visit.title}</h1>
          </div>
          <div className="flex items-center gap-3">
             <button 
               onClick={() => window.print()} 
               className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-all cursor-pointer mr-2 shadow-sm"
             >
               <Printer className="w-3.5 h-3.5" /> Print
             </button>
             <span className={`px-2.5 py-0.5 text-xs rounded-full font-medium ${visit.status === 'ready' ? 'bg-emerald-100 text-emerald-800' : visit.status === 'failed' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800 animate-pulse'}`}>
               {visit.status === 'ready' ? 'Completed' : visit.status === 'failed' ? 'Failed' : 'Processing'}
             </span>
          </div>
        </div>
      </header>

      {/* ── Meta Banner ── */}
      <div className="bg-white border-b border-slate-100 px-6 py-4">
         <div className="max-w-7xl mx-auto flex flex-wrap gap-6 text-sm text-slate-500">
             <div className="flex items-center gap-1.5">
                 <Calendar className="w-4 h-4 text-slate-400" />
                 <span>{new Date(visit.visit_date).toLocaleDateString()}</span>
             </div>
             <div className="flex items-center gap-1.5">
                 <User className="w-4 h-4 text-slate-400" />
                 <span>{visit.doctor_name || "No doctor assigned"}</span>
             </div>
         </div>
      </div>

      <main className="max-w-7xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-120px)]">
         
         {/* ── Left: Transcript Viewer ── */}
         <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col h-full overflow-hidden">
             <div className="p-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50/50">
                 <FileText className="w-4 h-4 text-cyan-600" />
                 <h2 className="font-heading font-semibold text-slate-800">Scribe Transcript</h2>
             </div>
             <div className="p-6 overflow-y-auto flex-1 text-slate-600 leading-relaxed text-sm whitespace-pre-wrap">
                 {transcript ? (
                     transcript.raw_text
                 ) : visit.status === 'ready' ? (
                     <div className="text-center py-20 text-slate-400">Transcript could not be loaded.</div>
                 ) : (
                     <div className="text-center py-20 text-slate-400 animate-pulse">Waiting for AI Speech-to-Text inference to finalize...</div>
                 )}
             </div>
         </div>

         {/* ── Right: Summary/SOAP Layout ── */}
         <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col h-full overflow-hidden">
             <div className="p-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50/50">
                 <ClipboardList className="w-4 h-4 text-teal-600" />
                 <h2 className="font-heading font-semibold text-slate-800">AI Medical Summary</h2>
             </div>
             <div className="p-6 overflow-y-auto flex-1 space-y-6">
                 {summary ? (
                     <>
                        <div>
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Overview</h3>
                            <p className="text-sm text-slate-700 bg-slate-50 p-4 rounded-xl border border-slate-100">{summary.overview}</p>
                        </div>
                        
                        <div>
                             <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Medications</h3>
                             <ul className="space-y-1.5">
                                 {summary.medications?.map((item: string) => <li key={item} className="text-sm text-slate-700 flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-teal-500"/> {item}</li>)}
                             </ul>
                        </div>

                        <div>
                             <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Diagnoses</h3>
                             <div className="flex flex-wrap gap-2">
                                 {summary.diagnoses?.map((item: string) => <span key={item} className="px-2 py-1 bg-cyan-50 border border-cyan-100 rounded text-xs font-medium text-cyan-800">{item}</span>)}
                             </div>
                        </div>

                        <div>
                             <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Action Items</h3>
                             <ul className="space-y-1.5">
                                 {summary.action_items?.map((item: string) => <li key={item} className="text-sm text-slate-700 flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-amber-500"/> {item}</li>)}
                             </ul>
                        </div>
                     </>
                 ) : visit.status === 'ready' ? (
                     <div className="text-center py-20 text-slate-400">SOAP notes could not be loaded.</div>
                 ) : (
                     <div className="text-center py-20 text-slate-400 animate-pulse">Running diagnostic models...</div>
                 )}
             </div>
         </div>

      </main>
    </div>
  );
}
