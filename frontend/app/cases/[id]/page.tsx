"use client";

import { useSession } from "next-auth/react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AgentPanel } from "@/components/AgentPanel";
import { OverrideForm } from "@/components/OverrideForm";
import { DecisionBadge, StatusBadge } from "@/components/StatusBadge";
import { getCase, overrideCase, type CaseDetail, type Decision } from "@/lib/api";

const POLL_MS = 2000;

export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: session, status } = useSession();
  const router = useRouter();
  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const token = session?.medishieldJwt;
  const role = session?.user?.role;

  const refresh = useCallback(async () => {
    if (!token || !id) return;
    try {
      const detail = await getCase(token, id);
      setCaseData(detail);
      setLoadError(null);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : String(err));
    }
  }, [token, id]);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
    }
  }, [status, router]);

  useEffect(() => {
    if (token) void refresh();
  }, [token, refresh]);

  // Poll while the case is still being processed.
  useEffect(() => {
    if (!caseData) return;
    const inFlight = ["RECEIVED", "CLASSIFIED", "PROCESSING"].includes(caseData.status);
    if (!inFlight) return;
    const t = setInterval(refresh, POLL_MS);
    return () => clearInterval(t);
  }, [caseData, refresh]);

  if (status !== "authenticated" || !token) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-slate-500">Loading…</p>
      </main>
    );
  }

  if (loadError) {
    return (
      <main className="min-h-screen p-8">
        <BackLink />
        <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {loadError}
        </p>
      </main>
    );
  }

  if (!caseData) {
    return (
      <main className="min-h-screen p-8">
        <BackLink />
        <p className="text-slate-500">Loading case…</p>
      </main>
    );
  }

  const agents = (caseData.agent_outputs ?? {}) as Record<string, unknown>;
  const canOverride = role === "ADMIN" && caseData.status === "DECIDED" && caseData.decision !== null;

  const submitOverride = async (decision: Decision, note: string) => {
    await overrideCase(token, caseData.case_id, decision, note);
    await refresh();
  };

  return (
    <main className="min-h-screen p-8">
      <BackLink />

      <header className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="font-mono text-xl">{caseData.case_id}</h1>
          <p className="mt-1 text-sm text-slate-500">
            {caseData.document_type ?? "Unclassified"} ·{" "}
            uploaded {new Date(caseData.created_at).toLocaleString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={caseData.status} />
          <DecisionBadge decision={caseData.decision} />
          {caseData.confidence != null && (
            <span className="text-sm text-slate-500">
              {(caseData.confidence * 100).toFixed(0)}% conf.
            </span>
          )}
        </div>
      </header>

      {caseData.error_message && (
        <p className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          Error: {caseData.error_message}
        </p>
      )}

      {caseData.justification && (
        <section className="mb-6 rounded-xl bg-white p-4 shadow">
          <h2 className="mb-2 text-sm font-semibold uppercase text-slate-500">
            Justification
          </h2>
          <p className="text-sm leading-relaxed text-slate-800">
            {caseData.justification}
          </p>
        </section>
      )}

      {canOverride && caseData.decision && (
        <section className="mb-6">
          <OverrideForm currentDecision={caseData.decision} onSubmit={submitOverride} />
        </section>
      )}

      <section className="space-y-2">
        <h2 className="mb-2 text-sm font-semibold uppercase text-slate-500">
          Agent outputs
        </h2>
        <AgentPanel title="Classifier" data={agents.classifier} defaultOpen />
        <AgentPanel title="KYC" data={agents.kyc} />
        <AgentPanel title="Claims" data={agents.claims} />
        <AgentPanel title="Policy RAG" data={agents.policy} />
        <AgentPanel title="Fraud" data={agents.fraud} />
        {agents.errors && (
          <AgentPanel title="Errors" data={agents.errors} defaultOpen />
        )}
      </section>
    </main>
  );
}

function BackLink() {
  return (
    <Link
      href="/dashboard"
      className="mb-4 inline-block text-sm text-brand-600 hover:underline"
    >
      ← Back to dashboard
    </Link>
  );
}
