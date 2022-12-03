#/usr/bin/python
import asyncio
import lightbulb, hikari
from lightbulb.ext import tasks
from datetime import datetime


from utils.botapp import BotApp
from utils.api import API
from utils.config import load_config, Config

from sys import argv
if "--debug" in argv:
	config = load_config('config copynew.json')

	debug = True
else:
	config = load_config('config.json')

	debug = False


bot = BotApp(
    config = config,
	debug = debug,
	token = config.discord_token,
	prefix = lightbulb.when_mentioned_or(config.prefix),
	intents = hikari.Intents.ALL,
	delete_unbound_commands = True,
	case_insensitive_prefix_commands = True,
	owner_ids = (config.owner_id),
	default_enabled_guilds = config.debug_guilds,
)

tasks.load(bot)

notifications = []
try:
	old_classes = load_config(config.tmp_filepath)
except:
	old_classes = []


api = API(
	config.base_url,
	config.username,
	config.password,
	config.tmp_filepath
)

bot.rest.fetch_my_guilds()


@bot.listen(hikari.StartedEvent)
async def ready_listener(event : hikari.StartedEvent) -> None:
	global notifications
	await bot.update_presence(
		status = hikari.Status.ONLINE,
		activity = hikari.Activity(
			name = f"{bot._config.prefix}help",
			type = hikari.ActivityType.LISTENING
		)
	)
	bot.unsubscribe(hikari.StartedEvent, ready_listener)
	asyncio.ensure_future(notifier())


async def process_classes(classes: Config):
	global notifications, old_classes
	new_class_names = {i.name:n for n, i in enumerate(classes)}
	for i in old_classes:
		if i.name not in new_class_names:
			if i.id:
				try:await bot.rest.delete_role(i.id)
				except Exception as e:print(e)
			if i.voice_channel:
				try:await bot.rest.delete_channel(i.voice_channel)
				except Exception as e:print(e)
			if i.text_channel:
				try:await bot.rest.delete_channel(i.text_channel)
				except Exception as e:print(e)
			if i.category_channel:
				try:await bot.rest.delete_channel(i.category_channel)
				except Exception as e:print(e)
		else:
			ind = new_class_names[i.name]
			classes[ind].id = i.id
			classes[ind].category_channel = i.category_channel
			classes[index].text_channel = i.text_channel
			classes[index].voice_channel = i.voice_channel

	for index, i in enumerate(classes):
		if i.id is None:
			role = await bot.rest.create_role(config.main_guild_id, name=i.name)
			pov = []
			pov.append(hikari.PermissionOverwrite(
        	    id=config.main_guild_id,
        	    type=hikari.PermissionOverwriteType.ROLE,
        	    deny=(
        	        hikari.Permissions.VIEW_CHANNEL
        	        | hikari.Permissions.CONNECT
        	        | hikari.Permissions.SPEAK
					| hikari.Permissions.STREAM
			    )))
			pov.append(hikari.PermissionOverwrite(id=role.id,
        	    type=hikari.PermissionOverwriteType.ROLE,
        	    allow=(
        	        hikari.Permissions.VIEW_CHANNEL
        	        | hikari.Permissions.CONNECT
        	    )))
			for teacher in i.leader:
				pov.append(hikari.PermissionOverwrite(
					id=teacher,
					type=hikari.PermissionOverwriteType.MEMBER,
					allow=(
						hikari.Permissions.VIEW_CHANNEL
        	        	| hikari.Permissions.SPEAK
        	        	| hikari.Permissions.CONNECT
						| hikari.Permissions.STREAM
					)
				))
			classes[index].id = role.id
			category_channel = await bot.rest.create_guild_category(config.main_guild_id, name=i.name, permission_overwrites=pov)
			classes[index].category_channel = category_channel.id
			text_channel = await bot.rest.create_guild_text_channel(config.main_guild_id, name="Text", category=category_channel, permission_overwrites=pov)
			voice_channel = await bot.rest.create_guild_voice_channel(config.main_guild_id, name="Voice", category=category_channel, permission_overwrites=pov)
			classes[index].text_channel = text_channel.id
			classes[index].voice_channel = voice_channel.id
			i.id = role.id
		for j in i.users:
			try:
				await bot.rest.add_role_to_member(config.main_guild_id, j, i.id, reason="Automatic class creation.")
			except Exception as e:
				print(e)
	old_classes = classes
	old_classes.save()
	notifications = []
	for i in classes:
		for n in i.notifications:
			notifications.append({"id": i.text_channel, 
								  "mention": f"<@&{i.id}>", 
								  "day": datetime.now().weekday()+1,#int(n.split("-")[0]), 
								  "hour": int(n.split("-")[-1].split(":")[0]), 
								  "minute": int(n.split("-")[-1].split(":")[1])}
								)


@tasks.task(m=30, auto_start=True)
async def sync_channels():
	config = await api.get_classes()
	await process_classes(config.classes)



async def notifier():
	global notifications
	while True:
		dt = datetime.now()
		for i in notifications:
			if i['day'] == 0 or i['day'] == (dt.weekday() + 1):
				if i['hour'] == dt.hour and i['minute'] == dt.minute:
					try:
						await bot.rest.create_message(i['id'], i['mention'])
					except Exception as e:
						print(e)
		await asyncio.sleep(60 - dt.second)

@bot.command
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command("logout", "Shuts the bot down", aliases = ['shutdown'], hidden = True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def logout_bot(ctx : lightbulb.Context) -> None:
	await ctx.respond(f"Shutting the bot down", reply = True)
	await bot.close()


if __name__ == '__main__':
	
	bot.run()
