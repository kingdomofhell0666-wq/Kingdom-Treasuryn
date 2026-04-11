import type { CatalogItem, ItemCategory, DiscordUser, UserData } from "../types";

const DC_ICON = "https://cdn.discordapp.com/emojis/1492184333392412692.webp?size=32&quality=lossless";

const RARITY_COLORS: Record<string, string> = {
  Default: "#666", Common: "#9a9a9a", Uncommon: "#4aad52",
  Rare: "#4a8dd4", Epic: "#9b59b6", Legendary: "#e67e22",
};

const FLAVOR: Record<ItemCategory, string> = {
  relics: "A dark presence surrounds you.",
  titles: "The shadows speak your name differently now.",
  skins: "The Exchange sees you as you truly are.",
  badges: "The mark is applied. It cannot be undone.",
};

interface Props {
  item: CatalogItem;
  category: ItemCategory;
  discordUser: DiscordUser;
  userData: UserData;
  canAfford: boolean;
  isAvailable: boolean;
  onBack: () => void;
  onAcquire: () => void;
}

export default function PreviewOverlay({ item, category, discordUser, userData, canAfford, isAvailable, onBack, onAcquire }: Props) {
  const rarColor = RARITY_COLORS[item.rarity] ?? "#666";

  return (
    <div className="preview-root">
      <div className="preview-dim" onClick={onBack} />

      <div className="preview-panel">
        {/* ── Left: identity card manifest ───── */}
        <div className="preview-card">
          <div className="preview-card-aura" style={{ boxShadow: `0 0 60px 15px ${rarColor}33` }} />

          {/* Energy particles */}
          <div className="preview-particles">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="preview-particle"
                style={{
                  "--angle": `${i * 45}deg`,
                  "--delay": `${i * 0.15}s`,
                  "--col": rarColor,
                } as React.CSSProperties}
              />
            ))}
          </div>

          {/* Identity card */}
          <div className="preview-identity-card" style={{ borderColor: rarColor + "44" }}>
            <div className="preview-card-header">
              <img src={discordUser.avatarUrl} alt="avatar" className="preview-card-avatar" />
              <div>
                <div className="preview-card-username">{discordUser.username}</div>
                <div className="preview-card-rank">{userData.rank}</div>
              </div>
            </div>

            <div className="preview-card-item">
              <span className="preview-card-item-icon" style={{ color: rarColor }}>
                {item.stat_icon ?? item.icon ?? "⬡"}
              </span>
              <div>
                <div className="preview-card-item-name" style={{ color: rarColor }}>
                  {item.name}
                </div>
                <div className="preview-card-item-cat">{category} — {item.rarity}</div>
              </div>
            </div>

            {/* Breathing glow */}
            <div className="preview-card-breathe" style={{ background: `radial-gradient(circle, ${rarColor}22 0%, transparent 70%)` }} />
          </div>

          <div className="preview-balance">
            <img src={DC_ICON} alt="dc" className="preview-dc" />
            <span>{userData.balance.toLocaleString()}</span>
          </div>
        </div>

        {/* ── Right: info + actions ─────────── */}
        <div className="preview-info">
          <div className="preview-info-glyph" style={{ color: rarColor }}>⬡</div>
          <h2 className="preview-info-name">{item.name}</h2>
          <p className="preview-info-desc">{item.description}</p>
          {item.effect_desc && (
            <p className="preview-info-effect">⟐ {item.effect_desc}</p>
          )}

          <p className="preview-flavor">{FLAVOR[category]}</p>

          <div className="preview-cost">
            <img src={DC_ICON} alt="dc" className="preview-dc" />
            <span className={canAfford ? "preview-cost-ok" : "preview-cost-low"}>
              {item.price_dc.toLocaleString()}
            </span>
          </div>

          <div className="preview-actions">
            <button className="preview-back-btn" onClick={onBack}>← Back</button>
            {isAvailable && (
              <button
                className="preview-acquire-btn"
                disabled={!canAfford}
                onClick={onAcquire}
              >
                🩸 Acquire
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
