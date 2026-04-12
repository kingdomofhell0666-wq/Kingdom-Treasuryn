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
import { useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { useEffect, useState } from "react";
import { Save, Gem, MessageSquare } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";

const currencySchema = z.object({
  currencyName: z.string().min(1, "Currency name is required").max(32),
  currencyIcon: z.string().min(1, "Icon/Emoji is required"),
});

type CurrencyFormValues = z.infer<typeof currencySchema>;

export default function CurrencyPage() {
  const params = useParams();
  const guildId = params.guildId as string;

  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-5xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-foreground">Currency Customization</h1>
            <p className="text-muted-foreground">Define the wealth that drives your realm.</p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            <CurrencyForm guildId={guildId} />
          </div>
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function CurrencyForm({ guildId }: { guildId: string }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  const { data: config, isLoading } = useGetGuildConfig(guildId, {
    query: { enabled: !!guildId, queryKey: getGetGuildConfigQueryKey(guildId) }
  });

  const updateConfig = useUpdateGuildConfig();

  const form = useForm<CurrencyFormValues>({
    resolver: zodResolver(currencySchema),
    defaultValues: {
      currencyName: "Souls",
      currencyIcon: "💀",
    }
  });

  // Watch values for live preview
  const previewName = form.watch("currencyName") || "Souls";
  const previewIcon = form.watch("currencyIcon") || "💀";

  useEffect(() => {
    if (config) {
      form.reset({
        currencyName: config.currencyName || "Souls",
        currencyIcon: config.currencyIcon || "💀",
      });
    }
  }, [config, form]);

  const onSubmit = (data: CurrencyFormValues) => {
    updateConfig.mutate({ guildId, data }, {
      onSuccess: (updatedConfig) => {
        queryClient.setQueryData(getGetGuildConfigQueryKey(guildId), updatedConfig);
        toast({
          title: "Currency updated",
          description: "Your realm's currency identity has been changed.",
        });
      },
      onError: () => {
        toast({
          variant: "destructive",
          title: "Failed to save",
          description: "There was an error updating the currency.",
        });
      }
    });
  };

  if (isLoading) {
    return <div className="lg:col-span-2 h-[400px] bg-card rounded-xl animate-pulse border border-border"></div>;
  }

  return (
    <>
      <Card className="border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-secondary">
            <Gem className="w-5 h-5" /> Identity
          </CardTitle>
          <CardDescription>Set the name and icon for your economy.</CardDescription>
        </CardHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <CardContent className="space-y-6">
              <FormField
                control={form.control}
                name="currencyName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Currency Name (Plural)</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. Souls, Gold, Credits" {...field} data-testid="input-currency-name" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="currencyIcon"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Currency Icon / Discord Emoji</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. 🪙 or <:custom:123456789>" {...field} data-testid="input-currency-icon" />
                    </FormControl>
                    <FormDescription>Can be a standard emoji or a custom Discord emoji tag.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
            <CardFooter className="bg-muted/50 border-t border-border pt-6">
              <Button 
                type="submit" 
                disabled={updateConfig.isPending}
                className="w-full"
                data-testid="button-save-currency"
              >
                {updateConfig.isPending ? (
                  <Spinner className="mr-2 h-4 w-4" />
                ) : (
                  <Save className="mr-2 h-4 w-4" />
                )}
                Save Identity
              </Button>
            </CardFooter>
          </form>
        </Form>
      </Card>

      <div className="space-y-6 sticky top-8">
        <Card className="border-primary/20 bg-background shadow-lg shadow-primary/5">
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <MessageSquare className="w-4 h-4" /> Live Preview
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Fake Discord Message */}
            <div className="flex gap-4 p-4 rounded bg-[#313338] text-[#dbdee1] font-sans">
              <div className="w-10 h-10 rounded-full bg-primary/80 flex-shrink-0 flex items-center justify-center text-primary-foreground font-bold">
                KT
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-[#f2f3f5]">Kingdom Treasury</span>
                  <span className="text-xs bg-[#5865F2] text-white px-1 rounded rounded-sm">APP</span>
                  <span className="text-xs text-[#949ba4]">Today at 12:00 PM</span>
                </div>
                
                {/* Fake Embed */}
                <div className="mt-2 border-l-4 border-primary bg-[#2b2d31] rounded p-4 max-w-sm">
                  <div className="font-bold text-[#f2f3f5] mb-2 flex items-center gap-2">
                    {previewIcon} Balance
                  </div>
                  <div className="text-sm">
                    <p>Wallet: <span className="font-semibold">1,284,560 {previewName}</span></p>
                    <p className="text-[#b5bac1] text-xs mt-2">Use /invest to grow your wealth.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-4 p-4 rounded bg-[#313338] text-[#dbdee1] font-sans">
              <div className="w-10 h-10 rounded-full bg-secondary/80 flex-shrink-0 flex items-center justify-center text-secondary-foreground font-bold">
                U
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-[#f2f3f5]">User</span>
                  <span className="text-xs text-[#949ba4]">Today at 12:05 PM</span>
                </div>
                <div className="text-sm">
                  You successfully grinded and found <strong>{previewIcon} 85 {previewName}</strong>!
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}