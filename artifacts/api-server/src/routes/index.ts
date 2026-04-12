import { Router } from "express";
import healthRouter from "./health";
import authRouter   from "./auth";
import guildsRouter from "./guilds";

const router = Router();

router.use("/health",  healthRouter);
router.use("/auth",    authRouter);
router.use("/guilds",  guildsRouter);

export default router;
