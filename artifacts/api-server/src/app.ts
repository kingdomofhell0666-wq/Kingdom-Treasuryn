import express, { type Express } from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import path from "path";
import { fileURLToPath } from "url";
import router from "./routes";
import { logger } from "./lib/logger";
import { sessionMiddleware } from "./lib/session";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const app: Express = express();

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return { id: req.id, method: req.method, url: req.url?.split("?")[0] };
      },
      res(res) {
        return { statusCode: res.statusCode };
      },
    },
  }),
);

app.use(cors({ origin: true, credentials: true }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(sessionMiddleware);

app.use("/api", router);

// Redirect root → dashboard
app.get("/", (_req, res) => {
  res.redirect(301, "/dashboard/");
});

// Serve the compiled Vite SPA from dist/public.
const apiServerRoot  = path.resolve(__dirname, "..");
const workspaceRoot  = path.resolve(apiServerRoot, "..", "..");
const dashboardDist  = path.join(workspaceRoot, "artifacts", "dashboard", "dist", "public");

app.use("/dashboard", express.static(dashboardDist));
app.get("/dashboard/*splat", (_req, res) => {
  res.sendFile(path.join(dashboardDist, "index.html"));
});

export default app;
