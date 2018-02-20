import telegram, time, os, code, re, json, psycopg2,utils

pc = re.compile('^/?([^_]*?)_?([0-9]+)$')
def on_message(m):
	u = utils.load_user(m.from_user.to_dict())
	if m.location:
		u.update(m.location.to_dict())
		utils.save_user(u)
		m.reply_text('Nova posição salva')
		return
	c = pc.match(m.text)
	if c:
		u['filter'][c.group(1)] = c.group(2)
		utils.save_user(u)
		m.reply_text('Filtro atualizado')
		return


import code
def on_event(e):
	if e['id'] is not None:
		b.editMessageText(chat_id=e['uid'],message_id=e['id'],text=e['msg'],parse_mode='Markdown')
	else:
		e['id']=b.send_message(chat_id=e['uid'],text=e['msg'],parse_mode='Markdown').message_id
	utils.save_msg(e)
	time.sleep(0.5)
	
b = telegram.Bot(os.environ['TT'])
b.send_message(chat_id=int(os.environ['EU']),text='starting')
o = None
while True:
	try:
		for e in b.get_updates(offset=o, timeout=10):
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