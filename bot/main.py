from telegram import ReplyKeyboardRemove,ReplyKeyboardMarkup,KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton as IB
import telegram, math, time, os, code, re, json, psycopg2,utils

print('starting')

def r(v):
	v = float(v)
	l = math.log10(v)
	e = math.floor(l)
	l -= e
	if l > math.log10(4.99):
		return str(5 * (10**e))
	if l > math.log10(1.99):
		return str(2 * (10**e))
	return str(10**e)

with open('/root/.telegram-cli/id') as f:
	myid = int(f.readline())

def filter(evt,b):
	if evt.message and evt.message.text:
		t,m = evt.message.text,evt.message
	elif evt.callback_query and evt.callback_query.data:
		code.interact(local=dict(locals(),**globals()))
		t,m = evt.callback_query.data,evt.callback_query
	else:
		return None
	u = utils.load_user(m.from_user.to_dict())
	c = re.compile('^/([^_]*)_([0-9]+)?%$').match(t)
	if c:
		p, i = c.groups()
		u['ifilter'][p] = i
	else:
		c = re.compile('^/([^_]*)_([0-9]+)?$').match('/Padrão_'+t if re.compile('^[0-9]+$').match(t) else t)
		if not c:
			return None
		p, d = c.groups()
		u['filter'][p] = d

	d,i = u['filter'].get(p),u['ifilter'].get(p)
	k = [[]]
	if d == '0':
		t, d = '%s:\nalerta desativado' % (p,),u['filter']['Padrão']
		k[0].append(IB("Ativar", callback_data='/%s_' % (p,)))
	else:
		if d is None:
			d = u['filter']['Padrão']
			t = '%s:\ndistância padrão: %sm' % (p,d)
		else:
			t = '%s:\ndistancia máxima: %sm' % (p,d)
			k[0].append(IB("Padrão", callback_data='/%s_' % (p,)))
		if p != 'Padrão':
			k[0].append(IB("Desativar", callback_data='/%s_0' % (p,)))
		k.append([])
		if i is None:
			t += '\nIV minimo padrão: %s%%' % (u['ifilter'].get('Padrão','90'),)
		else:
			t += '\nIV mínimo custom: %s%%' % (i,)
			k[1].append(IB("Padrão", callback_data='/%s_%%' % (p,)))
		for j in ['0','80','90','95','97','100']:
			if j != i:
				k[1].append(IB("%s%%"%(j,), callback_data='/%s_%s%%' % (p,j)))
		
	d = max(50,float(d))
	d1, d2 = r(d*0.9), r(d*3.9)
	k[0].append(IB(d1+"m", callback_data='/%s_%s' % (p,d1)))
	k[0].append(IB(d2+"m", callback_data='/%s_%s' % (p,d2)))

	if isinstance(m, telegram.callbackquery.CallbackQuery):
		m.answer()
		try:
			u['filter_msg']=m.edit_message_text(t,reply_markup=InlineKeyboardMarkup(k)).to_dict()
		except:
			pass
	else:
		try:
			if 'filter_msg' in u: # clear button of old msg
				b.edit_message_reply_markup(chat_id=u['filter_msg']['chat']['id'],message_id=u['filter_msg']['message_id'])
		except:
			pass
		u['filter_msg']=m.reply_text(text=t,reply_markup=InlineKeyboardMarkup(k)).to_dict()
	print(u)
	return utils.save_user(u)

def location(e):
	if e.message and e.message.location:
		u = utils.load_user(e.message.from_user.to_dict())
		u.update(e.message.location.to_dict())
		e.message.reply_text('Nova posição salva')
	elif e.edited_message and e.edited_message.location:
		u = utils.load_user(e.edited_message.from_user.to_dict())
		u.update(e.edited_message.location.to_dict())
	else:
		return False
	utils.save_user(u)
	return True

def on_event(e):
	if e['id'] is not None:
		b.editMessageText(chat_id=e['uid'],message_id=e['id'],text=e['msg'],parse_mode='html',disable_web_page_preview=True)
	else:
		e['id']=b.send_message(chat_id=e['uid'],text=e['msg'],parse_mode='html',disable_web_page_preview=True).message_id
		b.sendLocation(chat_id=e['uid'],latitude=e['lat'],longitude=e['lng'],disable_notification=True).message_id
	utils.save_msg(e)

b = telegram.Bot(os.environ['TELEGRAM_TOKEN'])

o = None
while True:
	try:
		for e in b.get_updates(offset=o, timeout=10):
			print(e.to_dict())
			if location(e):
				print('Location updated')
			elif filter(e,b):
				print('Filter updated')
			elif e.message and e.message.text:
				e.message.reply_text('Envie sua localização e uma distancia')
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