import { useState, useEffect, useRef } from "react";
import type { CatalogItem, ItemCategory, ItemStatus } from "../types";

const DC_ICON = "https://cdn.discordapp.com/emojis/1492184333392412692.webp?size=32&quality=lossless";

const RELIC_ICONS: Record<string, string> = {
  soul_aura:      "🌌",
  infernal_crown: "👑",
  void_drift:     "🌀",
  crimson_chains: "⛓️",
  abyssal_veil:   "🌑",
  sanguine_halo:  "💫",
};

const RARITY_GLOW: Record<string, string> = {
  Common:    "rgba(74,122,58,0.5)",
  Uncommon:  "rgba(58,106,138,0.5)",
  Rare:      "rgba(90,58,154,0.5)",
  Epic:      "rgba(138,58,122,0.5)",
  Legendary: "rgba(201,168,76,0.6)",
  Default:   "rgba(80,40,40,0.4)",
};

const RARITY_COLOR: Record<string, string> = {
  Common:    "#4A7A3A",
  Uncommon:  "#3A6A8A",
  Rare:      "#5A3A9A",
  Epic:      "#8A3A7A",
  Legendary: "#C9A84C",
  Default:   "#503838",
};

function getVisual(item: CatalogItem, category: ItemCategory): React.ReactNode {
  if (category === "relics") {
    return <span style={{ fontSize: "6rem" }}>{RELIC_ICONS[item.id] ?? "🔮"}</span>;
  }
  if (category === "badges") {
    return <span style={{ fontSize: "6rem" }}>{item.icon ?? "🔮"}</span>;
  }
  if (category === "skins") {
    return (
      <span style={{
        fontSize: "5rem",
        fontWeight: 900,
        color: item.color ?? "#C8B8A0",
        textShadow: `0 0 40px ${item.color ?? "#C8B8A0"}, 0 0 80px ${item.color ?? "#C8B8A0"}55`,
        letterSpacing: "-0.02em",
      }}>
        {item.stat_icon ?? "✦"}
      </span>
    );
  }
  return <span style={{ fontSize: "4.5rem" }}>📜</span>;
}

interface Props {
  items:      CatalogItem[];
  category:   ItemCategory;
  statusMap:  Map<string, ItemStatus>;
  onPreview:  (item: CatalogItem) => void;
  onAcquire:  (item: CatalogItem) => void;
  userBalance: number;
}

export default function ItemShowcase({
  items, category, statusMap, onPreview, onAcquire, userBalance,
}: Props) {
  const [idx,       setIdx]       = useState(0);
  const [direction, setDirection] = useState<"left" | "right" | null>(null);
  const [animating, setAnimating] = useState(false);
  const prevCatRef = useRef(category);

  // Reset index when category changes
  useEffect(() => {
    if (prevCatRef.current !== category) {
      prevCatRef.current = category;
      setIdx(0);
      setAnimating(false);
    }
  }, [category]);

  if (!items.length) return (
    <div className="showcase-empty">
      <span style={{ fontSize: "3rem", opacity: 0.3 }}>🔮</span>
      <p>No items available in this category.</p>
    </div>
  );

  const item   = items[Math.min(idx, items.length - 1)];
  const status = statusMap.get(item.id) ?? "available";
  const rarityGlow  = RARITY_GLOW[item.rarity]  ?? RARITY_GLOW.Default;
  const rarityColor = RARITY_COLOR[item.rarity]  ?? RARITY_COLOR.Default;
  const skinBg      = category === "skins" && item.color
    ? `radial-gradient(ellipse at center, ${item.color}18 0%, transparent 65%)`
    : "";
  const canAfford   = userBalance >= item.price_dc;

  function navigate(dir: "left" | "right") {
    if (animating || items.length <= 1) return;
    setDirection(dir);
    setAnimating(true);
    setTimeout(() => {
      setIdx(i => {
        if (dir === "right") return (i + 1) % items.length;
        return (i - 1 + items.length) % items.length;
      });
      setAnimating(false);
      setDirection(null);
    }, 280);
  }

  return (
    <div className="showcase-wrap">
      {/* Nav arrows */}
      <button
        className="showcase-arrow showcase-arrow-l"
        onClick={() => navigate("left")}
        disabled={items.length <= 1}
        aria-label="Previous"
      >
        ‹
      </button>
      <button
        className="showcase-arrow showcase-arrow-r"
        onClick={() => navigate("right")}
        disabled={items.length <= 1}
        aria-label="Next"
      >
        ›
      </button>

      {/* Item counter */}
      <div className="showcase-counter">
        {Math.min(idx, items.length - 1) + 1} / {items.length}
      </div>

      {/* Main content */}
      <div className={`showcase-content ${animating ? `showcase-slide-${direction === "right" ? "out-l" : "out-r"}` : "showcase-in"}`}>
        {/* Visual orb */}
        <div className="showcase-orb-wrap">
          <div
            className="showcase-orb-glow"
            style={{ background: `radial-gradient(ellipse at center, ${rarityGlow} 0%, transparent 70%)` }}
          />
          {skinBg && (
            <div className="showcase-skin-bg" style={{ background: skinBg }} />
          )}
          <div className="showcase-visual">
            {getVisual(item, category)}
          </div>
          {/* Floating particles */}
          <div className="showcase-particles">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="showcase-particle"
                style={{
                  "--p-angle": `${i * 60}deg`,
                  "--p-radius": `${55 + (i % 3) * 15}px`,
                  "--p-dur":   `${3 + i * 0.4}s`,
                  "--p-delay": `${i * 0.5}s`,
                  background: rarityColor,
                } as React.CSSProperties}
              />
            ))}
          </div>
        </div>

        {/* Item info */}
        <div className="showcase-info">
          {/* Rarity badge */}
          <div className="showcase-rarity" style={{ color: rarityColor, borderColor: rarityColor + "55" }}>
            <div className="showcase-rarity-dot" style={{ background: rarityColor }} />
            {item.rarity}
          </div>

          {/* Name */}
          <h2 className="showcase-name">{item.name}</h2>

          {/* Description */}
          <p className="showcase-desc">{item.description}</p>

          {/* Effect */}
          {item.effect_desc && (
            <blockquote className="showcase-effect">
              <span className="showcase-effect-quote">❝</span>
              {item.effect_desc}
            </blockquote>
          )}

          {/* Price + status */}
          <div className="showcase-price-row">
            <div className="showcase-price">
              <img src={DC_ICON} alt="DC" className="showcase-dc-icon" />
              <span className="showcase-price-num">{item.price_dc.toLocaleString()}</span>
              <span className="showcase-price-unit">DC</span>
            </div>

            {status === "locked" && item.min_rank && (
              <div className="showcase-locked-badge">
                🔒 Requires {item.min_rank}
              </div>
            )}
            {status === "owned" && (
              <div className="showcase-status-badge showcase-owned">✓ Owned</div>
            )}
            {status === "equipped" && (
              <div className="showcase-status-badge showcase-equipped">⚡ Equipped</div>
            )}
            {status === "available" && !canAfford && (
              <div className="showcase-status-badge showcase-broke">
                -{(item.price_dc - userBalance).toLocaleString()} DC
              </div>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="showcase-actions">
          <button
            className="showcase-preview-btn"
            onClick={() => onPreview(item)}
          >
            <span className="showcase-btn-icon">👁</span>
            Preview
          </button>

          {status === "available" && (
            <button
              className={`showcase-acquire-btn ${!canAfford ? "showcase-acquire-broke" : ""}`}
              onClick={() => canAfford && onAcquire(item)}
              disabled={!canAfford}
            >
              <span className="showcase-btn-icon">🩸</span>
              Acquire
              {!canAfford && <span className="showcase-broke-label">Insufficient Funds</span>}
            </button>
          )}
          {status === "locked" && (
            <button className="showcase-acquire-btn showcase-acquire-locked" disabled>
              🔒 Rank Required
            </button>
          )}
          {(status === "owned" || status === "equipped") && (
            <button className="showcase-acquire-btn showcase-acquire-owned" disabled>
              {status === "equipped" ? "⚡ Equipped" : "✓ Owned"}
            </button>
          )}
        </div>
      </div>

      {/* Dot navigation */}
      <div className="showcase-dots">
        {items.map((_, i) => (
          <button
            key={i}
            className={`showcase-dot ${i === Math.min(idx, items.length - 1) ? "showcase-dot-active" : ""}`}
            onClick={() => { if (!animating) setIdx(i); }}
            aria-label={`Item ${i + 1}`}
          />
        ))}
      </div>
    </div>
  );
}
