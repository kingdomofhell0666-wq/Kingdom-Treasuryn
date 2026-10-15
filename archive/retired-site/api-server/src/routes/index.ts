import { Router } from "express";
import healthRouter   from "./health";
import authRouter     from "./auth";
import guildsRouter   from "./guilds";
import guildRouter    from "./guild";
import internalRouter from "./internal";

const router = Router();

router.use("/health",  healthRouter);
router.use("/auth",    authRouter);
router.use("/guilds",  guildsRouter);
router.use("/guilds",  guildRouter);

export { internalRouter };
export default router;
