import type { ItemCategory } from "../types";

interface Tab { id: ItemCategory; icon: string; label: string; count: number }
interface Props { active: ItemCategory; tabs: Tab[]; onChange: (cat: ItemCategory) => void }

const GLYPHS: Record<ItemCategory, string> = {
  relics: "⬡", titles: "◈", skins: "▣", badges: "⬟",
};

export default function CategoryNav({ active, tabs, onChange }: Props) {
  return (
    <nav className="cat-nav">
      <div className="cat-nav-header">
        <span className="cat-nav-glyph">⛧</span>
        <span className="cat-nav-title">Archive</span>
      </div>
      <div className="cat-nav-divider" />
      {tabs.map(tab => (
        <button
          key={tab.id}
          className={`cat-btn ${active === tab.id ? "cat-btn-active" : ""}`}
          onClick={() => onChange(tab.id)}
        >
          <span className="cat-btn-glyph">{GLYPHS[tab.id]}</span>
          <span className="cat-btn-text">{tab.label}</span>
          <span className="cat-btn-count">{tab.count}</span>
          {active === tab.id && <div className="cat-btn-bar" />}
        </button>
      ))}
      <div style={{ flex: 1 }} />
      <div className="cat-nav-footer">
        <span className="cat-nav-footer-text">Kingdom Exchange</span>
      </div>
    </nav>
  );
}
