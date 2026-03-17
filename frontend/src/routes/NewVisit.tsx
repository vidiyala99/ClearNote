import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import RecordingButton from "../components/recording/RecordingButton";
import { api } from "../lib/api";
import { s3Upload } from "../lib/s3Upload";
import { Activity, ArrowLeft, Loader2, AlertCircle } from "lucide-react";

const inputCls =
  "mt-1.5 block w-full px-3.5 py-2.5 border border-slate-200 rounded-lg text-slate-900 text-sm bg-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed";

export default function NewVisit() {
  const [title, setTitle]         = useState("");
  const [visitDate, setVisitDate] = useState(new Date().toISOString().split("T")[0]);
  const [doctorName, setDoctorName] = useState("");
  const [consentAt, setConsentAt]   = useState<string | null>(null);
  const [uploading, setUploading]   = useState(false);
  const [progress, setProgress]     = useState(0);
  const [error, setError]           = useState<string | null>(null);

  const navigate = useNavigate();

  const handleRecordingDone = async (blob: Blob) => {
    if (!consentAt) {
      setError("Consent was not recorded. Please start a new recording.");
      return;
    }
    if (!title.trim()) {
      setError("Please provide a visit title before saving.");
      return;
    }
    setError(null);
    setUploading(true);
    try {
      const visitRes = await api.post("/visits", {
        title,
        visit_date: visitDate,
        doctor_name: doctorName.trim() || null,
        consent_at: consentAt,
      });
      const visitId = visitRes.data.visit_id;

      const jobRes = await api.post("/jobs/transcribe", { visit_id: visitId });
      const { job_id, upload_url, upload_fields } = jobRes.data;

      const { promise } = s3Upload({
        upload_url,
        upload_fields,
        blob,
        onProgress: (p) => setProgress(p),
      });
      await promise;
      await api.post(`/jobs/${job_id}/confirm`);
      navigate("/dashboard");
    } catch (err: any) {
      console.error("New Visit Pipeline failed:", err);
      setError(
        "Error completing visit creation: " +
          (err?.response?.data?.detail || err.message)
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 font-body">

      {/* ── Header ── */}
      <header className="sticky top-0 z-40 bg-white border-b border-slate-100 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center gap-4">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-cyan-600 transition-colors duration-150 cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" aria-hidden="true" />
            Back
          </Link>
          <div className="h-4 w-px bg-slate-200" aria-hidden="true" />
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-cyan-600 flex items-center justify-center" aria-hidden="true">
              <Activity className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-heading font-bold text-slate-900 tracking-tight">ClearNote</span>
          </div>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="max-w-2xl mx-auto px-4 py-10">
        <div className="mb-8">
          <h1 className="font-heading text-2xl font-bold text-slate-900 tracking-tight">Record New Visit</h1>
          <p className="text-slate-500 text-sm mt-1">Fill in the details below, then record your clinical session.</p>
        </div>

        <div className="space-y-6">
          {/* Visit details card */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100">
              <h2 className="font-heading font-semibold text-slate-900">Visit Details</h2>
            </div>
            <div className="p-6 grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div className="sm:col-span-2">
                <label htmlFor="title" className="block text-sm font-medium text-slate-700">
                  Visit Title <span className="text-red-500" aria-label="required">*</span>
                </label>
                <input
                  id="title"
                  type="text"
                  disabled={uploading}
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className={inputCls}
                  placeholder="e.g., Annual Checkup"
                  autoComplete="off"
                  required
                />
              </div>

              <div>
                <label htmlFor="visitDate" className="block text-sm font-medium text-slate-700">
                  Visit Date <span className="text-red-500" aria-label="required">*</span>
                </label>
                <input
                  id="visitDate"
                  type="date"
                  disabled={uploading}
                  value={visitDate}
                  onChange={(e) => setVisitDate(e.target.value)}
                  className={inputCls}
                  required
                />
              </div>

              <div>
                <label htmlFor="doctorName" className="block text-sm font-medium text-slate-700">
                  Doctor's Name{" "}
                  <span className="text-slate-400 font-normal text-xs">(optional)</span>
                </label>
                <input
                  id="doctorName"
                  type="text"
                  disabled={uploading}
                  value={doctorName}
                  onChange={(e) => setDoctorName(e.target.value)}
                  className={inputCls}
                  placeholder="e.g., Dr. Smith"
                  autoComplete="off"
                />
              </div>
            </div>
          </div>

          {/* Recording card */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100">
              <h2 className="font-heading font-semibold text-slate-900">Voice Recording</h2>
              <p className="text-slate-500 text-xs mt-0.5">Patient consent will be captured before recording begins.</p>
            </div>
            <div className="p-6">
              <RecordingButton
                onConsentGiven={(ts) => setConsentAt(ts)}
                onRecordingComplete={handleRecordingDone}
              />

              {error && (
                <div
                  className="mt-4 flex items-start gap-3 p-3.5 bg-red-50 border border-red-100 rounded-xl text-sm text-red-700"
                  role="alert"
                >
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
                  {error}
                </div>
              )}

              {uploading && (
                <div className="mt-4 p-4 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center gap-2 mb-3">
                    <Loader2 className="w-4 h-4 text-cyan-600 animate-spin flex-shrink-0" aria-hidden="true" />
                    <p className="text-sm font-medium text-slate-700">Uploading and processing…</p>
                  </div>
                  <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="bg-cyan-600 h-full rounded-full transition-all duration-300"
                      style={{ width: `${progress}%` }}
                      role="progressbar"
                      aria-valuenow={progress}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label="Upload progress"
                    />
                  </div>
                  <p className="text-xs text-slate-500 mt-1.5 tabular-nums">{progress}% complete</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
