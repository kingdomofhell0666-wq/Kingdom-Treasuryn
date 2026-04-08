import discord


class IdentityView(discord.ui.View):
    """
    Action buttons attached to /identity cards.
    Buttons trigger ephemeral prompts guiding users to the full commands.
    """

    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="💸  Transfer", style=discord.ButtonStyle.secondary)
    async def transfer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Use `/transfer @user amount` to send DevilCoins to another soul.",
            ephemeral=True,
        )

    @discord.ui.button(label="🏪  Market", style=discord.ButtonStyle.secondary)
    async def market_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Use `/market` to browse all purchasable ranks and their costs.",
            ephemeral=True,
        )

    @discord.ui.button(label="👑  Ascend", style=discord.ButtonStyle.danger)
    async def ascend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Use `/ascend <rank>` to purchase a rank with your DevilCoins.",
            ephemeral=True,
        )
