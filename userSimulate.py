
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
        await self.channel.send(*args, **kwargs)

    @property
    def response(self):
        class Response:
            def __init__(self, interaction):
                self.interaction = interaction

            async def send_message(self, *args, **kwargs):
                await self.interaction.response_send_message(*args, **kwargs)

        return Response(self)
