import os
import json
from datetime import datetime, timezone, timedelta
from nextcord.ext import commands, tasks
from nextcord import Interaction, SlashOption, Embed, TextChannel, Color, slash_command

# 檔案與時區設置
tz = timezone(timedelta(hours=8))  # 台北時區
MEETING_PATH = "data/meeting.json"
CONFIG_PATH = "data/config.json"


def load_meeting_data():
    default = {"single": {}, "weekly": {}}
    if os.path.exists(MEETING_PATH):
        with open(MEETING_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("single", {})
        data.setdefault("weekly", {})
        # 相容舊版格式：將 string 轉為 dict
        for name, info in list(data["single"].items()):
            if isinstance(info, str):
                data["single"][name] = {"time": info, "description": ""}
        return data
    return default


def save_meeting_data(data):
    os.makedirs(os.path.dirname(MEETING_PATH), exist_ok=True)
    with open(MEETING_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


class Meeting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.meeting_reminder.start()

    def cog_unload(self):
        self.meeting_reminder.cancel()

    @slash_command(name="meeting", description="會議管理功能", force_global=True)
    async def meeting(self, interaction: Interaction):
        await interaction.response.send_message(
            "請使用子指令：add, weekly, remove_single, remove_weekly, list, set_channel, set_reminder, clear_reminders",
            ephemeral=True
        )

    @meeting.subcommand(name="add", description="新增單次會議")
    async def add_meeting(
        self,
        interaction: Interaction,
        name: str = SlashOption(name="名稱", description="會議名稱", required=True),
        datetime_str: str = SlashOption(name="datetime", description="會議時間 (YYYY-MM-DD HH:MM)", required=True),
        description: str = SlashOption(name="description", description="會議說明", required=False, default="")
    ):
        try:
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            meeting_time = dt.replace(tzinfo=tz)
        except Exception:
            await interaction.response.send_message("❌ 時間格式錯誤，請使用 YYYY-MM-DD HH:MM。", ephemeral=True)
            return

        data = load_meeting_data()
        data["single"][name] = {"time": meeting_time.isoformat(), "description": description}
        save_meeting_data(data)
        await interaction.response.send_message(
            f"✅ 已新增單次會議「{name}」，時間：{meeting_time.strftime('%Y-%m-%d %H:%M')}，說明：{description or '無'}"
        )

    @meeting.subcommand(name="weekly", description="新增每週固定會議")
    async def add_weekly_meeting(
        self,
        interaction: Interaction,
        weekday: str = SlashOption(name="星期", description="星期幾", choices=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]),
        time_str: str = SlashOption(name="time", description="時間 (HH:MM)", required=True),
        name: str = SlashOption(name="名稱", description="會議名稱", required=True),
        description: str = SlashOption(name="description", description="會議說明", required=False, default="")
    ):
        try:
            h, m = map(int, time_str.split(':'))
            if not (0 <= h < 24 and 0 <= m < 60): raise ValueError
        except Exception:
            await interaction.response.send_message("❌ 時間格式錯誤，請使用 HH:MM。", ephemeral=True)
            return

        data = load_meeting_data()
        data["weekly"][name] = {"weekday": weekday, "hour": h, "minute": m, "description": description}
        save_meeting_data(data)
        await interaction.response.send_message(
            f"✅ 已設定每週 {weekday} {h:02}:{m:02} 的會議「{name}」，說明：{description or '無'}"
        )

    @meeting.subcommand(name="remove_single", description="刪除單次會議")
    async def remove_single(
        self, interaction: Interaction,
        name: str = SlashOption(name="名稱", description="要刪除的會議名稱", required=True)
    ):
        data = load_meeting_data()
        if name in data["single"]:
            del data["single"][name]
            save_meeting_data(data)
            await interaction.response.send_message(f"✅ 已刪除單次會議「{name}」。")
        else:
            await interaction.response.send_message(f"❌ 找不到單次會議「{name}」。", ephemeral=True)

    @meeting.subcommand(name="remove_weekly", description="關閉每週會議")
    async def remove_weekly(
        self, interaction: Interaction,
        name: str = SlashOption(name="名稱", description="要關閉的每週會議名稱", required=True)
    ):
        data = load_meeting_data()
        if name in data["weekly"]:
            del data["weekly"][name]
            save_meeting_data(data)
            await interaction.response.send_message(f"✅ 已關閉每週會議「{name}」。")
        else:
            await interaction.response.send_message(f"❌ 找不到每週會議「{name}」。", ephemeral=True)

    @meeting.subcommand(name="list", description="顯示所有會議")
    async def list_meetings(self, interaction: Interaction):
        data = load_meeting_data()
        single = data.get("single", {})
        weekly = data.get("weekly", {})
        if not single and not weekly:
            await interaction.response.send_message("📭 目前沒有任何會議。")
            return

        embed = Embed(title="📅 會議列表", color=Color.blue())
        if single:
            for name, info in sorted(single.items(), key=lambda x: x[1]["time"]):
                dt = datetime.fromisoformat(info["time"]).astimezone(tz).strftime("%Y-%m-%d %H:%M")
                desc = info.get("description", "")
                embed.add_field(name=name, value=f"🕒 單次會議：{dt}\n說明：{desc or '無'}", inline=False)
        if weekly:
            for name, info in sorted(weekly.items(), key=lambda x: (x[1]["weekday"], x[1]["hour"], x[1]["minute"])):
                wd = info["weekday"]
                desc = info.get("description", "")
                embed.add_field(name=name, value=f"🗓️ 每週：{wd} {info['hour']:02}:{info['minute']:02}\n說明：{desc or '無'}", inline=False)
        await interaction.response.send_message(embed=embed)

    @meeting.subcommand(name="set_channel", description="設定會議提醒頻道")
    async def set_channel(self, interaction: Interaction,
        channel: TextChannel = SlashOption(name="頻道", description="提醒要發送的頻道", required=True)
    ):
        config = load_config()
        config["meeting_channel_id"] = channel.id
        save_config(config)
        await interaction.response.send_message(f"✅ 已設定提醒頻道為 {channel.mention}")

    @meeting.subcommand(name="set_reminder", description="設定提前提醒時間")
    async def set_reminder(self, interaction: Interaction,
        hours: int = SlashOption(name="小時", description="幾小時前提醒", required=True),
        minutes: int = SlashOption(name="分鐘", description="幾分鐘前提醒", required=True)
    ):
        config = load_config()
        total = hours * 3600 + minutes * 60
        reminders = config.get("reminder_minutes", [])
        if total not in reminders:
            reminders.append(total)
            config["reminder_minutes"] = reminders
            save_config(config)
        await interaction.response.send_message(f"✅ 已設定提前 {hours} 小時 {minutes} 分鐘提醒。")

    @meeting.subcommand(name="clear_reminders", description="關閉所有會議提醒")
    async def clear_reminders(self, interaction: Interaction):
        config = load_config()
        config["reminder_minutes"] = []
        save_config(config)
        await interaction.response.send_message("✅ 所有會議提醒已關閉。")

    @tasks.loop(minutes=1)
    async def meeting_reminder(self):
        now = datetime.now(tz)
        data = load_meeting_data()
        config = load_config()
        channel_id = config.get("meeting_channel_id")
        if not channel_id:
            return
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
        reminders = config.get("reminder_minutes", [])

        new_data = {"single": {}, "weekly": {}}
        # 處理單次會議
        for name, info in data["single"].items():
            meeting_time = datetime.fromisoformat(info["time"]).astimezone(tz)
            diff = (meeting_time - now).total_seconds()
            for sec in reminders:
                if sec - 60 <= diff <= sec + 60:
                    desc = info.get("description", "")
                    await channel.send(f"@everyone ⏰ 提醒：單次會議「{name}」將在 {int(sec//3600)} 小時{int((sec%3600)//60)} 分鐘後舉行（{meeting_time.strftime('%H:%M')}），說明：{desc or '無'}")
            if diff > 0:
                new_data["single"][name] = info
        # 處理每週會議
        today = now.strftime("%A")
        for name, info in data["weekly"].items():
            if info.get("weekday") == today:
                meeting_time = now.replace(hour=info["hour"], minute=info["minute"], second=0, microsecond=0)
                diff = (meeting_time - now).total_seconds()
                for sec in reminders:
                    if sec - 60 <= diff <= sec + 60:
                        desc = info.get("description", "")
                        await channel.send(f"@everyone ⏰ 提醒：每週會議「{name}」將在 {int(sec//3600)} 小時{int((sec%3600)//60)} 分鐘後舉行（{meeting_time.strftime('%H:%M')}），說明：{desc or '無'}")
            new_data["weekly"][name] = info
        save_meeting_data(new_data)

    @meeting_reminder.before_loop
    async def before_meeting_reminder(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(Meeting(bot))
