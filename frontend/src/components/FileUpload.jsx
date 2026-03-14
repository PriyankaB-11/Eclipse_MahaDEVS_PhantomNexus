import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadDataset } from '../services/api';

export default function FileUpload({ onUploadComplete }) {
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function handleUpload(file) {
    setError('');
    setMessage('');
    setProgress(0);
    setIsUploading(true);

    try {
      const response = await uploadDataset(file, setProgress);
      setMessage(`Analysis refreshed for ${response.devices_analyzed} devices.`);
      onUploadComplete?.(response);
    } catch (uploadError) {
      setError(uploadError.message);
    } finally {
      setIsUploading(false);
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
    disabled: isUploading,
    onDrop: (acceptedFiles) => {
      const [file] = acceptedFiles;
      if (file) {
        handleUpload(file);
      }
    },
  });

  return (
    <div className="surface-card rounded-3xl p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.32em] text-[var(--accent-primary)]">Dataset Upload</p>
          <h3 className="mt-2 font-display text-2xl font-semibold">Drag a CSV into the pipeline</h3>
          <p className="mt-2 max-w-2xl text-sm soft-label">
            Upload telemetry with the required columns to refresh trust scoring, anomaly detection, peer correlation, and report generation.
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-xs soft-label">
          Expected: device_id, timestamp, src_ip, dest_ip, dest_port, protocol, bytes, packets
        </div>
      </div>

      <div
        {...getRootProps()}
        className={`mt-5 cursor-pointer rounded-3xl border border-dashed p-8 text-center transition ${
          isDragActive ? 'border-[var(--accent-primary)] bg-[rgba(61,232,203,0.08)]' : 'border-white/10 bg-white/5 hover:bg-white/10'
        } ${isUploading ? 'pointer-events-none opacity-70' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="mx-auto max-w-xl">
          <div className="font-display text-xl font-semibold text-white">
            {isDragActive ? 'Release to upload the CSV' : 'Drop a CSV file here or click to browse'}
          </div>
          <p className="mt-2 text-sm soft-label">The backend stores the dataset temporarily and reruns the ML analysis automatically.</p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        <div className="h-3 overflow-hidden rounded-full bg-white/5">
          <div className="h-full rounded-full bg-[linear-gradient(90deg,var(--accent-primary),var(--accent-strong))] transition-all" style={{ width: `${progress}%` }} />
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
          <span className="soft-label">{isUploading ? `Uploading dataset... ${progress}%` : 'Ready for a new dataset'}</span>
          {message ? <span className="text-[var(--accent-strong)]">{message}</span> : null}
          {error ? <span className="text-red-200">{error}</span> : null}
        </div>
      </div>
    </div>
  );
}