import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { Shield, Lock, EyeOff } from "lucide-react";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "AFTR — 18+ Anonymous Campus Social Platform",
  description: "A private, invite-only anonymous social and connection network for adult campus communities.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} min-h-screen bg-background text-foreground antialiased flex flex-col`}
      >
        <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-14 max-w-screen-2xl items-center justify-between px-4 sm:px-8">
            <div className="flex items-center space-x-3">
              <span className="font-extrabold text-xl tracking-widest text-primary flex items-center gap-1.5">
                <EyeOff className="w-5 h-5 text-primary" />
                AFTR
              </span>
              <span className="text-[11px] font-semibold uppercase tracking-wider bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded-full">
                18+ Adult Network
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Lock className="w-3.5 h-3.5 text-emerald-500" />
                <span>Invite Only</span>
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 flex flex-col">{children}</main>

        <footer className="border-t border-border/40 py-6 md:py-8 bg-card/40">
          <div className="container flex flex-col md:flex-row items-center justify-between gap-4 px-4 sm:px-8 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-primary" />
              <p>
                AFTR. Strictly 18+. Invitation-only. Pseudonymous identity isolation enforced.
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <span>Campus Affiliation Self-Declared</span>
              <span>Consent-Based Connections</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
