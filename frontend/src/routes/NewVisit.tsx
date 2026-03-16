import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import RecordingButton from "../components/recording/RecordingButton";
import { api } from "../lib/api";
import { s3Upload } from "../lib/s3Upload";

export default function NewVisit() {
    const [title, setTitle] = useState("");
    const [visitDate, setVisitDate] = useState(new Date().toISOString().split('T')[0]);
    const [doctorName, setDoctorName] = useState("");
    const [consentAt, setConsentAt] = useState<string | null>(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);

    const navigate = useNavigate();

    const handleRecordingDone = async (blob: Blob) => {
        if (!consentAt) {
            alert("Consent was not recorded properly!");
            return;
        }

        if (!title.trim()) {
            alert("Please provide a visit title.");
            return;
        }

        setUploading(true);
        try {
            // 1. Create Visit
            const visitRes = await api.post("/visits", {
                title,
                visit_date: visitDate,
                doctor_name: doctorName.trim() || null,
                consent_at: consentAt
            });
            const visitId = visitRes.data.visit_id;

            // 2. Generate Presigned URL
            const jobRes = await api.post("/jobs/transcribe", { visit_id: visitId });
            const { job_id, upload_url, upload_fields } = jobRes.data;

            // 3. Upload to S3
            const { promise } = s3Upload({
                upload_url,
                upload_fields,
                blob,
                onProgress: (p) => setProgress(p)
            });
            await promise;

            // 4. Confirm upload to trigger pipeline
            await api.post(`/jobs/${job_id}/confirm`);

            // Success, navigate back to dashboard
            navigate("/dashboard");
        } catch (err: any) {
             console.error("New Visit Pipeline failed:", err);
             alert("Error completing visit creation: " + (err?.response?.data?.detail || err.message));
        } finally {
             setUploading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50">
            <nav className="p-4 bg-white border-b shadow-sm">
                <Link to="/dashboard" className="text-blue-600 hover:text-blue-700">← Back to Dashboard</Link>
            </nav>

            <main className="max-w-md p-8 mx-auto mt-8 bg-white border rounded-lg shadow-sm">
                <h1 className="text-2xl font-bold text-slate-900 border-b pb-4">Record New Visit</h1>

                <div className="flex flex-col gap-4 mt-6">
                    <div>
                        <label className="block text-sm font-medium text-slate-700">Visit Title</label>
                        <input 
                            type="text" 
                            disabled={uploading}
                            value={title} 
                            onChange={(e) => setTitle(e.target.value)} 
                            className="mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                            placeholder="e.g., Annual Checkup" 
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700">Visit Date</label>
                        <input 
                            type="date" 
                            disabled={uploading}
                            value={visitDate} 
                            onChange={(e) => setVisitDate(e.target.value)} 
                            className="mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700">Doctor's Name</label>
                        <input 
                            type="text" 
                            disabled={uploading}
                            value={doctorName} 
                            onChange={(e) => setDoctorName(e.target.value)} 
                            className="mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                            placeholder="e.g., Dr. Smith" 
                        />
                    </div>
                </div>

                <div className="mt-8">
                    <p className="block text-sm font-medium text-slate-700 mb-2">Voice Recording</p>
                    <RecordingButton 
                         onConsentGiven={(timestamp) => setConsentAt(timestamp)}
                         onRecordingComplete={handleRecordingDone}
                    />

                    {uploading && (
                         <div className="mt-4">
                              <p className="text-sm font-medium text-blue-600">Uploading and processing: {progress}%</p>
                              <div className="w-full h-2 bg-slate-200 rounded mt-1 overflow-hidden">
                                   <div className="bg-blue-600 h-full transition-all duration-300" style={{ width: `${progress}%` }} />
                              </div>
                         </div>
                    )}
                </div>
            </main>
        </div>
    )
}
