CREATE TABLE raw (evt jsonb);
CREATE TABLE events (id text unique, evt jsonb);
CREATE TABLE users (id text unique, usr jsonb);
CREATE TABLE msgs (id text, uid text, eid text, msg text);
CREATE TABLE addrs (latlng text, adr text);

CREATE OR REPLACE FUNCTION dst(e jsonb,u jsonb) RETURNS bigint LANGUAGE SQL IMMUTABLE AS $$ 
SELECT (2*6371000*asin(sqrt(
        (sin(radians((($2->>'latitude')::real-($1->>'latitude')::real)/2)))^2
        +cos(radians(($1->>'latitude')::real))*cos(radians(($2->>'latitude')::real))
        *(sin(radians((($2->>'longitude')::real-($1->>'longitude')::real)/2)))^2
    )))::bigint
$$;

CREATE OR REPLACE FUNCTION msg(e jsonb, dst bigint) RETURNS text LANGUAGE 'plpgsql' IMMUTABLE AS $$
DECLARE
r text;
t timestamp;
i bigint;
BEGIN
t := to_timestamp((e->>'end')::real);
i := extract(EPOCH FROM t-now());
RETURN concat_ws(chr(10),
    '*' || e->'tags'->>0 ||'* [a'|| dst::text || 'metros]',
    'https://maps.google.com?q='||(e->>'latitude')||(e->>'longitude'),
    '*disponivel até:* '||to_char(t,'HH24:MI:SS') || ' (' || (i/60) || 'min)'
);
END;$$;

CREATE OR REPLACE VIEW queue AS WITH 
e AS (SELECT id eid, evt FROM events WHERE (evt->>'end')::real > date_part('epoch',now())),
u AS (SELECT id uid, usr FROM users WHERE NOT (usr->>'latitude') IS NULL ),
m AS (SELECT *, msg(evt,dst) FROM (
SELECT e.*, u.*, dst(usr, evt),COALESCE(usr->'filter'->>(evt->'tags'->>0),usr->'filter'->>'')::bigint AS lmt
FROM e CROSS JOIN u
WHERE dst(usr, evt) < COALESCE(usr->'filter'->>(evt->'tags'->>0),usr->'filter'->>'')::bigint
)_)
SELECT id, eid, uid, m.msg FROM m LEFT JOIN msgs USING(uid,eid) WHERE (msgs.id IS NULL) OR (split_part(m.msg,'(',1) != split_part(msgs.msg,'(',1)) ORDER BY dst;
