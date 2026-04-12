import { useParams } from "wouter";
import { Zap } from "lucide-react";
import { PlaceholderPage } from "@/components/layout";

export default function AutomationPage() {
  const { guildId } = useParams() as { guildId: string };
  return (
    <PlaceholderPage
      guildId={guildId}
      icon={Zap}
      title="Automation"
      description="Set up scheduled tasks — automated leaderboard posts, rank announcements, and economy resets on your schedule."
    />
  );
}
