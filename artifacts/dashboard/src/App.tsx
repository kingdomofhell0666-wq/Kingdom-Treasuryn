import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import Login from "@/pages/login";
import GuildsPage from "@/pages/guilds";
import GuildDashboardPage from "@/pages/guilds/dashboard";
import EconomyPage from "@/pages/guilds/economy";
import CurrencyPage from "@/pages/guilds/currency";
import ChannelsPage from "@/pages/guilds/channels";
import SettingsPage from "@/pages/guilds/settings";
import CommandsPage from "@/pages/guilds/commands";
import RanksPage from "@/pages/guilds/ranks";
import LeaderboardPage from "@/pages/guilds/leaderboard";
import AscensionPage from "@/pages/guilds/ascension";
import TreasuryPage from "@/pages/guilds/treasury";
import ResetPage from "@/pages/guilds/reset";
import BotStatusPage from "@/pages/guilds/bot-status";

const queryClient = new QueryClient();

function Router() {
  return (
    <Switch>
      <Route path="/" component={Login} />
      <Route path="/guilds" component={GuildsPage} />
      <Route path="/guilds/:guildId" component={GuildDashboardPage} />
      <Route path="/guilds/:guildId/economy" component={EconomyPage} />
      <Route path="/guilds/:guildId/currency" component={CurrencyPage} />
      <Route path="/guilds/:guildId/channels" component={ChannelsPage} />
      <Route path="/guilds/:guildId/settings" component={SettingsPage} />
      <Route path="/guilds/:guildId/commands" component={CommandsPage} />
      <Route path="/guilds/:guildId/ranks" component={RanksPage} />
      <Route path="/guilds/:guildId/leaderboard" component={LeaderboardPage} />
      <Route path="/guilds/:guildId/ascension" component={AscensionPage} />
      <Route path="/guilds/:guildId/treasury" component={TreasuryPage} />
      <Route path="/guilds/:guildId/reset" component={ResetPage} />
      <Route path="/guilds/:guildId/bot-status" component={BotStatusPage} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
          <Router />
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
