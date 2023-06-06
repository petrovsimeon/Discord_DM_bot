# bot.py
import os
from datetime import datetime
import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
from time import sleep
import json

# Loading env variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DELAY = 0.03 # time in seconds

# Adding user intents
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

# Reads all existing tasks
with open('tasks.log', 'r') as f:
    current_commands = json.load(f)

message_id = 0


# Connecting to API and checking user list
@client.event
async def on_ready():
    for guild in client.guilds:
        print(guild.name)

        print(
            f'{client.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})\n'
        )

        members = '\n - '.join([member.name for member in guild.members[1:]])
        print(f'Guild Members:\n - {members}')


# Event listener for commands
@client.event
async def on_message(message):
    global message_id
    print("Got new message:")
    print(message.content)

    # DM all users at scheduled time
    if '$dm_all' in message.content and len(message.content.split(";")) == 3:
        current_commands[str(message_id)] = {"command": "$dm_all",
                                             "message": message.content.split("; ")[1],
                                             "time": message.content.split("; ")[2]}

        # Saves the current tasks to file
        with open('tasks.log', 'w') as f:
            f.write(json.dumps(current_commands))

        message_id += 1
        if message.author == client.user:
            return
        if not message.guild:
            await message.channel.send(f'DM will be sent to all users daily at {message.content.split("; ")[2]}!')

    elif "$dm_all_now" in message.content and len(message.content.split(";")) == 2:
        actual_message = message.content.split(";")[1]
        if message.author == client.user:
            return
        if not message.guild:
            await message.channel.send('DM sent to all users!')

            for guild in client.guilds:
                for m in guild.members[1:]:
                    await m.send("Hi!\n" + actual_message.strip() + "\nThanks!")
                    sleep(DELAY)



    # Shows all running tasks
    elif "$show_tasks" in message.content:
        if message.author == client.user:
            return
        if not message.guild:
            await message.channel.send("These are all the currently running tasks:")
            for k, v in current_commands.items():
                await message.channel.send(
                    f"{k}. Message: {current_commands[k]['message']} - Time: {current_commands[k]['time']}")

    elif "$delete_task" in message.content:
        if message.author == client.user:
            return
        if not message.guild:
            task_index = message.content.split(":")[1]
            current_commands.pop(task_index)
            await message.channel.send("Task successfully deleted!")

            # Saves the current tasks to file
            with open('tasks.log', 'w') as f:
                f.write(json.dumps(current_commands))


    # Shows all available commands
    elif "$help" in message.content:
        if message.author == client.user:
            return
        if not message.guild:
            await message.channel.send("List of available commands:"
                                       "\n1.$dm_all; Message; HH:mm - sends DM to all users in the server at scheduled time;"
                                       "\n2.$dm_all_now; Message - sends DM to all users in the server immediately;"
                                       "\n3.$show_tasks - shows currently running routines"
                                       "\n4.$delete_task:number - deletes a running task"
                                       "\n5.$help - shows all available commands")

    else:
        if message.author == client.user:
            return
        if not message.guild:
            await message.channel.send(
                "Invalid command! Message needs to have: $command; Message; time in format HH:mm")


@tasks.loop(seconds=31.0)
async def execute_commands():
    global current_commands

    for k, v in current_commands.items():
        target_time = current_commands[k]["time"]
        current_time = datetime.now().strftime("%H:%M")

        if current_time == target_time:
            actual_message = "Hi!\n" + current_commands[k]["message"] + "\nThanks!"
            for guild in client.guilds:
                for m in guild.members[1:]:
                    await m.send(actual_message)
                    sleep(DELAY)


# @execute_commands.before_loop
# async def before():
#     await client.wait_until_ready()
#     print("Finished waiting")

# Handles errors
@client.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise


# Starting API client
while True:
    execute_commands.start()
    client.run(TOKEN)


