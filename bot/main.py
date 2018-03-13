from telegram import ReplyKeyboardRemove,ReplyKeyboardMarkup,KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton as IB
import telegram, math, time, os, code, re, json, psycopg2,utils

from math import log10

print('starting')
F = [0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 7.5, 10.0]
def inc(v):
	e, f = divmod(log10(float(v)*1.02), 1)
	for i in range(len(F)):
		if f < log10(F[i]):
			return str(int(F[i]*(10.0**e)))
def dec(v):
	e, f = divmod(log10(float(v)*0.98), 1)
	for i in range(len(F)-1,0,-1):
		if f > log10(F[i]):
			return str(int(F[i]*(10.0**e)))

with open('/root/.telegram-cli/id') as f:
	myid = int(f.readline())

def help(evt,b):
	if evt.message and evt.message.text:
		if evt.message.text == '/sair':
			u = utils.load_user(e.message.from_user)
			if 'latitude' in u:
				del u['latitude']
				utils.save_user(u)
			evt.message.reply_text(text='Bye bye')
		else:
			evt.message.reply_text(text='''Esse bot aceita os seguintes exemplos de comandos:
- Enviar sua localização
- Compartilhar sua localização
- <pre>2000</pre> 
- /2000
- <pre>90%</pre>
- /filtro
- /Aron_set
- /sair
''',parse_mode='html')
		return True
	return False

def menu(evt,b):
	if evt.message and evt.message.text and evt.message.text in ['/m','/_m','/filtro','/filtros','/filter','/filters']:
		u = utils.load_user(evt.message.from_user)
		t = 'Filtros definidos:'
		for p in sorted({'Padrao','Ultra','Rare','EXGYM','LEVEL1','LEVEL2','LEVEL3','LEVEL4','LEVEL5'}.union(u['filter'].keys()).union(u['ifilter'].keys())):
			t += '\n/'+p+'_set '
			if p in u['filter']:
				t += str(u['filter'][p])+'m '
			if p in u['ifilter']:
				t += str(u['ifilter'][p])+'%'
		evt.message.reply_text(text=t)
		return True
	return False
		
	
def filter(evt,b):
	if evt.message and evt.message.text:
		t,m = evt.message.text,evt.message
	elif evt.callback_query and evt.callback_query.data:
		t,m = evt.callback_query.data,evt.callback_query
	else:
		return None
	u = utils.load_user(m.from_user.to_dict())
	c = re.compile('^/([^_]*)_([0-9]+)?%$').match('/Padrao_'+t if re.compile('^[0-9]+%$').match(t) else t)
	if c:
		p, i = c.groups()
		if i is None:
			u['ifilter'].pop(p,None)
		else:
			u['ifilter'][p] = i
	else:
		c = re.compile('^/([^_]*)_([0-9]+)?$').match('/Padrao_'+t if re.compile('^[0-9]+$').match(t) else t)
		if c:
			p, d = c.groups()
			if (d is None) and (p in u['filter']):
				u['filter'].pop(p,None)
			else:
				u['filter'][p] = d
		else:
			c = re.compile('^/([^_]+)_(m|set|reset)$').match(t)
			if c:
				p = c.group(1)
				if c.group(2)=='reset':
					if p=='Padrao':
						u['filter'][p]='2000'
						u['ifilter'][p]='90'
					else:
						u['filter'].pop(p,None)
						u['ifilter'].pop(p,None)
			else:
				return None
	d,i = u['filter'].get(p),u['ifilter'].get(p)
	k = [[]]
	if d == '0':
		t, d = '%s:\nalerta desativado' % (p,),u['filter']['Padrao']
		k[0].append(IB("Ativar", callback_data='/%s_' % (p,)))
	else:
		if d is None:
			d = u['filter']['Padrao']
			t = '%s:\ndistância padrão: %sm' % (p,d)
		else:
			t = '%s:\ndistancia máxima: %sm' % (p,d)
			k[0].append(IB("Padrao", callback_data='/%s_' % (p,)))
		if p != 'Padrao':
			k[0].append(IB("Desativar", callback_data='/%s_0' % (p,)))
		k.append([])
		if p != p.upper():
			if i is None:
				t += '\nIV minimo padrão: %s%%' % (u['ifilter'].get('Padrao','90'),)
			else:
				t += '\nIV mínimo custom: %s%%' % (i,)
				k[1].append(IB("Padrão", callback_data='/%s_%%' % (p,)))
			for j in ['0','80','90','95','97','100']:
				if j != i:
					k[1].append(IB("%s%%"%(j,), callback_data='/%s_%s%%' % (p,j)))
		
	d = max(50,float(d))
	d1, d2 = dec(d), inc(d)
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
				del u['filter_msg']
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
			elif menu(e,b):
				print('Menu')
			elif filter(e,b):
				print('Filter updated')
			elif help(e,b):
				print('ajuda')
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