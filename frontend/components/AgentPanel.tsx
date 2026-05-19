"use client";

import { useState } from "react";

export function AgentPanel({
  title,
  data,
  defaultOpen = false,
}: {
  title: string;
  data: unknown;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  if (data == null) {
    return (
      <details className="rounded-md border border-slate-200 bg-white p-3 text-sm text-slate-500">
        <summary className="cursor-pointer font-medium text-slate-700">{title}</summary>
        <p className="mt-2">No output recorded.</p>
      </details>
    );
  }

  return (
    <div className="rounded-md border border-slate-200 bg-white">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between p-3 text-left text-sm font-medium text-slate-700 hover:bg-slate-50"
      >
        <span>{title}</span>
        <span className="text-slate-400">{open ? "▾" : "▸"}</span>
      </button>
      {open && (
        <pre className="overflow-x-auto border-t bg-slate-50 p-3 text-xs text-slate-800">
{JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}
