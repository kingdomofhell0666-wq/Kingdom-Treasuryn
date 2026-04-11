import type { CatalogItem, ItemCategory } from "../types";
import type { DiscordUser, UserData } from "../types";

const RELIC_AURAS: Record<string, { color: string; icon: string; label: string }> = {
  soul_aura:      { color: "#7B4DFF", icon: "🌌", label: "Soul Aura" },
  infernal_crown: { color: "#FF8800", icon: "👑", label: "Infernal Crown" },
  void_drift:     { color: "#4488FF", icon: "🌀", label: "Void Drift" },
  crimson_chains: { color: "#CC0000", icon: "⛓️", label: "Crimson Chains" },
  abyssal_veil:   { color: "#220033", icon: "🌑", label: "Abyssal Veil" },
  sanguine_halo:  { color: "#FFD700", icon: "💫", label: "Sanguine Halo" },
};

const CATEGORY_FLAVOR: Record<ItemCategory, string> = {
  relics: "A dark presence surrounds you. The air grows cold.",
  titles: "The name precedes you. The Kingdom takes note.",
  skins:  "Your identity shifts. The card accepts its new face.",
  badges: "The mark burns itself into the record. Permanently.",
};

interface Props {
  item:        CatalogItem;
  category:    ItemCategory;
  discordUser: DiscordUser;
  userData:    UserData;
  onBack:      () => void;
  onAcquire:   () => void;
  canAfford:   boolean;
  isAvailable: boolean;
}

export default function PreviewOverlay({
  item, category, discordUser, userData,
  onBack, onAcquire, canAfford, isAvailable,
}: Props) {
  const aura        = category === "relics" ? RELIC_AURAS[item.id] : null;
  const skinColor   = category === "skins"  ? item.color            : null;
  const equippedTitle = userData.equipped_title || "—";
  const displayName = discordUser.username;

  const cardBg = skinColor
    ? `linear-gradient(160deg, ${skinColor}22 0%, #0A0404 60%)`
    : "linear-gradient(160deg, #1A0808 0%, #0A0404 60%)";

  const cardBorder = skinColor
    ? `1px solid ${skinColor}55`
    : "1px solid rgba(80,20,20,0.6)";

  return (
    <div className="preview-backdrop" onClick={onBack}>
      <div className="preview-modal" onClick={e => e.stopPropagation()}>

        {/* Aura effect behind card */}
        {aura && (
          <div
            className="preview-aura"
            style={{ background: `radial-gradient(ellipse at center, ${aura.color}55 0%, transparent 70%)` }}
          />
        )}
        {skinColor && (
          <div
            className="preview-aura"
            style={{ background: `radial-gradient(ellipse at center, ${skinColor}44 0%, transparent 70%)` }}
          />
        )}

        {/* Identity card preview */}
        <div
          className="preview-card"
          style={{ background: cardBg, border: cardBorder }}
        >
          {/* Card accent bar */}
          {skinColor && (
            <div style={{
              position: "absolute", top: 0, left: 0, right: 0, height: 3,
              background: skinColor, opacity: 0.8,
            }} />
          )}
          {aura && (
            <div style={{
              position: "absolute", top: 0, left: 0, right: 0, height: 3,
              background: aura.color, opacity: 0.8,
            }} />
          )}

          {/* Avatar area */}
          <div className="preview-card-avatar-wrap">
            <div
              className="preview-card-avatar-ring"
              style={aura ? { borderColor: aura.color + "99", boxShadow: `0 0 24px ${aura.color}55` } :
                     skinColor ? { borderColor: skinColor + "88", boxShadow: `0 0 24px ${skinColor}44` } : {}}
            />
            <img
              src={discordUser.avatarUrl}
              alt="avatar"
              className="preview-card-avatar"
            />
            {aura && (
              <div className="preview-card-relic-icon" style={{ color: aura.color }}>
                {aura.icon}
              </div>
            )}
          </div>

          {/* Info */}
          <div className="preview-card-info">
            {category === "titles" ? (
              <span className="preview-card-title-disp">[{item.name}]</span>
            ) : (
              equippedTitle !== "—" && (
                <span className="preview-card-title-disp">[{equippedTitle}]</span>
              )
            )}
            <span className="preview-card-name">{displayName}</span>
            <span className="preview-card-rank">{userData.rank}</span>
          </div>

          {/* Item preview */}
          <div className="preview-card-item-strip">
            {category === "relics" && aura && (
              <span style={{ color: aura.color, fontWeight: 700, fontSize: "0.75rem", letterSpacing: "0.1em" }}>
                {aura.icon} {aura.label} equipped
              </span>
            )}
            {category === "skins" && skinColor && (
              <span style={{ color: skinColor, fontWeight: 700, fontSize: "0.75rem", letterSpacing: "0.1em" }}>
                {item.stat_icon} {item.name} skin applied
              </span>
            )}
            {category === "badges" && (
              <span style={{ fontSize: "0.75rem", color: "var(--text-dim)", letterSpacing: "0.08em" }}>
                {item.icon} {item.name} badge displayed
              </span>
            )}
          </div>

          {/* Breathing glow overlay */}
          <div className="preview-card-breathe" />
        </div>

        {/* Flavor text */}
        <p className="preview-flavor">{CATEGORY_FLAVOR[category]}</p>

        {/* Action buttons */}
        <div className="preview-actions">
          <button className="preview-back-btn" onClick={onBack}>
            ← Back
          </button>
          {isAvailable && (
            <button
              className="preview-acquire-btn"
              disabled={!canAfford}
              onClick={onAcquire}
            >
              🩸 Acquire — {item.price_dc.toLocaleString()} DC
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
