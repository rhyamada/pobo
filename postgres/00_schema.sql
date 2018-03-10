CREATE TABLE raw (evt jsonb);
CREATE TABLE events (id text unique, evt jsonb);
CREATE TABLE users (id text unique, usr jsonb);
CREATE TABLE msgs (id text, uid text, eid text, msg text);
ALTER TABLE msgs ADD CONSTRAINT msgs_u UNIQUE(uid,eid);
CREATE TABLE addrs (latlng text unique, adr text);
CREATE TABLE events_history (LIKE events);
CREATE TABLE msgs_history (LIKE msgs);
CREATE TABLE filter (pokemon_name text unique, iv integer);

CREATE OR REPLACE FUNCTION latlng(j jsonb) RETURNS text LANGUAGE SQL IMMUTABLE AS $$
SELECT round(($1->>'latitude')::numeric,4)::text || ',' || round(($1->>'longitude')::numeric,4)::text$$;

CREATE OR REPLACE FUNCTION dst(e jsonb,u jsonb) RETURNS bigint LANGUAGE SQL IMMUTABLE AS $$ 
SELECT (2*6371000*asin(sqrt((sin(radians((($2->>'latitude')::real-($1->>'latitude')::real)/2)))^2 +cos(radians(($1->>'latitude')::real))*cos(radians(($2->>'latitude')::real))  *(sin(radians((($2->>'longitude')::real-($1->>'longitude')::real)/2)))^2)))::bigint $$;

CREATE OR REPLACE FUNCTION ivm(t text) RETURNS text LANGUAGE SQL STABLE AS $$ 
SELECT iv::text FROM filter WHERE pokemon_name=$1 LIMIT 1 $$;

CREATE OR REPLACE FUNCTION clr(t text) RETURNS text LANGUAGE SQL IMMUTABLE AS $$ 
SELECT regexp_replace($1, '[^0-9A-Za-z]', '', 'g')$$;

CREATE OR REPLACE FUNCTION msg(e jsonb, dst bigint, adr text)
RETURNS text LANGUAGE 'plpgsql' IMMUTABLE AS $$
DECLARE
n text;
t timestamp;
i bigint;
d text;
BEGIN
t := to_timestamp((e->>'disappear_time')::real);
i := extract(EPOCH FROM t-now());
SELECT CASE WHEN (e->'tags'->>0) = UPPER(e->'tags'->>0) THEN 'Raid ' || (e->'tags'->>0) ELSE (e->'tags'->>0) END INTO n;
SELECT string_agg('/'||clr(value)||'_m', ' ') from jsonb_array_elements_text(e->'tags') INTO d;
RETURN concat_ws(chr(10),
	concat_ws(' ',
		'<b>' || n,
		(e->>'iv') || '%',
		'a '|| dst::text || 'm</b>'
	),
	concat_ws(' ',
		'(' ||(e->>'ivs') ||')',
		'<i>cp:</i>' || (e->>'cp') || '', 
		'<i>lvl:</i>' || (e->>'level') || '',
		'<i>form:</i> ' || (e->>'form') || ''
	),
    adr,
    'https://maps.google.com/?q='||(e->>'latitude')||','||(e->>'longitude'),
    '<i>Ate:</i> <b>'||to_char(t,'HH24:MI:SS') || ' (' || (i/60) || 'min)</b>',
    d
);
END;$$;

DROP VIEW IF EXISTS queue;
CREATE OR REPLACE VIEW queue AS WITH 
e AS (SELECT id eid, evt FROM events WHERE (evt->>'disappear_time')::real > date_part('epoch',now())),
u AS (SELECT id uid, usr FROM users WHERE NOT (usr->>'latitude') IS NULL),
ms AS (SELECT id, eid, uid, msg FROM msgs),
m AS (SELECT *, msg(evt,dst,adr) FROM (
SELECT e.*, u.*, dst(usr, evt),adr
FROM e CROSS JOIN u
LEFT JOIN addrs ON latlng = latlng(evt)
WHERE 
dst(usr, evt) <= (CASE WHEN '100' = evt->>'iv' THEN 3 ELSE 1 END)*COALESCE(usr->'filter'->>(clr(evt->'tags'->>0)),usr->'filter'->>'Padrao','2000')::numeric
AND COALESCE(evt->>'iv','50')::numeric >= COALESCE(usr->'ifilter'->>(clr(evt->'tags'->>0)),ivm(evt->'tags'->>0),usr->'ifilter'->>'Padrao','90')::numeric
)_)
SELECT DISTINCT ON (uid) id, eid, uid, m.msg, evt->>'latitude' lat, evt->>'longitude' lng FROM m 
LEFT JOIN ms USING(uid,eid) 
WHERE (ms.id IS NULL) OR split_part(m.msg,'Ate:',1) != split_part(ms.msg,'Ate:',1)
ORDER BY uid, dst;


 select * from events where id = '1520648757:-23.671813:-46.779179:Feebas'
--update users set usr = ( usr #- '{ifilter,""}' #- '{ifilter,Padrão}' #- '{filter,Padrão}' #- '{filter,""}' );
--update users set usr = jsonb_set(usr,'{ifilter,Padrao}','90', True)

