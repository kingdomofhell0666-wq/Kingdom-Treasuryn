import { useGetGuildConfig, useGetGuild, useUpdateGuildConfig, getGetGuildConfigQueryKey } from "@workspace/api-client-react";
import { useParams } from "wouter";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { AppLayout, AuthGuard } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { useEffect } from "react";
import { Save, Map, ShieldAlert } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";

const commands = [
  { id: "grind", name: "Grind", description: "Base income command (!grind)" },
  { id: "tribute", name: "Tribute", description: "Daily reward command (!tribute)" },
  { id: "market", name: "Black Market", description: "Illegal goods (!market)" },
  { id: "invest", name: "Investments", description: "Investment management (!invest)" },
];

export default function ChannelsPage() {
  const params = useParams();
  const guildId = params.guildId as string;

  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-4xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-foreground">Command Routing</h1>
            <p className="text-muted-foreground">Restrict certain bot commands to specific channels.</p>
          </div>
          <ChannelsForm guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function ChannelsForm({ guildId }: { guildId: string }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  const { data: config, isLoading: isConfigLoading } = useGetGuildConfig(guildId, {
    query: { enabled: !!guildId, queryKey: getGetGuildConfigQueryKey(guildId) }
  });

  const { data: guild, isLoading: isGuildLoading } = useGetGuild(guildId);
  const updateConfig = useUpdateGuildConfig();

  const form = useForm({
    defaultValues: {
      commandRouting: {} as Record<string, string>
    }
  });

  useEffect(() => {
    if (config?.commandRouting) {
      form.reset({
        commandRouting: config.commandRouting
      });
    }
  }, [config, form]);

  const onSubmit = (data: { commandRouting: Record<string, string> }) => {
    updateConfig.mutate({ guildId, data }, {
      onSuccess: (updatedConfig) => {
        queryClient.setQueryData(getGetGuildConfigQueryKey(guildId), updatedConfig);
        toast({
          title: "Routing saved",
          description: "Command routing rules have been updated.",
        });
      },
      onError: () => {
        toast({
          variant: "destructive",
          title: "Failed to save",
          description: "There was an error updating the command routing.",
        });
      }
    });
  };

  if (isConfigLoading || isGuildLoading) {
    return <div className="h-[400px] bg-card rounded-xl animate-pulse border border-border"></div>;
  }

  const textChannels = guild?.channels.filter(c => c.type === 0 || c.type === 5) || [];

  return (
    <Card className="border-border">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-primary">
          <Map className="w-5 h-5" /> Channel Rules
        </CardTitle>
        <CardDescription>
          If a channel is selected, the bot will only respond to that command in the specified channel. Leave empty to allow anywhere.
        </CardDescription>
      </CardHeader>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardContent className="space-y-6">
            {commands.map((cmd) => (
              <FormField
                key={cmd.id}
                control={form.control}
                name={`commandRouting.${cmd.id}`}
                render={({ field }) => (
                  <FormItem className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center border-b border-border/50 pb-4 last:border-0">
                    <div className="md:col-span-1">
                      <FormLabel className="text-base">{cmd.name}</FormLabel>
                      <FormDescription className="text-xs">{cmd.description}</FormDescription>
                    </div>
                    <div className="md:col-span-2">
                      <Select 
                        value={field.value || "any"} 
                        onValueChange={(val) => field.onChange(val === "any" ? undefined : val)}
                      >
                        <FormControl>
                          <SelectTrigger data-testid={`select-channel-${cmd.id}`}>
                            <SelectValue placeholder="Allow anywhere" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="any">Allow anywhere</SelectItem>
                          {textChannels.map(c => (
                            <SelectItem key={c.id} value={c.id}>
                              #{c.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </div>
                  </FormItem>
                )}
              />
            ))}
            
            {textChannels.length === 0 && (
              <div className="p-4 bg-destructive/10 text-destructive border border-destructive/20 rounded flex items-start gap-3">
                <ShieldAlert className="w-5 h-5 mt-0.5" />
                <div>
                  <p className="font-semibold">No channels available</p>
                  <p className="text-sm opacity-90">We couldn't find any text channels in this server or the bot lacks permissions to see them.</p>
                </div>
              </div>
            )}
          </CardContent>
          <CardFooter className="bg-muted/50 border-t border-border pt-6 flex justify-end">
            <Button 
              type="submit" 
              disabled={updateConfig.isPending}
              className="min-w-[120px]"
              data-testid="button-save-routing"
            >
              {updateConfig.isPending ? (
                <Spinner className="mr-2 h-4 w-4" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Save Routing
            </Button>
          </CardFooter>
        </form>
      </Form>
    </Card>
  );
}