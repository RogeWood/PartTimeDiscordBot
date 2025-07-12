from nextcord.ext import commands
from nextcord import __version__, Interaction, slash_command, Colour, Embed, Member
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

    @slash_command(description = "return with latency", force_global = True)
    async def ping(self, interaction: Interaction):
        embed = Embed(title = "機器人延遲狀態", description = "Pong !", color = Colour.dark_gold(), timestamp = datetime.now(tz))
        embed.add_field(name = "Bot Latency", value = f"{round(self.bot.latency * 1000)} ms")
        await interaction.send(embed = embed)

    @slash_command(description = "return bot infomation", force_global = True)
    async def bot(self, interaction: Interaction):
        print("bot")
        embed = Embed(
            title = "機器人相關資訊", 
            description = 
                "LeisurSlime 的無情打卡機機人\n\n" + 
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
            # "1. 洗衣部洗衣機狀態列\n" +
            # "2. 中正火車公車交通資訊\n" +
            # "3. 校網最新消息\n" +
            # "4. 校內疫情資訊（確診資訊）\n" +
            # "5. 行事曆\n" + 
            # "6. 常用連結\n" + 
            "1. 上下班打卡\n" + 
            "2. 請假",
            inline = False
        )
        await interaction.send(embed = embed)

    @slash_command(description = "show up user's information", force_global = True)
    async def user_info(self, interaction: Interaction, user: Member = None):
        target = user or interaction.user
        guild = interaction.guild

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
        today_str = datetime.now().strftime("%Y-%m-%d")
        future_leaves = [d for d in leave_data if d["user_id"] == target.id and d["date"] >= today_str]

        leave_lines = []
        for record in sorted(future_leaves, key=lambda r: r["date"]):
            leave_lines.append(f'{record["date"]}：{record["reason"]}')

        leave_summary = "\n".join(leave_lines) if leave_lines else "（無）"

        embed = Embed(
            title = "使用者資訊", description = f"關於{interaction.user}", color = interaction.user.color, timestamp = datetime.now(tz)
        )
        embed.add_field(name = "Account ID", value = interaction.user.id, inline = False)
        embed.add_field(name = "Created At", value = interaction.user.created_at.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"), inline = False)
        embed.set_thumbnail(url = interaction.user.avatar.url)
        embed.add_field(name="Mention", value=mention, inline=True)
        embed.add_field(name="Nick", value=nick, inline=True)
        embed.add_field(name="Joined at", value=joined_at, inline=False)
        embed.add_field(name="Server", value=server, inline=True)
        embed.add_field(name="Top Role", value=top_role, inline=True)
        embed.add_field(name="狀態", value=work_status, inline=False)
        embed.add_field(name="📅 請假紀錄", value=leave_summary, inline=False)
        embed.set_footer(text = f"{interaction.user.name}的個人資訊", icon_url = interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed)

    # @slash_command(description = "showing the frequently used links", force_global = True)
    # async def links(self, interaction: Interaction):
    #     embed = Embed(title = "常用連結", description = "阿梨 bot version a0.0.4", color = Colour.dark_gold(), timestamp = datetime.now(tz))
    #     links = {
    #         "學校官網": "https://www.ccu.edu.tw/",
    #         "單一入口": "https://portal.ccu.edu.tw/sso_index.php",
    #         "選課系統": "http://kiki.ccu.edu.tw/~ccmisp06/cgi-bin/class/index.php",
    #         "成績查詢系統": "http://kiki.ccu.edu.tw/~ccmisp06/cgi-bin/Query/",
    #         "秘書室官網": "https://secretar.ccu.edu.tw/",
    #         "資訊處官網": "https://it.ccu.edu.tw/",
    #         "校內疫情資訊站": "https://www.ccu.edu.tw/2019-nCoV.php"
    #     }
    #     for key, items in links.items():
    #         emoji = "<a:arrow:981828049635004426>"
    #         embed.add_field(name = f"{emoji} {key}", value = items, inline = False)
    #     embed.set_thumbnail(url = "https://i.imgur.com/5PLhiwr.png")
    #     await interaction.send(embed = embed)

def setup(bot: commands.Bot):
    bot.add_cog(React(bot))