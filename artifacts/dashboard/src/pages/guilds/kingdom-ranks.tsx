import { useParams } from "wouter";
import { Trophy } from "lucide-react";
import { PlaceholderPage } from "@/components/layout";

export default function KingdomRanksPage() {
  const { guildId } = useParams() as { guildId: string };
  return (
    <PlaceholderPage
      guildId={guildId}
      icon={Trophy}
      title="Kingdom Ranks"
      description="Configure the weekly Kingdom rank tier system — thresholds, tiers, and reward structures for the infernal ladder."
    />
  );
}
