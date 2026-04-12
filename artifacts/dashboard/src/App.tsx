import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import LoginPage  from "@/pages/login";
import GuildsPage from "@/pages/guilds";
import OverviewPage from "@/pages/guilds/overview";
import {
  BotStatusPage, EconomyPage, CurrencyPage, TreasuryPage,
  RoutingPage, PermissionsPage, RanksPage, AscensionPage,
  MarketPage, InventoryPage, IdentityPage,
  KingdomRanksPage, AutomationPage, SettingsPage, ResetPage,
} from "@/pages/guilds/placeholder-pages";

const queryClient = new QueryClient();

function AppRoutes() {
  return (
    <Switch>
      {/* Auth + selection */}
      <Route path="/"       component={LoginPage} />
      <Route path="/guilds" component={GuildsPage} />

      {/* Guild dashboard — overview */}
      <Route path="/guilds/:guildId"          component={OverviewPage} />

      {/* Overview section */}
      <Route path="/guilds/:guildId/bot-status"    component={BotStatusPage} />

      {/* Economy section */}
      <Route path="/guilds/:guildId/economy"       component={EconomyPage} />
      <Route path="/guilds/:guildId/currency"      component={CurrencyPage} />
      <Route path="/guilds/:guildId/treasury"      component={TreasuryPage} />

      {/* Commands section */}
      <Route path="/guilds/:guildId/routing"       component={RoutingPage} />
      <Route path="/guilds/:guildId/permissions"   component={PermissionsPage} />

      {/* Ranks & roles section */}
      <Route path="/guilds/:guildId/ranks"         component={RanksPage} />
      <Route path="/guilds/:guildId/ascension"     component={AscensionPage} />

      {/* Player systems section */}
      <Route path="/guilds/:guildId/market"        component={MarketPage} />
      <Route path="/guilds/:guildId/inventory"     component={InventoryPage} />
      <Route path="/guilds/:guildId/identity"      component={IdentityPage} />

      {/* Automation section */}
      <Route path="/guilds/:guildId/kingdom-ranks" component={KingdomRanksPage} />
      <Route path="/guilds/:guildId/automation"    component={AutomationPage} />

      {/* Server section */}
      <Route path="/guilds/:guildId/settings"      component={SettingsPage} />
      <Route path="/guilds/:guildId/reset"         component={ResetPage} />

      {/* 404 */}
      <Route>
        <div className="min-h-screen bg-background flex items-center justify-center">
          <div className="text-center space-y-2">
            <p className="text-2xl font-bold text-foreground">404</p>
            <p className="text-muted-foreground text-sm">Page not found</p>
          </div>
        </div>
      </Route>
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
          <AppRoutes />
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
