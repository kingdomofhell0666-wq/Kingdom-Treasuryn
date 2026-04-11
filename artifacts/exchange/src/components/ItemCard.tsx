import type { CatalogItem, ItemCategory, ItemStatus } from "../types";

const DC_ICON = "https://cdn.discordapp.com/emojis/1492184333392412692.webp?size=32&quality=lossless";

const CATEGORY_LABELS: Record<ItemCategory, string> = {
  relics: "Relic",
  titles: "Title",
  skins:  "Skin",
  badges: "Badge",
};

const RELIC_ICONS: Record<string, string> = {
  soul_aura:       "🌌",
  infernal_crown:  "👑",
  void_drift:      "🌀",
  crimson_chains:  "⛓️",
  abyssal_veil:    "🌑",
  sanguine_halo:   "💫",
};

function getVisual(item: CatalogItem, category: ItemCategory): React.ReactNode {
  if (category === "badges") {
    return <span>{item.icon ?? "🔮"}</span>;
  }
  if (category === "relics") {
    return <span>{RELIC_ICONS[item.id] ?? "🔮"}</span>;
  }
  if (category === "skins") {
    return (
      <span
        className="item-skin-visual"
        style={{ color: item.color ?? "#C8B8A0" }}
      >
        {item.stat_icon ?? "✦"}
      </span>
    );
  }
  // titles
  return <span>📜</span>;
}

function getVisualBg(item: CatalogItem, category: ItemCategory): string {
  if (category === "skins" && item.color) return item.color;
  return "";
}

const RARITY_CLASS: Record<string, string> = {
  Common: "rarity-common",
  Uncommon: "rarity-uncommon",
  Rare: "rarity-rare",
  Epic: "rarity-epic",
  Legendary: "rarity-legendary",
};

const RARITY_BG_CLASS: Record<string, string> = {
  Common: "bg-rarity-common",
  Uncommon: "bg-rarity-uncommon",
  Rare: "bg-rarity-rare",
  Epic: "bg-rarity-epic",
  Legendary: "bg-rarity-legendary",
};

interface Props {
  item: CatalogItem;
  category: ItemCategory;
  status: ItemStatus;
  onClick: () => void;
}

export default function ItemCard({ item, category, status, onClick }: Props) {
  const rarityClass = RARITY_CLASS[item.rarity] ?? "rarity-uncommon";
  const rarityBg    = RARITY_BG_CLASS[item.rarity] ?? "";
  const visualBg    = getVisualBg(item, category);

  return (
    <div
      className={`item-card ${status}`}
      onClick={status !== "locked" ? onClick : undefined}
    >
      {/* Rarity stripe */}
      <div className={`rarity-stripe ${rarityBg}`} />

      {/* Visual */}
      <div
        className="item-visual"
        style={visualBg ? { background: `${visualBg}22` } : undefined}
      >
        {visualBg && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: `radial-gradient(ellipse at center, ${visualBg}33 0%, transparent 70%)`,
            }}
          />
        )}
        <div className="item-visual-inner">
          {getVisual(item, category)}
        </div>
      </div>

      {/* Body */}
      <div className="item-body">
        <span className={`item-rarity-badge ${rarityClass}`}>{item.rarity}</span>
        <span className="item-name">{item.name}</span>
        <span className="item-desc">
          {item.description.length > 80
            ? `${item.description.slice(0, 80)}…`
            : item.description}
        </span>
      </div>

      {/* Footer */}
      <div className="item-footer">
        <span className="item-price">
          <img src={DC_ICON} alt="DC" className="dc-icon" />
          {item.price_dc.toLocaleString()}
        </span>

        {status === "equipped" && (
          <button className="item-action-btn equipped-btn" disabled>Equipped</button>
        )}
        {status === "owned" && (
          <button className="item-action-btn owned-btn" disabled>Owned</button>
        )}
        {status === "available" && (
          <button className="item-action-btn acquire" onClick={onClick}>
            Acquire
          </button>
        )}
        {status === "locked" && (
          <span className="min-rank-tag">⚔ {item.min_rank}</span>
        )}
      </div>
    </div>
  );
}
