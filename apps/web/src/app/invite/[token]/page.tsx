"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  CheckCircle2,
  Clock,
  Ban,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  Loader2,
  Mail,
  Key,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type InvitationState =
  | "LOADING"
  | "VALID"
  | "EXPIRED"
  | "REVOKED"
  | "ALREADY_REDEEMED"
  | "NOT_FOUND";

export default function InviteValidationPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;

  const [state, setState] = useState<InvitationState>("LOADING");
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Recipient email binding verification input
  const [recipientEmail, setRecipientEmail] = useState("");
  const [claimLoading, setClaimLoading] = useState(false);
  const [claimError, setClaimError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const validateToken = useCallback(async () => {
    if (!token) return;
    setState("LOADING");
    setErrorMessage(null);

    try {
      const res = await fetch(`${apiUrl}/api/v1/invitations/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });

      if (!res.ok) {
        throw new Error(`Validation service returned ${res.status}`);
      }

      const data = await res.json();
      setState(data.status as InvitationState);
      setExpiresAt(data.expires_at || null);
      setErrorMessage(data.message);
    } catch (err: unknown) {
      setState("NOT_FOUND");
      setErrorMessage(err instanceof Error ? err.message : "Failed to validate invitation code.");
    }
  }, [token, apiUrl]);

  useEffect(() => {
    validateToken();
  }, [validateToken]);

  const handleClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    setClaimLoading(true);
    setClaimError(null);

    try {
      const res = await fetch(`${apiUrl}/api/v1/invitations/claim`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, recipient_email: recipientEmail }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Recipient email does not match invitation binding.");
      }

      // Store claim ticket and recipient email for onboarding
      sessionStorage.setItem("aftr_claim_ticket", data.claim_ticket);
      sessionStorage.setItem("aftr_intended_email", recipientEmail);

      router.push("/onboarding");
    } catch (err: unknown) {
      setClaimError(err instanceof Error ? err.message : "Recipient verification failed.");
    } finally {
      setClaimLoading(false);
    }
  };

  // 1. Loading State
  if (state === "LOADING") {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-border/60 bg-card/70 backdrop-blur p-8 text-center space-y-4">
          <Loader2 className="w-10 h-10 text-primary animate-spin mx-auto" />
          <h2 className="text-xl font-bold">Verifying Invitation Code</h2>
          <p className="text-xs text-muted-foreground">Checking cryptographic signature and expiry window...</p>
        </Card>
      </div>
    );
  }

  // 2. EXPIRED State Screen
  if (state === "EXPIRED") {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-rose-500/30 bg-card/70 backdrop-blur text-center shadow-xl">
          <CardHeader className="space-y-2">
            <div className="flex justify-center mb-2">
              <Badge variant="destructive" className="px-3 py-1 text-xs gap-1.5">
                <Clock className="w-3.5 h-3.5" />
                Invitation Expired
              </Badge>
            </div>
            <CardTitle className="text-2xl font-black tracking-tight text-rose-300">
              72-Hour TTL Exceeded
            </CardTitle>
            <CardDescription className="text-xs">
              Every AFTR invitation is strictly valid for 72 hours from the moment of issuance to preserve network freshness and security.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground space-y-3">
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-200">
              {errorMessage || "This invitation code has passed its expiration deadline."}
            </div>
            <p>Please contact the member who invited you and request a newly issued invitation code.</p>
          </CardContent>
          <CardFooter className="flex flex-col space-y-2">
            <Link href="/invite" className="w-full">
              <Button variant="outline" className="w-full">
                Try Another Code
              </Button>
            </Link>
          </CardFooter>
        </Card>
      </div>
    );
  }

  // 3. REVOKED State Screen
  if (state === "REVOKED") {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-amber-500/30 bg-card/70 backdrop-blur text-center shadow-xl">
          <CardHeader className="space-y-2">
            <div className="flex justify-center mb-2">
              <Badge variant="outline" className="border-amber-500/40 text-amber-400 px-3 py-1 text-xs gap-1.5">
                <Ban className="w-3.5 h-3.5" />
                Invitation Revoked
              </Badge>
            </div>
            <CardTitle className="text-2xl font-black tracking-tight text-amber-300">
              Code Revoked by Sender
            </CardTitle>
            <CardDescription className="text-xs">
              This invitation token was actively revoked by the issuing member prior to redemption.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground space-y-3">
            <p>Revoked invitations are permanently deactivated and cannot be claimed or renewed.</p>
          </CardContent>
          <CardFooter className="flex flex-col space-y-2">
            <Link href="/invite" className="w-full">
              <Button variant="outline" className="w-full">
                Enter Different Invitation
              </Button>
            </Link>
          </CardFooter>
        </Card>
      </div>
    );
  }

  // 4. ALREADY_REDEEMED State Screen
  if (state === "ALREADY_REDEEMED") {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-indigo-500/30 bg-card/70 backdrop-blur text-center shadow-xl">
          <CardHeader className="space-y-2">
            <div className="flex justify-center mb-2">
              <Badge variant="secondary" className="px-3 py-1 text-xs gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />
                Already Redeemed
              </Badge>
            </div>
            <CardTitle className="text-2xl font-black tracking-tight text-indigo-300">
              Single-Use Token Consumed
            </CardTitle>
            <CardDescription className="text-xs">
              AFTR invitations are single-use only. This token has already been successfully redeemed to create an account.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground space-y-3">
            <p>If you have already created your anonymous persona, please proceed directly to sign in.</p>
          </CardContent>
          <CardFooter className="flex flex-col space-y-2">
            <Link href="/login" className="w-full">
              <Button className="w-full">
                Proceed to Sign In
              </Button>
            </Link>
          </CardFooter>
        </Card>
      </div>
    );
  }

  // 5. NOT_FOUND State Screen
  if (state === "NOT_FOUND") {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-border/60 bg-card/70 backdrop-blur text-center shadow-xl">
          <CardHeader className="space-y-2">
            <div className="flex justify-center mb-2">
              <AlertTriangle className="w-10 h-10 text-muted-foreground" />
            </div>
            <CardTitle className="text-2xl font-black tracking-tight">
              Invitation Not Found
            </CardTitle>
            <CardDescription className="text-xs">
              The invitation code provided could not be verified in our records.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            <p>Ensure you copied the complete token from your invitation message.</p>
          </CardContent>
          <CardFooter className="flex flex-col space-y-2">
            <Link href="/invite" className="w-full">
              <Button variant="outline" className="w-full">
                Re-enter Code
              </Button>
            </Link>
          </CardFooter>
        </Card>
      </div>
    );
  }

  // 6. VALID State Screen (Recipient Binding & Claim Form)
  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <Card className="w-full max-w-md border-border/60 bg-card/70 backdrop-blur shadow-xl">
        <CardHeader className="space-y-2 text-center">
          <div className="flex justify-center mb-2">
            <Badge variant="outline" className="border-emerald-500/40 text-emerald-400 px-3 py-1 text-xs gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Invitation Valid
            </Badge>
          </div>
          <CardTitle className="text-2xl font-black tracking-tight">
            Claim Your Invitation
          </CardTitle>
          <CardDescription className="text-xs">
            Verify the email address where your invitation was dispatched.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleClaim}>
          <CardContent className="space-y-4">
            {expiresAt && (
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-background/50 border border-border/40 text-xs">
                <span className="text-muted-foreground flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-primary" />
                  Expires In:
                </span>
                <span className="font-mono text-[11px] text-foreground">
                  {new Date(expiresAt).toLocaleString()}
                </span>
              </div>
            )}

            {claimError && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Recipient Mismatch</p>
                  <p className="text-[11px] opacity-90">{claimError}</p>
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="email">Your Bound Email Address</Label>
              <div className="relative">
                <Mail className="w-4 h-4 text-muted-foreground absolute left-3 top-3" />
                <Input
                  id="email"
                  type="email"
                  className="pl-9"
                  placeholder="name@example.com"
                  value={recipientEmail}
                  onChange={(e) => setRecipientEmail(e.target.value)}
                  required
                />
              </div>
              <p className="text-[11px] text-muted-foreground">
                Must match the exact email your inviter specified.
              </p>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-3">
            <Button type="submit" className="w-full gap-2" disabled={claimLoading || !recipientEmail.trim()}>
              <Key className="w-4 h-4" />
              {claimLoading ? "Verifying..." : "Verify & Continue to Onboarding"}
              <ArrowRight className="w-4 h-4" />
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
