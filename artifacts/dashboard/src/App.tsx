import { Switch, Route, Router as WouterRouter } from "wouter";
import LoginPage     from "@/pages/login";
import GuildsPage    from "@/pages/guilds";
import OverviewPage  from "@/pages/guilds/overview";
import BotStatusPage from "@/pages/guilds/bot-status";
import {
  EconomyPage, CurrencyPage, TreasuryPage,
  RoutingPage, PermissionsPage, RanksPage, AscensionPage,
  MarketPage, InventoryPage, IdentityPage,
  KingdomRanksPage, AutomationPage, SettingsPage, ResetPage,
} from "@/pages/guilds/placeholder-pages";

const base = import.meta.env.BASE_URL?.replace(/\/$/, "") ?? "";

function AppRoutes() {
  return (
    <Switch>
      {/* Auth + selection */}
      <Route path="/"       component={LoginPage} />
      <Route path="/guilds" component={GuildsPage} />

      {/* Guild dashboard */}
      <Route path="/guilds/:guildId"                  component={OverviewPage} />
      <Route path="/guilds/:guildId/bot-status"       component={BotStatusPage} />

      <Route path="/guilds/:guildId/economy"          component={EconomyPage} />
      <Route path="/guilds/:guildId/currency"         component={CurrencyPage} />
      <Route path="/guilds/:guildId/treasury"         component={TreasuryPage} />

      <Route path="/guilds/:guildId/routing"          component={RoutingPage} />
      <Route path="/guilds/:guildId/permissions"      component={PermissionsPage} />

      <Route path="/guilds/:guildId/ranks"            component={RanksPage} />
      <Route path="/guilds/:guildId/ascension"        component={AscensionPage} />

      <Route path="/guilds/:guildId/market"           component={MarketPage} />
      <Route path="/guilds/:guildId/inventory"        component={InventoryPage} />
      <Route path="/guilds/:guildId/identity"         component={IdentityPage} />

      <Route path="/guilds/:guildId/kingdom-ranks"    component={KingdomRanksPage} />
      <Route path="/guilds/:guildId/automation"       component={AutomationPage} />

      <Route path="/guilds/:guildId/settings"         component={SettingsPage} />
      <Route path="/guilds/:guildId/reset"            component={ResetPage} />

      {/* 404 */}
      <Route>
        <div className="min-h-screen bg-[#0a0a0b] flex items-center justify-center">
          <div className="text-center space-y-2">
            <p className="text-[24px] font-bold text-white/80">404</p>
            <p className="text-[13px] text-white/35">Page not found</p>
          </div>
        </div>
      </Route>
    </Switch>
  );
}

export default function App() {
  return (
    <WouterRouter base={base}>
      <AppRoutes />
    </WouterRouter>
  );
}
