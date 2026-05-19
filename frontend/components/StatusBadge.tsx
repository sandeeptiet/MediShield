import type { CaseStatus, Decision } from "@/lib/api";

const STATUS_STYLES: Record<CaseStatus, string> = {
  RECEIVED: "bg-slate-100 text-slate-700",
  CLASSIFIED: "bg-blue-100 text-blue-700",
  PROCESSING: "bg-amber-100 text-amber-700",
  DECIDED: "bg-emerald-50 text-emerald-700",
  FAILED: "bg-red-100 text-red-700",
};

const DECISION_STYLES: Record<Decision, string> = {
  APPROVE: "bg-emerald-100 text-emerald-800",
  REJECT: "bg-red-100 text-red-800",
  ESCALATE: "bg-amber-100 text-amber-800",
};

export function StatusBadge({ status }: { status: CaseStatus }) {
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {status}
    </span>
  );
}

export function DecisionBadge({ decision }: { decision: Decision | null }) {
  if (!decision) return <span className="text-slate-400">—</span>;
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${DECISION_STYLES[decision]}`}
    >
      {decision}
    </span>
  );
}
