import discord


class IdentityView(discord.ui.View):
    """
    Action buttons attached to /identity cards.
    Provides quick access to economy commands directly from the card.
    """

    def __init__(self, is_own_card: bool = True):
        super().__init__(timeout=180)
        self.is_own_card = is_own_card
        if not is_own_card:
            # Remove equip buttons if viewing someone else's card
            for item in list(self.children):
                if getattr(item, "custom_id", None) in ("btn_skins", "btn_titles"):
                    self.remove_item(item)

    @discord.ui.button(
        label="⛏  Grind",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_grind",
    )
    async def grind_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Use `/grind` to descend into the Infernal Mines and extract DevilCoins.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="🏪  Market",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_market",
    )
    async def market_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Use `/market` to browse purchasable ranks.\nUse `/ascend <rank>` to claim the next rank in sequence.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="🎨  Skins",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_skins",
    )
    async def skins_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Use `/skins` to browse your card skins.\nUse `/equip-skin <skin_id>` to change your card's appearance.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="🎭  Titles",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_titles",
    )
    async def titles_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Use `/titles` to browse your titles.\nUse `/equip-title <title>` to display a new title on your card.",
            ephemeral=True,
        )
