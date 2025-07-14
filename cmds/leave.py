# cmds/leave.py

import json
import os
from datetime import datetime, timezone, timedelta

from nextcord.ext import commands
from nextcord import slash_command, Interaction, SlashOption, TextChannel, Embed, Colour

# 資料檔位置
LEAVE_FILE  = "data/leave.json"

# 台北時區
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

    @leave.subcommand(
        name="add",
        description="新增一筆請假紀錄"
    )
    async def add(
        self,
        interaction: Interaction,
        user: str = SlashOption(
            name="user",
            description="請假使用者（Tag 或 ID）",
            required=True
        ),
        year: int = SlashOption(
            name="year",
            description="年份",
            required=True,
            choices={str(y): y for y in [datetime.now(tz).year, datetime.now(tz).year + 1, datetime.now(tz).year + 2]}
        ),
        month: int = SlashOption(
            name="month",
            description="月份 (1–12)",
            required=True,
            min_value=1,
            max_value=12
        ),
        day: int = SlashOption(
            name="day",
            description="日期 (1–31)",
            required=True,
            min_value=1,
            max_value=31
        ),
        reason: str = SlashOption(
            name="reason",
            description="請假理由（可不填）",
            required=False
        ),
        channel: TextChannel = SlashOption(
            name="channel",
            description="要公告的頻道 (不填則使用當前頻道)",
            required=False
        )
    ):
        date_str = f"{year}-{month:02d}-{day:02d}"
        record = {
            "user_name": user,
            "date": date_str,
            "reason": reason or ""
        }
        self.leave_data.append(record)
        save_leave_data(self.leave_data)

        target = channel or interaction.channel
        await interaction.response.send_message(
            f"✅ 已新增 {user} 的請假：{date_str}" + (f"\n理由：{reason}" if reason else ""),
            channel=target
        )

    @leave.subcommand(
        name="list",
        description="列出所有請假紀錄"
    )
    async def _list(self, interaction: Interaction):
        if not self.leave_data:
            await interaction.response.send_message("目前沒有任何請假紀錄。")
            return

        embed = Embed(title="📋 請假紀錄", colour=Colour.blue())
        for i, rec in enumerate(self.leave_data, start=1):
            title = f"{i}. {rec['user_name']} — {rec['date']}"
            value = f"理由：{rec['reason']}" if rec.get("reason") else "理由：無"
            embed.add_field(name=title, value=value, inline=False)

        await interaction.response.send_message(embed=embed)

    @leave.subcommand(
        name="remove",
        description="刪除指定編號的請假紀錄"
    )
    async def remove(
        self,
        interaction: Interaction,
        index: int = SlashOption(
            name="index",
            description="要刪除的紀錄編號 (從 `/leave list` 中看到的序號)",
            required=True,
            min_value=1
        )
    ):
        if 1 <= index <= len(self.leave_data):
            rec = self.leave_data.pop(index - 1)
            save_leave_data(self.leave_data)
            await interaction.response.send_message(
                f"🗑 已刪除 {rec['user_name']} 的 {rec['date']} 請假紀錄。"
            )
        else:
            await interaction.response.send_message(
                "❌ 指定的編號不存在，請重新確認後再試。", 
                ephemeral=True
            )

def setup(bot):
    bot.add_cog(Leave(bot))
