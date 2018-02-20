import utils, re, time

pt = re.compile('ate (\d\d):(\d\d):(\d\d)')
pc = re.compile('http://maps.google.com/maps.q=([-.0-9]+),([-.0-9]+)')
pb = re.compile('Um (.+) selvagem')
pr = re.compile('raide de (.+)!')

while True:
	for e in utils.read_raw_events():
		if 'text' in e['evt']:
			m = e['evt']['text']
			t = pt.search(m)
			c = pc.search(m)
			if t and c:
				b = pb.search(m)
				if b:
					utils.save_event({
						'end':utils.get_timestamp(int(t[1]),int(t[2]),int(t[3])),
						'latitude':c[1], 'longitude':c[2],
						'tags':[b[1],'WILD'], 'bte': e
						})
				else:
					r = pr.search(m)
					if r:
						utils.save_event({
							'end':utils.get_timestamp(int(t[1]),int(t[2]),int(t[3])),
							'latitude':c[1], 'longitude':c[2],
							'tags':[r[1].upper(),'RAID'], 'bte': e
							})
		utils.close_raw_event(e)
	utils.pool_resolve_addr()
	time.sleep(3)