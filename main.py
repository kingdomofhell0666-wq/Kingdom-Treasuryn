import asyncio
import logging
import os
from dotenv import load_dotenv
from bot.bot import KingdomTreasuryBot

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("kingdom_treasury")


def main():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error(
            "DISCORD_BOT_TOKEN is not set. "
            "Add it to your .env file or environment secrets."
        )
        return

    bot = KingdomTreasuryBot()

    try:
        asyncio.run(bot.start(token))
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
