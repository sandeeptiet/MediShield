import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MediShield AI",
  description: "Multi-agent claims intake & triage",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
