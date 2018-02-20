local json = require "cjson"
local driver = require "luasql.postgres"
local env = assert (driver.postgres())
local author = os.getenv('TELEGRAM_AUTHOR')
local dbstr = os.getenv('DB')

function on_msg_receive (msg)
  if (msg.from.username == author) then
    con = assert (env:connect(dbstr))
    con:execute(string.format("INSERT INTO raw VALUES ($pg$%s$pg$)",json.encode(msg)))
    con:close()
  end
end

function on_our_id (id)
end

function on_user_update (user, what)
end

function on_chat_update (chat, what)
end

function on_secret_chat_update (schat, what)
end

function on_get_difference_end ()
end

function on_binlog_replay_end ()
end