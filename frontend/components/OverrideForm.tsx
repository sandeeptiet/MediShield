"use client";

import { useState } from "react";

import type { Decision } from "@/lib/api";

interface Props {
  currentDecision: Decision;
  onSubmit: (decision: Decision, note: string) => Promise<void>;
}

const OPTIONS: Decision[] = ["APPROVE", "REJECT", "ESCALATE"];

export function OverrideForm({ currentDecision, onSubmit }: Props) {
  const [decision, setDecision] = useState<Decision>(
    currentDecision === "APPROVE" ? "REJECT" : "APPROVE",
  );
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <form
      className="space-y-3 rounded-md border border-amber-200 bg-amber-50 p-4"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setError(null);
        try {
          await onSubmit(decision, note);
        } catch (err) {
          setError(err instanceof Error ? err.message : String(err));
        } finally {
          setBusy(false);
        }
      }}
    >
      <h3 className="text-sm font-semibold text-amber-900">Admin override</h3>
      <div className="flex flex-wrap gap-2">
        {OPTIONS.filter((d) => d !== currentDecision).map((d) => (
          <label
            key={d}
            className={`cursor-pointer rounded-md border px-3 py-1 text-sm ${
              decision === d
                ? "border-amber-500 bg-amber-100 font-semibold"
                : "border-slate-200 bg-white"
            }`}
          >
            <input
              type="radio"
              name="decision"
              value={d}
              checked={decision === d}
              onChange={() => setDecision(d)}
              className="sr-only"
            />
            {d}
          </label>
        ))}
      </div>

      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Reason for overriding (visible in audit log)"
        className="w-full rounded-md border border-slate-300 bg-white p-2 text-sm"
        rows={2}
      />

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={busy}
        className="rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50"
      >
        {busy ? "Submitting…" : `Override → ${decision}`}
      </button>
    </form>
  );
}
