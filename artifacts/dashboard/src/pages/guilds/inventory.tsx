import { useParams } from "wouter";
import { Package } from "lucide-react";
import { PlaceholderPage } from "@/components/layout";

export default function InventoryPage() {
  const { guildId } = useParams() as { guildId: string };
  return (
    <PlaceholderPage
      guildId={guildId}
      icon={Package}
      title="Inventory"
      description="Browse member-owned items — equipped skins, titles, relics, and badges across your server's economy."
    />
  );
}
