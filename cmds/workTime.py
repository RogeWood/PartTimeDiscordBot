import os
import json
from typing import Optional
from datetime import datetime, timezone, timedelta
from nextcord.ext import commands
from nextcord import Interaction, TextChannel, ui, Embed, ButtonStyle, slash_command, Member, SlashOption, User
import math

# 時區與檔案路徑設置
tz = timezone(timedelta(hours=8))  # 台灣時區
WORK_LOG_PATH = "data/work_logs.json"
CHECKIN_PATH = "data/checkin_data.json"
CONFIG_PATH = "data/config.json"
WORK_CHANNEL_ID = "work_channel_id"


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
        # 將 work_logs 改為 dict 格式: { user_id: [entries] }
        self.work_logs = load_json(WORK_LOG_PATH, {})
        self.selectUser = None
        if not isinstance(self.work_logs, dict):
            self.work_logs = {}
            save_json(WORK_LOG_PATH, self.work_logs)

    def get_channel_obj(self, guild_id: int) -> Optional[TextChannel]:
        cid = self.config.get(WORK_CHANNEL_ID)
        return self.bot.get_channel(cid) if cid else None

    @slash_command(name="work", description="打卡功能", force_global=False)
    async def work(self, interaction: Interaction):
        await interaction.response.send_message(
            "請使用子指令：/work set_channel, checkin, checkout, duration, menu, list, clear_log", ephemeral=True
        )

    @work.subcommand(name="set_channel", description="設定打卡訊息傳送的頻道")
    async def set_channel(self, interaction: Interaction, channel: TextChannel):
        self.config[WORK_CHANNEL_ID] = channel.id
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
            await interaction.response.send_message("您已經打過上班卡了！", ephemeral=False)
            return
        now = datetime.now(tz)
        self.checkin_data[gid][str(user.id)] = now.isoformat()
        save_json(CHECKIN_PATH, self.checkin_data)
        ch = self.get_channel_obj(interaction.guild_id)
        if ch:
            now = datetime.now(tz)
            embed = Embed(
                title="✅ 上班打卡",
                description=f" {user.mention} 於 {now.strftime('%Y-%m-%d %H:%M:%S')} 上班打卡",
                color=0x00FF00,
                timestamp=now
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
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
        uid = str(user.id)
        if uid not in self.work_logs:
            self.work_logs[uid] = []
        self.work_logs[uid].append({
            "guild_id": interaction.guild_id,
            "checkin": checkin_time.isoformat(),
            "checkout": now.isoformat(),
            "duration_seconds": total
        })
        save_json(WORK_LOG_PATH, self.work_logs)
        del self.checkin_data[gid][str(user.id)]
        save_json(CHECKIN_PATH, self.checkin_data)
        ch = self.get_channel_obj(interaction.guild_id)
        if ch:
            now = datetime.now(tz)
            embed = Embed(
                title="🏁 下班打卡",
                description=(
                    f" {user.mention} 於 {now.strftime('%Y-%m-%d %H:%M:%S')} 下班打卡\n"
                    f"本次工作時長：**{dur_str}**"
                ),
                color=0xFF0000,
                timestamp=now
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await ch.send(embed=embed)
        await interaction.response.send_message(f"🏁 下班打卡完成！本次工作時長：{dur_str}", ephemeral=True)

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
        await interaction.response.send_message(f"⏱️ {interaction.user.mention} 已工作：**{dur_str}**", ephemeral=True)

    @work.subcommand(name="menu", description="顯示打卡操作選單")
    async def menu(self, interaction: Interaction):
        ch = self.get_channel_obj(interaction.guild_id)
        if not ch:
            await interaction.response.send_message(
                "❌ 尚未設定打卡訊息頻道，請先使用 /work set_channel 設定。", ephemeral=True
            )
            return
        
        
        now = datetime.now(tz)
        embed = Embed(
            title="📋 工作打卡選單",
            description="請點擊下方按鈕進行打卡或查詢當前工作時長",
            color=0x3498DB,
            timestamp=now
        )
        view = WorkMenuView(self)
        await interaction.response.send_message(embed=embed, view=view)

    @work.subcommand(name="list", description="列出工作紀錄")
    async def list(self, interaction: Interaction, user: Member = SlashOption(name="user", description="指定使用者 (Tag)，不填為自己", required=False, default=None)):
        self.selectUser = interaction.user

        ch = self.get_channel_obj(interaction.guild_id)
        if not ch:
            await interaction.response.send_message(
                "❌ 尚未設定打卡訊息頻道，請先使用 /work set_channel 設定。", ephemeral=True
            )
            return
        embed = self.generate_worklist_embed(interaction.guild_id, 0, "all", self.selectUser)
        view = WorkListView(self, interaction.guild_id, 0, "all")
        
        ch = self.get_channel_obj(interaction.guild_id)
        await ch.send(embed=embed, view=view)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @work.subcommand(name="clear_log", description="清除工作紀錄")
    async def clear_log(self, interaction: Interaction, user: Optional[Member] = None):
        target = user or interaction.user
        view = ClearLogView(self, target)
        await interaction.response.send_message(
            f"確定要清除 {target.mention} 的工作紀錄嗎？", view=view, ephemeral=True
        )

    def generate_worklist_embed(self, guild_id: int, page: int, mode: str, user: User) -> Embed:
        user = self.selectUser
        # 展平 dict 為 list 並附上 user_id
        entries = []
        for user_id, user_logs in self.work_logs.items():
            for log in user_logs:
                log_copy = log.copy()
                log_copy['user_id'] = user_id
                entries.append(log_copy)
        logs = [log for log in entries if log["guild_id"] == guild_id]

        if mode == "daily":
            summary = {}
            for log in logs:
                date = log['checkout'][:10]
                summary[date] = summary.get(date, 0) + log['duration_seconds']
            items = [
                f"{d}: {s//3600}小時{(s%3600)//60}分鐘" for d, s in sorted(summary.items())
            ] or ["（無資料）"]
            embed = Embed(title="📅 每日加總", description="\n".join(items), color=0x3498DB)
            if user:
                embed.set_thumbnail(url=user.display_avatar.url)
            return embed

        if mode == "monthly":
            summary = {}
            for log in logs:
                month = log['checkout'][:7]
                summary[month] = summary.get(month, 0) + log['duration_seconds']
            items = [
                f"{m}: {s//3600}小時{(s%3600)//60}分鐘" for m, s in sorted(summary.items())
            ] or ["（無資料）"]
            embed = Embed(title="🗓️ 每月加總", description="\n".join(items), color=0x3498DB)
            if user:
                embed.set_thumbnail(url=user.display_avatar.url)
            return embed

        # all mode pagination
        per_page = 20
        total = len(logs)
        max_page = max(math.ceil(total/per_page)-1, 0)
        page = min(max(page, 0), max_page)
        title = f"📑工作紀錄 (第 {page+1}/{max_page+1} 頁)"
        items = [
            f"{i+1}. {log['checkin'][:19].replace('T',' ')} → {log['checkout'][:19].replace('T',' ')}，{log['duration_seconds']//3600}小時{(log['duration_seconds']%3600)//60}分鐘"
            for i, log in enumerate(logs)
        ]
        start = page * per_page
        page_items = items[start:start+per_page] or ["（無資料）"]
        
        now = datetime.now(tz)
        embed = Embed(title=title, description=f"{user.mention} 的工作紀錄\n\n" + "\n".join(page_items), color=0x3498DB, timestamp=now)

        if user:
            embed.set_thumbnail(url=user.display_avatar.url)
        return embed


class ClearLogView(ui.View):
    def __init__(self, cog: WorkTime, target: Member):
        super().__init__(timeout=None)
        self.cog = cog
        self.target = target

    @ui.button(label="是", style=ButtonStyle.danger)
    async def confirm(self, button: ui.Button, interaction: Interaction):
        uid = str(self.target.id)
        if uid in self.cog.work_logs:
            del self.cog.work_logs[uid]
            save_json(WORK_LOG_PATH, self.cog.work_logs)
        await interaction.response.edit_message(content=f"已清除 {self.target.mention} 的工作紀錄。", view=None, ephemeral=False)

    @ui.button(label="否", style=ButtonStyle.secondary)
    async def cancel(self, button: ui.Button, interaction: Interaction):
        await interaction.response.edit_message(content="已取消清除。", view=None, ephemeral=True)


class WorkListView(ui.View):
    def __init__(self, cog: WorkTime, guild_id: int, page: int = 0, mode: str = "all"):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
        self.page = page
        self.mode = mode

    @ui.button(label="上一頁", style=ButtonStyle.primary, custom_id="worklist_prev")
    async def prev_page(self, button: ui.Button, interaction: Interaction):
        new_page = max(self.page - 1, 0)
        new_view = WorkListView(self.cog, self.guild_id, new_page, self.mode)
        embed = self.cog.generate_worklist_embed(self.guild_id, new_page, self.mode, self.selectUser)
        await interaction.response.edit_message(embed=embed, view=new_view)

    @ui.button(label="下一頁", style=ButtonStyle.primary, custom_id="worklist_next")
    async def next_page(self, button: ui.Button, interaction: Interaction):
        entries = []
        for user_logs in self.cog.work_logs.values():
            entries.extend(user_logs)
        max_page = max(math.ceil(len([log for log in entries if log["guild_id"] == self.guild_id])/20)-1, 0)
        new_page = min(self.page + 1, max_page)
        new_view = WorkListView(self.cog, self.guild_id, new_page, self.mode)
        embed = self.cog.generate_worklist_embed(self.guild_id, new_page, self.mode, self.selectUser)
        await interaction.response.edit_message(embed=embed, view=new_view)

    @ui.button(label="日加總", style=ButtonStyle.secondary, custom_id="worklist_daily")
    async def daily(self, button: ui.Button, interaction: Interaction):
        new_view = WorkListView(self.cog, self.guild_id, 0, "daily")
        embed = self.cog.generate_worklist_embed(self.guild_id, 0, "daily", self.selectUser)
        await interaction.response.edit_message(embed=embed, view=new_view)

    @ui.button(label="月加總", style=ButtonStyle.secondary, custom_id="worklist_monthly")
    async def monthly(self, button: ui.Button, interaction: Interaction):
        new_view = WorkListView(self.cog, self.guild_id, 0, "monthly")
        embed = self.cog.generate_worklist_embed(self.guild_id, 0, "monthly", self.selectUser)
        await interaction.response.edit_message(embed=embed, view=new_view)


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
    
    @ui.button(label="查看工作記錄", style=ButtonStyle.secondary, custom_id="work_btn_list")
    async def btn_list(self, button: ui.Button, interaction: Interaction):
        await self.cog.list(interaction)


def setup(bot: commands.Bot):
    bot.add_cog(WorkTime(bot))
