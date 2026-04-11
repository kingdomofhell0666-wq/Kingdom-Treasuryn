import { useState } from "react";
import type { CatalogItem, ItemCategory } from "../types";
import { api, ApiError } from "../api";

const DC_ICON = "https://cdn.discordapp.com/emojis/1492184333392412692.webp?size=32&quality=lossless";

const RELIC_ICONS: Record<string, string> = {
  soul_aura:       "🌌",
  infernal_crown:  "👑",
  void_drift:      "🌀",
  crimson_chains:  "⛓️",
  abyssal_veil:    "🌑",
  sanguine_halo:   "💫",
};

const CATEGORY_LABEL: Record<ItemCategory, string> = {
  relics: "Relic",
  titles: "Title",
  skins:  "Skin",
  badges: "Badge",
};

const RARITY_CLASS: Record<string, string> = {
  Common: "rarity-common",
  Uncommon: "rarity-uncommon",
  Rare: "rarity-rare",
  Epic: "rarity-epic",
  Legendary: "rarity-legendary",
};

function getVisual(item: CatalogItem, category: ItemCategory): string {
  if (category === "badges") return item.icon ?? "🔮";
  if (category === "relics") return RELIC_ICONS[item.id] ?? "🔮";
  if (category === "skins") return item.stat_icon ?? "✦";
  return "📜";
}

type ModalState = "confirm" | "sealing" | "success" | "error";

interface Props {
  item: CatalogItem;
  category: ItemCategory;
  userBalance: number;
  onClose: () => void;
  onSuccess: (newBalance: number) => void;
}

export default function PurchaseModal({
  item,
  category,
  userBalance,
  onClose,
  onSuccess,
}: Props) {
  const [state, setState]   = useState<ModalState>("confirm");
  const [error, setError]   = useState("");
  const [acquired, setAcquired] = useState("");
  const [newBal, setNewBal] = useState(0);

  const canAfford = userBalance >= item.price_dc;
  const balAfter  = userBalance - item.price_dc;

  async function handlePurchase() {
    setState("sealing");
    // Minimum dramatic delay — the kingdom does not rush
    await new Promise(r => setTimeout(r, 1800));
    try {
      const result = await api.purchase(category, item.id);
      setAcquired(result.name);
      setNewBal(result.new_balance);
      setState("success");
      onSuccess(result.new_balance);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "The Exchange rejected this transaction.";
      setError(msg);
      setState("error");
    }
  }

  function handleBackdropClick(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget && state !== "sealing") onClose();
  }

  const visual      = getVisual(item, category);
  const visualBg    = category === "skins" && item.color ? `${item.color}22` : "";
  const rarityClass = RARITY_CLASS[item.rarity] ?? "rarity-uncommon";

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-box">
        {state !== "sealing" && state !== "success" && (
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        )}

        {/* Visual */}
        <div
          className="modal-item-visual"
          style={visualBg ? { background: visualBg } : undefined}
        >
          {visualBg && (
            <div style={{
              position: "absolute",
              inset: 0,
              background: `radial-gradient(ellipse at center, ${item.color}44 0%, transparent 70%)`,
            }} />
          )}
          <div style={{ position: "relative", zIndex: 1, fontSize: category === "skins" ? "3rem" : "4.5rem" }}>
            {category === "skins" ? (
              <span style={{ color: item.color ?? "#C8B8A0", fontWeight: 800, textShadow: `0 0 20px ${item.color}` }}>
                {visual}
              </span>
            ) : <span>{visual}</span>}
          </div>
        </div>

        {/* ── CONFIRM ─────────────────────────────────────────────────── */}
        {state === "confirm" && (
          <div className="modal-body">
            <div>
              <div className="modal-item-name">{item.name}</div>
              <div className={`modal-item-type ${rarityClass}`}>
                {item.rarity} · {CATEGORY_LABEL[category]}
              </div>
            </div>

            <p className="modal-desc">{item.description}</p>

            {item.effect_desc && (
              <blockquote className="modal-effect">{item.effect_desc}</blockquote>
            )}

            <hr className="modal-divider" />

            <div className="modal-cost-row">
              <span className="modal-cost-label">Cost</span>
              <span className="modal-cost-value">
                <img src={DC_ICON} alt="DC" className="dc-icon" />
                {item.price_dc.toLocaleString()} DC
              </span>
            </div>

            <div className="modal-cost-row">
              <span className="modal-cost-label">Your balance</span>
              <span className="modal-cost-value" style={{ fontSize: "0.82rem", color: canAfford ? "var(--gold)" : "#FF6B6B" }}>
                <img src={DC_ICON} alt="DC" className="dc-icon" />
                {userBalance.toLocaleString()} DC
              </span>
            </div>

            {canAfford && (
              <div className="modal-balance-after">
                After purchase: {balAfter.toLocaleString()} DC
              </div>
            )}

            {!canAfford && (
              <div className="modal-error">
                Insufficient funds. You need{" "}
                <strong>{(item.price_dc - userBalance).toLocaleString()} DC</strong> more.
              </div>
            )}

            <button
              className="modal-seal-btn"
              disabled={!canAfford}
              onClick={handlePurchase}
            >
              Seal the Exchange
            </button>
          </div>
        )}

        {/* ── SEALING ─────────────────────────────────────────────────── */}
        {state === "sealing" && (
          <div className="modal-sealing">
            <div className="seal-spinner" />
            <p className="modal-sealing-text">Sealing the exchange…</p>
          </div>
        )}

        {/* ── SUCCESS ─────────────────────────────────────────────────── */}
        {state === "success" && (
          <div className="modal-success">
            <span className="modal-success-glyph">🩸</span>
            <p className="modal-success-title">Acquisition Complete</p>
            <p className="modal-success-item">{acquired}</p>
            <p className="modal-success-flavor">
              The Kingdom acknowledges your offering.<br />
              It is now yours.
            </p>
            <p className="modal-success-balance">
              <img src={DC_ICON} alt="DC" className="dc-icon" style={{ width: 14, height: 14 }} />
              New balance: {newBal.toLocaleString()} DC
            </p>
            <button className="modal-close-btn" onClick={onClose}>
              Return to the Exchange
            </button>
          </div>
        )}

        {/* ── ERROR ───────────────────────────────────────────────────── */}
        {state === "error" && (
          <div className="modal-body">
            <p className="modal-error">{error}</p>
            <button
              className="modal-seal-btn"
              style={{ marginTop: "1rem" }}
              onClick={() => setState("confirm")}
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
