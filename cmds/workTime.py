import os
import json
from typing import Optional
from nextcord.ext import commands
from nextcord import Interaction, slash_command, ui, Embed, Member, ButtonStyle
from datetime import datetime, timezone, timedelta

tz = timezone(timedelta(hours=8))  # 台灣時區
WORK_LOG_PATH = "data/work_logs.json"
CHECKIN_PATH = "data/checkin_data.json"

class WorkTime(commands.Cog, name="WorkTime"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.work_logs = self.load_json(WORK_LOG_PATH)
        self.checkin_data = self.load_checkin_data()

    def load_json(self, path):
        if not os.path.exists("data"):
            os.makedirs("data")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_checkin_data(self):
        raw_data = self.load_json(CHECKIN_PATH)
        # 將時間字串轉回 datetime
        parsed = {}
        for user_id, time_str in raw_data.items():
            parsed[user_id] = datetime.fromisoformat(time_str)
        return parsed

    def save_checkin_data(self):
        # 將 datetime 轉為 ISO 格式字串儲存
        to_save = {user_id: dt.isoformat() for user_id, dt in self.checkin_data.items()}
        self.save_json(CHECKIN_PATH, to_save)

    def save_work_logs(self):
        self.save_json(WORK_LOG_PATH, self.work_logs)

    @slash_command(name="checkin", description="上班打卡", force_global=True)
    async def checkin(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        now = datetime.now(tz)

        if user_id in self.checkin_data:
            await interaction.send(f"你已在 {self.checkin_data[user_id].strftime('%H:%M:%S')} 打過卡了。")
        else:
            self.checkin_data[user_id] = now
            self.save_checkin_data()
            await interaction.send(f"✅ 上班打卡成功！時間：{now.strftime('%H:%M:%S')}")

    @slash_command(name="checkout", description="下班打卡並儲存工作時長", force_global=True)
    async def checkout(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        now = datetime.now(tz)

        if user_id not in self.checkin_data:
            await interaction.send("⚠️ 尚未上班打卡，請先使用 `/checkin`。")
            return

        start_time = self.checkin_data.pop(user_id)
        self.save_checkin_data()

        duration = now - start_time
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = f"{int(hours)} 小時 {int(minutes)} 分 {int(seconds)} 秒"
        date_str = start_time.strftime("%Y-%m-%d")

        self.work_logs.setdefault(user_id, []).append((date_str, duration_str))
        self.save_work_logs()

        await interaction.send(
            f"🕔 下班打卡成功！時間：{now.strftime('%H:%M:%S')}\n"
            f"🧾 今日工作時長：{duration_str}"
        )

    @slash_command(name="work_log", description="查看工作紀錄", force_global=True)
    async def work_log(self, interaction: Interaction, user: Optional[Member] = None):
        target = user or interaction.user
        user_id = str(target.id)
        logs = self.work_logs.get(user_id, [])

        if not logs:
            await interaction.send(f"📭 {target.display_name} 目前沒有任何工作紀錄。")
            return

        embed = Embed(title=f"📒 {target.display_name} 的工作紀錄", color=0x00BFFF)
        embed.set_thumbnail(url = interaction.user.avatar.url)
        for date_str, duration_str in logs:
            embed.add_field(name=date_str, value=duration_str, inline=False)

        await interaction.send(embed=embed)

    @slash_command(name="working_duration", description="查看目前已工作多久", force_global=True)
    async def working_duration(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        now = datetime.now(tz)

        if user_id not in self.checkin_data:
            await interaction.send("⚠️ 你尚未打上班卡，請先使用 `/checkin`。")
            return

        start_time = self.checkin_data[user_id]
        duration = now - start_time

        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = f"{int(hours)} 小時 {int(minutes)} 分 {int(seconds)} 秒"

        await interaction.send(f"⏱️ 你目前已工作：**{duration_str}**")

    @slash_command(name="clear_work_log", description="清除工作紀錄", force_global=True)
    async def clear_work_log(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        logs = self.work_logs.get(user_id)

        if not logs:
            await interaction.send("⚠️ 沒有可清除的紀錄。")
            return

        view = ConfirmClearView(self, user_id)
        await interaction.send("⚠️ 確定要清除你的所有工作紀錄嗎？", view=view)

class ConfirmClearView(ui.View):
    def __init__(self, cog: WorkTime, user_id: str):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
    
    @ui.button(label="是", style=ButtonStyle.danger)
    async def confirm(self, button: ui.Button, interaction: Interaction):
        self.cog.work_logs.pop(self.user_id, None)
        self.cog.save_work_logs()
        await interaction.response.edit_message(content="✅ 已成功清除所有工作紀錄！", view=None)
    @ui.button(label="否", style=ButtonStyle.secondary)
    async def cancel(self, button: ui.Button, interaction: Interaction):
        await interaction.response.edit_message(content="❌ 已取消清除。", view=None)

def setup(bot: commands.Bot):
    bot.add_cog(WorkTime(bot))
