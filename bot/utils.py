import psycopg2,psycopg2.extras,json, os,datetime,urllib.request

def get_timestamp(hour,minute,second,microsecond=0):
	t = datetime.datetime.now().replace(**locals())
	if (t-datetime.datetime.now()).total_seconds() < -79200:
		return int(t.timestamp()+86400)
	return int(t.timestamp())

def save_event(e):
	for k in ['end','latitude','longitude']:
		e[k]=round(float(e[k]),6)
	e['id']="{end:.0f}:{latitude:.6f}:{longitude:.6f}:{tags[0]}".format(**e)
	with psycopg2.connect(os.environ['DB']) as con:
		con.cursor().execute('''INSERT INTO events VALUES (%s, %s) ON CONFLICT(id) DO UPDATE SET evt = events.evt || excluded.evt''',(e['id'],json.dumps(e)))

def load_user(u):
	u.update({"filter":{'':2000}})
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

def save_msg(r):
	with psycopg2.connect(os.environ['DB']) as con:
		c = con.cursor()
		c.execute('''INSERT INTO msgs VALUES (%(id)s, %(uid)s, %(eid)s, %(msg)s)''', r)

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

def pool_resolve_addr():
	with psycopg2.connect(os.environ['DB']) as con:
		c = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		c.execute("""SELECT concat_ws(',',evt->>'latitude',evt->>'longitude') latlng FROM events LEFT JOIN addrs ON (latlng=concat_ws(',',evt->>'latitude',evt->>'longitude'))WHERE adr IS NULL ORDER BY evt->>'end' DESC LIMIT 1;""")
		for r in c:
			with urllib.request.urlopen("https://maps.googleapis.com/maps/api/geocode/json?latlng=%(latlng)s" % r ) as url:
				data = json.loads(url.read().decode())
				if ('results' in data) and len(data['results'])>0:
					r['addr']=data['results'][0]['formatted_address']
					con.cursor().execute('INSERT INTO addrs VALUES(%(latlng)s, %(addr)s)',r)

