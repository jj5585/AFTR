"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Lock, ArrowRight, ShieldAlert, Key } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function RegisterGatePage() {
  const router = useRouter();
  const [inviteToken, setInviteToken] = useState("");

  const handleProceedWithToken = (e: React.FormEvent) => {
    e.preventDefault();
    if (inviteToken.trim()) {
      router.push(`/invite/${encodeURIComponent(inviteToken.trim())}`);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <Card className="w-full max-w-md border-border/60 bg-card/70 backdrop-blur shadow-xl">
        <CardHeader className="space-y-2 text-center">
          <div className="flex justify-center mb-2">
            <Badge variant="outline" className="border-amber-500/40 text-amber-400 px-3 py-1 text-xs gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5" />
              Invitation Required
            </Badge>
          </div>
          <CardTitle className="text-2xl font-black tracking-tight">
            Invitation Gate
          </CardTitle>
          <CardDescription className="text-xs">
            AFTR is an 18+ invitation-only platform. Public self-registration without a single-use invitation is disabled.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleProceedWithToken}>
          <CardContent className="space-y-4">
            <div className="p-3.5 rounded-lg bg-background/50 border border-border/40 text-xs text-muted-foreground space-y-2">
              <div className="flex items-center gap-1.5 font-semibold text-foreground">
                <Lock className="w-4 h-4 text-emerald-400" />
                How to join AFTR:
              </div>
              <ol className="list-decimal list-inside space-y-1 text-[11px]">
                <li>Receive a personal invitation from an existing adult member.</li>
                <li>Enter your 32-character invitation code below.</li>
                <li>Verify your bound email address and complete age assurance (18+).</li>
              </ol>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="token">Enter Invitation Code</Label>
              <Input
                id="token"
                placeholder="Paste your 32-character invitation code..."
                value={inviteToken}
                onChange={(e) => setInviteToken(e.target.value)}
                required
              />
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full gap-2" disabled={!inviteToken.trim()}>
              <Key className="w-4 h-4" />
              Validate & Continue
              <ArrowRight className="w-4 h-4" />
            </Button>

            <div className="text-center pt-2 border-t border-border/40 w-full text-xs text-muted-foreground">
              Already have an account?{" "}
              <Link href="/login" className="text-primary hover:underline font-semibold">
                Sign In
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
