"use client";

import { signOut, useSession } from "next-auth/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { DecisionBadge, StatusBadge } from "@/components/StatusBadge";
import { UploadCard } from "@/components/UploadCard";
import { listCases, type CaseListItem } from "@/lib/api";

const REFRESH_INTERVAL_MS = 3000;

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  const token = session?.medishieldJwt;

  const refresh = useCallback(async () => {
    if (!token) return;
    try {
      const res = await listCases(token);
      setCases(res.items);
      setLoadError(null);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : String(err));
    }
  }, [token]);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
    }
  }, [status, router]);

  useEffect(() => {
    if (!token) return;
    void refresh();
  }, [token, refresh]);

  // Poll while any case is still in-flight.
  useEffect(() => {
    if (!token) return;
    const inFlight = cases.some((c) =>
      ["RECEIVED", "CLASSIFIED", "PROCESSING"].includes(c.status),
    );
    if (!inFlight) return;
    const id = setInterval(refresh, REFRESH_INTERVAL_MS);
    return () => clearInterval(id);
  }, [cases, token, refresh]);

  if (status !== "authenticated" || !token) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-slate-500">Loading…</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-8">
      <header className="mb-8 flex items-center justify-between">
        <h1 className="text-3xl font-semibold">Dashboard</h1>
        <div className="flex items-center gap-4">
          <div className="text-right text-sm">
            <div className="font-medium">{session.user?.name}</div>
            <div className="text-slate-500">
              {session.user?.email} · {session.user?.role}
            </div>
          </div>
          <button
            type="button"
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
          >
            Sign out
          </button>
        </div>
      </header>

      <section className="mb-6">
        <UploadCard token={token} onUploaded={() => void refresh()} />
      </section>

      <section className="rounded-xl bg-white shadow">
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="text-lg font-medium">Cases</h2>
          <button
            type="button"
            onClick={() => void refresh()}
            className="rounded-md border border-slate-200 bg-white px-3 py-1 text-sm text-slate-600 hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>

        {loadError && (
          <p className="m-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Failed to load cases: {loadError}
          </p>
        )}

        <table className="w-full text-sm">
          <thead className="border-b text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2 font-medium">Case ID</th>
              <th className="px-4 py-2 font-medium">Document type</th>
              <th className="px-4 py-2 font-medium">Status</th>
              <th className="px-4 py-2 font-medium">Decision</th>
              <th className="px-4 py-2 font-medium">Confidence</th>
              <th className="px-4 py-2 font-medium">Created</th>
            </tr>
          </thead>
          <tbody>
            {cases.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                  No cases yet. Upload a document to get started.
                </td>
              </tr>
            ) : (
              cases.map((c) => (
                <tr key={c.case_id} className="border-b last:border-b-0 hover:bg-slate-50">
                  <td className="px-4 py-2 font-mono">
                    <Link href={`/cases/${c.case_id}`} className="text-brand-600 hover:underline">
                      {c.case_id.slice(0, 8)}…
                    </Link>
                  </td>
                  <td className="px-4 py-2">{c.document_type ?? "—"}</td>
                  <td className="px-4 py-2"><StatusBadge status={c.status} /></td>
                  <td className="px-4 py-2"><DecisionBadge decision={c.decision} /></td>
                  <td className="px-4 py-2">
                    {c.confidence != null ? `${(c.confidence * 100).toFixed(0)}%` : "—"}
                  </td>
                  <td className="px-4 py-2 text-slate-500">
                    {new Date(c.created_at).toLocaleString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </main>
  );
}
