"use client";

// Phase 2 will replace the placeholder button with `signIn("google")` from next-auth.

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow">
        <h1 className="mb-2 text-2xl font-semibold">Sign in to MediShield</h1>
        <p className="mb-6 text-sm text-slate-500">
          Only authorized reviewers and admins can access this system.
        </p>

        <button
          type="button"
          disabled
          className="w-full rounded-md border border-slate-300 bg-white px-4 py-3 text-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Sign in with Google (Phase 2)
        </button>
      </div>
    </main>
  );
}
