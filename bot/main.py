import telegram, time, os, code, re, json, psycopg2,utils

with open('/root/.telegram-cli/id') as f:
	myid = int(f.readline())

pc = re.compile('^/?([^_]*?)_?([0-9]*)$')
def on_message(m):
	u = utils.load_user(m.from_user.to_dict())
	if m.location:
		u.update(m.location.to_dict())
		utils.save_user(u)
		m.reply_text('Nova posição salva')
		return
	if m.text:
		c = pc.match(m.text)
		if c:
			if c.group(2) == '':
				if c.group(1) in u['filter']:
					del u['filter'][c.group(1)]
			else:
				u['filter'][c.group(1)] = c.group(2)
			utils.save_user(u)
			m.reply_text('Filtro atualizado')
		return

import code
def on_event(e):
	if e['id'] is not None:
		b.editMessageText(chat_id=e['uid'],message_id=e['id'],text=e['msg'],parse_mode='Markdown',disable_web_page_preview=True)
	else:
		e['id']=b.send_message(chat_id=e['uid'],text=e['msg'],parse_mode='Markdown',disable_web_page_preview=True).message_id		
		b.sendLocation(chat_id=e['uid'],latitude=e['lat'],longitude=e['lng'],disable_notification=True).message_id
	utils.save_msg(e)
	
b = telegram.Bot(os.environ['TELEGRAM_TOKEN'])
b.send_message(chat_id=myid,text='starting')
o = None
while True:
	try:
		for e in b.get_updates(offset=o, timeout=5):
			if not e.message:
				continue
			m = e.message
			on_message(m)
			o = e.update_id + 1
		for e in utils.read_events():
			on_event(e)
			break
	except psycopg2.OperationalError as e:
		print(e)
	except telegram.error.NetworkError as e:
		print(e)
	except telegram.error.Unauthorized:
		o += 1