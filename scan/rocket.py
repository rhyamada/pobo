#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests, re, time, json, code

class Rocket:
	def __init__(_,url):
		_.u = url
		_.s = requests.session()
		_.s.headers.update({
			'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7','Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
			'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/63.0.3239.84 Chrome/63.0.3239.84 Safari/537.36'
		})
		_.token = re.compile("token = '([^']+)").search(_.s.get(url).text).group(1)
		_.s.headers.update({
			'Origin': url,'Referer': url,'authority': re.compile("//([^/]+)").search(url).group(1),
			'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8','Accept': 'application/json, text/javascript, */*; q=0.01',
			'X-Requested-With': 'XMLHttpRequest'
		})
	def raw(_,data):
		j = _.s.post(_.u+'raw_data', data=data).json()
		for k in j:
			if isinstance(j[k],dict):
				j[k] = list(j[k].values())
		return j
	def gyms(_,c):
		return _.raw([
			('pokemon', 'false'),('pokestops', 'false'),('luredonly', 'false'),
			('gyms', 'true'),('scanned', 'false'),('spawnpoints', 'false'),
			('swLat', c[0]),('swLng', c[1]),('neLat', c[2]),('neLng', c[3]),
			('reids', ''),('eids', ''),('token', _.token)])

	def pokemons(_,c):
		return _.raw([
			('pokemon', 'true'),('pokestops', 'false'),('luredonly', 'false'),
			('gyms', 'false'),('scanned', 'false'),('spawnpoints', 'false'),
			('swLat', c[0]),('swLng', c[1]),('neLat', c[2]),('neLng', c[3]),
			('oSwLat', c[0]),('oSwLng', c[1]),('oNeLat', c[2]),('oNeLng', c[3]),
			('reids', ''),('eids', ''),('token', _.token)])
