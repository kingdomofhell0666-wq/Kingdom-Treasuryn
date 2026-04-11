import { useState } from "react";
import type { Catalog, UserData, DiscordUser, ItemCategory, CatalogItem } from "../types";
import { getItemStatus, RANK_ORDER, RARITY_RANK } from "../types";
import { api, ApiError } from "../api";

import CategoryNav  from "./CategoryNav";
import ItemShowcase  from "./ItemShowcase";
import PlayerPanel   from "./PlayerPanel";
import PreviewOverlay from "./PreviewOverlay";
import PurchaseModal  from "./PurchaseModal";

const DC_ICON = "https://cdn.discordapp.com/emojis/1492184333392412692.webp?size=32&quality=lossless";

const CATEGORY_TABS = [
  { id: "relics" as ItemCategory,  icon: "🔮", label: "Relics" },
  { id: "titles" as ItemCategory,  icon: "👑", label: "Titles" },
  { id: "skins"  as ItemCategory,  icon: "🎭", label: "Skins"  },
  { id: "badges" as ItemCategory,  icon: "🎖️", label: "Badges" },
];

interface Props {
  discordUser: DiscordUser;
  userData:    UserData;
  catalog:     Catalog;
  onLeave:     () => void;
  onRefresh:   () => void;
}

export default function MarketHub({
  discordUser, userData, catalog, onLeave, onRefresh,
}: Props) {
  const [activeTab, setActiveTab]   = useState<ItemCategory>("relics");
  const [balance,   setBalance]     = useState(userData.balance);
  const [ownedMap,  setOwnedMap]    = useState({
    relics: userData.owned_relics,
    titles: userData.owned_titles,
    skins:  userData.owned_skins,
    badges: userData.owned_badges,
  });

  const [preview,  setPreview]  = useState<CatalogItem | null>(null);
  const [purchase, setPurchase] = useState<CatalogItem | null>(null);

  // Mobile sidebar toggle
  const [mobileCatOpen, setMobileCatOpen] = useState(false);

  const userRankIdx = RANK_ORDER[userData.rank] ?? 0;

  const mergedUser: UserData = {
    ...userData,
    balance,
    owned_relics: ownedMap.relics,
    owned_titles: ownedMap.titles,
    owned_skins:  ownedMap.skins,
    owned_badges: ownedMap.badges,
  };

  const items = (catalog[activeTab] as CatalogItem[])
    .slice()
    .sort((a, b) => (RARITY_RANK[a.rarity] ?? 0) - (RARITY_RANK[b.rarity] ?? 0));

  const statusMap = new Map<string, ReturnType<typeof getItemStatus>>(
    items.map(item => [item.id, getItemStatus(item, activeTab, mergedUser, userRankIdx)])
  );

  const tabs = CATEGORY_TABS.map(t => ({
    ...t,
    count: (catalog[t.id] as CatalogItem[]).length,
  }));

  function handlePurchaseSuccess(item: CatalogItem, newBalance: number) {
    setBalance(newBalance);
    setOwnedMap(prev => ({
      ...prev,
      [activeTab]: [...prev[activeTab as keyof typeof prev], item.id],
    }));
    onRefresh();
  }

  const previewItem = preview;
  const previewStatus = previewItem ? (statusMap.get(previewItem.id) ?? "available") : "available";

  return (
    <div className="hub-root">
      {/* ── Tavern fog / ambient layers ──────────────────────────── */}
      <div className="hub-bg-fog fog-1" />
      <div className="hub-bg-fog fog-2" />
      <div className="hub-bg-vignette" />

      {/* ── Mobile top bar ───────────────────────────────────────── */}
      <div className="hub-mobile-bar">
        <button
          className="hub-mobile-cat-btn"
          onClick={() => setMobileCatOpen(o => !o)}
        >
          ☰ {CATEGORY_TABS.find(t => t.id === activeTab)?.icon}{" "}
          {CATEGORY_TABS.find(t => t.id === activeTab)?.label}
        </button>
        <div className="hub-mobile-balance">
          <img src={DC_ICON} alt="DC" className="dc-icon" />
          {balance.toLocaleString()}
        </div>
      </div>

      {/* ── 3-panel layout ───────────────────────────────────────── */}
      <div className="hub-layout">

        {/* LEFT — Category nav */}
        <div className={`hub-left ${mobileCatOpen ? "hub-left-open" : ""}`}>
          <CategoryNav
            active={activeTab}
            tabs={tabs}
            onChange={cat => { setActiveTab(cat); setMobileCatOpen(false); }}
          />
        </div>

        {/* Mobile overlay */}
        {mobileCatOpen && (
          <div className="hub-mobile-overlay" onClick={() => setMobileCatOpen(false)} />
        )}

        {/* CENTER — Item showcase */}
        <main className="hub-center">
          {userData.sacrifice_active && (
            <div className="hub-debt-banner">
              🩸 The gates are sealed by debt. All purchases are suspended.
            </div>
          )}

          <ItemShowcase
            key={activeTab}
            items={items}
            category={activeTab}
            statusMap={statusMap}
            onPreview={setPreview}
            onAcquire={item => !userData.sacrifice_active && setPurchase(item)}
            userBalance={balance}
          />
        </main>

        {/* RIGHT — Player panel */}
        <div className="hub-right">
          <PlayerPanel
            discordUser={discordUser}
            userData={mergedUser}
            balance={balance}
            onLeave={onLeave}
          />
        </div>
      </div>

      {/* ── Preview overlay ─────────────────────────────────────── */}
      {previewItem && (
        <PreviewOverlay
          item={previewItem}
          category={activeTab}
          discordUser={discordUser}
          userData={mergedUser}
          canAfford={balance >= previewItem.price_dc}
          isAvailable={previewStatus === "available"}
          onBack={() => setPreview(null)}
          onAcquire={() => {
            setPreview(null);
            setPurchase(previewItem);
          }}
        />
      )}

      {/* ── Purchase modal ──────────────────────────────────────── */}
      {purchase && (
        <PurchaseModal
          item={purchase}
          category={activeTab}
          userBalance={balance}
          onClose={() => setPurchase(null)}
          onSuccess={(newBalance) => {
            handlePurchaseSuccess(purchase, newBalance);
            setPurchase(null);
          }}
        />
      )}
    </div>
  );
}
