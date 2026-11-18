"use client";

import { useEffect, useState, useCallback } from "react";
import { ShieldCheck, Activity, Database, Server, Key, EyeOff, CheckCircle2, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface HealthData {
  status: string;
  app: string;
  environment: string;
  timestamp_utc: string;
  services: {
    api: string;
    database: string;
    redis: string;
  };
}

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/api/v1/health`);
      if (!res.ok) {
        throw new Error(`Health check returned HTTP ${res.status}`);
      }
      const data = await res.json();
      setHealth(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to connect to backend API";
      setError(message);
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  return (
    <div className="flex-1 container max-w-5xl mx-auto px-4 py-12 flex flex-col items-center justify-center space-y-10">
      <div className="text-center space-y-4 max-w-2xl">
        <Badge variant="outline" className="border-primary/40 text-primary px-3 py-1 text-xs">
          Stage 1: Monorepo Foundation & Health Verification
        </Badge>
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight text-foreground">
          AFTR Platform
        </h1>
        <p className="text-muted-foreground text-sm sm:text-base">
          A private, invitation-only anonymous social and connection platform for adult (18+) campus communities.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
        {/* Backend & Services Live Health Card */}
        <Card className="border-border/60 bg-card/60 backdrop-blur">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Activity className="w-5 h-5 text-primary" />
                <CardTitle className="text-lg">Backend Health Bridge</CardTitle>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={fetchHealth}
                disabled={loading}
                className="h-8 gap-1 text-xs"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>
            <CardDescription className="text-xs">
              Direct verification of Frontend to FastAPI, PostgreSQL, and Redis connectivity.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-3 rounded-lg bg-background/50 border border-border/40 space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Target API URL:</span>
                <span className="font-mono text-[11px] text-foreground">{apiUrl}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">API Status:</span>
                {health?.services.api === "healthy" ? (
                  <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Healthy
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-rose-400 font-medium">
                    <AlertCircle className="w-3.5 h-3.5" /> {error ? "Unreachable" : "Checking..."}
                  </span>
                )}
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Database Engine:</span>
                {health?.services.database === "connected" ? (
                  <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Connected
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-amber-400 font-medium">
                    <AlertCircle className="w-3.5 h-3.5" /> {health?.services.database || "Disconnected"}
                  </span>
                )}
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Redis State:</span>
                {health?.services.redis === "connected" ? (
                  <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Connected
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-amber-400 font-medium">
                    <AlertCircle className="w-3.5 h-3.5" /> {health?.services.redis || "Disconnected"}
                  </span>
                )}
              </div>
              {health?.timestamp_utc && (
                <div className="flex justify-between items-center pt-1 border-t border-border/40">
                  <span className="text-muted-foreground">UTC Sync:</span>
                  <span className="font-mono text-[10px] text-muted-foreground">{health.timestamp_utc}</span>
                </div>
              )}
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Connection Notice</p>
                  <p className="text-[11px] opacity-90">{error}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Architectural Principles Card */}
        <Card className="border-border/60 bg-card/60 backdrop-blur">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <CardTitle className="text-lg">Architectural Enforcements</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Core platform rules verified across monorepo boundaries.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5 text-xs">
            <div className="flex items-start space-x-2.5">
              <Key className="w-4 h-4 text-primary shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-foreground">Strict 72-Hour Bound Invitations</p>
                <p className="text-muted-foreground text-[11px]">3 invites allocated per adult member, single-use, recipient-bound cryptographic tokens.</p>
              </div>
            </div>
            <div className="flex items-start space-x-2.5">
              <EyeOff className="w-4 h-4 text-primary shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-foreground">Zero College Email or ID Verification</p>
                <p className="text-muted-foreground text-[11px]">No .edu harvesting. Campus affiliation is 100% self-declared and optional.</p>
              </div>
            </div>
            <div className="flex items-start space-x-2.5">
              <Server className="w-4 h-4 text-primary shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-foreground">Identity & Persona Decoupling</p>
                <p className="text-muted-foreground text-[11px]">Authentication accounts strictly partitioned from pseudonymous social identities.</p>
              </div>
            </div>
            <div className="flex items-start space-x-2.5">
              <Database className="w-4 h-4 text-primary shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-foreground">Consent-Gated Messaging</p>
                <p className="text-muted-foreground text-[11px]">Direct messages locked until recipient explicitly accepts connection requests.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
