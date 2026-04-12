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

// Redirect root → dashboard holding page
app.get("/", (_req, res) => {
  res.redirect(301, "/dashboard/");
});

// Serve the dashboard.
// During the rebuild phase this is a plain static HTML file.
// When the SPA is ready, swap this to serve the Vite dist folder.
const apiServerRoot  = path.resolve(__dirname, "..");
const workspaceRoot  = path.resolve(apiServerRoot, "..", "..");
const dashboardSrc   = path.join(workspaceRoot, "artifacts", "dashboard", "src");

app.use("/dashboard", express.static(dashboardSrc));
app.get("/dashboard/*splat", (_req, res) => {
  res.sendFile(path.join(dashboardSrc, "index.html"));
});

export default app;
