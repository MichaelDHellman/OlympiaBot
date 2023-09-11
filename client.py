import discord

class client(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}")
    
    async def on_message(self, message):
        print(f"Message from {message.author}: {message.content}")
    
intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run('')