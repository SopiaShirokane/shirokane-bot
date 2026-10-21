import time as pytime
import discord
from discord.ext import commands
import requests
import json
from datetime import datetime

_token = None
_token_expires = 0
CLIENT_ID =
CLIENT_SECRET =
def numFormat(num):
    return format(num, ",").replace(',', ' ')
def getToken():
    global _token, _token_expires
    if _token and pytime.time() < _token_expires - 60:
        return _token
    response = requests.post(
        "https://osu.ppy.sh/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
            "scope": "public"
        }
    )
    data = response.json()
    _token = data["access_token"]
    _token_expires = pytime.time() + data["expires_in"]
    return _token

def apiGet(path, params=None):
    headers = {"Authorization": f"Bearer {getToken()}"}
    return requests.get(f"https://osu.ppy.sh/api/v2/{path}", headers=headers, params=params).json()

def time(timestamp):
    formattedTime = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return formattedTime.strftime("%d/%m/%Y %H:%M")

def getUser(ids):
    return apiGet("users", params={"ids[]": ids})["users"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="s!", intents=intents, helpCommand=None)

@bot.command(name="about")
async def version(ctx):
    await ctx.send(f"Made by Sopia with ❤ using discordpy version {discord.__version__} for my beloved Shirokane's Family")

@bot.command(name="commands", aliases=["c"])
async def cmd(ctx):
    fileData = apiGet(f"teams/27574")
    embed = discord.Embed(title="Commands", color=0xff00ff, description="Bot prefix: s!")
    embed.add_field(name="Available rulesets", inline=False, value="osu, mania, fruits, taiko")
    embed.add_field(name="commands/c", inline=False, value="Shows this message")
    embed.add_field(name="team/t {ruleset}", inline=False, value="Shows the team's members and stats based on the chosen ruleset")
    embed.add_field(name="online/o", inline=False, value="Shows currently online members")
    embed.add_field(name="leaderboard/lb {ruleset}", inline=False, value="Shows leaderboards of members in the team using the chosen ruleset")
    embed.add_field(name="member/m {name}", inline=False, value="Shows information about the chosen member (only name needed, you don't have to type Shoka Shirokane, just Shoka)")
    embed.add_field(name="discord/d (name)", inline=False, value="Shows information about every/or just one member's discord account")
    embed.add_field(name="birthday/bd (name)", inline=False, value="Shows every/or just one member's birthday")
    embed.add_field(name='join/j "{osu_username}" {account_link} "{reason}"', inline=False, value="Joining the team (just an application, also DO NOT use if you don't really want to join our team)")
    embed.add_field(name="about", inline=False, value="Shows information about the bot")
    embed.add_field(name="Small notice", inline=False, value="Please don't spam the commands since I'm rate-limited to 60 requests/minute, also if you found any bugs or want to suggest a feature drop me a DM on <@891082078383382548>")
    embed.set_image(url=fileData["cover_url"])
    await ctx.send(embed=embed)

@bot.command(name="team", aliases=["t"])
async def members(ctx, gamemode):
    validModes = ["osu", "mania", "fruits", "taiko"]
    if gamemode not in validModes:
        await ctx.send(f"Invalid ruleset. Choose from: {', '.join(validModes)}")
        return

    fileData = apiGet(f"teams/27574/{gamemode}")

    # Basic team data
    teamId = fileData["id"]
    flag = fileData["flag_url"]
    name = fileData["name"]
    shortName = fileData["short_name"]
    cover = fileData["cover_url"]
    created = fileData["created_at"]
    isOpen = fileData["is_open"]
    emptySlots = fileData["empty_slots"]

    # Team stats
    stats = fileData["statistics"]
    ruleset = gamemode
    playCount = stats["play_count"] 
    rankedScore = stats["ranked_score"]
    pp = stats["performance"]

    author = ctx.author
    memberList = []
    memberList.append(fileData["leader"]["username"])
    for member in fileData["members"]:
        memberList.append(member["username"])
    embed = discord.Embed(title="Shirokane's Family", color=0xff00ff, description="\n".join(memberList), url=f"https://osu.ppy.sh/teams/{teamId}")
    embed.set_thumbnail(url=flag)
    embed.add_field(name="Leader", inline=True, value=f"{fileData["leader"]["username"]}")
    embed.add_field(name="ID", inline=True, value=teamId)
    embed.add_field(name="Empty slots", inline=True, value=emptySlots)
    embed.add_field(name="Created at", inline=True, value=f"{time(created)}")
    embed.add_field(name="Ruleset", inline=True, value=ruleset)
    embed.add_field(name="Playcount", inline=True, value=f"{numFormat(playCount)}")
    embed.add_field(name="Ranked score", inline=True, value=f"{numFormat(rankedScore)}")
    embed.add_field(name="PP", inline=True, value=f"{numFormat(pp)}")
    embed.set_footer(text=f"Requested by {author.name}", icon_url=author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="online", aliases=["o"])
async def player(ctx):
    author = ctx.author
    fileData = apiGet(f"teams/27574")
    embed = discord.Embed(title="Online members", color=0xff00ff)
    embed.set_thumbnail(url=fileData["flag_url"])
    if fileData["leader"]["is_online"]:
        embed.add_field(name=f"{fileData["leader"]["username"]}", value="")
    for member in fileData["members"]:
        if member["is_online"]:
            embed.add_field(name=f"{member["username"]}", value="")
    embed.set_footer(text=f"Requested by {author.name}", icon_url=author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="leaderboard", aliases=["lb"])
async def leaderboard(ctx, gamemode):
    validModes = ["osu", "mania", "fruits", "taiko"]
    if gamemode not in validModes:
        await ctx.send(f"Invalid ruleset. Choose from: {', '.join(validModes)}")
        return
    author = ctx.author
    embed = discord.Embed(title="Leaderboard", description=f"Mode: {gamemode}", color=0xff00ff)
    team = apiGet(f"teams/27574/{gamemode}")
    embed.set_thumbnail(url=team["flag_url"])
    ids = [team["leader"]["id"]] + [m["id"] for m in team["members"]]
    users = getUser(ids)
    ranked = sorted(
        users,
        key=lambda u: u.get("statistics_rulesets", {}).get(gamemode, {}).get("pp", 0),
        reverse=True,
    )
    for i, u in enumerate(ranked, start=1):
        stats = u.get("statistics_rulesets", {}).get(gamemode, 0)
        if gamemode == "fruits":
            if u["username"] != "Shizu Shirokane":
                if stats["pp"] > 0:
                    if i == 1:
                        embed.add_field(name=f"🥇 {u['username']} - {stats["pp"]:,.0f}pp (#{numFormat(stats["global_rank"])})", inline=False, value="")
                        continue
                    if i == 2:
                        embed.add_field(name=f"🥈 {u['username']} - {stats["pp"]:,.0f}pp (#{numFormat(stats["global_rank"])})", inline=False, value="")
                        continue
                    if i == 3:
                        embed.add_field(name=f"🥉 {u['username']} - {stats["pp"]:,.0f}pp (#{numFormat(stats["global_rank"])})", inline=False, value="")
                        continue
                    embed.add_field(name=f"{i}. {u['username']} - {stats["pp"]:,.0f}pp (#{numFormat(stats["global_rank"])})", inline=False, value="")
        else:
            if stats["pp"] > 0:
                    if i == 1:
                        embed.add_field(name=f"🥇 {u['username']} - {stats["pp"]:,.0f}pp (#{numFormat(stats["global_rank"])})", inline=False, value="")
                        continue
                    if i == 2:
                        embed.add_field(name=f"🥈 {u['username']} - {stats["pp"]:,.0f}pp (#{numFormat(stats["global_rank"])})", inline=False, value="")
                        continue
                    if i == 3:
                        embed.add_field(name=f"🥉 {u['username']} - {stats["pp"]:,.0f}pp (#{numFormat(stats["global_rank"])})", inline=False, value="")
                        continue
                    embed.add_field(name=f"{i}. {u['username']} - {stats["pp"]:,.0f}pp (#{numFormat(stats["global_rank"])})", inline=False, value="")
    # if it works dont touch it
    embed.set_footer(text=f"Requested by {author.name}", icon_url=author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="member", aliases=["m"])
async def member(ctx, username):
    validNames = ["Shoka", "Ahiru", "Ayoko", "Fuyu", "Huna", "Izuna", "Kuru", "Mita", "Mofu", "Shizu", "Sopia", "Sora", "Yuuki"]
    if username not in validNames:
        await ctx.send(f"Invalid name, perhaps that person isn't in the family?")
        return
    author = ctx.author
    username += " Shirokane"
    mem = apiGet(f"users/@{username}")
    embed = discord.Embed(title=username, url=f"https://osu.ppy.sh/users/{mem["id"]}", color=0xff00ff, description=f"Level: {mem["statistics"]["level"]["current"]}")
    embed.set_thumbnail(url=mem["avatar_url"])
    embed.add_field(name="Main gamemode", inline=True, value=mem["playmode"])
    embed.add_field(name="PP", inline=True, value=mem["statistics"]["pp"])
    embed.add_field(name="Accuracy", inline=True, value=f'{mem["statistics"]["hit_accuracy"]}%')
    embed.add_field(name="Playcount", inline=True, value=mem["statistics"]["play_count"])
    embed.add_field(name="Max combo", inline=True, value=mem["statistics"]["maximum_combo"])
    embed.add_field(name="Global rank", inline=True, value=f'#{numFormat(mem["statistics"]["global_rank"])}')
    embed.add_field(name="Country rank", inline=True, value=f'#{numFormat(mem["statistics"]["country_rank"])}')
    if not mem["matchmaking_stats"]:
        embed.add_field(name="Ranked play", inline=True, value="N/A")
    else:
        embed.add_field(name="Ranked play", inline=True, value=f'#{mem["matchmaking_stats"][0]["rank"]}')
    embed.add_field(name="Highest rank", inline=True, value=f"#{numFormat(mem["rank_highest"]["rank"])} at {time(mem["rank_highest"]["updated_at"])}")
    embed.add_field(name="Followers", inline=True, value=mem["follower_count"])
    embed.add_field(name="Kudosu", inline=True, value=mem["kudosu"]["total"])
    embed.add_field(name="Ranked beatmaps", inline=True, value=mem["ranked_beatmapset_count"])
    await ctx.send(embed=embed)

@bot.command(name="discord", aliases=["d"])
async def dc(ctx, *name):
    author = ctx.author
    team = apiGet("teams/27574")
    dcID = [993465312500527144, 874515432298659850, 1093105047996465233, 891082078383382548, 1053613020338728961, 944864649407528972, 1034103806536978453, 904895148700348437, 943810069051609200, 392482017712930836, 977761484354490388, 652844542881693710, 1021040111997165600, 937726510796779560]
    osuUsername = ["Shizu Shirokane", "Fuyu Shirokane", "Shoka Shirokane", "Sopia Shirokane", "Yuuki Shirokane", "Mofu Shirokane", "Mita Shirokane", "Ayoko Shirokane", "Ahiru Shirokane", "Huna Shirokane", "Izuna Shirokane", "Kuru Shirokane", "Izumi Shirokane", "Sora Shirokane"]
    embed = discord.Embed(title="SF discord", color=0xff00ff)
    embed.set_thumbnail(url=team["flag_url"])
    embed.set_footer(text=f"Requested by {author.name}", icon_url=author.display_avatar.url)
    validNames = ["Shoka", "Ahiru", "Ayoko", "Fuyu", "Huna", "Izuna", "Kuru", "Mita", "Mofu", "Shizu", "Sopia", "Sora", "Yuuki", "Izumi"]
    if len(name) != 1 or name[0] not in validNames:
        for i in range(len(osuUsername)):
            if osuUsername[i] == "Izumi Shirokane":
                embed.add_field(name=osuUsername[i], inline=False, value=f"<@{dcID[i]}> \n(member not currently in the team)")
                continue
            embed.add_field(name=osuUsername[i], inline=False, value=f"<@{dcID[i]}>")
        await ctx.send(embed=embed)
    else:
        for i in range(len(osuUsername)):
            if name[0] + " Shirokane" == "Izumi Shirokane":
                embed.add_field(name=osuUsername[i], inline=False, value=f"<@{dcID[i]}> \n(member not currently in the team)")
                continue
            if osuUsername[i] == name[0] + " Shirokane":
                embed.add_field(name=osuUsername[i], inline=False, value=birthdays[i])
        await ctx.send(embed=embed)
        
@bot.command(name="birthday", aliases=["bd"])
async def birthday(ctx, *name):
    author = ctx.author
    team = apiGet("teams/27574")
    birthdays = ["20/09", "22/12", "16/02", "13/12", "08/05", "21/07", "18/03", "04/03", "02/04", "12/03", "02/08", "27/04", "22/07 \n(member not currently in the team)", "21/01"]
    osuUsername = ["Shizu Shirokane", "Fuyu Shirokane", "Shoka Shirokane", "Sopia Shirokane", "Yuuki Shirokane", "Mofu Shirokane", "Mita Shirokane", "Ayoko Shirokane", "Ahiru Shirokane", "Huna Shirokane", "Izuna Shirokane", "Kuru Shirokane", "Izumi Shirokane", "Sora Shirokane"]
    embed = discord.Embed(title="SF birthday", color=0xff00ff)
    embed.set_thumbnail(url=team["flag_url"])
    embed.set_footer(text=f"Requested by {author.name}", icon_url=author.display_avatar.url)
    validNames = ["Shoka", "Ahiru", "Ayoko", "Fuyu", "Huna", "Izuna", "Kuru", "Mita", "Mofu", "Shizu", "Sopia", "Sora", "Yuuki", "Izumi"]
    if len(name) != 1 or name[0] not in validNames:
        for i in range(len(osuUsername)):
            embed.add_field(name=osuUsername[i], inline=False, value=birthdays[i])
        await ctx.send(embed=embed)
    else:
        for i in range(len(osuUsername)):
            if osuUsername[i] == name[0] + " Shirokane":
                embed.add_field(name=osuUsername[i], inline=False, value=birthdays[i])
        await ctx.send(embed=embed)

@bot.command(name="join", aliases=["j"])
async def join_cmd(ctx, name, link, reason):
    author = ctx.author
    embed = discord.Embed(color=0xff00ff)
    dcID = [993465312500527144, 874515432298659850, 1093105047996465233, 891082078383382548, 1053613020338728961, 944864649407528972, 1034103806536978453, 904895148700348437, 943810069051609200, 392482017712930836, 977761484354490388, 652844542881693710, 1021040111997165600, 937726510796779560]
    for discordid in dcID:
        if author.id == discordid:
            await ctx.send("You are already a part of the team! Maybe find someone else to join?")
            return
    team = apiGet("teams/27574")
    embed.set_thumbnail(url=team["flag_url"])
    if team["is_open"]:
        embed.add_field(name="Successfully applied! One of the members will be with you shortly (Using this command won't guarantee you a spot, it just shows that you wanted to join us.)", inline=False, value=f"Username: {name} \nAccount link: {link} \nReason: {reason} \nIf anything didn't look right, feel free to apply again, but check if you already have double quotes around your name and reason.")
        embed.add_field(name="", inline=False, value="P/S: If you applied just for fun, without any intentions of joining the team, good luck joining next time you actually want to.")
        channel = bot.get_channel(1562537373416423524)
        applyEmbed = discord.Embed(title="Team application", color=0xff00ff)
        applyEmbed.add_field(name="", inline=False, value=f"Discord: <@{author.id}> \nUsername: {name} \nAccount link: {link} \nReason: {reason}")
        if channel:
            await channel.send('<@891082078383382548>')
            await channel.send(embed=applyEmbed)
    else:
        embed.add_field(name="Our team is closed or out of slots, please try again later")
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Running on discordpy version {discord.__version__}')
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    content = message.content.strip()
    if content == "s!" or content.startswith("s! "):
        channel = message.channel
        await channel.send("You just wanted to summon me didn't you?")
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("That command doesn't exist. Run `s!c` to see the list of commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: `{error.param.name}`. Run `s!c` for usage.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("One of your arguments isn't valid. Run `s!c` for usage.")
    else:
        await ctx.send("Something went wrong running that command. Pinging <@891082078383382548>")
        raise error

bot.run()
