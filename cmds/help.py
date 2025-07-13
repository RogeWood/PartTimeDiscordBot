from nextcord.ext import commands
from nextcord import Interaction, slash_command, Colour, Embed, SlashOption, ui
from datetime import datetime, timezone, timedelta

tz = timezone(timedelta(hours=8))

class PageButton(ui.Button):
    def __init__(self, label, id, embeds):
        super().__init__(label = label)
        self.id = id
        self.embeds = embeds
    
    async def callback(self, interaction: Interaction):
        await interaction.response.edit_message(embed = self.embeds[self.id], view = self.view)

class HelpPageView(ui.View):
    def __init__(self, embeds):
        super().__init__()
        self.add_item(PageButton("一般指令", 1, embeds))
        self.add_item(PageButton("會議指令", 2, embeds))
        self.add_item(PageButton("請假指令", 3, embeds))
        self.add_item(PageButton("打卡指令", 4, embeds))

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(name="help", description="查看指令說明", force_global=True)
    async def help(self, interaction: Interaction, category: str = SlashOption(
        name="分類",
        description="選擇要查看的指令分類",
        required=False,
        choices=["normal", "meet", "leave", "work_time"]
    )):
        now = datetime.now(tz)

        normalEmbed = Embed(title="📚 一般指令", description="常用基本功能", color=Colour.dark_gold(), timestamp=now)
        normalEmbed.add_field(name="/bot", value="查看機器人相關介紹資訊", inline=False)
        normalEmbed.add_field(name="/ping", value="顯示機器人延遲數據", inline=False)
        normalEmbed.add_field(name="/user_info", value="查看使用者帳號資訊", inline=False)
        normalEmbed.add_field(name="/purge", value="*清除訊息", inline=False)
        normalEmbed.set_footer(text="* 為管理員專用指令")

        meetingEmbed = Embed(title="📅 會議功能指令", description="管理與提醒會議", color=Colour.dark_green(), timestamp=now)
        meetingEmbed.add_field(name="/meeting add", value="新增單次會議", inline=False)
        meetingEmbed.add_field(name="/meeting list", value="顯示所有會議", inline=False)
        meetingEmbed.add_field(name="/meeting weekly", value="設定每週固定會議時間", inline=False)
        meetingEmbed.add_field(name="/meeting set_channel", value="設定提醒用頻道", inline=False)
        meetingEmbed.add_field(name="/meeting clear_reminders", value="開啟或關閉會議提醒", inline=False)
        
        leaveEmbed = Embed(title="📝 請假功能指令", description="使用請假系統", color=Colour.orange(), timestamp=now)
        leaveEmbed.add_field(name="/leave add", value="新增請假", inline=False)
        leaveEmbed.add_field(name="/leave list", value="列出所有請假", inline=False)
        leaveEmbed.add_field(name="/leave clear", value="清除自己或指定使用者的請假紀錄", inline=False)
        leaveEmbed.add_field(name="/leave clear_all", value="清除所有請假紀錄（限管理員）", inline=False)
        leaveEmbed.add_field(name="/leave set_channel", value="設定請假提醒頻道", inline=False)

        workTimeEmbed = Embed(title="⏱️ 打卡功能指令", description="上班打卡、查詢工時", color=Colour.blue(), timestamp=now)
        workTimeEmbed.add_field(name="/checkin", value="上班打卡", inline=False)
        workTimeEmbed.add_field(name="/checkout", value="下班打卡", inline=False)
        workTimeEmbed.add_field(name="/working_duration", value="查看目前已工作多久", inline=False)
        workTimeEmbed.add_field(name="/work_log", value="查看打卡紀錄", inline=False)
        workTimeEmbed.add_field(name="/clear_work_log", value="清除打卡紀錄", inline=False)
        
        if category == "normal":
            embed = normalEmbed

        elif category == "meeting":
            embed = meetingEmbed

        elif category == "leave":
            embed = leaveEmbed

        elif category == "work_time":
            embed = workTimeEmbed
        elif category is None:
            helpEmbed = Embed(
                title="📖 指令類型說明",
                description="請使用 `/help [指令類型]` 查詢對應功能：",
                color=Colour.gold(),
                timestamp=now
            )
            helpEmbed.add_field(name="/help meet", value="📅 會議功能指令", inline=False)
            helpEmbed.add_field(name="/help leave", value="📝 請假功能指令", inline=False)
            helpEmbed.add_field(name="/help work_time", value="⏱️ 打卡功能指令", inline=False)
            helpEmbed.add_field(name="/help normal", value="📦 一般功能指令", inline=False)
            embeds = [helpEmbed, normalEmbed, meetingEmbed, leaveEmbed, workTimeEmbed]
            await interaction.response.send_message(embed=embeds[0], view=HelpPageView(embeds))

        if category:
            await interaction.response.send_message(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Help(bot))
