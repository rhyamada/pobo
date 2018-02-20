import discord,asyncio,os,re,utils

client = discord.Client()
pt = re.compile('Até.{1,8}(\d\d):(\d\d):(\d\d)')
pc = re.compile('Coords.{1,8} ([-.0-9]+),([-.0-9]+)')
pb = re.compile('#(\d+) (.*) (.) ([()0-9hms ]+)')

@client.event
@asyncio.coroutine 
def on_message(message):
	if message.embeds and (message.author.name  in os.environ['DISCORD_AUTHOR']):
		for e in message.embeds:
			t = pt.search(e['description'])
			c = pc.search(e['description'])
			b = pb.search(e['title'])
			if t and c and b:
				utils.save_event({
					'end':utils.get_timestamp(int(t[1]),int(t[2]),int(t[3])),
					'latitude':c[1], 'longitude':c[2], 'tags':[b[2]], 'pid':b[1], 'g':b[3], 'pds':e
					})
client.run(os.environ['DISCORD_CLIENT_TOKEN'], bot=False)