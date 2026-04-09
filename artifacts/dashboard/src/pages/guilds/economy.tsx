import { useGetGuildConfig, useUpdateGuildConfig, getGetGuildConfigQueryKey } from "@workspace/api-client-react";
import { useParams } from "wouter";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { AppLayout, AuthGuard } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { useEffect } from "react";
import { Swords, Flame, Save, ShieldAlert } from "lucide-react";

const economySchema = z.object({
  grindCooldownSeconds: z.coerce.number().min(0).max(86400),
  grindMinReward: z.coerce.number().min(0),
  grindMaxReward: z.coerce.number().min(1),
  tributeCooldownSeconds: z.coerce.number().min(0).max(86400),
  tributeMinReward: z.coerce.number().min(0),
  tributeMaxReward: z.coerce.number().min(1),
  blackMarketRiskPct: z.coerce.number().min(0).max(100),
  investmentTaxRate: z.coerce.number().min(0).max(100),
});

type EconomyFormValues = z.infer<typeof economySchema>;

export default function EconomyPage() {
  const params = useParams();
  const guildId = params.guildId as string;

  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-4xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-foreground">Economy Tuning</h1>
            <p className="text-muted-foreground">Adjust the flows of wealth and blood in your realm.</p>
          </div>
          <EconomyForm guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function EconomyForm({ guildId }: { guildId: string }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  const { data: config, isLoading } = useGetGuildConfig(guildId, {
    query: { enabled: !!guildId, queryKey: getGetGuildConfigQueryKey(guildId) }
  });

  const updateConfig = useUpdateGuildConfig();

  const form = useForm<EconomyFormValues>({
    resolver: zodResolver(economySchema),
    defaultValues: {
      grindCooldownSeconds: 300,
      grindMinReward: 10,
      grindMaxReward: 100,
      tributeCooldownSeconds: 86400,
      tributeMinReward: 1000,
      tributeMaxReward: 5000,
      blackMarketRiskPct: 30,
      investmentTaxRate: 5,
    }
  });

  useEffect(() => {
    if (config) {
      form.reset({
        grindCooldownSeconds: config.grindCooldownSeconds ?? 300,
        grindMinReward: config.grindMinReward ?? 10,
        grindMaxReward: config.grindMaxReward ?? 100,
        tributeCooldownSeconds: config.tributeCooldownSeconds ?? 86400,
        tributeMinReward: config.tributeMinReward ?? 1000,
        tributeMaxReward: config.tributeMaxReward ?? 5000,
        blackMarketRiskPct: config.blackMarketRiskPct ?? 30,
        investmentTaxRate: config.investmentTaxRate ?? 5,
      });
    }
  }, [config, form]);

  const onSubmit = (data: EconomyFormValues) => {
    updateConfig.mutate({ guildId, data }, {
      onSuccess: (updatedConfig) => {
        queryClient.setQueryData(getGetGuildConfigQueryKey(guildId), updatedConfig);
        toast({
          title: "Economy settings saved",
          description: "Your realm's economy has been updated.",
        });
      },
      onError: () => {
        toast({
          variant: "destructive",
          title: "Failed to save",
          description: "There was an error updating the economy settings.",
        });
      }
    });
  };

  if (isLoading) {
    return <div className="h-[500px] bg-card rounded-xl animate-pulse border border-border"></div>;
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        
        <Card className="border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-primary">
              <Swords className="w-5 h-5" /> The Grind
            </CardTitle>
            <CardDescription>Base income generation for active members.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FormField
                control={form.control}
                name="grindCooldownSeconds"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Cooldown (seconds)</FormLabel>
                    <FormControl>
                      <Input type="number" {...field} data-testid="input-grind-cooldown" />
                    </FormControl>
                    <FormDescription>Time between !grind commands.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="grindMinReward"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Min Reward</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} data-testid="input-grind-min" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="grindMaxReward"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Max Reward</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} data-testid="input-grind-max" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-secondary">
              <Flame className="w-5 h-5" /> The Tribute
            </CardTitle>
            <CardDescription>Daily massive rewards to keep members engaged.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FormField
                control={form.control}
                name="tributeCooldownSeconds"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Cooldown (seconds)</FormLabel>
                    <FormControl>
                      <Input type="number" {...field} data-testid="input-tribute-cooldown" />
                    </FormControl>
                    <FormDescription>Usually 86400 (24 hours).</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="tributeMinReward"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Min Reward</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} data-testid="input-tribute-min" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="tributeMaxReward"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Max Reward</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} data-testid="input-tribute-max" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-500">
              <ShieldAlert className="w-5 h-5" /> Risk & Taxes
            </CardTitle>
            <CardDescription>Global modifiers for the economy.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-8">
            <FormField
              control={form.control}
              name="blackMarketRiskPct"
              render={({ field }) => (
                <FormItem>
                  <div className="flex justify-between items-center mb-2">
                    <FormLabel>Black Market Confiscation Risk: {field.value}%</FormLabel>
                  </div>
                  <FormControl>
                    <Slider
                      min={0}
                      max={100}
                      step={1}
                      value={[field.value]}
                      onValueChange={(vals) => field.onChange(vals[0])}
                      className="py-4"
                      data-testid="slider-blackmarket"
                    />
                  </FormControl>
                  <FormDescription>Chance that illegal transactions are seized by guards.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="investmentTaxRate"
              render={({ field }) => (
                <FormItem>
                  <div className="flex justify-between items-center mb-2">
                    <FormLabel>Investment Yield Tax: {field.value}%</FormLabel>
                  </div>
                  <FormControl>
                    <Slider
                      min={0}
                      max={100}
                      step={1}
                      value={[field.value]}
                      onValueChange={(vals) => field.onChange(vals[0])}
                      className="py-4 [&_[role=slider]]:bg-secondary"
                      data-testid="slider-tax"
                    />
                  </FormControl>
                  <FormDescription>Percentage of investment profits diverted to the Treasury.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
          <CardFooter className="bg-muted/50 border-t border-border pt-6 flex justify-end">
            <Button 
              type="submit" 
              disabled={updateConfig.isPending}
              className="min-w-[120px]"
              data-testid="button-save-economy"
            >
              {updateConfig.isPending ? (
                <Spinner className="mr-2 h-4 w-4" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Save Changes
            </Button>
          </CardFooter>
        </Card>

      </form>
    </Form>
  );
}