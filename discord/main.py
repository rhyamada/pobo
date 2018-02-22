import discord,asyncio,os,re,utils,code

client = discord.Client()
pats = [
	(re.compile('^#(?P<pid>\d+) (?P<name>.*) (?P<gender>.) (?P<dur>[()0-9hms ]+)'),True),	
	(re.compile('\*\*Até.{1,8}(?P<hour>\d\d):(?P<minute>\d\d):(?P<second>\d\d)'),True),
	(re.compile('\*\*Coords:\*\* (?P<latitude>[-.0-9]+),(?P<longitude>[-.0-9]+)'),True),
	(re.compile('\*\*IV:\*\* (?P<iv>[0-9.]+)% \((?P<ivs>[0-9/]+)\)'),False),
	(re.compile('\*\*CP:\*\* (?P<cp>[0-9]+) \| \*\*Level:\*\* (?P<lvl>[0-9]+) \| \*\*Forma:\*\* (?P<form>.+)?'),False)
]
@client.event
@asyncio.coroutine 
def on_message(message):
	if message.embeds and (message.author.name  in os.environ['DISCORD_AUTHOR']):
		for e in message.embeds:
			t = e['title'] + e['description']
			evt = {'pds':e}
			for p, c in pats:
				m = p.search(t)
				if m:
					evt.update(m.groupdict())
				elif c:
					break
			else:
				evt.update({
					'end':utils.get_timestamp(int(evt['hour']),int(evt['minute']),int(evt['second'])),
					'tags':[evt['name']]
				})
				utils.save_event(evt)

client.run(os.environ['DISCORD_CLIENT_TOKEN'], bot=False)