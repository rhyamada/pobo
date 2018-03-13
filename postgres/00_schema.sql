CREATE TABLE raw (evt jsonb);
CREATE TABLE events (id text unique, evt jsonb);
CREATE TABLE users (id text unique, usr jsonb);
CREATE TABLE msgs (id text, uid text, eid text, msg text);
ALTER TABLE msgs ADD CONSTRAINT msgs_u UNIQUE(uid,eid);
CREATE TABLE addrs (latlng text unique, adr text);
CREATE TABLE events_history (LIKE events);
CREATE TABLE msgs_history (LIKE msgs);
CREATE TABLE filter (pokemon_name text unique, iv integer,tags text[]);

CREATE OR REPLACE FUNCTION latlng(j jsonb) RETURNS text LANGUAGE SQL IMMUTABLE AS $$
SELECT round(($1->>'latitude')::numeric,4)::text || ',' || round(($1->>'longitude')::numeric,4)::text$$;

CREATE OR REPLACE FUNCTION dst(e jsonb,u jsonb) RETURNS bigint LANGUAGE SQL IMMUTABLE AS $$ 
SELECT (2*6371000*asin(sqrt((sin(radians((($2->>'latitude')::real-($1->>'latitude')::real)/2)))^2 +cos(radians(($1->>'latitude')::real))*cos(radians(($2->>'latitude')::real))  *(sin(radians((($2->>'longitude')::real-($1->>'longitude')::real)/2)))^2)))::bigint $$;

CREATE OR REPLACE FUNCTION ivm(t text) RETURNS text LANGUAGE SQL STABLE AS $$ 
SELECT iv::text FROM filter WHERE pokemon_name=$1 LIMIT 1 $$;

CREATE OR REPLACE FUNCTION clr(t text) RETURNS text LANGUAGE SQL IMMUTABLE AS $$ 
SELECT regexp_replace($1, '[^0-9A-Za-z]', '', 'g')$$;

CREATE OR REPLACE FUNCTION msg(e jsonb, tags text[], dst bigint, adr text)
RETURNS text LANGUAGE 'plpgsql' IMMUTABLE AS $$
DECLARE
n text;
t timestamp;
i bigint;
d text;
BEGIN
t := to_timestamp((e->>'disappear_time')::real);
i := extract(EPOCH FROM t-now());
SELECT CASE WHEN (tags[1]) = UPPER(tags[1]) THEN 'Raid ' || (tags[1]) ELSE (tags[1]) END INTO n;
SELECT string_agg('/'||clr(unnest)||'_set', ' ') FROM UNNEST(tags) INTO d;
RETURN concat_ws(chr(10),
	CASE WHEN 'EXGYM' = ANY(tags) THEN '<b>CHANCE PASSE EX!!!</b>' END,
	concat_ws(' ',
		'<b>' || n,
		'(' || (e->>'form') || ')',
		(e->>'iv') || '%',
		'a '|| dst::text || 'm</b>'
	),
	concat_ws(' ',
		'(' ||(e->>'ivs') ||')',
		'<i>cp:</i>' || (e->>'cp') || '', 
		'<i>lvl:</i>' || (e->>'level') || '',
		'<i>gym:</i> '|| (e->>'name')
	),
    adr,
    'https://maps.google.com/?q='||(e->>'latitude')||','||(e->>'longitude'),
    '<i>Ate:</i> <b>'||to_char(t,'HH24:MI:SS') || ' (' || (i/60) || 'min)</b>',
    d
);
END;$$;

CREATE OR REPLACE FUNCTION tags(e jsonb) RETURNS text[] AS $$
DECLARE
t text[];
BEGIN
	IF COALESCE(e->>'pokemon_name','') != '' THEN
		t := array_append(t,e->>'pokemon_name');
		IF COALESCE(e->>'iv','') = '100' THEN
			t := array_append(t,'IV100');
		END IF;
		t := array_cat(t,(SELECT tags FROM filter WHERE pokemon_name = e->>'pokemon_name'));
	END IF;
	IF COALESCE(e->>'raid_pokemon_name','') != '' THEN
		t := array_append(t,UPPER(e->>'raid_pokemon_name'));
	END IF;
	IF COALESCE(e->>'park','') != '' THEN
		t := array_append(t,'EXGYM');
	END IF;
	IF COALESCE(e->>'raid_level','') != '' THEN
		t := array_append(t,'LEVEL' || (e->>'raid_level'));
	END IF;
	RETURN t;
END;$$ LANGUAGE 'plpgsql' IMMUTABLE;

CREATE OR REPLACE FUNCTION lmt(tags text[], u jsonb) RETURNS numeric LANGUAGE SQL IMMUTABLE AS $$
SELECT COALESCE(max(l),(u->'filter'->>'Padrao')::numeric,2000) FROM (SELECT(u->'filter'->>(UNNEST(tags)))::numeric l)_$$; 
CREATE OR REPLACE FUNCTION ilmt(tags text[], u jsonb) RETURNS numeric LANGUAGE SQL IMMUTABLE AS $$
SELECT COALESCE(min(l),(u->'ifilter'->>'Padrao')::numeric,90) FROM (SELECT(u->'ifilter'->>(UNNEST(tags)))::numeric l)_$$; 


DROP VIEW IF EXISTS queue;
CREATE OR REPLACE VIEW queue AS WITH 
e AS (SELECT id eid, evt, tags(evt) FROM events WHERE (evt->>'disappear_time')::real > date_part('epoch',now())),
u AS (SELECT id uid, usr FROM users WHERE NOT (usr->>'latitude') IS NULL),
ms AS (SELECT id, eid, uid, msg FROM msgs),
m AS (SELECT *, msg(evt,tags,dst,adr) FROM (
SELECT e.*, u.*, dst(usr, evt),adr
FROM e CROSS JOIN u LEFT JOIN addrs ON latlng = latlng(evt)
WHERE dst(usr, evt) <= lmt(tags,usr)
AND ( tags[1] = UPPER(tags[1]) OR (COALESCE(evt->>'iv','50')::numeric >= ilmt(tags,usr))))_)
SELECT DISTINCT ON (uid) id, eid, uid, m.msg, evt->>'latitude' lat, evt->>'longitude' lng FROM m 
LEFT JOIN ms USING(uid,eid) 
WHERE (ms.id IS NULL) OR split_part(m.msg,'Ate:',1) != split_part(ms.msg,'Ate:',1)
ORDER BY uid, dst;


UPDATE users SET usr=jsonb_set(usr,'{filter,IV100}','"5000"'::jsonb);
UPDATE users SET usr=jsonb_set(usr,'{filter,LEVEL4}','"500"'::jsonb);
UPDATE users SET usr=usr #- '{ifilter,EXGYM}';