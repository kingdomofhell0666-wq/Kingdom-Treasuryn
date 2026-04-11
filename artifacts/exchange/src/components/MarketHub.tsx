import { useState } from "react";
import type { Catalog, UserData, DiscordUser, ItemCategory, CatalogItem } from "../types";
import { getItemStatus, RANK_ORDER, RARITY_RANK } from "../types";
import ItemCard from "./ItemCard";
import PurchaseModal from "./PurchaseModal";

const DC_ICON = "https://cdn.discordapp.com/emojis/1492184333392412692.webp?size=32&quality=lossless";

const TABS: { id: ItemCategory; label: string; desc: string }[] = [
  {
    id: "relics",
    label: "Relics",
    desc: "Artifacts of infernal power that alter your identity's very essence.",
  },
  {
    id: "titles",
    label: "Titles",
    desc: "Names that precede you. Choose the weight you carry.",
  },
  {
    id: "skins",
    label: "Skins",
    desc: "The face you wear in the Kingdom. Some are borrowed. These are bought.",
  },
  {
    id: "badges",
    label: "Badges",
    desc: "Marks that speak before you enter a room.",
  },
];

interface Props {
  discordUser: DiscordUser;
  userData: UserData;
  catalog: Catalog;
  onLeave: () => void;
  onRefresh: () => void;
}

export default function MarketHub({ discordUser, userData, catalog, onLeave, onRefresh }: Props) {
  const [activeTab, setActiveTab]   = useState<ItemCategory>("relics");
  const [selected, setSelected]     = useState<{ item: CatalogItem; cat: ItemCategory } | null>(null);
  const [localBalance, setLocalBalance] = useState(userData.balance);
  const [ownedMap, setOwnedMap]     = useState({
    relics: userData.owned_relics,
    titles: userData.owned_titles,
    skins:  userData.owned_skins,
    badges: userData.owned_badges,
  });

  const userRankIdx = RANK_ORDER[userData.rank] ?? 0;

  // Merge local ownership into userData for status checks
  const mergedUser: UserData = {
    ...userData,
    balance:      localBalance,
    owned_relics: ownedMap.relics,
    owned_titles: ownedMap.titles,
    owned_skins:  ownedMap.skins,
    owned_badges: ownedMap.badges,
  };

  function handlePurchaseSuccess(item: CatalogItem, category: ItemCategory, newBalance: number) {
    setLocalBalance(newBalance);
    setOwnedMap(prev => ({
      ...prev,
      [category]: [...prev[category], item.id],
    }));
    onRefresh();
  }

  const items = (catalog[activeTab] as CatalogItem[]).slice().sort((a, b) => {
    const sa = RARITY_RANK[a.rarity] ?? 0;
    const sb = RARITY_RANK[b.rarity] ?? 0;
    return sa - sb;
  });

  const activeDesc = TABS.find(t => t.id === activeTab)?.desc ?? "";

  return (
    <div className="market-wrap">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="market-header">
        <div className="market-brand">
          <span className="market-title">Kingdom Exchange</span>
          <span className="market-subtitle">The Infernal Marketplace</span>
        </div>

        <div className="market-user">
          <div className="market-user-info">
            <span className="market-username">{discordUser.username}</span>
            <span className="market-rank">{userData.rank}</span>
          </div>

          <img
            src={discordUser.avatarUrl}
            alt="avatar"
            className="market-avatar"
          />

          <div className="market-balance">
            <img src={DC_ICON} alt="DC" className="dc-icon" />
            {localBalance.toLocaleString()}
          </div>

          <button className="market-leave-btn" onClick={onLeave}>
            Leave
          </button>
        </div>
      </header>

      {/* ── Sacrifice gate banner ──────────────────────────────────────── */}
      {userData.sacrifice_active && (
        <div style={{
          background: "rgba(139,0,0,0.15)",
          border: "1px solid rgba(139,0,0,0.4)",
          borderLeft: "3px solid var(--crimson-bright)",
          padding: "0.85rem 1.5rem",
          fontSize: "0.8rem",
          color: "#FF6B6B",
          fontStyle: "italic",
          letterSpacing: "0.06em",
        }}>
          🩸 The gates are sealed by debt. Purchases are suspended until your debt is cleared.
        </div>
      )}

      {/* ── Category tabs ──────────────────────────────────────────────── */}
      <nav className="category-tabs">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`category-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Category description */}
      <p className="category-desc">{activeDesc}</p>

      {/* ── Item grid ──────────────────────────────────────────────────── */}
      <div className="item-grid">
        {items.map(item => {
          const status = getItemStatus(item, activeTab, mergedUser, userRankIdx);
          return (
            <ItemCard
              key={item.id}
              item={item}
              category={activeTab}
              status={status}
              onClick={() => {
                if (status !== "locked" && status !== "owned" && status !== "equipped") {
                  setSelected({ item, cat: activeTab });
                }
              }}
            />
          );
        })}
      </div>

      {/* ── Purchase modal ─────────────────────────────────────────────── */}
      {selected && (
        <PurchaseModal
          item={selected.item}
          category={selected.cat}
          userBalance={localBalance}
          onClose={() => setSelected(null)}
          onSuccess={(newBalance) => {
            handlePurchaseSuccess(selected.item, selected.cat, newBalance);
            setSelected(null);
          }}
        />
      )}
    </div>
  );
}
