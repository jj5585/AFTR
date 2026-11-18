"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { KeyRound, ArrowRight, ShieldCheck, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function InviteEntryPage() {
  const router = useRouter();
  const [tokenInput, setTokenInput] = useState("");

  const handleValidate = (e: React.FormEvent) => {
    e.preventDefault();
    let cleaned = tokenInput.trim();
    // Support pasting full invite URLs (e.g. http://localhost:3000/invite/xyz)
    if (cleaned.includes("/invite/")) {
      cleaned = cleaned.split("/invite/")[1].split("?")[0];
    }
    if (cleaned) {
      router.push(`/invite/${encodeURIComponent(cleaned)}`);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <Card className="w-full max-w-md border-border/60 bg-card/70 backdrop-blur shadow-xl">
        <CardHeader className="space-y-2 text-center">
          <div className="flex justify-center mb-2">
            <Badge variant="outline" className="border-primary/40 text-primary px-3 py-1 text-xs gap-1.5">
              <Lock className="w-3 h-3 text-emerald-400" />
              Member Access Gate
            </Badge>
          </div>
          <CardTitle className="text-2xl font-black tracking-tight">
            Invitation Entry
          </CardTitle>
          <CardDescription className="text-xs">
            Every eligible adult member is allocated 3 single-use invitations with a strict 72-hour TTL.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleValidate}>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="invite-token">Invitation Token or Link</Label>
              <Input
                id="invite-token"
                placeholder="Paste code or link here..."
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                required
              />
              <p className="text-[11px] text-muted-foreground">
                Tokens are 32-character high-entropy cryptographic strings.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-background/50 border border-border/40 text-[11px] text-muted-foreground flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                Invitations are bound to their recipient’s intended email address. You will verify this address in the next step.
              </span>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full gap-2" disabled={!tokenInput.trim()}>
              <KeyRound className="w-4 h-4" />
              Validate Invitation
              <ArrowRight className="w-4 h-4" />
            </Button>

            <div className="text-center pt-2 border-t border-border/40 w-full text-xs text-muted-foreground">
              Already a member?{" "}
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
