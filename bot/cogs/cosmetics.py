import discord
from discord import app_commands
from discord.ext import commands

from ..services.cosmetic_service import CosmeticService
from ..services.badge_service import BadgeService
from ..utils.skins import (
    get_skin, get_all_skins, SKINS, TITLES_CATALOG,
    RARITY_COLORS as SKIN_RARITY_COLORS,
)
from ..utils.badges import BADGES_CATALOG, RARITY_COLORS as BADGE_RARITY_COLORS
from ..utils.formatting import format_dc


VOID_BLACK  = 0x0A0A0A
BLOOD_RED   = 0x6B0000
GOLD        = 0xFFD700
DARK_RED    = 0x8B0000
SEP         = "━━━━━━━━━━━━━━━━━━━━━━━━━━"

RARITY_EMBED_COLORS = {
    "Default":   VOID_BLACK,
    "Common":    0x444444,
    "Uncommon":  0x1A5C1A,
    "Rare":      0x0D3D80,
    "Epic":      0x4B0082,
    "Legendary": 0x8B6914,
    "Special":   0x8B0000,
}


def _skin_shop_embed(owned_ids: list, equipped_id: str) -> discord.Embed:
    embed = discord.Embed(
        title="🎨  Card Skins — Kingdom Identity Store",
        description=(
            "*Your identity card's visual character. Each skin changes colors, borders, and tone.*\n"
            "*Purchase with DevilCoins via `/buy-skin`. Equip with `/equip-skin`.*"
        ),
        color=BLOOD_RED,
    )
    embed.add_field(name="\u200b", value=SEP, inline=False)
    for sid, skin in get_all_skins().items():
        owned   = sid in owned_ids
        equipped = sid == equipped_id
        dot     = SKIN_RARITY_COLORS.get(skin.rarity, "⬜")
        if equipped:   status = "**[EQUIPPED]**"
        elif owned:    status = "✓ Owned"
        elif skin.price_dc == 0: status = "✓ Free"
        else:          status = f"🔒 {format_dc(skin.price_dc)}"
        embed.add_field(name=f"{dot} {skin.name}  ·  {skin.rarity}", value=f"*{skin.description}*\n{status}", inline=True)
    embed.add_field(name="\u200b", value=SEP, inline=False)
    embed.set_footer(text=f"Equipped: {equipped_id}  ·  Use /buy-skin to purchase  ·  Kingdom Treasury")
    return embed


def _title_shop_embed(owned: list, equipped: str) -> discord.Embed:
    embed = discord.Embed(
        title="🎭  Kingdom Titles — Identity Store",
        description=(
            "*Titles mark your distinction within the Kingdom. Displayed on your Identity Card.*\n"
            "*Purchase with DevilCoins via `/buy-title`. Equip with `/equip-title`.*"
        ),
        color=BLOOD_RED,
    )
    embed.add_field(name="\u200b", value=SEP, inline=False)
    from ..utils.skins import RARITY_COLORS as RC
    for title_name, title in TITLES_CATALOG.items():
        is_owned    = title_name in owned
        is_equipped = title_name == equipped
        dot         = RC.get(title.rarity, "⬜")
        if is_equipped:   status = "**[EQUIPPED]**"
        elif is_owned:    status = "✓ Owned"
        elif title.price_dc == 0: status = "✓ Free"
        else:             status = f"🔒 {format_dc(title.price_dc)}"
        embed.add_field(name=f"{dot} *{title.name}*  ·  {title.rarity}", value=f"*{title.description}*\n{status}", inline=True)
    embed.add_field(name="\u200b", value=SEP, inline=False)
    embed.set_footer(text=f"Equipped: {equipped}  ·  Use /buy-title to purchase  ·  Kingdom Treasury")
    return embed


def _badges_embed(owned_ids: list) -> discord.Embed:
    owned_set = set(owned_ids)
    embed = discord.Embed(
        title="🏅  Kingdom Badges — Achievement Record",
        description=(
            "*Badges are earned through real actions in the Kingdom — never purchased.*\n"
            "*They represent achievement, loyalty, status, and history.*"
        ),
        color=DARK_RED,
    )
    embed.add_field(name="\u200b", value=SEP, inline=False)
    for badge_id, badge in BADGES_CATALOG.items():
        dot    = BADGE_RARITY_COLORS.get(badge.rarity, "⬜")
        earned = badge_id in owned_set
        status = "✅ **EARNED**" if earned else f"🔒 *{badge.unlock_label}*"
        embed.add_field(name=f"{dot} {badge.icon}  {badge.name}  ·  {badge.rarity}", value=f"*{badge.description}*\n{status}", inline=True)
    embed.add_field(name="\u200b", value=SEP, inline=False)
    embed.set_footer(text=f"Earned: {len(owned_set)} / {len(BADGES_CATALOG)}  ·  Badges cannot be purchased  ·  Kingdom Treasury")
    return embed


class CosmeticsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def cosmetics(self) -> CosmeticService: return self.bot.cosmetic_service
    @property
    def badges(self) -> BadgeService:       return self.bot.badge_service
    @property
    def db(self):                           return self.bot.db

    @app_commands.command(name="skins", description="Browse all card skins and their DevilCoin prices.")
    async def skins(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        await self.db.upsert_user(guild_id, discord_id, interaction.user.display_name)
        owned    = await self.cosmetics.get_owned_skins(guild_id, discord_id)
        equipped = await self.cosmetics.get_equipped_skin_id(guild_id, discord_id)
        await interaction.followup.send(embed=_skin_shop_embed(owned, equipped), ephemeral=True)

    @app_commands.command(name="buy-skin", description="Purchase a card skin with DevilCoins.")
    @app_commands.describe(skin_id="The skin to purchase.")
    @app_commands.choices(skin_id=[
        app_commands.Choice(name=f"{s.name} — {format_dc(s.price_dc)} ({s.rarity})", value=sid)
        for sid, s in SKINS.items() if s.price_dc > 0
    ])
    async def buy_skin(self, interaction: discord.Interaction, skin_id: str):
        await interaction.response.defer(ephemeral=True)
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        await self.db.upsert_user(guild_id, discord_id, interaction.user.display_name)
        try:
            result = await self.cosmetics.buy_skin(guild_id, discord_id, skin_id)
        except ValueError as e:
            embed = discord.Embed(description=f"*{e}*", color=VOID_BLACK)
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        skin  = result["skin"]
        embed = discord.Embed(
            title=f"{skin.title_banner.split('  ')[0]}  Skin Acquired — {skin.name}",
            description=f"*{skin.description}*\n\n*Use `/equip-skin` to activate it on your Identity Card.*",
            color=skin.color,
        )
        embed.add_field(name="COST",    value=f"**{format_dc(result['cost'])}**",        inline=True)
        embed.add_field(name="BALANCE", value=f"**{format_dc(result['new_balance'])}**", inline=True)
        embed.add_field(name="RARITY",  value=skin.rarity,                               inline=True)
        embed.add_field(name="THEME",   value=skin.theme_tag,                            inline=True)
        embed.add_field(name="FLAVOR",  value=skin.footer_flavor,                        inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="equip-skin", description="Equip an owned card skin.")
    @app_commands.describe(skin_id="The skin ID to equip.")
    @app_commands.choices(skin_id=[app_commands.Choice(name=s.name, value=sid) for sid, s in SKINS.items()])
    async def equip_skin(self, interaction: discord.Interaction, skin_id: str):
        await interaction.response.defer(ephemeral=True)
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        await self.db.upsert_user(guild_id, discord_id, interaction.user.display_name)
        try:
            result = await self.cosmetics.equip_skin(guild_id, discord_id, skin_id)
        except ValueError as e:
            embed = discord.Embed(description=f"*{e}*", color=VOID_BLACK)
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        skin  = result["skin"]
        embed = discord.Embed(
            title=f"{skin.title_banner.split('  ')[0]}  Skin Equipped",
            description=f"*You have equipped the **{skin.name}** card skin.*\n*Use `/identity` to see your updated card.*",
            color=skin.color,
        )
        embed.add_field(name="Theme",  value=skin.theme_tag,    inline=True)
        embed.add_field(name="Flavor", value=skin.footer_flavor, inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="titles", description="Browse all Kingdom titles and their DevilCoin prices.")
    async def titles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        await self.db.upsert_user(guild_id, discord_id, interaction.user.display_name)
        owned    = await self.cosmetics.get_owned_titles(guild_id, discord_id)
        equipped = await self.cosmetics.get_equipped_title(guild_id, discord_id)
        await interaction.followup.send(embed=_title_shop_embed(owned, equipped), ephemeral=True)

    @app_commands.command(name="buy-title", description="Purchase a Kingdom title with DevilCoins.")
    @app_commands.describe(title="The title to purchase.")
    @app_commands.choices(title=[
        app_commands.Choice(name=f"{t.name} — {format_dc(t.price_dc)} ({t.rarity})", value=t.name)
        for t in TITLES_CATALOG.values() if t.price_dc > 0
    ])
    async def buy_title(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer(ephemeral=True)
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        await self.db.upsert_user(guild_id, discord_id, interaction.user.display_name)
        try:
            result = await self.cosmetics.buy_title(guild_id, discord_id, title)
        except ValueError as e:
            embed = discord.Embed(description=f"*{e}*", color=VOID_BLACK)
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        t_obj = result["title"]
        embed = discord.Embed(
            title="🎭  Title Acquired",
            description=f"*You now hold the title **{t_obj.name}**.*\n*{t_obj.description}*\n\n*Use `/equip-title` to display it on your Identity Card.*",
            color=RARITY_EMBED_COLORS.get(t_obj.rarity, BLOOD_RED),
        )
        embed.add_field(name="COST",    value=f"**{format_dc(result['cost'])}**",        inline=True)
        embed.add_field(name="BALANCE", value=f"**{format_dc(result['new_balance'])}**", inline=True)
        embed.add_field(name="RARITY",  value=t_obj.rarity,                              inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="equip-title", description="Equip a title you own.")
    @app_commands.describe(title="The title to equip.")
    @app_commands.choices(title=[app_commands.Choice(name=t.name, value=t.name) for t in TITLES_CATALOG.values()])
    async def equip_title(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer(ephemeral=True)
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        await self.db.upsert_user(guild_id, discord_id, interaction.user.display_name)
        try:
            await self.cosmetics.equip_title(guild_id, discord_id, title)
        except ValueError as e:
            embed = discord.Embed(description=f"*{e}*", color=VOID_BLACK)
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        t_obj = TITLES_CATALOG.get(title)
        embed = discord.Embed(
            title="🎭  Title Equipped",
            description=f"*You now bear the title **{title}**.*\n*It is displayed on your `/identity` card.*",
            color=RARITY_EMBED_COLORS.get(t_obj.rarity if t_obj else "Common", BLOOD_RED),
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="badges", description="View all Kingdom badges and your earned achievements.")
    async def badges_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        await self.db.upsert_user(guild_id, discord_id, interaction.user.display_name)
        owned = await self.badges.get_owned_badges(guild_id, discord_id)
        await interaction.followup.send(embed=_badges_embed(owned), ephemeral=True)
