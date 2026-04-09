import { Router, type IRouter } from "express";
import healthRouter from "./health";
import authRouter from "./auth";
import guildsRouter from "./guilds";
import configRouter from "./config";

const router: IRouter = Router();

router.use(healthRouter);
router.use(authRouter);
router.use(guildsRouter);
router.use(configRouter);

export default router;
