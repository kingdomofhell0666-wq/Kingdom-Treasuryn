export default function Home() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center space-y-4 max-w-md px-6">
        <div className="text-6xl">👑</div>
        <h1 className="text-3xl font-bold text-foreground">Kingdom Treasury</h1>
        <p className="text-muted-foreground">
          Admin dashboard — rebuilding on clean foundations.
        </p>
        <div className="inline-flex items-center gap-2 text-sm text-muted-foreground border border-border rounded-full px-4 py-2">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          Core is running
        </div>
      </div>
    </div>
  );
}
