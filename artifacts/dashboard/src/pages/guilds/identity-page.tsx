import { useParams } from "wouter";
import { IdCard } from "lucide-react";
import { PlaceholderPage } from "@/components/layout";

export default function IdentityPage() {
  const { guildId } = useParams() as { guildId: string };
  return (
    <PlaceholderPage
      guildId={guildId}
      icon={IdCard}
      title="Identity"
      description="Manage the identity card system — override display names, titles, and flag custom profiles for moderation."
    />
  );
}
