import utils, re, time, code
pats = [
	(re.compile('ate (?P<hour>\d\d):(?P<minute>\d\d):(?P<second>\d\d)'),True),
	(re.compile('http://maps.google.com/maps.q=(?P<latitude>[-.0-9]+),(?P<longitude>[-.0-9]+)'),True),
	(re.compile('^Um (?P<name>.+) selvagem'),False),
	(re.compile('^Detectada raid de (?P<raid>.+)!'),False)]

while True:
	for e in utils.read_raw_events():
		if 'text' in e['evt']:
			t = e['evt']['text']
			evt = {'btg':e['evt']}
			for p, c in pats:
				m = p.search(t)
				if m:
					evt.update(m.groupdict())
				elif c:
					break
			else:
				if ('name' in evt) or ('raid' in evt):
					evt.update({
						'end':utils.get_timestamp(int(evt['hour']),int(evt['minute']),int(evt['second'])),
						'tags':[evt['name'] if 'name' in evt else evt['raid'].upper()]
					})
					utils.save_event(evt)
				else:
					print('failed msg'+t)
		utils.close_raw_event(e)
	utils.clean()
	time.sleep(2)