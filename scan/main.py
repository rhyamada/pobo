#!/usr/bin/env python
# -*- coding: utf-8 -*-
import code,datetime,time,rocket,utils,os
from random import shuffle

data = []
with open('/scan/.scan') as f:
	for r in f.read().split('\n'):
		try:
			u,*c = r.split(' ')
			if u:
				c = [float(v) for v in c]
				data.append((u,c))
		except:
			pass
while True:
	shuffle(data)
	for u, c in data:
		R = rocket.Rocket(u)
		i = j = 0
		for g in R.gyms(c)['gyms']:
			if g.get('raid_end',False):
				if utils.save_event(g):
					i += 1
				else:
					j += 1
		for p in R.pokemons(c)['pokemons']:
			if utils.save_event(p):
				i += 1
			else:
				j += 1
	time.sleep(10)