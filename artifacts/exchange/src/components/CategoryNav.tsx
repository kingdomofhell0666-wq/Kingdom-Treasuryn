import type { ItemCategory } from "../types";

interface Tab {
  id:    ItemCategory;
  icon:  string;
  label: string;
  count: number;
}

interface Props {
  active:  ItemCategory;
  tabs:    Tab[];
  onChange: (cat: ItemCategory) => void;
}

export default function CategoryNav({ active, tabs, onChange }: Props) {
  return (
    <nav className="cat-nav">
      <div className="cat-nav-brand">
        <span className="cat-nav-skull">💀</span>
        <span className="cat-nav-title">Exchange</span>
      </div>

      <div className="cat-nav-items">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`cat-item ${active === tab.id ? "cat-item-active" : ""}`}
            onClick={() => onChange(tab.id)}
          >
            <span className="cat-item-icon">{tab.icon}</span>
            <span className="cat-item-label">{tab.label}</span>
            <span className="cat-item-count">{tab.count}</span>
            {active === tab.id && <div className="cat-item-glow" />}
          </button>
        ))}
      </div>

      <div className="cat-nav-footer">
        <div className="cat-nav-line" />
        <span className="cat-nav-lore">Kingdom of Hell</span>
        <div className="cat-nav-line" />
      </div>
    </nav>
  );
}
