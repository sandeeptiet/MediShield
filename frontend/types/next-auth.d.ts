import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    medishieldJwt?: string;
    user: {
      id?: number;
      email?: string | null;
      name?: string | null;
      role?: "REVIEWER" | "ADMIN";
    };
    error?: "BackendDenied" | "BackendUnavailable";
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    medishieldJwt?: string;
    medishieldUserId?: number;
    medishieldRole?: "REVIEWER" | "ADMIN";
    medishieldExpiresAt?: number;
    error?: "BackendDenied" | "BackendUnavailable";
  }
}
