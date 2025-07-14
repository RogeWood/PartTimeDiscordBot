# cmds/leave.py

import json
import os
from datetime import datetime, timezone, timedelta

from nextcord.ext import commands
from nextcord import slash_command, Interaction, SlashOption, TextChannel, Embed, Colour

# 資料檔位置
LEAVE_FILE = "data/leave.json"

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

    @slash_command(
        name="leave",
        description="管理請假紀錄 (add, list, remove)",
        force_global=True
    )
    async def leave(self, interaction: Interaction):
        await interaction.response.send_message(
            "請使用 `/leave add`、`/leave list` 或 `/leave remove`。", 
            ephemeral=True
        )

    @leave.subcommand(
        name="add",
        description="新增請假紀錄"
    )
    async def add(
        self,
        interaction: Interaction,
        user: str = SlashOption(
            name="user",
            description="請假使用者 (Tag 或 ID)",
            required=True
        ),
        date: str = SlashOption(
            name="date",
            description="請假日期 (YYYY-MM-DD)",
            required=True
        ),
        reason: str = SlashOption(
            name="reason",
            description="請假理由",
            required=False,
            default=""
        )
    ):
        # 驗證日期格式
        try:
            d = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            await interaction.response.send_message(
                "❌ 日期格式錯誤，請使用 YYYY-MM-DD。", 
                ephemeral=True
            )
            return
        # 檢查日期未過
        if d < datetime.now(tz).date():
            await interaction.response.send_message(
                "❌ 請假日期已過，無法新增。", 
                ephemeral=True
            )
            return
        # 新增紀錄
        self.leave_data.append({
            "user_name": user,
            "date": date,
            "reason": reason
        })
        save_leave_data(self.leave_data)
        await interaction.response.send_message(
            f"✅ 已新增 {user} 的 {date} 請假紀錄。理由：{reason or '無'}"
        )

    @leave.subcommand(
        name="list",
        description="列出請假紀錄"
    )
    async def list(
        self,
        interaction: Interaction,
        user: str = SlashOption(
            name="user",
            description="指定使用者 (Tag 或 ID)，不填則顯示全部",
            required=False,
            default=""
        )
    ):
        # 過濾紀錄
        recs = [
            r for r in self.leave_data
            if not user or r["user_name"] == user
        ]
        if not recs:
            await interaction.response.send_message(
                "目前沒有符合條件的請假紀錄。", 
                ephemeral=True
            )
            return
        # 建立 Embed
        embed = Embed(title="📋 請假紀錄", color=Colour.blue())
        for i, rec in enumerate(recs, start=1):
            embed.add_field(
                name=f"{i}. {rec['user_name']} — {rec['date']}",
                value=f"理由：{rec['reason'] or '無'}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @leave.subcommand(
        name="remove",
        description="刪除指定使用者的請假紀錄"
    )
    async def remove(
        self,
        interaction: Interaction,
        user: str = SlashOption(
            name="user",
            description="請假使用者 (Tag 或 ID)",
            required=True
        ),
        date: str = SlashOption(
            name="date",
            description="選擇請假日期",
            required=True,
            autocomplete=True
        )
    ):
        # 找到符合 user+date 的第一筆並刪除
        for i, rec in enumerate(self.leave_data):
            if rec["user_name"] == user and rec["date"] == date:
                self.leave_data.pop(i)
                save_leave_data(self.leave_data)
                await interaction.response.send_message(
                    f"🗑 已刪除 {user} 的 {date} 請假紀錄。"
                )
                return
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
        # 收集該使用者的所有請假日期
        dates = [
            rec["date"]
            for rec in self.leave_data
            if rec["user_name"] == user
        ]
        # 過濾並限制 25 筆
        suggestions = [d for d in dates if date in d][:25]
        await interaction.response.send_autocomplete(suggestions)

def setup(bot):
    bot.add_cog(Leave(bot))
