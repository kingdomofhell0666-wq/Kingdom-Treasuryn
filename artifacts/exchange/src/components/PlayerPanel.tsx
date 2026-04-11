import type { DiscordUser, UserData } from "../types";
import { RANK_ORDER } from "../types";

const DC_ICON = "https://cdn.discordapp.com/emojis/1492184333392412692.webp?size=32&quality=lossless";

const RANK_EPITHETS: Record<string, string> = {
  Forsaken:"The Forsaken", Vermin:"Of the Vermin", Corrupted:"The Corrupted",
  Folklore:"Of Folklore", Mythology:"Of Mythology", Demonology:"Of Demonology",
  Eschatology:"Of Eschatology", Archangel:"The Archangel", Archdemon:"The Archdemon",
  Knight:"The Knight", Baron:"The Baron", Viscount:"The Viscount",
  Count:"The Count", Marquis:"The Marquis", Duke:"The Duke", Chancellor:"The Chancellor",
};

interface Props {
  discordUser: DiscordUser;
  userData: UserData;
  balance: number;
  onLeave: () => void;
}

export default function PlayerPanel({ discordUser, userData, balance, onLeave }: Props) {
  const rankIdx = RANK_ORDER[userData.rank] ?? 0;
  const maxRank = Object.keys(RANK_ORDER).length - 1;
  const rankPct = (rankIdx / maxRank) * 100;
  const epithet = RANK_EPITHETS[userData.rank] ?? userData.rank;
  const ownedTotal =
    userData.owned_relics.length + userData.owned_titles.length +
    userData.owned_skins.length  + userData.owned_badges.length;

  return (
    <aside className="player-panel">
      {/* ── Seal glyph ───────────────────────────────── */}
      <div className="pp-seal">⛧</div>

      {/* ── Identity ──────────────────────────────────── */}
      <div className="pp-identity">
        <div className="pp-avatar-ring">
          <img src={discordUser.avatarUrl} alt="avatar" className="pp-avatar" />
          <div className="pp-avatar-glow" />
        </div>
        <div className="pp-name-block">
          <span className="pp-username">{discordUser.username}</span>
          <span className="pp-epithet">{epithet}</span>
        </div>
      </div>

      <div className="pp-sep" />

      {/* ── Balance ───────────────────────────────────── */}
      <div className="pp-block">
        <span className="pp-label">Treasury Balance</span>
        <div className="pp-balance">
          <img src={DC_ICON} alt="dc" className="pp-dc-icon" />
          <span className="pp-balance-num">{balance.toLocaleString()}</span>
        </div>
      </div>

      <div className="pp-sep" />

      {/* ── Rank ──────────────────────────────────────── */}
      <div className="pp-block">
        <span className="pp-label">Rank Standing</span>
        <span className="pp-rank-name">{userData.rank}</span>
        <div className="pp-rank-track">
          <div className="pp-rank-fill" style={{ width: `${rankPct}%` }} />
        </div>
        <span className="pp-rank-pos">{rankIdx} / {maxRank}</span>
      </div>

      <div className="pp-sep" />

      {/* ── Holdings ──────────────────────────────────── */}
      <div className="pp-grid">
        {([
          ["Relics",  userData.owned_relics.length],
          ["Titles",  userData.owned_titles.length],
          ["Skins",   userData.owned_skins.length],
          ["Badges",  userData.owned_badges.length],
        ] as [string, number][]).map(([label, val]) => (
          <div key={label} className="pp-grid-cell">
            <span className="pp-grid-val">{val}</span>
            <span className="pp-grid-key">{label}</span>
          </div>
        ))}
      </div>

      {userData.sacrifice_active && (
        <div className="pp-debt">
          🩸 Debt Active — Purchases suspended
        </div>
      )}

      <div style={{ flex: 1 }} />

      <button className="pp-leave" onClick={onLeave}>
        Leave the Exchange
        <span className="pp-leave-arrow">⟶</span>
      </button>
    </aside>
  );
}
