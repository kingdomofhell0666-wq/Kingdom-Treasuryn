import { Switch, Route, Router as WouterRouter, useParams, Redirect } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { GuildProvider } from "@/context/guild-context";
import { DashboardLayout } from "@/components/dashboard/layout";

import LoginPage from "@/pages/login";
import GuildsPage from "@/pages/guilds";
import OverviewPage from "@/pages/guilds/overview";
import {
  MembersPage,
  EconomyPage,
  InvestmentsPage,
  BlackMarketPage,
  LeaderboardPage,
  RanksPage,
  AuditLogPage,
  SettingsPage,
} from "@/pages/guilds/placeholder-pages";
import NotFound from "@/pages/not-found";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30 * 1000,
    },
  },
});

function GuildRoutes() {
  const { guildId } = useParams<{ guildId: string }>();

  if (!guildId) return <NotFound />;

  return (
    <DashboardLayout guildId={guildId}>
      <Switch>
        <Route path={`/guilds/${guildId}/overview`} component={OverviewPage} />
        <Route path={`/guilds/${guildId}/members`} component={MembersPage} />
        <Route path={`/guilds/${guildId}/economy`} component={EconomyPage} />
        <Route path={`/guilds/${guildId}/investments`} component={InvestmentsPage} />
        <Route path={`/guilds/${guildId}/black-market`} component={BlackMarketPage} />
        <Route path={`/guilds/${guildId}/leaderboard`} component={LeaderboardPage} />
        <Route path={`/guilds/${guildId}/ranks`} component={RanksPage} />
        <Route path={`/guilds/${guildId}/audit-log`} component={AuditLogPage} />
        <Route path={`/guilds/${guildId}/settings`} component={SettingsPage} />
        <Route>
          <Redirect to={`/guilds/${guildId}/overview`} />
        </Route>
      </Switch>
    </DashboardLayout>
  );
}

function Router() {
  return (
    <Switch>
      <Route path="/" component={LoginPage} />
      <Route path="/guilds" component={GuildsPage} />
      <Route path="/guilds/:guildId/:page*" component={GuildRoutes} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <GuildProvider>
        <TooltipProvider>
          <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
            <Router />
          </WouterRouter>
          <Toaster />
        </TooltipProvider>
      </GuildProvider>
    </QueryClientProvider>
  );
}

export default App;
