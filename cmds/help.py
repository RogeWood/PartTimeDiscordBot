from nextcord.ext import commands
from nextcord import Interaction, slash_command, Colour, Embed, SlashOption, ui
from datetime import datetime, timezone, timedelta

tz = timezone(timedelta(hours=8))

class PageButton(ui.Button):
    def __init__(self, label, idx, embeds):
        super().__init__(label=label)
        self.idx = idx
        self.embeds = embeds

    async def callback(self, interaction: Interaction):
        await interaction.response.edit_message(embed=self.embeds[self.idx], view=self.view)

class HelpPageView(ui.View):
    def __init__(self, embeds):
        super().__init__()
        # embeds list indices: 0=home,1=normal,2=meeting,3=leave,4=work_time,5=other
        self.add_item(PageButton("一般指令", 1, embeds))
        self.add_item(PageButton("會議指令", 2, embeds))
        self.add_item(PageButton("請假指令", 3, embeds))
        self.add_item(PageButton("打卡指令", 4, embeds))
        self.add_item(PageButton("其他功能", 5, embeds))

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(name="help", description="查看指令說明", force_global=False)
    async def help(
        self,
        interaction: Interaction,
        category: str = SlashOption(
            name="分類",
            description="選擇要查看的指令分類",
            required=False,
            choices=["normal", "meeting", "leave", "work_time", "other"]
        )
    ):
        now = datetime.now(tz)
        # 一般指令
        normalEmbed = Embed(title="📚 一般指令", description="常用基本功能", color=Colour.dark_gold(), timestamp=now)
        normalEmbed.add_field(name="/bot", value="查看機器人介紹資訊", inline=False)
        normalEmbed.add_field(name="/ping", value="顯示延遲數據", inline=False)
        normalEmbed.add_field(name="/user_info", value="查看使用者帳號資訊", inline=False)
        normalEmbed.add_field(name="/purge", value="清除訊息 (管理員專用)", inline=False)
        normalEmbed.add_field(name="/clear_data", value="清除儲存資料 (管理員專用)", inline=False)

        # 會議指令
        meetingEmbed = Embed(title="📅 會議指令", description="管理與提醒會議", color=Colour.dark_green(), timestamp=now)
        meetingEmbed.add_field(name="/meeting add", value="新增單次會議", inline=False)
        meetingEmbed.add_field(name="/meeting list", value="顯示所有會議", inline=False)
        meetingEmbed.add_field(name="/meeting weekly", value="設定每週會議", inline=False)
        meetingEmbed.add_field(name="/meeting remove_single", value="刪除單次會議", inline=False)
        meetingEmbed.add_field(name="/meeting remove_weekly", value="關閉每週會議", inline=False)
        meetingEmbed.add_field(name="/meeting set_channel", value="設定提醒頻道", inline=False)
        meetingEmbed.add_field(name="/meeting set_reminder", value="設定提前提醒時間", inline=False)
        meetingEmbed.add_field(name="/meeting clear_reminders", value="清除所有提醒", inline=False)

        # 請假指令
        leaveEmbed = Embed(title="📝 請假指令", description="請假紀錄管理與公告", color=Colour.orange(), timestamp=now)
        leaveEmbed.add_field(name="/leave add", value="新增請假紀錄", inline=False)
        leaveEmbed.add_field(name="/leave list", value="列出請假紀錄", inline=False)
        leaveEmbed.add_field(name="/leave remove", value="刪除請假紀錄", inline=False)
        leaveEmbed.add_field(name="/leave set_channel", value="設定請假公告頻道", inline=False)
        leaveEmbed.add_field(name="/leave set_time", value="設定請假公告時間", inline=False)

        # 打卡指令
        workTimeEmbed = Embed(title="⏱️ 打卡指令", description="上班打卡與工時查詢", color=Colour.blue(), timestamp=now)
        workTimeEmbed.add_field(name="/work set_channel", value="設定打卡頻道", inline=False)
        workTimeEmbed.add_field(name="/work checkin", value="上班打卡", inline=False)
        workTimeEmbed.add_field(name="/work checkout", value="下班打卡並儲存工時", inline=False)
        workTimeEmbed.add_field(name="/work duration", value="查看當前工時", inline=False)
        workTimeEmbed.add_field(name="/work menu", value="顯示打卡選單", inline=False)
        workTimeEmbed.add_field(name="/work list", value="列出工作紀錄", inline=False)
        workTimeEmbed.add_field(name="/work clear_log", value="清除工作紀錄", inline=False)

        # 其他功能：排程任務
        otherEmbed = Embed(title="🔧 其他功能", description="排程任務列表", color=Colour.light_grey(), timestamp=now)
        otherEmbed.add_field(name="會議提醒排程", value="指定時間提前提醒會議", inline=False)
        otherEmbed.add_field(name="請假公告排程", value="每天指定時間發布請假公告", inline=False)

        # 決定回傳
        if category == "normal":
            await interaction.response.send_message(embed=normalEmbed)
        elif category == "meeting":
            await interaction.response.send_message(embed=meetingEmbed)
        elif category == "leave":
            await interaction.response.send_message(embed=leaveEmbed)
        elif category == "work_time":
            await interaction.response.send_message(embed=workTimeEmbed)
        elif category == "other":
            await interaction.response.send_message(embed=otherEmbed)
        else:
            # 首頁與按鈕
            homeEmbed = Embed(title="📖 指令類型說明", description="請選擇要查看的分類：", color=Colour.gold(), timestamp=now)
            homeEmbed.add_field(name="/help normal", value="一般指令", inline=False)
            homeEmbed.add_field(name="/help meeting", value="會議指令", inline=False)
            homeEmbed.add_field(name="/help leave", value="請假指令", inline=False)
            homeEmbed.add_field(name="/help work_time", value="打卡指令", inline=False)
            homeEmbed.add_field(name="/help other", value="其他功能", inline=False)
            embeds = [homeEmbed, normalEmbed, meetingEmbed, leaveEmbed, workTimeEmbed, otherEmbed]
            await interaction.response.send_message(embed=homeEmbed, view=HelpPageView(embeds))


def setup(bot: commands.Bot):
    bot.add_cog(Help(bot))
