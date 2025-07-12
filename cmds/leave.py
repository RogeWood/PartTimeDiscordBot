import json
import os
from datetime import datetime
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, Embed
import nextcord

LEAVE_FILE = "data/leave.json"

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

    @nextcord.slash_command(name="leave", description="請假功能")
    async def leave(self, interaction: Interaction):
        pass  # 留空即可，子指令用

    @leave.subcommand(name="add", description="新增請假記錄")
    async def add(
        self,
        interaction: Interaction,
        year: int = SlashOption(
            name="年", 
            description="選擇年份",
            choices=[datetime.now().year + i for i in range(3)],
            required=True
        ),
        month: int = SlashOption(
            name="月",
            description="選擇月份",
            choices=list(range(1, 13)),
            required=True
        ),
        day: int = SlashOption(
            name="日",
            description="請輸入日 (1~31)",
            required=True
        ),
        reason: str = SlashOption(
            name="理由", 
            description="可選填請假理由",
            required=False, 
            default=""
        ),
    ):
        # 範圍檢查
        if not (1 <= day <= 31):
            await interaction.response.send_message("❌ 請輸入 1~31 之間的日期。", ephemeral=True)
            return

        # 日期檢查
        try:
            leave_date = datetime(year, month, day)
        except ValueError:
            await interaction.response.send_message("❌ 請輸入有效的日期（例如 2 月不能超過 29 日）", ephemeral=True)
            return

        # 是否為未來
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if leave_date < today:
            await interaction.response.send_message("❌ 請假日期已過，請選擇未來的日期。", ephemeral=True)
            return

        # 儲存資料
        data = load_leave_data()
        data.append({
            "user_id": interaction.user.id,
            "user_name": interaction.user.name,
            "user_avatar": interaction.user.display_avatar.url,
            "date": leave_date.strftime("%Y-%m-%d"),
            "reason": reason.strip() or "（未填寫）"
        })
        save_leave_data(data)

        await interaction.response.send_message(f"✅ 已成功登記 {leave_date.strftime('%Y-%m-%d')} 的請假！")

    @leave.subcommand(name="list", description="列出所有請假記錄")
    async def list(self, interaction: Interaction):
        data = load_leave_data()
        if not data:
            await interaction.response.send_message("目前沒有任何請假記錄。", ephemeral=True)
            return

        embed = Embed(title="📅 請假列表", color=nextcord.Color.blue())

        for record in data:
            user_mention = f"<@{record['user_id']}>"
            date_str = f"**{record['date']}**"
            reason = record['reason']
            embed.add_field(
                name=f"{user_mention}",
                value=f"{date_str}\n{reason}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(Leave(bot))
