"use client";

import { signIn, useSession } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";

export default function LoginPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const params = useSearchParams();
  const errorParam = params.get("error");

  useEffect(() => {
    if (status === "authenticated" && !session.error) {
      router.replace("/dashboard");
    }
  }, [status, session, router]);

  const errorMessage =
    errorParam === "denied"
      ? "Access denied — your account is not authorized for MediShield."
      : errorParam === "backend"
        ? "The backend is unreachable. Please try again."
        : null;

  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow">
        <h1 className="mb-2 text-2xl font-semibold">Sign in to MediShield</h1>
        <p className="mb-6 text-sm text-slate-500">
          Only authorized reviewers and admins can access this system.
        </p>

        {errorMessage && (
          <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {errorMessage}
          </div>
        )}

        <button
          type="button"
          onClick={() => signIn("google", { callbackUrl: "/dashboard" })}
          className="w-full rounded-md border border-slate-300 bg-white px-4 py-3 text-slate-700 transition hover:bg-slate-50"
        >
          Sign in with Google
        </button>
      </div>
    </main>
  );
}
