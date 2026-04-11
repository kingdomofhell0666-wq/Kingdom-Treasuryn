import type { DiscordUser, UserData } from "../types";
import { RANK_ORDER } from "../types";

const DC_ICON = "https://cdn.discordapp.com/emojis/1492184333392412692.webp?size=32&quality=lossless";

const RANK_TITLES: Record<string, string> = {
  Forsaken:    "The Forsaken",   Vermin:    "Of the Vermin",
  Corrupted:   "The Corrupted",  Folklore:  "Of Folklore",
  Mythology:   "Of Mythology",   Demonology:"Of Demonology",
  Eschatology: "Of Eschatology", Archangel: "The Archangel",
  Archdemon:   "The Archdemon",  Knight:    "The Knight",
  Baron:       "The Baron",      Viscount:  "The Viscount",
  Count:       "The Count",      Marquis:   "The Marquis",
  Duke:        "The Duke",       Chancellor:"The Chancellor",
};

interface Props {
  discordUser: DiscordUser;
  userData:    UserData;
  balance:     number;
  onLeave:     () => void;
}

export default function PlayerPanel({ discordUser, userData, balance, onLeave }: Props) {
  const rankIdx   = RANK_ORDER[userData.rank] ?? 0;
  const maxRank   = Object.keys(RANK_ORDER).length - 1;
  const rankPct   = (rankIdx / maxRank) * 100;
  const rankTitle = RANK_TITLES[userData.rank] ?? userData.rank;

  const ownedCount =
    userData.owned_relics.length +
    userData.owned_titles.length +
    userData.owned_skins.length  +
    userData.owned_badges.length;

  return (
    <aside className="player-panel">
      {/* Avatar + name */}
      <div className="pp-identity">
        <div className="pp-avatar-wrap">
          <img
            src={discordUser.avatarUrl}
            alt="avatar"
            className="pp-avatar"
          />
          <div className="pp-avatar-ring" />
        </div>
        <div className="pp-name-block">
          <span className="pp-username">{discordUser.username}</span>
          <span className="pp-rank-tag">{rankTitle}</span>
        </div>
      </div>

      <div className="pp-divider" />

      {/* Balance */}
      <div className="pp-stat-block pp-balance-block">
        <span className="pp-stat-label">Treasury Balance</span>
        <div className="pp-balance">
          <img src={DC_ICON} alt="DC" className="pp-dc-icon" />
          <span className="pp-balance-num">{balance.toLocaleString()}</span>
          <span className="pp-balance-unit">DC</span>
        </div>
      </div>

      <div className="pp-divider" />

      {/* Rank progress */}
      <div className="pp-stat-block">
        <span className="pp-stat-label">Rank Standing</span>
        <span className="pp-rank-name">{userData.rank}</span>
        <div className="pp-rank-bar-wrap">
          <div className="pp-rank-bar" style={{ width: `${rankPct}%` }} />
        </div>
        <span className="pp-rank-pct">{rankIdx} / {maxRank}</span>
      </div>

      <div className="pp-divider" />

      {/* Stats */}
      <div className="pp-stats-grid">
        <div className="pp-mini-stat">
          <span className="pp-mini-val">{userData.owned_relics.length}</span>
          <span className="pp-mini-key">Relics</span>
        </div>
        <div className="pp-mini-stat">
          <span className="pp-mini-val">{userData.owned_titles.length}</span>
          <span className="pp-mini-key">Titles</span>
        </div>
        <div className="pp-mini-stat">
          <span className="pp-mini-val">{userData.owned_skins.length}</span>
          <span className="pp-mini-key">Skins</span>
        </div>
        <div className="pp-mini-stat">
          <span className="pp-mini-val">{userData.owned_badges.length}</span>
          <span className="pp-mini-key">Badges</span>
        </div>
      </div>

      {userData.sacrifice_active && (
        <div className="pp-debt-notice">
          🩸 Debt Active<br />Purchases suspended
        </div>
      )}

      <div style={{ flex: 1 }} />

      {/* Leave button */}
      <button className="pp-leave-btn" onClick={onLeave}>
        <span>Leave the Exchange</span>
        <span className="pp-leave-arrow">→</span>
      </button>
    </aside>
  );
}
