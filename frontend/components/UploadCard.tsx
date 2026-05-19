"use client";

import { useCallback, useRef, useState } from "react";

import { uploadCase } from "@/lib/api";

interface Props {
  token: string;
  onUploaded?: (caseId: string) => void;
}

export function UploadCard({ token, onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      setBusy(true);
      setError(null);
      try {
        const res = await uploadCase(token, files[0]);
        onUploaded?.(res.case_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setBusy(false);
        if (inputRef.current) inputRef.current.value = "";
      }
    },
    [token, onUploaded],
  );

  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white p-6">
      <h2 className="mb-2 text-lg font-medium">Upload a document</h2>
      <p className="mb-4 text-sm text-slate-500">
        JPEG, PNG, or PDF. The case will appear in the table below while it is processed.
      </p>

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,application/pdf,image/tiff"
        disabled={busy}
        onChange={(e) => handleFiles(e.target.files)}
        className="block w-full text-sm text-slate-600 file:mr-4 file:rounded-md file:border-0 file:bg-brand-600 file:px-4 file:py-2 file:text-white hover:file:bg-brand-700 disabled:opacity-50"
      />

      {busy && <p className="mt-3 text-sm text-slate-500">Uploading…</p>}
      {error && (
        <p className="mt-3 rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">
          {error}
        </p>
      )}
    </div>
  );
}
