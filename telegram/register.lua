function on_msg_receive (msg)
end

function exit()
	os.exit()
end

function on_our_id (id)
	f = io.open('/root/.telegram-cli/id', 'w')
	f:write(tostring(id))
	f:close()
	print("Our id is: "..tostring(id).."\nexiting in 3s...")
	postpone (exit, false, 3.0)
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