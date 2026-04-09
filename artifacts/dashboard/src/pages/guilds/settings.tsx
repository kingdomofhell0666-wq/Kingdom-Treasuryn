import { useGetGuildConfig, useUpdateGuildConfig, getGetGuildConfigQueryKey } from "@workspace/api-client-react";
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
import { Save, Settings, Globe } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";

const settingsSchema = z.object({
  timezone: z.string().min(1, "Timezone is required"),
});

type SettingsFormValues = z.infer<typeof settingsSchema>;

const TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Asia/Tokyo",
  "Australia/Sydney",
];

export default function SettingsPage() {
  const params = useParams();
  const guildId = params.guildId as string;

  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-4xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-foreground">General Settings</h1>
            <p className="text-muted-foreground">Core configuration for your realm.</p>
          </div>
          <SettingsForm guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function SettingsForm({ guildId }: { guildId: string }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  const { data: config, isLoading } = useGetGuildConfig(guildId, {
    query: { enabled: !!guildId, queryKey: getGetGuildConfigQueryKey(guildId) }
  });

  const updateConfig = useUpdateGuildConfig();

  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      timezone: "UTC",
    }
  });

  useEffect(() => {
    if (config) {
      form.reset({
        timezone: config.timezone || "UTC",
      });
    }
  }, [config, form]);

  const onSubmit = (data: SettingsFormValues) => {
    updateConfig.mutate({ guildId, data }, {
      onSuccess: (updatedConfig) => {
        queryClient.setQueryData(getGetGuildConfigQueryKey(guildId), updatedConfig);
        toast({
          title: "Settings saved",
          description: "General settings have been updated.",
        });
      },
      onError: () => {
        toast({
          variant: "destructive",
          title: "Failed to save",
          description: "There was an error updating the settings.",
        });
      }
    });
  };

  if (isLoading) {
    return <div className="h-[300px] bg-card rounded-xl animate-pulse border border-border"></div>;
  }

  return (
    <Card className="border-border">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-primary">
          <Globe className="w-5 h-5" /> Localization
        </CardTitle>
        <CardDescription>Adjust how dates and times are displayed to your members.</CardDescription>
      </CardHeader>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardContent className="space-y-6">
            <FormField
              control={form.control}
              name="timezone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Server Timezone</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger data-testid="select-timezone">
                        <SelectValue placeholder="Select a timezone" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {TIMEZONES.map(tz => (
                        <SelectItem key={tz} value={tz}>{tz}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    Affects when daily limits reset (like Tributes).
                  </FormDescription>
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
              data-testid="button-save-settings"
            >
              {updateConfig.isPending ? (
                <Spinner className="mr-2 h-4 w-4" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Save Settings
            </Button>
          </CardFooter>
        </form>
      </Form>
    </Card>
  );
}