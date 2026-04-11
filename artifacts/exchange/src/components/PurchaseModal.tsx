import { useState, useEffect } from "react";
import type { CatalogItem, ItemCategory } from "../types";
import { api, ApiError } from "../api";

const DC_ICON = "https://cdn.discordapp.com/emojis/1492184333392412692.webp?size=32&quality=lossless";

interface Props {
  item: CatalogItem;
  category: ItemCategory;
  userBalance: number;
  onClose: () => void;
  onSuccess: (newBalance: number) => void;
}

type State = "confirm" | "sealing" | "success" | "error";

export default function PurchaseModal({ item, userBalance, onClose, onSuccess }: Props) {
  const [state, setState] = useState<State>("confirm");
  const [error, setError] = useState("");
  const [newBal, setNewBal] = useState(0);
  const [pulseRing, setPulseRing] = useState(false);

  const canAfford = userBalance >= item.price_dc;

  useEffect(() => {
    if (state === "sealing") {
      const t = setInterval(() => setPulseRing(p => !p), 600);
      return () => clearInterval(t);
    }
  }, [state]);

  async function seal() {
    if (!canAfford) return;
    setState("sealing");
    try {
      const result = await api.purchase(item.id.split(":")[0] ?? "relics", item.id);
      setNewBal(result.new_balance);
      setState("success");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "The sealing failed.";
      setError(msg);
      setState("error");
    }
  }

  return (
    <div className="modal-root" onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className={`modal-box ${state === "sealing" ? "modal-sealing-mode" : ""}`}>

        {/* ── Confirm ──────────────────────────────────── */}
        {state === "confirm" && (
          <>
            <div className="modal-glyph">⛧</div>
            <h2 className="modal-title">Seal the Exchange</h2>
            <p className="modal-subtitle">
              You are about to claim possession of this artifact.
            </p>

            <div className="modal-item-preview">
              <span className="modal-item-icon">{item.stat_icon ?? item.icon ?? "⬡"}</span>
              <div className="modal-item-info">
                <span className="modal-item-name">{item.name}</span>
                <span className="modal-item-desc">{item.description}</span>
              </div>
            </div>

            <div className="modal-cost">
              <span className="modal-cost-label">Cost</span>
              <div className="modal-cost-amount">
                <img src={DC_ICON} alt="dc" className="modal-dc" />
                <span className={canAfford ? "modal-cost-ok" : "modal-cost-low"}>
                  {item.price_dc.toLocaleString()}
                </span>
              </div>
              {!canAfford && (
                <span className="modal-insufficient">Insufficient treasury funds.</span>
              )}
            </div>

            <div className="modal-warning">
              <span className="modal-warning-text">
                The Kingdom does not offer refunds.<br />
                Once sealed, the offering is complete.
              </span>
            </div>

            <div className="modal-actions">
              <button className="modal-back-btn" onClick={onClose}>Step Back</button>
              <button
                className="modal-seal-btn"
                disabled={!canAfford}
                onClick={seal}
              >
                🩸 Seal the Exchange
              </button>
            </div>
          </>
        )}

        {/* ── Sealing ──────────────────────────────────── */}
        {state === "sealing" && (
          <div className="modal-sealing-body">
            <div className={`modal-seal-ring ${pulseRing ? "modal-seal-ring-pulse" : ""}`} />
            <div className="modal-seal-inner" />
            <p className="modal-sealing-text">Sealing the exchange…</p>
            <p className="modal-sealing-sub">The Kingdom acknowledges your offering.</p>
          </div>
        )}

        {/* ── Success ──────────────────────────────────── */}
        {state === "success" && (
          <div className="modal-success-body">
            <div className="modal-success-glyph">🩸</div>
            <h2 className="modal-success-title">Acquisition Complete</h2>
            <p className="modal-success-name">{item.name}</p>
            <p className="modal-success-flavor">
              The Kingdom acknowledges your offering.<br />
              It is now yours.
            </p>
            <div className="modal-success-bal">
              <img src={DC_ICON} alt="dc" className="modal-dc" />
              <span>New balance: {newBal.toLocaleString()}</span>
            </div>
            <button className="modal-done-btn" onClick={() => { onSuccess(newBal); }}>
              Return to the Exchange
            </button>
          </div>
        )}

        {/* ── Error ────────────────────────────────────── */}
        {state === "error" && (
          <div className="modal-error-body">
            <div className="modal-error-glyph">🔥</div>
            <h2 className="modal-error-title">The Seal Failed</h2>
            <p className="modal-error-msg">{error}</p>
            <div className="modal-actions">
              <button className="modal-back-btn" onClick={onClose}>Leave</button>
              <button className="modal-seal-btn" onClick={() => setState("confirm")}>
                Try Again
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
