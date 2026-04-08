import discord
from discord import app_commands
from discord.ext import commands

from ..services.cosmetic_service import CosmeticService
from ..utils.skins import get_skin, get_all_skins, SKINS, TITLES
from ..utils.formatting import format_dc


VOID_BLACK = 0x0A0A0A
BLOOD_RED = 0x6B0000
GOLD = 0xFFD700


def _skin_list_embed(owned_ids: list, equipped_id: str) -> discord.Embed:
    all_skins = get_all_skins()
    embed = discord.Embed(
        title="🎨  Card Skins",
        description=(
            "*The face of your Kingdom identity. Each skin changes the visual character of your card.*\n"
            "*Acquire new skins through the Black Market or Kingdom events.*"
        ),
        color=BLOOD_RED,
    )
    embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)

    for sid, skin in all_skins.items():
        owned = sid in owned_ids
        equipped = sid == equipped_id
        status = "**[EQUIPPED]**" if equipped else ("✓ Owned" if owned else "🔒 Locked")
        embed.add_field(
            name=f"{skin.title_banner.split('  ')[0]}  {skin.name}",
            value=f"{skin.footer_flavor}\n{status}",
            inline=True,
        )

    embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)
    embed.set_footer(
        text=f"Use /equip-skin <skin_id> to activate a skin  ·  Equipped: {equipped_id}  ·  Kingdom Treasury"
    )
    return embed


def _title_list_embed(owned: list, equipped: str) -> discord.Embed:
    embed = discord.Embed(
        title="🎭  Kingdom Titles",
        description=(
            "*Titles mark your distinction within the Kingdom.*\n"
            "*Displayed prominently on your Identity Card.*"
        ),
        color=BLOOD_RED,
    )
    embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)

    for title in TITLES:
        is_owned = title in owned
        is_equipped = title == equipped
        if is_equipped:
            status = "**[EQUIPPED]**"
        elif is_owned:
            status = "✓ Owned"
        else:
            status = "🔒 Locked"
        embed.add_field(name=f"*{title}*", value=status, inline=True)

    embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)
    embed.set_footer(
        text=f"Use /equip-title <title> to activate  ·  Equipped: {equipped}  ·  Kingdom Treasury"
    )
    return embed


class CosmeticsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def cosmetics(self) -> CosmeticService:
        return self.bot.cosmetic_service

    @property
    def db(self):
        return self.bot.db

    # ─── /skins ───────────────────────────────────────────────

    @app_commands.command(
        name="skins",
        description="Browse all card skins and see which you own.",
    )
    async def skins(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        discord_id = str(interaction.user.id)
        username = interaction.user.display_name
        await self.db.upsert_user(discord_id, username)

        owned = await self.cosmetics.get_owned_skins(discord_id)
        equipped = await self.cosmetics.get_equipped_skin_id(discord_id)

        embed = _skin_list_embed(owned, equipped)
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ─── /equip-skin ──────────────────────────────────────────

    @app_commands.command(
        name="equip-skin",
        description="Equip an owned card skin. Changes the appearance of /identity.",
    )
    @app_commands.describe(skin_id="The skin ID to equip (e.g. blood_crown, infernal_gold).")
    @app_commands.choices(skin_id=[
        app_commands.Choice(name="Infernal Standard (default)", value="default"),
        app_commands.Choice(name="Blood Crown", value="blood_crown"),
        app_commands.Choice(name="Abyss Smoke", value="abyss_smoke"),
        app_commands.Choice(name="Infernal Gold", value="infernal_gold"),
        app_commands.Choice(name="Royal Dark", value="royal_dark"),
        app_commands.Choice(name="Black Throne", value="black_throne"),
        app_commands.Choice(name="Crimson Sigil", value="crimson_sigil"),
    ])
    async def equip_skin(self, interaction: discord.Interaction, skin_id: str):
        await interaction.response.defer(ephemeral=True)

        discord_id = str(interaction.user.id)
        username = interaction.user.display_name
        await self.db.upsert_user(discord_id, username)

        try:
            result = await self.cosmetics.equip_skin(discord_id, skin_id)
        except ValueError as e:
            embed = discord.Embed(description=f"*{e}*", color=VOID_BLACK)
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        skin = result["skin"]
        embed = discord.Embed(
            title=f"{skin.title_banner.split('  ')[0]}  Skin Equipped",
            description=(
                f"*You have equipped the **{skin.name}** card skin.*\n"
                f"*Use `/identity` to see your updated card.*"
            ),
            color=skin.color,
        )
        embed.add_field(name="Theme", value=skin.theme_tag, inline=True)
        embed.add_field(name="Flavor", value=skin.footer_flavor, inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ─── /titles ──────────────────────────────────────────────

    @app_commands.command(
        name="titles",
        description="Browse all available Kingdom titles.",
    )
    async def titles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        discord_id = str(interaction.user.id)
        username = interaction.user.display_name
        await self.db.upsert_user(discord_id, username)

        owned = await self.cosmetics.get_owned_titles(discord_id)
        equipped = await self.cosmetics.get_equipped_title(discord_id)

        embed = _title_list_embed(owned, equipped)
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ─── /equip-title ─────────────────────────────────────────

    @app_commands.command(
        name="equip-title",
        description="Equip a title. Displayed on your /identity card.",
    )
    @app_commands.describe(title="The title to equip.")
    @app_commands.choices(title=[
        app_commands.Choice(name=t, value=t) for t in TITLES
    ])
    async def equip_title(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer(ephemeral=True)

        discord_id = str(interaction.user.id)
        username = interaction.user.display_name
        await self.db.upsert_user(discord_id, username)

        try:
            await self.cosmetics.equip_title(discord_id, title)
        except ValueError as e:
            embed = discord.Embed(description=f"*{e}*", color=VOID_BLACK)
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="🎭  Title Equipped",
            description=(
                f"*You now bear the title **{title}**.*\n"
                f"*It is displayed on your `/identity` card.*"
            ),
            color=BLOOD_RED,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)
