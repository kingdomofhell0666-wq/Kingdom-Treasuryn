import { useState, useEffect } from "react";
import type { ItemCategory, CatalogItem } from "../types";
import { RARITY_RANK } from "../types";

const DC_ICON = "https://cdn.discordapp.com/emojis/1492184333392412692.webp?size=32&quality=lossless";

const RARITY_COLORS: Record<string, string> = {
  Default: "#666", Common: "#9a9a9a", Uncommon: "#4aad52",
  Rare: "#4a8dd4", Epic: "#9b59b6", Legendary: "#e67e22",
};

const CAT_GLYPHS: Record<ItemCategory, string> = {
  relics: "⬡", titles: "◈", skins: "▣", badges: "⬟",
};


interface Props {
  items: CatalogItem[];
  category: ItemCategory;
  statusMap: Map<string, "available" | "owned" | "equipped" | "locked">;
  userBalance: number;
  onPreview: (item: CatalogItem) => void;
  onAcquire: (item: CatalogItem) => void;
}

function rarityBadge(rarity: string) {
  const col = RARITY_COLORS[rarity] ?? "#666";
  return (
    <span className="item-rarity" style={{ color: col, borderColor: col + "55" }}>
      {rarity}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "equipped") return <span className="item-status item-status-equipped">Equipped</span>;
  if (status === "owned")    return <span className="item-status item-status-owned">Owned</span>;
  if (status === "locked")   return <span className="item-status item-status-locked">Locked</span>;
  return null;
}

export default function ItemShowcase({
  items, category, statusMap, userBalance, onPreview, onAcquire,
}: Props) {
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    if (items.length > 0 && !items.find(i => i.id === selected)) {
      setSelected(items[0].id);
    }
  }, [items, selected]);

  const activeItem = items.find(i => i.id === selected) ?? items[0] ?? null;
  const activeStatus = activeItem ? (statusMap.get(activeItem.id) ?? "available") : "available";

  if (!items.length) {
    return (
      <div className="showcase-empty">
        <span className="showcase-empty-glyph">{CAT_GLYPHS[category]}</span>
        <p>Nothing stirs in this archive.</p>
      </div>
    );
  }

  return (
    <div className="showcase-root">
      {/* ── Item grid (left) ─────────────────── */}
      <div className="showcase-list">
        {items.map(item => {
          const status = statusMap.get(item.id) ?? "available";
          const rarColor = RARITY_COLORS[item.rarity] ?? "#666";
          const isActive = item.id === (activeItem?.id ?? "");
          const canAfford = userBalance >= item.price_dc;
          return (
            <button
              key={item.id}
              className={`showcase-card ${isActive ? "showcase-card-active" : ""} ${status === "locked" ? "showcase-card-locked" : ""}`}
              onClick={() => setSelected(item.id)}
              style={{ "--rarity-color": rarColor } as React.CSSProperties}
            >
              {/* Rarity bar */}
              <div className="sc-rarity-bar" style={{ background: rarColor }} />
              {/* Icon */}
              <div className="sc-icon">
                <span>{item.stat_icon ?? item.icon ?? CAT_GLYPHS[category]}</span>
              </div>
              {/* Info */}
              <div className="sc-info">
                <span className="sc-name">{item.name}</span>
                <span className="sc-rarity" style={{ color: rarColor }}>{item.rarity}</span>
              </div>
              {/* Status / price */}
              <div className="sc-right">
                {status === "available" ? (
                  <div className={`sc-price ${canAfford ? "" : "sc-price-unaffordable"}`}>
                    <img src={DC_ICON} alt="dc" className="sc-dc" />
                    <span>{item.price_dc.toLocaleString()}</span>
                  </div>
                ) : (
                  <StatusBadge status={status} />
                )}
              </div>
              {/* Lock overlay */}
              {status === "locked" && <div className="sc-lock-overlay">🔒</div>}
            </button>
          );
        })}
      </div>

      {/* ── Item detail (right) ──────────────── */}
      {activeItem && (
        <div className="showcase-detail">
          <div className="detail-glow" style={{ "--rarity-color": RARITY_COLORS[activeItem.rarity] ?? "#666" } as React.CSSProperties} />

          {/* Icon orb */}
          <div className="detail-orb" style={{ boxShadow: `0 0 40px 8px ${RARITY_COLORS[activeItem.rarity] ?? "#666"}44` }}>
            <span className="detail-orb-icon">
              {activeItem.stat_icon ?? activeItem.icon ?? CAT_GLYPHS[category]}
            </span>
          </div>

          {/* Name + rarity */}
          <div className="detail-header">
            <h2 className="detail-name">{activeItem.name}</h2>
            {rarityBadge(activeItem.rarity)}
          </div>

          {/* Description */}
          <p className="detail-desc">{activeItem.description}</p>
          {activeItem.effect_desc && (
            <p className="detail-effect">⟐ {activeItem.effect_desc}</p>
          )}

          {/* Min rank */}
          {activeItem.min_rank && (
            <div className={`detail-rank-req ${activeStatus === "locked" ? "detail-rank-locked" : ""}`}>
              {activeStatus === "locked" ? "🔒" : "✦"} Requires {activeItem.min_rank}
            </div>
          )}

          {/* Status bar */}
          <div className="detail-status-row">
            <StatusBadge status={activeStatus} />
          </div>

          {/* Price */}
          {activeStatus === "available" && (
            <div className="detail-price">
              <img src={DC_ICON} alt="dc" className="detail-dc-icon" />
              <span className={userBalance >= activeItem.price_dc ? "detail-price-ok" : "detail-price-low"}>
                {activeItem.price_dc.toLocaleString()}
              </span>
            </div>
          )}

          {/* Actions */}
          <div className="detail-actions">
            <button
              className="detail-preview-btn"
              onClick={() => onPreview(activeItem)}
            >
              Preview
            </button>
            {activeStatus === "available" && (
              <button
                className="detail-acquire-btn"
                disabled={userBalance < activeItem.price_dc}
                onClick={() => onAcquire(activeItem)}
              >
                🩸 Acquire
              </button>
            )}
            {activeStatus === "locked" && (
              <button className="detail-locked-btn" disabled>
                🔒 Rank Required
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
