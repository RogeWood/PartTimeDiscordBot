import json
import os
from datetime import datetime, timezone, timedelta

from nextcord.ext import commands
from nextcord import slash_command, Interaction, SlashOption, Member, Embed, Colour

# 資料檔位置
LEAVE_FILE = "data/leave.json"
# 台北時區
tz = timezone(timedelta(hours=+8))
# 年度選項
CURRENT_YEAR = datetime.now(tz).year
YEARS = [str(CURRENT_YEAR + i) for i in range(3)]  # 今年, 今年+1, 今年+2


def load_leave_data():
    if os.path.exists(LEAVE_FILE):
        with open(LEAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_leave_data(data):
    os.makedirs(os.path.dirname(LEAVE_FILE), exist_ok=True)
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

    @leave.subcommand(name="add", description="新增請假紀錄")
    async def add(
        self,
        interaction: Interaction,
        name: str = SlashOption(name="name", description="請假名稱", required=True),
        description: str = SlashOption(name="description", description="請假說明", required=True),
        year: str = SlashOption(name="year", description="西元年", choices=YEARS, required=True),
        month: int = SlashOption(name="month", description="月份", choices=list(range(1,13)), required=True),
        day: int = SlashOption(name="day", description="日期", required=True, min_value=1, max_value=31),
        hour: int = SlashOption(name="hour", description="小時 (0-23)", required=True, min_value=0, max_value=23),
        minute: int = SlashOption(name="minute", description="分鐘 (0-59)", required=True, min_value=0, max_value=59),
        user: Member = SlashOption(name="user", description="請假使用者 (Tag)，不填則預設自己", required=False, default=None)
    ):
        target = user or interaction.user
        try:
            d = datetime(int(year), month, day, hour, minute, tzinfo=tz)
        except ValueError:
            await interaction.response.send_message("❌ 請假時間不正確，請確認輸入。", ephemeral=True)
            return
        if d < datetime.now(tz):
            await interaction.response.send_message("❌ 請假時間已過，無法新增。", ephemeral=True)
            return
        self.leave_data.append({
            "user_id": str(target.id),
            "name": name,
            "time": d.isoformat(),
            "description": description
        })
        save_leave_data(self.leave_data)
        await interaction.response.send_message(
            f"✅ 已新增請假：{target.mention}，名稱：{name}，時間：{d.strftime('%Y-%m-%d %H:%M')}，說明：{description}"
        )

    @leave.subcommand(name="list", description="列出請假紀錄")
    async def list(
        self,
        interaction: Interaction,
        user: Member = SlashOption(name="user", description="指定使用者 (Tag)，不填則顯示全部", required=False, default=None)
    ):
        recs = [r for r in self.leave_data if not user or r["user_id"] == str(user.id)]
        if not recs:
            await interaction.response.send_message("目前沒有符合條件的請假紀錄。", ephemeral=True)
            return
        embed = Embed(title="📋 請假紀錄", color=Colour.blue())
        for i, rec in enumerate(recs, start=1):
            member = interaction.guild.get_member(int(rec['user_id']))
            mention = member.mention if member else f"<@{rec['user_id']}>"
            dt = datetime.fromisoformat(rec['time']).astimezone(tz).strftime('%Y-%m-%d %H:%M')
            embed.add_field(
                name=f"{i}. {mention} — {rec['name']} @ {dt}",
                value=f"說明：{rec['description']}", inline=False
            )
        await interaction.response.send_message(embed=embed)

    @leave.subcommand(name="remove", description="刪除指定請假紀錄")
    async def remove(
        self,
        interaction: Interaction,
        date: str = SlashOption(name="date", description="請假日期 (選擇)", autocomplete=True, required=True),
        user: Member = SlashOption(name="user", description="指定使用者 (Tag)，不填則預設自己", required=False, default=None)
    ):
        target = user or interaction.user
        for i, rec in enumerate(self.leave_data):
            if rec["user_id"] == str(target.id) and rec["time"][:10] == date:
                self.leave_data.pop(i)
                save_leave_data(self.leave_data)
                member = interaction.guild.get_member(int(rec['user_id']))
                mention = member.mention if member else f"<@{rec['user_id']}>"
                await interaction.response.send_message(
                    f"🗑 已刪除 {mention} 的請假紀錄：{rec['name']} @ {datetime.fromisoformat(rec['time']).astimezone(tz).strftime('%Y-%m-%d %H:%M')}"
                )
                return
        await interaction.response.send_message("❌ 找不到對應的請假紀錄，請確認使用者與日期是否正確。", ephemeral=True)

    @remove.on_autocomplete("date")
    async def remove_date_autocomplete(self, interaction: Interaction, current: str):
        user_opt = interaction.options.get('user')
        uid = int(user_opt) if user_opt else interaction.user.id
        dates = sorted({rec["time"][:10] for rec in self.leave_data if rec["user_id"] == str(uid)})
        suggestions = [d for d in dates if current in d][:25]
        await interaction.response.send_autocomplete(suggestions)


def setup(bot):
    bot.add_cog(Leave(bot))
