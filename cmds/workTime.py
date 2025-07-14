import os
import json
from typing import Optional
from datetime import datetime, timezone, timedelta
from nextcord.ext import commands
from nextcord import Interaction, TextChannel, ui, Embed, ButtonStyle, slash_command
import math

# 時區與檔案路徑設置
tz = timezone(timedelta(hours=8))  # 台灣時區
WORK_LOG_PATH = "data/work_logs.json"
CHECKIN_PATH = "data/checkin_data.json"
CONFIG_PATH = "data/work_config.json"


def load_json(path: str, default):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default


def save_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class WorkTime(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = load_json(CONFIG_PATH, {})
        self.checkin_data = load_json(CHECKIN_PATH, {})
        self.work_logs = load_json(WORK_LOG_PATH, [])

        # 確保 work_logs 為 list，並修正舊版 dict 格式
        if not isinstance(self.work_logs, list):
            self.work_logs = []
            save_json(WORK_LOG_PATH, self.work_logs)

    def get_channel_obj(self, guild_id: int) -> Optional[TextChannel]:
        cid = self.config.get(str(guild_id))
        return self.bot.get_channel(cid) if cid else None

    @slash_command(name="work", description="打卡功能", force_global=True)
    async def work(self, interaction: Interaction):
        await interaction.response.send_message(
            "請使用子指令：/work set_channel, checkin, checkout, duration, menu", ephemeral=True
        )

    @work.subcommand(name="set_channel", description="設定打卡訊息傳送的頻道")
    async def set_channel(self, interaction: Interaction, channel: TextChannel):
        self.config[str(interaction.guild_id)] = channel.id
        save_json(CONFIG_PATH, self.config)
        await interaction.response.send_message(
            f"已設定打卡訊息頻道為 {channel.mention}", ephemeral=True
        )

    @work.subcommand(name="checkin", description="上班打卡")
    async def checkin(self, interaction: Interaction):
        gid = str(interaction.guild_id)
        user = interaction.user

        if gid not in self.checkin_data:
            self.checkin_data[gid] = {}

        if str(user.id) in self.checkin_data[gid]:
            await interaction.response.send_message("您已經打過上班卡了！", ephemeral=True)
            return

        now = datetime.now(tz)
        self.checkin_data[gid][str(user.id)] = now.isoformat()
        save_json(CHECKIN_PATH, self.checkin_data)

        ch = self.get_channel_obj(interaction.guild_id)
        if ch:
            embed = Embed(
                title="✅ 上班打卡",
                description=f"{user.mention} 於 {now.strftime('%Y-%m-%d %H:%M:%S')} 上班打卡",
                color=0x00FF00
            )
            await ch.send(embed=embed)

        await interaction.response.send_message("✅ 上班打卡完成！", ephemeral=True)

    @work.subcommand(name="checkout", description="下班打卡並儲存工作時長")
    async def checkout(self, interaction: Interaction):
        gid = str(interaction.guild_id)
        user = interaction.user

        if gid not in self.checkin_data or str(user.id) not in self.checkin_data[gid]:
            await interaction.response.send_message("還沒打卡！", ephemeral=True)
            return

        checkin_time = datetime.fromisoformat(self.checkin_data[gid][str(user.id)])
        now = datetime.now(tz)
        delta = now - checkin_time
        total = int(delta.total_seconds())
        h, rem = divmod(total, 3600)
        m, _ = divmod(rem, 60)
        dur_str = f"{h}小時{m}分鐘"

        # 儲存並清除
        self.work_logs.append({
            "guild_id": interaction.guild_id,
            "user_id": user.id,
            "checkin": checkin_time.isoformat(),
            "checkout": now.isoformat(),
            "duration_seconds": total
        })
        save_json(WORK_LOG_PATH, self.work_logs)
        del self.checkin_data[gid][str(user.id)]
        save_json(CHECKIN_PATH, self.checkin_data)

        ch = self.get_channel_obj(interaction.guild_id)
        if ch:
            embed = Embed(
                title="🏁 下班打卡",
                description=(
                    f"{user.mention} 於 {now.strftime('%Y-%m-%d %H:%M:%S')} 下班打卡\n"
                    f"本次工作時長：**{dur_str}**"
                ),
                color=0xFF0000
            )
            await ch.send(embed=embed)

        # await interaction.response.send_message(
        #     f"🏁 下班打卡完成！本次工作時長：{dur_str}", ephemeral=True
        # )

    @work.subcommand(name="duration", description="查看目前已工作多久")
    async def duration(self, interaction: Interaction):
        gid = str(interaction.guild_id)
        user = interaction.user

        if gid not in self.checkin_data or str(user.id) not in self.checkin_data[gid]:
            await interaction.response.send_message("還沒打卡！", ephemeral=True)
            return

        checkin_time = datetime.fromisoformat(self.checkin_data[gid][str(user.id)])
        now = datetime.now(tz)
        delta = now - checkin_time
        total = int(delta.total_seconds())
        h, rem = divmod(total, 3600)
        m, _ = divmod(rem, 60)
        dur_str = f"{h}小時{m}分鐘"

        await interaction.response.send_message(f"⏱️ 您已工作：**{dur_str}**", ephemeral=True)

    @work.subcommand(name="menu", description="顯示打卡操作選單")
    async def menu(self, interaction: Interaction):
        ch = self.get_channel_obj(interaction.guild_id)
        if not ch:
            await interaction.response.send_message(
                "❌ 尚未設定打卡訊息頻道，請先使用 /work set_channel 設定。", ephemeral=True
            )
            return

        embed = Embed(
            title="📋 工作打卡選單",
            description="請點擊下方按鈕進行打卡或查詢當前工作時長",
            color=0x3498DB
        )
        view = WorkMenuView(self)

        await interaction.response.send_message(embed=embed, view=view)

    @work.subcommand(name="list", description="列出工作紀錄（支援分頁與加總）")
    async def list(self, interaction: Interaction):
        ch = self.get_channel_obj(interaction.guild_id)
        if not ch:
            await interaction.response.send_message(
                "❌ 尚未設定打卡訊息頻道，請先使用 /work set_channel 設定。", ephemeral=True
            )
            return
        embed = self.generate_worklist_embed(0)
        view = WorkListView(self, 0)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    def generate_worklist_embed(self, page: int) -> Embed:
        per_page = 20
        total = len(self.work_logs)
        title = f"📑 所有工作紀錄 (第 {page+1}/{math.ceil(total/per_page) or 1} 頁)"
        items = [
            f"{i+1}. <@{log['user_id']}>：{log['checkin'][:19].replace('T',' ')} → {log['checkout'][:19].replace('T',' ')}，{log['duration_seconds']//3600}小時{(log['duration_seconds']%3600)//60}分鐘"
            for i, log in enumerate(self.work_logs)
        ]
        start = page * per_page
        page_items = items[start:start+per_page] or ["（無資料）"]
        return Embed(title=title, description="\n".join(page_items), color=0x3498DB)

class WorkListView(ui.View):
    def __init__(self, cog: WorkTime, page: int):
        super().__init__()
        # 分頁按鈕省略，與舊版一致
        self.cog = cog

class WorkMenuView(ui.View):
    def __init__(self, cog: WorkTime):
        super().__init__(timeout=None)
        self.cog = cog

    @ui.button(label="上班打卡", style=ButtonStyle.primary, custom_id="work_btn_checkin")
    async def btn_checkin(self, button: ui.Button, interaction: Interaction):
        await self.cog.checkin(interaction)

    @ui.button(label="下班打卡", style=ButtonStyle.danger, custom_id="work_btn_checkout")
    async def btn_checkout(self, button: ui.Button, interaction: Interaction):
        await self.cog.checkout(interaction)

    @ui.button(label="查看工作時長", style=ButtonStyle.secondary, custom_id="work_btn_duration")
    async def btn_duration(self, button: ui.Button, interaction: Interaction):
        await self.cog.duration(interaction)


def setup(bot: commands.Bot):
    bot.add_cog(WorkTime(bot))
