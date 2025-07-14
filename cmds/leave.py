import json
import os
from datetime import datetime, timezone, timedelta

from nextcord.ext import commands, tasks
from nextcord import slash_command, Interaction, SlashOption, Member, Embed, Colour, TextChannel

# 檔案與時區設置
tz = timezone(timedelta(hours=8))  # 台北時區
LEAVE_FILE = "data/leave.json"
CONFIG_PATH = "data/config.json"

# 年度選項
CURRENT_YEAR = datetime.now(tz).year
YEARS = [str(CURRENT_YEAR + i) for i in range(3)]  # 今年,今年+1,今年+2


def load_leave_data():
    if os.path.exists(LEAVE_FILE):
        with open(LEAVE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_leave_data(data):
    os.makedirs(os.path.dirname(LEAVE_FILE), exist_ok=True)
    with open(LEAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leave_data = load_leave_data()
        self.config = load_config()
        self.last_announce = None
        self.announce_task.start()

    def cog_unload(self):
        self.announce_task.cancel()

    @slash_command(name='leave', description='管理請假紀錄', force_global=False)
    async def leave(self, interaction: Interaction):
        await interaction.response.send_message(
            '請使用 `/leave add`、`/leave list`、`/leave remove`、`/leave set_channel` 或 `/leave set_time`',
            ephemeral=True
        )

    @leave.subcommand(name='add', description='新增請假紀錄')
    async def add(
        self,
        interaction: Interaction,
        name: str = SlashOption(name='name', description='請假名稱', required=True),
        description: str = SlashOption(name='description', description='請假說明', required=True),
        year: str = SlashOption(name='year', description='西元年', choices=YEARS, required=True),
        month: int = SlashOption(name='month', description='月份', choices=list(range(1, 13)), required=True),
        day: int = SlashOption(name='day', description='日期', required=True, min_value=1, max_value=31),
        hour: int = SlashOption(name='hour', description='小時 (0-23)', required=True, min_value=0, max_value=23),
        minute: int = SlashOption(name='minute', description='分鐘 (0-59)', required=True, min_value=0, max_value=59),
        user: Member = SlashOption(name='user', description='指定使用者，預設自己', required=False, default=None)
    ):
        target = user
        if user == None:
            target = interaction.user
        
        try:
            dt = datetime(int(year), month, day, hour, minute, tzinfo=tz)
        except ValueError:
            await interaction.response.send_message('❌ 請假時間不正確', ephemeral=True)
            return
        if dt < datetime.now(tz):
            await interaction.response.send_message('❌ 請假時間已過', ephemeral=True)
            return
        self.leave_data.append({
            'user_id': str(target.id),
            'name': name,
            'time': dt.isoformat(),
            'description': description
        })
        save_leave_data(self.leave_data)
        await interaction.response.send_message(
            f'✅ 已新增請假：{target.mention} {name} @ {dt.strftime("%Y-%m-%d %H:%M")}'
        )

    @leave.subcommand(name='list', description='列出請假紀錄')
    async def list(
        self,
        interaction: Interaction,
        user: Member = SlashOption(name='user', description='指定使用者，不填則顯示全部', required=False, default=None)
    ):
        recs = [r for r in self.leave_data if not user or r['user_id'] == str(user.id)]
        if not recs:
            await interaction.response.send_message('目前無請假紀錄', ephemeral=True)
            return
        embed = Embed(title='📋 請假紀錄', color=Colour.blue())
        for idx, rec in enumerate(recs, 1):
            member = interaction.guild.get_member(int(rec['user_id']))
            t = rec.get('time') or rec.get('date')
            if t and 'T' in t:
                dt = datetime.fromisoformat(t).astimezone(tz)
                dt_str = dt.strftime('%Y-%m-%d %H:%M')
            else:
                dt_str = t
            embed.add_field(
                name=f"{idx}. **{member.nick}** — {rec.get('name','')} @ {dt_str}",
                value=f"說明：{rec.get('description','')}"
            )
        await interaction.response.send_message(embed=embed)

    @leave.subcommand(name='remove', description='刪除請假紀錄')
    async def remove(
        self,
        interaction: Interaction,
        date: str = SlashOption(name='date', description='請假日期 (選擇)', autocomplete=True, required=True),
        user: Member = SlashOption(name='user', description='指定使用者，不填則為自己', required=False, default=None)
    ):
        target = user
        if user == None:
            target = interaction.user

        for i, rec in enumerate(self.leave_data):
            rec_date = (rec.get('time', rec.get('date','')))[:10]
            if rec['user_id'] == str(target.id) and rec_date == date:
                self.leave_data.pop(i)
                save_leave_data(self.leave_data)
                await interaction.response.send_message(f'🗑 已刪除 {target.mention} 的請假：{rec.get("name","")} @ {date}')
                return
        await interaction.response.send_message('❌ 找不到該記錄', ephemeral=True)

    @remove.on_autocomplete('date')
    async def remove_date_autocomplete(self, interaction: Interaction, current: str, user: str = None):
        uid = int(user) if user else interaction.user.id
        dates = sorted({(r.get('time', r.get('date','')))[:10] for r in self.leave_data if r['user_id']==str(uid)})
        await interaction.response.send_autocomplete([d for d in dates if current in d][:25])

    @leave.subcommand(name='set_channel', description='設定公告頻道')
    async def set_channel(
        self,
        interaction: Interaction,
        channel: TextChannel = SlashOption(name='channel', description='公告頻道', required=True)
    ):
        self.config['leave_announcement_channel_id'] = channel.id
        save_config(self.config)
        await interaction.response.send_message(f'✅ 已設定公告頻道：{channel.mention}', ephemeral=True)

    @leave.subcommand(name='set_time', description='設定公告時間')
    async def set_time(
        self,
        interaction: Interaction,
        hour: int = SlashOption(name='hour', description='小時', required=True, min_value=0, max_value=23),
        minute: int = SlashOption(name='minute', description='分鐘', required=True, min_value=0, max_value=59)
    ):
        self.config['leave_announcement_time'] = {'hour': hour, 'minute': minute}
        save_config(self.config)
        await interaction.response.send_message(f'✅ 已設定公告時間：{hour:02}:{minute:02}', ephemeral=True)

    @tasks.loop(minutes=1)
    async def announce_task(self):
        now = datetime.now(tz)
        cfg = self.config.get('leave_announcement_time')
        chan_id = self.config.get('leave_announcement_channel_id')
        if not cfg or not chan_id:
            return
        if now.strftime('%H:%M') == f"{cfg['hour']:02}:{cfg['minute']:02}":
            date_str = now.strftime('%Y-%m-%d')
            if self.last_announce == date_str:
                return
            recs = [r for r in self.leave_data if (r.get('time',r.get('date','')))[:10]==date_str]
            channel = self.bot.get_channel(chan_id)
            if channel and recs:
                embed = Embed(title=f'📢 {date_str} 請假公告', color=Colour.orange())
                for rec in recs:
                    m = channel.guild.get_member(int(rec['user_id']))
                    t = rec.get('time') or rec.get('date')
                    if 'T' in t:
                        dt = datetime.fromisoformat(t).astimezone(tz)
                        time_str = dt.strftime('%H:%M')
                    else:
                        time_str = ''
                    embed.add_field(name=f"{m.mention}：{rec.get('name','')}", value=f"時間：{time_str}\n說明：{rec.get('description','')}")
                await channel.send(embed=embed)
            self.last_announce = date_str

    @announce_task.before_loop
    async def before_announce(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Leave(bot))
