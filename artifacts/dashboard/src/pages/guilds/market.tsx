import { useParams } from "wouter";
import { ShoppingBag } from "lucide-react";
import { PlaceholderPage } from "@/components/layout";

export default function MarketPage() {
  const { guildId } = useParams() as { guildId: string };
  return (
    <PlaceholderPage
      guildId={guildId}
      icon={ShoppingBag}
      title="Market"
      description="View and manage the infernal cosmetics marketplace — skins, titles, relics, and badges available to your members."
    />
  );
}
