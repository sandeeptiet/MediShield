import GoogleProvider from "next-auth/providers/google";
import type { AuthOptions } from "next-auth";

const BACKEND_URL =
  process.env.BACKEND_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000/api/v1";

export const authOptions: AuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID ?? "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
      authorization: { params: { prompt: "consent", access_type: "offline" } },
    }),
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, account }) {
      // First sign-in: exchange Google id_token for a MediShield JWT.
      if (account?.id_token) {
        try {
          const res = await fetch(`${BACKEND_URL}/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id_token: account.id_token }),
          });
          if (res.ok) {
            const data = await res.json();
            token.medishieldJwt = data.access_token;
            token.medishieldUserId = data.user.id;
            token.medishieldRole = data.user.role;
            token.medishieldExpiresAt = Math.floor(Date.now() / 1000) + data.expires_in;
          } else if (res.status === 403) {
            token.error = "BackendDenied";
          } else {
            token.error = "BackendUnavailable";
          }
        } catch {
          token.error = "BackendUnavailable";
        }
      }
      return token;
    },
    async session({ session, token }) {
      session.medishieldJwt = token.medishieldJwt;
      session.error = token.error;
      session.user = {
        ...session.user,
        id: token.medishieldUserId,
        role: token.medishieldRole,
      };
      return session;
    },
    async signIn({ account }) {
      // Block sign-in if we couldn't get a MediShield JWT.
      // We re-call the backend here so an unauthorized email never lands a session.
      if (!account?.id_token) return false;
      try {
        const res = await fetch(`${BACKEND_URL}/auth/google`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id_token: account.id_token }),
        });
        if (res.status === 403) return "/login?error=denied";
        if (!res.ok) return "/login?error=backend";
        return true;
      } catch {
        return "/login?error=backend";
      }
    },
  },
  pages: { signIn: "/login" },
};
