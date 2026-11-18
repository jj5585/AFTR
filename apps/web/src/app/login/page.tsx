"use client";

import { useState } from "react";
import Link from "next/link";
import { Lock, EyeOff, KeyRound, AlertCircle, CheckCircle2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    // Demonstration of authentication bridge
    if (!email || !password) {
      setError("Please supply both email address and password.");
      setLoading(false);
      return;
    }

    try {
      // In production, this communicates with Supabase Auth client:
      // const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      await new Promise((resolve) => setTimeout(resolve, 800));
      setSuccess("Authentication verified. Entering AFTR...");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to log in.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <Card className="w-full max-w-md border-border/60 bg-card/70 backdrop-blur shadow-xl">
        <CardHeader className="space-y-2 text-center">
          <div className="flex justify-center mb-2">
            <Badge variant="outline" className="border-primary/40 text-primary px-3 py-1 text-xs gap-1">
              <Lock className="w-3 h-3 text-emerald-400" />
              Strictly Invitation-Only
            </Badge>
          </div>
          <CardTitle className="text-2xl font-black tracking-tight flex items-center justify-center gap-2">
            <EyeOff className="w-6 h-6 text-primary" />
            Sign in to AFTR
          </CardTitle>
          <CardDescription className="text-xs">
            Enter your credentials to access your anonymous adult campus community.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleLogin}>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                <span>{error}</span>
              </div>
            )}
            {success && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                <span>{success}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="email">Registered Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <Label htmlFor="password">Password</Label>
                <Link
                  href="/login#recovery"
                  className="text-[11px] text-muted-foreground hover:text-primary transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full gap-2" disabled={loading}>
              <KeyRound className="w-4 h-4" />
              {loading ? "Authenticating..." : "Sign In"}
            </Button>

            <div className="text-center space-y-2 pt-2 border-t border-border/40 w-full text-xs text-muted-foreground">
              <p>Received an invitation?</p>
              <Link
                href="/invite"
                className="inline-flex items-center gap-1 text-primary hover:underline font-semibold"
              >
                Validate Invitation Code
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
