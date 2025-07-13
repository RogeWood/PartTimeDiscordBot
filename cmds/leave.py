import json
import os
from datetime import datetime
from nextcord.ext import commands, tasks
from nextcord import Interaction, SlashOption, Embed, TextChannel
import nextcord

LEAVE_FILE = "data/leave.json"
CONFIG_FILE = "data/config.json"

def load_leave_data():
    if os.path.exists(LEAVE_FILE):
        with open(LEAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_leave_data(data):
    with open(LEAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_leave_notifier.start()

    def cog_unload(self):
        self.daily_leave_notifier.cancel()

    @tasks.loop(minutes=20)
    async def daily_leave_notifier(self):
        now = datetime.now()
        if not (now.hour == 8 and 0 <= now.minute <= 1):
            return

        today_str = now.strftime("%Y-%m-%d")
        config = load_config()

        if config.get("last_leave_notify") == today_str:
            return  # 今天已經提醒過

        channel_id = config.get("leave_announcement_channel")
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        data = load_leave_data()
        today_leaves = [d for d in data if d["date"] == today_str]
        if not today_leaves:
            return

        embed = Embed(title="📢 今日請假通知", color=nextcord.Color.orange())
        for record in today_leaves:
            embed.add_field(
                name=record["user_name"],
                value=f"📝 {record['reason']}",
                inline=False
            )
        await channel.send(embed=embed)

        config["last_leave_notify"] = today_str
        save_config(config)


    @daily_leave_notifier.before_loop
    async def before_notifier(self):
        await self.bot.wait_until_ready()

    @nextcord.slash_command(name="leave", description="請假功能")
    async def leave(self, interaction: Interaction):
        pass

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
        if not (1 <= day <= 31):
            await interaction.response.send_message("❌ 請輸入 1~31 之間的日期。", ephemeral=True)
            return

        try:
            leave_date = datetime(year, month, day)
        except ValueError:
            await interaction.response.send_message("❌ 請輸入有效的日期（例如 2 月不能超過 29 日）", ephemeral=True)
            return

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if leave_date < today:
            await interaction.response.send_message("❌ 請假日期已過，請選擇未來的日期。", ephemeral=True)
            return

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

        rows = []
        for record in data:
            member = interaction.guild.get_member(record["user_id"])
            display_name = member.display_name if member else record["user_name"]
            rows.append((record["date"], display_name, record["reason"]))


        rows.sort(key=lambda r: r[0])

        header = f"`{'日期':<12} {'請假人':<12} 理由`"
        lines = [header]
        for date, name, reason in rows:
            short_reason = reason[:30] + "…" if len(reason) > 30 else reason
            line = f"`{date:<12} {name:<12} {short_reason}`"
            lines.append(line)

        embed = Embed(title="📅 請假列表", color=nextcord.Color.blue())
        embed.description = "\n".join(lines)

        await interaction.response.send_message(embed=embed)

    @leave.subcommand(name="set_channel", description="設定請假通知要發送的頻道")
    async def set_channel(
        self,
        interaction: Interaction,
        channel: TextChannel = SlashOption(
            name="頻道",
            description="選擇發送通知的頻道",
            required=True
        )
    ):
        config = load_config()
        config["leave_announcement_channel"] = channel.id
        save_config(config)
        await interaction.response.send_message(f"✅ 已設定通知頻道為 {channel.mention}")

    @leave.subcommand(name="clear", description="清除指定使用者的請假紀錄（預設為自己）")
    async def clear(
        self,
        interaction: Interaction,
        user: nextcord.User = SlashOption(
            name="使用者",
            description="要清除的請假使用者，預設為自己",
            required=False,
            default=None
        )
    ):
        target_user = user or interaction.user
        data = load_leave_data()
        original_len = len(data)
        data = [record for record in data if record["user_id"] != target_user.id]
        save_leave_data(data)
        removed = original_len - len(data)

        await interaction.response.send_message(
            f"🧹 已清除 {target_user.mention} 的請假紀錄（共 {removed} 筆）。"
        )

    @leave.subcommand(name="clear_all", description="❗ 清除所有請假紀錄（僅限管理員）")
    async def clear_all(self, interaction: Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ 你沒有權限執行此指令。", ephemeral=True)
            return

        save_leave_data([])
        await interaction.response.send_message("⚠️ 已清除所有請假紀錄。")

def setup(bot):
    bot.add_cog(Leave(bot))
