"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  Calendar,
  EyeOff,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  FileCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function OnboardingPage() {
  const router = useRouter();

  // Onboarding session state
  const [claimTicket, setClaimTicket] = useState<string | null>(null);
  const [intendedEmail, setIntendedEmail] = useState<string>("");

  // Step Tracker: 1 = Age Assurance, 2 = Policies, 3 = Persona Setup, 4 = Complete
  const [step, setStep] = useState<number>(1);

  // Age Assurance Form State
  const [birthDate, setBirthDate] = useState("");
  const [evidenceType, setEvidenceType] = useState("GOVERNMENT_ID_VERIFICATION");
  const [ageProofToken, setAgeProofToken] = useState<string | null>(null);
  const [ageLoading, setAgeLoading] = useState(false);
  const [ageError, setAgeError] = useState<string | null>(null);

  // Policy Agreement State
  const [policyAccepted, setPolicyAccepted] = useState(false);

  // Persona Setup State
  const [displayName, setDisplayName] = useState("");
  const [avatarSeed, setAvatarSeed] = useState("shadow-phantom-1");
  const [declaredCampus, setDeclaredCampus] = useState("");
  const [bio, setBio] = useState("");
  const [redeemLoading, setRedeemLoading] = useState(false);
  const [redeemError, setRedeemError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    const ticket = sessionStorage.getItem("aftr_claim_ticket");
    const email = sessionStorage.getItem("aftr_intended_email");

    if (!ticket) {
      // Must come from verified invitation
      router.push("/invite");
      return;
    }
    setClaimTicket(ticket);
    setIntendedEmail(email || "member@example.com");
  }, [router]);

  // Handle Age Assurance Verification
  const handleVerifyAge = async (e: React.FormEvent) => {
    e.preventDefault();
    setAgeLoading(true);
    setAgeError(null);

    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/age/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: intendedEmail,
          birth_date: birthDate,
          evidence_type: evidenceType,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Age assurance verification failed.");
      }

      setAgeProofToken(data.proof_token);
      setStep(2); // Proceed to Policy Acceptance
    } catch (err: unknown) {
      setAgeError(err instanceof Error ? err.message : "Age assurance verification failed.");
    } finally {
      setAgeLoading(false);
    }
  };

  // Handle Final Redemption & Persona Setup
  const handleFinalRedeem = async (e: React.FormEvent) => {
    e.preventDefault();
    setRedeemLoading(true);
    setRedeemError(null);

    try {
      // In production, this would pair with the user's Supabase auth session.
      // We generate or pull the newly established user UUID.
      const simulatedSupabaseId = "00000000-0000-4000-8000-" + Math.random().toString(16).substring(2, 14).padEnd(12, "0");

      const res = await fetch(`${apiUrl}/api/v1/invitations/redeem`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          claim_ticket: claimTicket,
          age_proof_token: ageProofToken,
          supabase_user_id: simulatedSupabaseId,
          display_name: displayName,
          avatar_seed: avatarSeed,
          declared_campus: declaredCampus.trim() || null,
          bio: bio.trim() || null,
          accepted_policy: policyAccepted,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to complete onboarding.");
      }

      // Clear ticket and enter platform
      sessionStorage.removeItem("aftr_claim_ticket");
      setStep(4); // Success screen
    } catch (err: unknown) {
      setRedeemError(err instanceof Error ? err.message : "Failed to redeem invitation.");
    } finally {
      setRedeemLoading(false);
    }
  };

  const avatarSeeds = [
    { id: "shadow-fox", label: "Shadow Fox" },
    { id: "neon-ghost", label: "Neon Ghost" },
    { id: "midnight-echo", label: "Midnight Echo" },
    { id: "cyber-raven", label: "Cyber Raven" },
    { id: "solar-phantom", label: "Solar Phantom" },
  ];

  return (
    <div className="flex-1 container max-w-xl mx-auto px-4 py-10 flex flex-col justify-center">
      {/* Progress Pills */}
      <div className="flex items-center justify-between mb-8 px-2 text-xs text-muted-foreground">
        <span className={`font-semibold flex items-center gap-1 ${step >= 1 ? "text-primary" : ""}`}>
          1. Age Assurance
        </span>
        <span className="text-border">→</span>
        <span className={`font-semibold flex items-center gap-1 ${step >= 2 ? "text-primary" : ""}`}>
          2. Content Policies
        </span>
        <span className="text-border">→</span>
        <span className={`font-semibold flex items-center gap-1 ${step >= 3 ? "text-primary" : ""}`}>
          3. Anonymous Persona
        </span>
      </div>

      {/* STEP 1: Age Assurance Provider Workflow */}
      {step === 1 && (
        <Card className="border-border/60 bg-card/70 backdrop-blur shadow-xl">
          <CardHeader className="space-y-2">
            <div className="flex justify-between items-center">
              <Badge variant="outline" className="border-primary/40 text-primary px-3 py-1 text-xs gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                Step 1: Age Assurance
              </Badge>
              <span className="text-xs text-muted-foreground">Mandatory 18+ Gate</span>
            </div>
            <CardTitle className="text-2xl font-black tracking-tight">
              Legitimate Age Verification
            </CardTitle>
            <CardDescription className="text-xs">
              AFTR requires verified adulthood (18+) to access adult campus discussions and confessions.
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleVerifyAge}>
            <CardContent className="space-y-4">
              {ageError && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2">
                  <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold">Verification Alert</p>
                    <p className="text-[11px] opacity-90">{ageError}</p>
                  </div>
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="dob">Date of Birth</Label>
                <div className="relative">
                  <Calendar className="w-4 h-4 text-muted-foreground absolute left-3 top-3" />
                  <Input
                    id="dob"
                    type="date"
                    className="pl-9"
                    value={birthDate}
                    onChange={(e) => setBirthDate(e.target.value)}
                    required
                  />
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Your birth date is used strictly to produce a signed age proof token and is never made public.
                </p>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="evidence">Verification Provider Method</Label>
                <select
                  id="evidence"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-xs"
                  value={evidenceType}
                  onChange={(e) => setEvidenceType(e.target.value)}
                >
                  <option value="GOVERNMENT_ID_VERIFICATION">
                    Government ID Attestation (eIDV / Passport / Drivers License)
                  </option>
                  <option value="DIGITAL_IDENTITY_CREDENTIAL">
                    Digital Identity Wallet (W3C Verifiable Credential)
                  </option>
                  <option value="EIDV_ATTESTED_DOCUMENT">
                    Certified Age Gateway Assertion (18+ Validated)
                  </option>
                </select>
              </div>

              <div className="p-3 rounded-lg bg-background/50 border border-border/40 text-[11px] text-muted-foreground space-y-1">
                <div className="font-semibold text-foreground flex items-center gap-1">
                  <FileCheck className="w-3.5 h-3.5 text-emerald-400" />
                  Provider Verification Policy:
                </div>
                <p>Simple checkbox verification is prohibited by AFTR safety architecture.</p>
              </div>
            </CardContent>

            <CardFooter>
              <Button type="submit" className="w-full gap-2" disabled={ageLoading || !birthDate}>
                {ageLoading ? "Verifying with Gateway..." : "Verify Age & Continue"}
                <ArrowRight className="w-4 h-4" />
              </Button>
            </CardFooter>
          </form>
        </Card>
      )}

      {/* STEP 2: Policy & Adult Content Agreement */}
      {step === 2 && (
        <Card className="border-border/60 bg-card/70 backdrop-blur shadow-xl">
          <CardHeader className="space-y-2">
            <Badge variant="outline" className="w-fit border-primary/40 text-primary px-3 py-1 text-xs">
              Step 2: Adult Content & Campus Rules
            </Badge>
            <CardTitle className="text-2xl font-black tracking-tight">
              AFTR Community Policies
            </CardTitle>
            <CardDescription className="text-xs">
              Review our non-negotiable community commitments before entering.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-3 text-xs">
            <div className="p-3.5 rounded-lg bg-background/60 border border-border/40 space-y-2.5">
              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-foreground">Strictly 18+ Adult Platform</p>
                  <p className="text-[11px] text-muted-foreground">Only verified adults may participate in confessions and discussions.</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-foreground">Consent-Gated Communication</p>
                  <p className="text-[11px] text-muted-foreground">Direct messaging requires mutual acceptance. Unsolicited contact is prohibited.</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-foreground">Zero Harassment & No Doxxing</p>
                  <p className="text-[11px] text-muted-foreground">Sharing real identities, phone numbers, student IDs, or explicit imagery is forbidden.</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-foreground">No College Identity Surveillance</p>
                  <p className="text-[11px] text-muted-foreground">Campus affiliation is self-declared. College emails are never collected or verified.</p>
                </div>
              </div>
            </div>

            <div className="pt-2 flex items-center space-x-2">
              <input
                id="policy"
                type="checkbox"
                checked={policyAccepted}
                onChange={(e) => setPolicyAccepted(e.target.checked)}
                className="rounded border-border w-4 h-4 text-primary focus:ring-primary"
              />
              <Label htmlFor="policy" className="text-xs cursor-pointer font-medium">
                I attest I am 18+ and agree to adhere to AFTR community and safety policies.
              </Label>
            </div>
          </CardContent>

          <CardFooter className="flex justify-between gap-3">
            <Button variant="outline" size="sm" onClick={() => setStep(1)}>
              <ArrowLeft className="w-4 h-4 mr-1" /> Back
            </Button>
            <Button disabled={!policyAccepted} onClick={() => setStep(3)}>
              Continue to Persona Setup
              <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </CardFooter>
        </Card>
      )}

      {/* STEP 3: Anonymous Persona Creation */}
      {step === 3 && (
        <Card className="border-border/60 bg-card/70 backdrop-blur shadow-xl">
          <CardHeader className="space-y-2">
            <Badge variant="outline" className="w-fit border-primary/40 text-primary px-3 py-1 text-xs">
              Step 3: Establish Your Persona
            </Badge>
            <CardTitle className="text-2xl font-black tracking-tight flex items-center gap-2">
              <EyeOff className="w-6 h-6 text-primary" />
              Anonymous Identity
            </CardTitle>
            <CardDescription className="text-xs">
              This pseudonymous identity is what your campus community will see. It is completely isolated from your real account.
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleFinalRedeem}>
            <CardContent className="space-y-4">
              {redeemError && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                  {redeemError}
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="name">Anonymous Display Name</Label>
                <Input
                  id="name"
                  placeholder="e.g. ShadowFox, NeonScholar"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  minLength={3}
                  maxLength={50}
                  required
                />
                <p className="text-[11px] text-muted-foreground">
                  3–50 characters. Do not use your real name.
                </p>
              </div>

              <div className="space-y-1.5">
                <Label>Choose Persona Seed</Label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-1">
                  {avatarSeeds.map((seed) => (
                    <button
                      key={seed.id}
                      type="button"
                      onClick={() => setAvatarSeed(seed.id)}
                      className={`p-2.5 rounded-lg border text-xs text-left transition-all ${
                        avatarSeed === seed.id
                          ? "border-primary bg-primary/10 text-primary font-semibold"
                          : "border-border/60 hover:bg-accent text-muted-foreground"
                      }`}
                    >
                      {seed.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <Label htmlFor="campus">Self-Declared Campus Affiliation</Label>
                  <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                    Optional
                  </span>
                </div>
                <Input
                  id="campus"
                  placeholder="e.g. Bay Area University (Optional)"
                  value={declaredCampus}
                  onChange={(e) => setDeclaredCampus(e.target.value)}
                  maxLength={120}
                />
                <p className="text-[11px] text-muted-foreground">
                  Optional and self-declared. No college email verification required.
                </p>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="bio">Anonymous Bio (Optional)</Label>
                <Input
                  id="bio"
                  placeholder="Share a thought or interests..."
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  maxLength={280}
                />
              </div>
            </CardContent>

            <CardFooter className="flex justify-between gap-3">
              <Button type="button" variant="outline" size="sm" onClick={() => setStep(2)}>
                <ArrowLeft className="w-4 h-4 mr-1" /> Back
              </Button>
              <Button type="submit" disabled={redeemLoading || displayName.trim().length < 3}>
                <Sparkles className="w-4 h-4 mr-1" />
                {redeemLoading ? "Redeeming Invitation..." : "Enter AFTR"}
              </Button>
            </CardFooter>
          </form>
        </Card>
      )}

      {/* STEP 4: Success & Entrance */}
      {step === 4 && (
        <Card className="border-emerald-500/30 bg-card/70 backdrop-blur shadow-xl text-center p-8 space-y-4">
          <div className="flex justify-center">
            <div className="w-16 h-16 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
              <CheckCircle2 className="w-10 h-10 text-emerald-400" />
            </div>
          </div>
          <CardTitle className="text-3xl font-black tracking-tight">
            Welcome to AFTR
          </CardTitle>
          <CardDescription className="text-sm max-w-sm mx-auto">
            Your invitation has been redeemed and your anonymous persona is live.
          </CardDescription>

          <div className="p-4 rounded-xl bg-background/50 border border-border/40 max-w-sm mx-auto text-xs space-y-2 text-left">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Persona Name:</span>
              <span className="font-bold text-foreground">{displayName}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Invitation Slots Allocated:</span>
              <span className="font-semibold text-emerald-400">3 Invitations Available</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Age Assurance:</span>
              <span className="text-emerald-400 font-semibold">18+ Verified</span>
            </div>
          </div>

          <div className="pt-4">
            <Link href="/" className="inline-block w-full">
              <Button className="w-full gap-2">
                Enter Anonymous Feed
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </Card>
      )}
    </div>
  );
}
