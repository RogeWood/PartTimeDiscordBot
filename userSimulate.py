import nextcord
from nextcord.ext import commands

class FakeUser:
    def __init__(self, member):
        self.id = member.id
        self.mention = member.mention
        self.display_avatar = member.display_avatar
        self.nick = member.nick if hasattr(member, "nick") else member.name

class FakeInteraction:
    def __init__(self, bot, guild, channel, user):
        self.bot = bot
        self.guild = guild
        self.channel = channel
        self.user = user
        self.guild_id = guild.id
        self.channel_id = channel.id

    async def response_send_message(self, *args, **kwargs):
        # 移除不支援的參數（如 ephemeral）
        kwargs.pop("ephemeral", None)
        await self.channel.send(*args, **kwargs)

    @property
    def response(self):
        class Response:
            def __init__(self, interaction):
                self.interaction = interaction

            async def send_message(self, *args, **kwargs):
                await self.interaction.response_send_message(*args, **kwargs)

        return Response(self)

async def SendSlashCommand(bot: commands.Bot, cog_str: str, channel_id: int, subCommand_str: str = None):
    cog = bot.get_cog(cog_str)
    guild = nextcord.utils.get(bot.guilds)
    channel = bot.get_channel(channel_id)

    if cog and guild and channel:
        fake_user = FakeUser(guild.me)
        fake_interaction = FakeInteraction(bot, guild, channel, fake_user)

        # 預設主指令
        if subCommand_str is None:
            if hasattr(cog, cog_str.lower()):
                await getattr(cog, cog_str.lower())(fake_interaction)
                print(f"✅ 預設呼叫主指令 /{cog_str}")
            else:
                print(f"❌ 找不到主指令 /{cog_str}")
            return

        # 呼叫子指令
        if hasattr(cog, subCommand_str):
            await getattr(cog, subCommand_str)(fake_interaction)
            print(f"✅ 成功呼叫 /{cog_str} {subCommand_str}")
        else:
            print(f"❌ Cog `{cog_str}` 沒有 `{subCommand_str}` 指令")
    else:
        print("❌ 找不到 cog、guild 或頻道")
