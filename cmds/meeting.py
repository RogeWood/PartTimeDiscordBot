import os
import json
from datetime import datetime, timedelta
from nextcord.ext import commands, tasks
from nextcord import Interaction, SlashOption, Embed, TextChannel
import nextcord

MEETING_FILE = "data/meeting.json"
CONFIG_FILE = "data/config.json"

def load_meeting_data():
    if os.path.exists(MEETING_FILE):
        with open(MEETING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_meeting_data(data):
    with open(MEETING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

class Meeting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.meeting_reminder.start()

    def cog_unload(self):
        self.meeting_reminder.cancel()

    @nextcord.slash_command(name="meeting", description="會議管理功能")
    async def meeting(self, interaction: Interaction):
        pass

    @meeting.subcommand(name="add", description="新增單次會議")
    async def add_meeting(
        self,
        interaction: Interaction,
        name: str = SlashOption(name="名稱", description="會議名稱", required=True),
        year: int = SlashOption(name="年", description="西元年", required=True),
        month: int = SlashOption(name="月", description="月份", required=True),
        day: int = SlashOption(name="日", description="日期", required=True),
        hour: int = SlashOption(name="時", description="24小時制", required=True),
        minute: int = SlashOption(name="分", description="分鐘", required=True),
    ):
        try:
            meeting_time = datetime(year, month, day, hour, minute)
        except ValueError:
            await interaction.response.send_message("❌ 無效的時間格式", ephemeral=True)
            return

        data = load_meeting_data()
        data.append({
            "name": name,
            "datetime": meeting_time.isoformat()
        })
        save_meeting_data(data)

        await interaction.response.send_message(f"✅ 已新增會議：{name}，時間：{meeting_time.strftime('%Y-%m-%d %H:%M')}")

    @meeting.subcommand(name="set_channel", description="設定會議提醒訊息的頻道")
    async def set_channel(
        self,
        interaction: Interaction,
        channel: TextChannel = SlashOption(name="頻道", description="提醒要發送的頻道", required=True)
    ):
        config = load_config()
        config["meeting_channel_id"] = channel.id
        save_config(config)
        await interaction.response.send_message(f"✅ 已設定提醒頻道為 {channel.mention}")

    @meeting.subcommand(name="set_reminders", description="開啟或關閉提醒設定")
    async def set_reminders(
        self,
        interaction: Interaction,
        enable_4h: bool = SlashOption(name="提前4小時提醒", description="是否啟用", required=True),
        enable_10m: bool = SlashOption(name="提前10分鐘提醒", description="是否啟用", required=True)
    ):
        config = load_config()
        config["remind_4h"] = enable_4h
        config["remind_10m"] = enable_10m
        save_config(config)
        await interaction.response.send_message(f"✅ 提醒設定更新完成")

    @tasks.loop(minutes=1)
    async def meeting_reminder(self):
        now = datetime.now()
        data = load_meeting_data()
        config = load_config()
        channel_id = config.get("meeting_channel_id")
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        new_data = []
        for meeting in data:
            meeting_time = datetime.fromisoformat(meeting["datetime"])
            time_until = (meeting_time - now).total_seconds()

            if config.get("remind_4h") and 14340 <= time_until <= 14520:  # 約等於4小時
                await channel.send(f"@everyone ⏰提醒：今天有會議「{meeting['name']}」，時間 {meeting_time.strftime('%H:%M')}")
            elif config.get("remind_10m") and 540 <= time_until <= 660:  # 約等於10分鐘
                await channel.send(f"@everyone ⏰提醒：會議「{meeting['name']}」即將在10分鐘內開始！")

            if time_until > 0:
                new_data.append(meeting)

        save_meeting_data(new_data)

    @meeting_reminder.before_loop
    async def before_reminder(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Meeting(bot))
