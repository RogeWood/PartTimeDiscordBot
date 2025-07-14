from nextcord.ext import commands
from nextcord import slash_command, Interaction, SlashOption, Embed, Colour
import json, os
from datetime import datetime, timezone, timedelta

LEAVE_FILE = "data/leave.json"
tz = timezone(timedelta(hours=+8))

def load_leave_data():
    if os.path.exists(LEAVE_FILE):
        with open(LEAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_leave_data(data):
    with open(LEAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leave_data = load_leave_data()

    @slash_command(name="leave", description="管理請假紀錄 (add, list, remove)", force_global=True)
    async def leave(self, interaction: Interaction):
        await interaction.response.send_message(
            "請使用 `/leave add`、`/leave list` 或 `/leave remove`。", 
            ephemeral=True
        )

    # ... add/list 省略 ...

    @leave.subcommand(
        name="remove",
        description="刪除指定使用者的請假紀錄"
    )
    async def remove(
        self,
        interaction: Interaction,
        user: str = SlashOption(
            name="user",
            description="請假使用者（Tag 或 ID）",
            required=True
        ),
        date: str = SlashOption(
            name="date",
            description="選擇請假日期",
            required=True,
            autocomplete=True
        )
    ):
        # 找出第一筆符合 user+date 的紀錄並刪除
        for i, rec in enumerate(self.leave_data):
            if rec["user_name"] == user and rec["date"] == date:
                self.leave_data.pop(i)
                save_leave_data(self.leave_data)
                await interaction.response.send_message(
                    f"🗑 已刪除 {user} 的 {date} 請假紀錄。"
                )
                return
        # 若找不到
        await interaction.response.send_message(
            "❌ 找不到對應的請假紀錄，請確認使用者與日期是否正確。",
            ephemeral=True
        )

    @remove.on_autocomplete("date")
    async def remove_date_autocomplete(
        self,
        interaction: Interaction,
        date: str,
        user: str
    ):
        """
        當使用者在 `date` 欄位輸入內容時，
        動態回傳該使用者所有請假日期，並過濾 substring。
        """
        # 取出該使用者的所有請假日期
        dates = [rec["date"] for rec in self.leave_data if rec["user_name"] == user]
        # 過濾並限制最多 25 個選項
        suggestions = [d for d in dates if date in d][:25]
        await interaction.response.send_autocomplete(suggestions)

def setup(bot):
    bot.add_cog(Leave(bot))
