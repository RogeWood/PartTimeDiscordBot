from nextcord.ext import commands
from nextcord import __version__, Interaction, slash_command, Colour, Embed, Member, SlashOption
from datetime import datetime, timezone, timedelta
import os
import json

tz = timezone(timedelta(hours = +8))

LEAVE_PATH = "data/leave.json"
CHECKIN_PATH = "data/checkin_data.json"

def load_leave_data():
    if os.path.exists(LEAVE_PATH):
        with open(LEAVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def load_checkin_data():
    if os.path.exists(CHECKIN_PATH):
        with open(CHECKIN_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

class React(commands.Cog, name = "React"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(description = "return with latency", force_global = False)
    async def ping(self, interaction: Interaction):
        embed = Embed(title = "機器人延遲狀態", description = "Pong !", color = Colour.dark_gold(), timestamp = datetime.now(tz))
        embed.add_field(name = "Bot Latency", value = f"{round(self.bot.latency * 1000)} ms")
        await interaction.send(embed = embed)

    @slash_command(description = "return bot infomation", force_global = False)
    async def bot(self, interaction: Interaction):
        embed = Embed(
            title = "機器人相關資訊", 
            description = 
                "LeisurSlime 的無情打卡機機人\n\n" + 
                "使用 \help 查看指令說明\n\n" + 
                "꙳✧˖°⌖꙳✧˖°⌖꙳✧˖°⌖꙳✧˖°⌖꙳✧˖°⌖꙳✧˖°⌖꙳✧˖°⌖꙳✧˖°\n"
                , 
            color = Colour.dark_gold(), 
            timestamp = datetime.now(tz)
        )
        embed.add_field(name = "開發語言", value = f"Python 3")
        embed.add_field(name = "使用函式庫", value = f"Nextcord {__version__}")
        embed.add_field(
            name = "功能",
            value = 
            "1. 上下班打卡\n" + 
            "2. 會議登記\n" + 
            "3. 請假功能",
            inline = False
        )
        await interaction.send(embed = embed)

    @slash_command(description = "show up user's information", force_global = False)
    async def user_info(self, interaction: Interaction, user: Member = SlashOption(name="user", description="指定使用者 (Tag)，不填為自己", required=False, default=None)):
        target = user
        if user == None:
            target = interaction.user

        guild = target.guild

        # 基本資訊
        mention = target.mention
        nick = target.nick or "（無）"
        joined_at = target.joined_at.strftime("%Y-%m-%d %H:%M")
        server = guild.name
        top_role = target.top_role.name if target.top_role else "無"

        # 上下班狀態
        checkin_data = load_checkin_data()
        user_id = str(target.id)
        is_working = user_id in checkin_data

        if is_working:
            start_time = datetime.fromisoformat(checkin_data[user_id])
            now = datetime.now(tz)
            duration = now - start_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{int(hours)} 小時 {int(minutes)} 分 {int(seconds)} 秒"
            work_status = f"正在努力工作中 💪（{duration_str}）"
        else:
            work_status = "休息中 😴"


                # 請假資料
        leave_data = load_leave_data()
        now = datetime.now(tz)
        future_leaves = [d for d in leave_data if str(d["user_id"]) == str(target.id) and datetime.fromisoformat(d["time"]) >= now]

        leave_lines = []
        for record in sorted(future_leaves, key=lambda r: r["time"]):
            dt = datetime.fromisoformat(record["time"]).astimezone(tz).strftime("%Y-%m-%d %H:%M")
            desc = record.get("description", "（無理由）")
            leave_lines.append(f'{dt}：{desc}')

        leave_summary = "\n".join(leave_lines) if leave_lines else "（無）"


        embed = Embed(
            title = "使用者資訊", description = f"關於{target.nick}", color = target.color, timestamp = datetime.now(tz)
        )
        embed.add_field(name = "Account ID", value = target.id, inline = False)
        embed.add_field(name = "Created At", value = target.created_at.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"), inline = False)
        embed.set_thumbnail(url = target.display_avatar.url)
        embed.add_field(name="Mention", value=mention, inline=True)
        embed.add_field(name="Nick", value=nick, inline=True)
        embed.add_field(name="Joined at", value=joined_at, inline=False)
        embed.add_field(name="Server", value=server, inline=True)
        embed.add_field(name="Top Role", value=top_role, inline=True)
        embed.add_field(name="狀態", value=work_status, inline=False)
        embed.add_field(name="📅 請假紀錄", value=leave_summary, inline=False)
        embed.set_footer(text = f"{target.name}的個人資訊", icon_url = target.avatar.url)

        await interaction.response.send_message(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(React(bot))