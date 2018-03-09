#
import psycopg2,psycopg2.extras,json,time,code, os,datetime,urllib.request

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
	e['disappear_time'] = e['disappear_time']/1000 if e['disappear_time'] > 1520000000000 else e['disappear_time']	
	if e['disappear_time'] < time.time(): # Já era
		return

	if not 'tags' in e:
		e['tags'] = [e['pokemon_name'] if 'pokemon_name' in e else ( e['raid_pokemon_name'].upper() if e['raid_pokemon_name'] else 'LEVEL'+str(e['raid_level']))]

	if e.get('individual_attack') in e: # Calcula iv
		e['iv'] = round((e['individual_attack']+e['individual_defense']+e['individual_stamina'])*100.0/45.0,1)
	
	e['id']="{disappear_time:.0f}:{latitude:.6f}:{longitude:.6f}:{tags[0]}".format(**e)
	if float(e.get('iv',30)) < ifilter.get(e['tags'][0],80): # IV muito baixo ?
		return	
	if s:
		with psycopg2.connect(os.environ['DB']) as con:
			con.cursor().execute('''INSERT INTO events VALUES (%s, %s) ON CONFLICT(id) DO UPDATE SET evt = events.evt || excluded.evt''',(e['id'],json.dumps(e)))
	print(e['id'])

def load_user(u):
	if not isinstance(u,dict):
		u = u.to_dict()
	u.update({"filter":{'Padrão':2000},'ifilter':{'Padrão':80}})
	with psycopg2.connect(os.environ['DB']) as con:
		c = con.cursor()
		c.execute("SELECT usr FROM users WHERE id='%s'",(u['id'],))
		r = c.fetchone()
		if r:
			u.update(r[0])
	return u

def save_user(u):
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
		c.execute('SELECT * FROM queue')
		for r in c:
			yield r

def read_raw_events():
	with psycopg2.connect(os.environ['DB']) as con:
		c = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		c.execute('SELECT ctid, evt FROM raw')
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
				with urllib.request.urlopen("https://maps.googleapis.com/maps/api/geocode/json?latlng=%(latlng)s" % r ) as url:
					data = json.loads(url.read().decode())
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