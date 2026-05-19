import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold">MediShield AI</h1>
      <p className="text-slate-600">Multi-agent claims intake & triage</p>
      <Link
        href="/login"
        className="rounded-md bg-brand-600 px-6 py-3 text-white hover:bg-brand-700"
      >
        Sign in
      </Link>
    </main>
  );
}
