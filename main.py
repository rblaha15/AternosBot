import asyncio
import threading

import pymongo
import certifi

import time
from aternosapi import AternosAPI
from typing import Union

import discord
from discord.ext import commands

# discord setup

client = commands.Bot(command_prefix=commands.when_mentioned_or('aternos '))


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online,
                                 activity=discord.Activity(name='aternos', type=discord.ActivityType.watching))
    print('\nBot je připraven!\n')


context: Union[discord.ext.commands.Context, None] = None
odpovidat = False
channel_id = None
user_id = None
token = None

# mongo setup

mongoClient = pymongo.MongoClient(
    'mongodb+srv://abc:UNVO0Vy0zGSNJ7yI@abcd.qpqdf.mongodb.net/abcd?retryWrites=true&w=majority',
    tlsCAFile=certifi.where()
)
database = mongoClient.abcd
collection: pymongo.collection.Collection = database.aternos

message2: Union[discord.Message, None] = None


# new message

@client.command()
async def new(ctx: discord.ext.commands.Context, _token):
    global channel_id, user_id, odpovidat, token, context, message2

    if collection.find_one({"guild_id": ctx.guild.id}) is None:
        collection.insert_one({
            "guild_id": ctx.guild.id,
            "messages": []
        })

    message2 = await ctx.send('Pošli prosím soubor s cookies:')

    context = ctx
    odpovidat = True
    channel_id = ctx.channel.id
    user_id = ctx.message.author.id
    token = _token

    await ctx.message.delete()


@client.event
async def on_message(message: discord.Message):
    global odpovidat

    if odpovidat:
        if message.channel.id == channel_id:
            if message.author.id == user_id:
                if len(message.attachments) != 0:
                    odpovidat = False

                    bytes_cookies = await message.attachments[0].read()
                    cookies = bytes_cookies.decode()

                    await message.delete()
                    await message2.delete()

                    mes = discord.Message = await context.send("Loading")
                    await mes.add_reaction("\U0001F7E9")

                    guild: dict = collection.find_one_and_delete({"guild_id": mes.guild.id})

                    guild["messages"].append({
                        "message_id": mes.id,
                        "channel_id": mes.channel.id,
                        "token": token,
                        "cookies": cookies
                    })

                    collection.insert_one(guild)

    await client.process_commands(message)


text = "{}\nStatus: {}\n\nZapnout server:"


async def mainloop():

    await client.wait_until_ready()

    while True:
        await asyncio.sleep(10)

        for mongoGuild in collection.find():

            guild: discord.Guild = client.get_guild(mongoGuild["guild_id"])

            for mongoMes in mongoGuild["messages"]:

                print(mongoMes)

                server = AternosAPI(mongoMes["cookies"], mongoMes["token"])

                channel: discord.TextChannel = guild.get_channel(mongoMes["channel_id"])

                message = await channel.fetch_message(mongoMes["message_id"])

                react = message.reactions[0]

                if react.count > 1:
                    await message.clear_reactions()
                    await message.add_reaction("\U0001F7E9")

                    print(server.StartServer())

                await message.edit(content=text.format(server.GetServerInfo().split(",")[0], server.GetStatus()))


def main():
    client.loop.create_task(mainloop())


threading.Thread(target=main).start()

client.run('OTA3NTA0NjQ5MzY2NTQ4NTEw.YYoJkQ.KWLpQSxGpVY_Ivob2sxXzLZo5Vs')
