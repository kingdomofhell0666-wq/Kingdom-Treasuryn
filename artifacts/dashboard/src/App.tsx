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
