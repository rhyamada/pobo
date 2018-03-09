#!/usr/bin/env python
# -*- coding: utf-8 -*-
import code,datetime,time,rocket,utils,os

R = rocket.Rocket(os.environ['SCAN'])
lat, lng, rad = -23.5869147,-46.6619466,15.0/110

c = [lat-rad,lng-rad,lat+rad,lng+rad]
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
for g in R.gyms(c)['gyms']:
	if g.get('raid_end',False):
		utils.save_event(g,False)


for s in nsect([c],1):
	print(s)
	for p in R.pokemons(s)['pokemons']:
		utils.save_event(p,False)

'''
select e.id,dst(evt,usr) from users u
cross join events e 
where u.id='16720681' 
order by dst limit 5;
'''