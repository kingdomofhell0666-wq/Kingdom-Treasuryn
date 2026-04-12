import { useState } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { apiPost } from "@/lib/api";
import { RotateCcw, AlertTriangle } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";

export default function ResetPage() {
  const params = useParams();
  const guildId = params.guildId as string;
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-2xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-destructive">Economy Reset</h1>
            <p className="text-muted-foreground">Permanently wipe all economy data for this server. This cannot be undone.</p>
          </div>
          <ResetPanel guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function ResetPanel({ guildId }: { guildId: string }) {
  const { toast } = useToast();
  const [step, setStep] = useState<1 | 2>(1);
  const [confirm, setConfirm] = useState("");
  const [resetting, setResetting] = useState(false);

  const doReset = async () => {
    if (confirm.toUpperCase() !== "RESET") {
      toast({ title: "Type RESET to confirm", variant: "destructive" });
      return;
    }
    setResetting(true);
    try {
      await apiPost(`/api/guilds/${guildId}/reset`, { confirm: "CONFIRM_RESET" });
      toast({ title: "Reset Complete", description: "All economy data has been wiped. The Kingdom starts fresh." });
      setStep(1);
      setConfirm("");
    } catch (e: unknown) {
      toast({ title: "Reset Failed", description: (e as Error).message, variant: "destructive" });
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="bg-card border-destructive/40">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="w-5 h-5" />
            Danger Zone
          </CardTitle>
          <CardDescription>
            Resetting will permanently delete all user balances, ranks, investments, cooldowns, and transaction history for this server.
            The <strong>bot configuration</strong> (currency name, cooldowns, etc.) is preserved.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
            <li>All user balances → 0</li>
            <li>All ranks → Forsaken</li>
            <li>All investments voided</li>
            <li>All cooldowns cleared</li>
            <li>Treasury balance wiped</li>
            <li>Transaction history deleted</li>
          </ul>
        </CardContent>
      </Card>

      {step === 1 ? (
        <Card className="bg-card border-border/60">
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground mb-4">
              Are you absolutely sure you want to reset the economy for this server?
              This action is <strong className="text-destructive">permanent and irreversible</strong>.
            </p>
            <Button variant="destructive" onClick={() => setStep(2)} className="gap-2">
              <RotateCcw className="w-4 h-4" />
              I understand — proceed to reset
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card className="bg-card border-destructive/60">
          <CardHeader>
            <CardTitle className="text-destructive text-base">Final Confirmation</CardTitle>
            <CardDescription>Type <strong>RESET</strong> below to confirm the economy wipe.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-sm">Type RESET to confirm</Label>
              <Input
                value={confirm}
                onChange={(e) => setConfirm(e.target.value.toUpperCase())}
                placeholder="RESET"
                className="font-mono border-destructive/50 focus:border-destructive"
              />
            </div>
          </CardContent>
          <CardFooter className="gap-3">
            <Button variant="outline" onClick={() => { setStep(1); setConfirm(""); }}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={doReset}
              disabled={resetting || confirm !== "RESET"}
              className="gap-2"
            >
              {resetting ? <Spinner className="w-4 h-4" /> : <RotateCcw className="w-4 h-4" />}
              Wipe Economy Data
            </Button>
          </CardFooter>
        </Card>
      )}
    </div>
  );
}
