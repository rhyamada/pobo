CREATE TABLE raw (evt jsonb);
CREATE TABLE events (id text unique, evt jsonb);
CREATE TABLE users (id text unique, usr jsonb);
CREATE TABLE msgs (id text, uid text, eid text, msg text);
ALTER TABLE msgs ADD CONSTRAINT msgs_u UNIQUE(uid,eid);
CREATE TABLE addrs (latlng text unique, adr text);
CREATE TABLE events_history (LIKE events);
CREATE TABLE msgs_history (LIKE msgs);

CREATE OR REPLACE FUNCTION latlng(j jsonb) RETURNS text LANGUAGE SQL IMMUTABLE AS $$
SELECT round(($1->>'latitude')::numeric,4)::text || ',' || round(($1->>'longitude')::numeric,4)::text$$;

CREATE OR REPLACE FUNCTION dst(e jsonb,u jsonb) RETURNS bigint LANGUAGE SQL IMMUTABLE AS $$ 
SELECT (2*6371000*asin(sqrt((sin(radians((($2->>'latitude')::real-($1->>'latitude')::real)/2)))^2 +cos(radians(($1->>'latitude')::real))*cos(radians(($2->>'latitude')::real))  *(sin(radians((($2->>'longitude')::real-($1->>'longitude')::real)/2)))^2)))::bigint $$;

CREATE OR REPLACE FUNCTION msg(e jsonb, dst bigint, adr text)
RETURNS text LANGUAGE 'plpgsql' IMMUTABLE AS $$
DECLARE
n text;
t timestamp;
i bigint;
BEGIN
t := to_timestamp((e->>'end')::real);
i := extract(EPOCH FROM t-now());
SELECT CASE WHEN (e->'tags'->>0) = UPPER(e->'tags'->>0) THEN 'Raid ' || (e->'tags'->>0) ELSE (e->'tags'->>0) END INTO n;
RETURN concat_ws(chr(10),
	concat_ws(' ',
		'*' || n,
		(e->>'iv') || '%',
		'(' ||(e->>'ivs') ||')',
		'a '|| dst::text || 'm*'
	),
	concat_ws(' ',
		'_CP:_ *' || (e->>'cp') || '*', 
		'_Level:_ *' || (e->>'lvl') || '*',
		'_Forma:_ *' || (e->>'form') || '*'
	),
    adr,
    'https://maps.google.com?q='||(e->>'latitude')||','||(e->>'longitude'),
    '_Ate:_ *'||to_char(t,'HH24:MI:SS') || ' (' || (i/60) || 'min)*',
	'desative com /'||(e->'tags'->>0)||'\_0'
);
END;$$;

CREATE OR REPLACE VIEW queue AS WITH 
e AS (SELECT id eid, evt FROM events WHERE (
	evt->>'end')::real > date_part('epoch',now())),
u AS (SELECT id uid, usr FROM users WHERE 
	NOT (usr->>'latitude') IS NULL 
	AND NOT (usr->'filter'->>'') IS NULL ),
ms AS (SELECT id, eid, uid, msg FROM msgs),
m AS (SELECT *, msg(evt,dst,adr) FROM (
SELECT e.*, u.*, dst(usr, evt),
COALESCE(usr->'filter'->>(evt->'tags'->>0),
	usr->'filter'->>'')::bigint AS lmt, adr
FROM e CROSS JOIN u
LEFT JOIN addrs ON latlng = latlng(evt)
WHERE dst(usr, evt) < COALESCE(
	usr->'filter'->>(evt->'tags'->>0),usr->'filter'->>'')::bigint
)_)
SELECT DISTINCT ON (uid) id, eid, uid, m.msg, evt->>'latitude' lat, evt->>'longitude' lng FROM m 
LEFT JOIN ms USING(uid,eid) WHERE 
(ms.id IS NULL) OR split_part(m.msg,'Ate:',1) != split_part(ms.msg,'Ate:',1)
ORDER BY uid, dst;
