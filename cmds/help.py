from nextcord.ext import commands
from nextcord import Interaction, slash_command, Colour, Embed, SlashOption
from datetime import datetime, timezone, timedelta

tz = timezone(timedelta(hours=8))

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(name="help", description="查看指令說明", force_global=True)
    async def help(self, interaction: Interaction, category: str = SlashOption(
        name="指令類型",
        description="選擇要查看的指令類型",
        required=False,
        choices=["normal", "meet", "leave", "work_time"]
    )):
        now = datetime.now(tz)

        if category is None:
            embed = Embed(
                title="📖 指令類型說明",
                description="請使用 `/help [指令類型]` 查詢對應功能：",
                color=Colour.gold(),
                timestamp=now
            )
            embed.add_field(name="/help meet", value="📅 會議功能指令", inline=False)
            embed.add_field(name="/help leave", value="📝 請假功能指令", inline=False)
            embed.add_field(name="/help work_time", value="⏱️ 打卡功能指令", inline=False)
            embed.add_field(name="/help normal", value="📦 一般功能指令", inline=False)
            await interaction.response.send_message(embed=embed)
            return

        if category == "normal":
            embed = Embed(title="📦 一般指令", color=Colour.dark_gold(), timestamp=now)
            embed.add_field(name="/bot", value="查看機器人介紹資訊", inline=False)
            embed.add_field(name="/ping", value="顯示機器人延遲數據", inline=False)
            embed.add_field(name="/user_info", value="查看使用者帳號資訊", inline=False)
            embed.add_field(name="/purge", value="* 清除訊息（管理員專用）", inline=False)

        elif category == "meet":
            embed = Embed(title="📅 會議功能指令", color=Colour.green(), timestamp=now)
            embed.add_field(name="/meeting add", value="新增單次會議", inline=False)
            embed.add_field(name="/meeting weekly", value="新增每週固定會議", inline=False)
            embed.add_field(name="/meeting list", value="顯示會議列表", inline=False)
            embed.add_field(name="/meeting set_channel", value="設定提醒發送頻道", inline=False)
            embed.add_field(name="/meeting set_reminders", value="開啟/關閉提醒通知", inline=False)

        elif category == "leave":
            embed = Embed(title="📝 請假功能指令", color=Colour.orange(), timestamp=now)
            embed.add_field(name="/leave add", value="新增請假記錄", inline=False)
            embed.add_field(name="/leave list", value="列出所有請假", inline=False)
            embed.add_field(name="/leave clear", value="清除自己的請假紀錄", inline=False)
            embed.add_field(name="/leave clear_all", value="清除所有請假（限管理員）", inline=False)
            embed.add_field(name="/leave set_channel", value="設定請假提醒頻道", inline=False)

        elif category == "work_time":
            embed = Embed(title="⏱️ 打卡功能指令", color=Colour.blue(), timestamp=now)
            embed.add_field(name="/checkin", value="上班打卡", inline=False)
            embed.add_field(name="/checkout", value="下班打卡", inline=False)
            embed.add_field(name="/working_duration", value="查看目前已工作多久", inline=False)
            embed.add_field(name="/work_log", value="查看打卡紀錄", inline=False)
            embed.add_field(name="/clear_work_log", value="清除打卡紀錄", inline=False)

        await interaction.response.send_message(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Help(bot))
