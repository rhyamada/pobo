#
import psycopg2,psycopg2.extras,json,time,code, os,datetime,urllib.request
limits = [-24.0,-47.0,-23.0,-46.0]
ifilter = {}
with psycopg2.connect(os.environ['DB']) as con:
	c = con.cursor()
	c.execute('SELECT * FROM filter')
	for r in c:
		ifilter[r[0]]=r[1]


def get_timestamp(hour,minute,second,microsecond=0):
	t = datetime.datetime.now().replace(**locals())
	if (t-datetime.datetime.now()).total_seconds() < -79200:
		return int(t.timestamp()+86400)
	return int(t.timestamp())

def save_event(e,s=True):	
	e['disappear_time'] = e.get('disappear_time') or e.get('raid_end') or get_timestamp(int(e['hour']),int(e['minute']),int(e['second']))
	for k in ['disappear_time','latitude','longitude']:
		e[k]=round(float(e[k]),6)
	if (e['latitude']<limits[0]) or (e['latitude']>limits[2]) or (e['longitude']<limits[1]) or (e['longitude']>limits[3]):
		return None # muito longe
	e['disappear_time'] = e['disappear_time']/1000 if e['disappear_time'] > 1520000000000 else e['disappear_time']	
	if e['disappear_time'] < time.time(): # Já era
		return None
	if 'pokemon_name' in e:
		e['id'] = e['pokemon_name']
		if e.get('individual_attack'): # Calcula iv
			e['iv'] = round((e['individual_attack']+e['individual_defense']+e['individual_stamina'])*100.0/45.0,0)
			e['ivs'] = '%(individual_attack)d/%(individual_defense)d/%(individual_stamina)d' % e
		if 'iv' in e:
			e['iv']=int(float(e['iv']))
		if float(e.get('iv',50)) < ifilter.get(e['id'],80): # IV muito baixo ?
			return	None
		e['_form']=e.pop('form',None)
	elif e.get('raid_pokemon_name'):
		e['id'] = e['raid_pokemon_name'].upper()
	elif e.get('raid_level') in e:
		e['id'] = 'LEVEL'+str(e['raid_level'])
	else:
		return None
	e['id']="{disappear_time:.0f}:{latitude:.6f}:{longitude:.6f}:{id}".format(**e)
	if s:
		with psycopg2.connect(os.environ['DB']) as con:
			con.cursor().execute('''INSERT INTO events VALUES (%s, %s) ON CONFLICT(id) DO UPDATE SET evt = events.evt || excluded.evt''',(e['id'],json.dumps(e)))
	print(e['id'])
	return e['id']

def load_user(u):
	if not isinstance(u,dict):
		u = u.to_dict()
	u.update({
		"filter":{
			'Padrao':'2000',
			'Feebas':'20000',
			'Unown':'40000'
		},
		'ifilter':{
			'Padrao':'90',
			'Feebas':'0',
			'Unown':'0'
		}})
	with psycopg2.connect(os.environ['DB']) as con:
		c = con.cursor()
		c.execute("SELECT usr FROM users WHERE id='%s'",(u['id'],))
		r = c.fetchone()
		if r:
			u.update(r[0])
	return u

def save_user(u):
	if not 'Padrao' in u['filter']:
		u['filter']['Padrao']='2000'
	if not 'Padrao' in u['ifilter']:
		u['ifilter']['Padrao']='90'
		
	with psycopg2.connect(os.environ['DB']) as con:
		c = con.cursor()
		c.execute('''INSERT INTO users VALUES (%s, %s) ON CONFLICT(id) DO UPDATE SET usr = excluded.usr''', (u['id'],json.dumps(u)))
	return load_user(u)

def save_msg(r):
	with psycopg2.connect(os.environ['DB']) as con:
		c = con.cursor()
		c.execute('''INSERT INTO msgs VALUES (%(id)s, %(uid)s, %(eid)s, %(msg)s)
		ON CONFLICT(uid,eid) DO UPDATE SET id = excluded.id, msg=excluded.msg
		''', r)

def read_events():
	with psycopg2.connect(os.environ['DB']) as con:
		c = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		c.execute('SELECT * FROM queue LIMIT 10')
		for r in c:
			yield r

def read_raw_events():
	with psycopg2.connect(os.environ['DB']) as con:
		c = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		c.execute('SELECT ctid, evt FROM raw') # is FOR UPDATE needed
		for r in c:
			yield r

def close_raw_event(e):
	with psycopg2.connect(os.environ['DB']) as con:
		c = con.cursor()
		c.execute('DELETE FROM raw WHERE ctid=%s',(e['ctid'],))

def clean():
	with psycopg2.connect(os.environ['DB']) as con:
		c = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		if clean.cooldown:
			clean.cooldown = clean.cooldown - 1
		else:
			c.execute("""SELECT latlng(evt) FROM events JOIN msgs ON eid=events.id LEFT JOIN addrs ON latlng=latlng(evt) WHERE adr IS NULL ORDER BY evt->>'end' DESC LIMIT 1""")
			for r in c:
				r['gkey']=os.environ['GKEY']
				with urllib.request.urlopen("https://maps.googleapis.com/maps/api/geocode/json?latlng=%(latlng)s&key=%(gkey)s" % r ) as url:
					data = json.loads(url.read().decode())
					print(data)
					if ('results' in data) and len(data['results'])>0:
						r['addr']=data['results'][0]['formatted_address']
						con.cursor().execute('INSERT INTO addrs VALUES(%(latlng)s, %(addr)s)',r)
					else:
						clean.cooldown = 1200
		c.execute('''WITH d AS (DELETE FROM events WHERE id < extract(epoch from now())::text RETURNING *) INSERT INTO events_history SELECT * FROM d;''')
		if c.rowcount:
			print('cleared %d events' % (c.rowcount,))
		c.execute('''WITH d AS (DELETE FROM msgs WHERE eid < extract(epoch from now())::text RETURNING *) INSERT INTO msgs_history SELECT * FROM d;''')
		if c.rowcount:
			print('cleared %d msgs' % (c.rowcount,))
		
clean.cooldown = 0

def close_raw_event(e):
	with psycopg2.connect(os.environ['DB']) as con:
		c = con.cursor()
		c.execute('DELETE FROM raw WHERE ctid=%s',(e['ctid'],))

def nsect(cs,n):
	def bisect(c,d=0):
		p , q = c[:], c[:]
		q[d] = p[2+d] = c[2+d]-(c[2+d] - c[0+d])/2
		return [ p, q ]
	while True:
		r = []
		n -= 1
		for c in cs:
			r += bisect(c,n%2)
		if n < 1:
			break
		cs = r
	return r
