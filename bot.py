import discord
import json
import random
import requests
import os 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.environ["DISCORD_TOKEN"]
KLIPY_API_KEY = os.environ["KLIPY_API_KEY"]
DISCORD_ADMIN_ID = int(os.environ["DISCORD_ADMIN_ID"])

# important variables 
chance_of_gif = 10 # 1 in x chance for a gif to be sent when a message is receieved.
variance_of_gif = 3 # number of pages to randomly select from when searching for a gif. higher variance means more random gifs, but also more likely to return no results.

# Set up the Discord client with the necessary intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# user id is used to track usage. required in URL for API call.
# page determines which result to return
def search_gif(urlencoded_keywords, user_id, page=1):
    page = page if page > 0 else 1
    per_page = 1
    url = f"https://api.klipy.com/api/v1/{KLIPY_API_KEY}/gifs/search?page={page}&per_page={per_page}&q={urlencoded_keywords}&customer_id={user_id}&locale=en"
    response = requests.get(url)
    data = json.loads(response.text)
    gif_url = data['data']['data'][0]['file']['hd']['gif']['url']
    return gif_url

def load_settings():
    global chance_of_gif, variance_of_gif, locked
    with open('settings.json', 'r') as f:
        settings = json.load(f)
        chance_of_gif = settings.get('chance_of_gif', chance_of_gif)
        variance_of_gif = settings.get('variance_of_gif', variance_of_gif)
        locked = settings.get('locked', False)

def save_settings():
    settings = {
        'chance_of_gif': chance_of_gif,
        'variance_of_gif': variance_of_gif,
        'locked': locked
    }
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

@client.event
async def on_ready():
    load_settings()
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('gb'):
        parts = message.content.split(' ')
        if len(parts) < 2:
            await message.channel.send("Please provide a command after 'gb'")
            return
        if parts[1] == "help":
            help_message = ("**GifBot Commands:**\n"
                            "`gb changechance <int>` - Adjusts the chance of a gif to '1/x'\n"
                            "`gb changevariance <int>` - Adjusts the randomness of gifs returned. e.g. 1 would always return the same gif.\n"
                            "`gb lock` - Locks the settings, preventing further changes.\n"
                            "`gb unlock` - Unlocks the settings, allowing changes to be made by anyone.\n"
                            "`gb help` - Display this help message.")
            await message.channel.send(help_message)
        if parts[1] == "ping":
            await message.channel.send("Pong!")
        if parts[1] == "lock":
            if message.author.id != DISCORD_ADMIN_ID:
                await message.channel.send("You do not have permission to use this command.")
                return
            locked = True
            save_settings()
            await message.channel.send("Settings have been locked. No further changes can be made.")
        if parts[1] == "unlock":
            if message.author.id != DISCORD_ADMIN_ID:
                await message.channel.send("You do not have permission to use this command.")
                return
            locked = False
            save_settings()
            await message.channel.send("Settings have been unlocked. Changes can now be made by anyone.")
        if parts[1] == "changechance" and (not locked or message.author.id == DISCORD_ADMIN_ID):
            try:
                new_chance = int(parts[2])
                if new_chance <= 0:
                    await message.channel.send("Chance must be a positive integer.")
                    return
                global chance_of_gif
                chance_of_gif = new_chance
                save_settings()
                await message.channel.send(f"Chance of gif changed to 1 in {chance_of_gif}")
            except (IndexError, ValueError):
                await message.channel.send("Please provide a valid integer for the new chance.")
        if parts[1] == "changevariance" and (not locked or message.author.id == DISCORD_ADMIN_ID):
            try:
                new_variance = int(parts[2])
                if new_variance <= 0:
                    await message.channel.send("Variance must be a positive integer.")
                    return
                global variance_of_gif
                variance_of_gif = new_variance
                save_settings()
                await message.channel.send(f"Variance of gif changed to {variance_of_gif} pages")
            except (IndexError, ValueError):
                await message.channel.send("Please provide a valid integer for the new variance.")


    # Whenever a message is receieved, 1 in x chance for a gif. use random 1-3 consecutive words from the message as keywords for the gif search. 
    if message.content and message.author != client.user and not message.content.startswith("gb"):
        if random.randint(1, chance_of_gif) == 1:
            keywords = message.content.split()
            num_keywords = random.randint(1, min(3, len(keywords)))
            max_start_index = len(keywords) - num_keywords
            start_index = random.randint(0, max_start_index)
            selected_keywords = keywords[start_index:start_index + num_keywords]
            urlencoded_keywords = "%20".join(selected_keywords)
            gif_url = search_gif(urlencoded_keywords, message.author.id, page=random.randint(1, variance_of_gif))
            await message.channel.send(gif_url)

client.run(TOKEN)