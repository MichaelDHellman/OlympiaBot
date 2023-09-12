import discord
import json

class olympiaClient(discord.Client):
    token = ""
    sheet = ""

    def __init__(self, fpath):
        with open(fpath, 'r') as file:
            tokens = json.load(f)
            token = tokens["token"]
            sheet = tokens["SS_ID"]
    
    async def on_ready(self):
        print(f"Logged in as {self.user}")
    
    async def on_message(self, message):
        print(f"Message from {message.author}: {message.content}")
    
intents = discord.Intents(intents=18048258362465, application_id=,)

client = Client(intents=intents)
client.run('')