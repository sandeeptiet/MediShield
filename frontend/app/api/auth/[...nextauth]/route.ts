// NextAuth Google provider handler. Phase 2 enables this:
//
// import NextAuth from "next-auth";
// import GoogleProvider from "next-auth/providers/google";
//
// const handler = NextAuth({
//   providers: [
//     GoogleProvider({
//       clientId: process.env.GOOGLE_CLIENT_ID!,
//       clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
//     }),
//   ],
//   callbacks: {
//     async signIn({ profile }) {
//       // Exchange Google ID token for a MediShield JWT via backend.
//       // Reject if backend says email is not in the allowlist.
//       return true;
//     },
//     async jwt({ token, account }) {
//       if (account) token.medishieldJwt = account.id_token;
//       return token;
//     },
//     async session({ session, token }) {
//       (session as any).medishieldJwt = token.medishieldJwt;
//       return session;
//     },
//   },
// });
//
// export { handler as GET, handler as POST };

export const dynamic = "force-dynamic";

export async function GET() {
  return new Response("NextAuth not yet wired up (Phase 2).", { status: 501 });
}

export async function POST() {
  return new Response("NextAuth not yet wired up (Phase 2).", { status: 501 });
}
