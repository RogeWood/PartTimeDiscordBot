import os
from nextcord.ext import commands, application_checks
from nextcord import Interaction, slash_command, ui, ButtonStyle

DATA_DIR = "data"

class ClearData(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(name="clear_data", description="清空機器人儲存資料", force_global=False)
    @application_checks.is_owner() # 機器人擁有者可以刪除資料
    async def clear(self, interaction: Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.send("❌ 你沒有權限使用此指令。", ephemeral=True)
            return

        view = ConfirmClearView()
        await interaction.send("⚠️ 確定要清空所有的儲存資料嗎？ (請假、工作、會議紀錄、機器人設定)", view=view, ephemeral=True)

class ConfirmClearView(ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @ui.button(label="✅ 是", style=ButtonStyle.danger)
    async def confirm(self, button: ui.Button, interaction: Interaction):
        deleted_files = 0

        if not os.path.exists(DATA_DIR):
            await interaction.response.edit_message(content="⚠️ `data/` 資料夾不存在。", view=None)
            return

        for filename in os.listdir(DATA_DIR):
            file_path = os.path.join(DATA_DIR, filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    deleted_files += 1
                except Exception as e:
                    await interaction.response.edit_message(
                        content=f"❌ 刪除失敗：{filename}（{e}）", view=None
                    )
                    return

        await interaction.response.edit_message(content=f"✅ 已清空 {deleted_files} 筆資料。", view=None)

    @ui.button(label="❌ 否", style=ButtonStyle.secondary)
    async def cancel(self, button: ui.Button, interaction: Interaction):
        await interaction.response.edit_message(content="❎ 已取消清除資料操作。", view=None)

def setup(bot: commands.Bot):
    bot.add_cog(ClearData(bot))
