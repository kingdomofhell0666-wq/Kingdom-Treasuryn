export interface NavItem {
  label: string;
  path:  string;
  icon:  string;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export const NAV_SECTIONS: NavSection[] = [
  {
    title: "Overview",
    items: [
      { label: "Dashboard",  path: "",            icon: "layout-dashboard" },
      { label: "Bot Status", path: "/bot-status", icon: "activity" },
    ],
  },
  {
    title: "Economy",
    items: [
      { label: "Economy",  path: "/economy",  icon: "coins" },
      { label: "Currency", path: "/currency", icon: "circle-dollar-sign" },
      { label: "Treasury", path: "/treasury", icon: "landmark" },
    ],
  },
  {
    title: "Commands",
    items: [
      { label: "Routing",     path: "/routing",     icon: "share-2" },
      { label: "Permissions", path: "/permissions", icon: "shield" },
    ],
  },
  {
    title: "Ranks & Roles",
    items: [
      { label: "Ranks & Roles", path: "/ranks",     icon: "crown" },
      { label: "Ascension",     path: "/ascension", icon: "trending-up" },
    ],
  },
  {
    title: "Player Systems",
    items: [
      { label: "Market",    path: "/market",    icon: "shopping-bag" },
      { label: "Inventory", path: "/inventory", icon: "package" },
      { label: "Identity",  path: "/identity",  icon: "id-card" },
    ],
  },
  {
    title: "Automation",
    items: [
      { label: "Kingdom Ranks", path: "/kingdom-ranks", icon: "trophy" },
      { label: "Automation",    path: "/automation",    icon: "zap" },
    ],
  },
  {
    title: "Server",
    items: [
      { label: "Settings",        path: "/settings", icon: "settings" },
      { label: "Reset / Maint.",  path: "/reset",    icon: "alert-triangle" },
    ],
  },
];
