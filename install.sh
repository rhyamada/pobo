#!/bin/bash
set -e

read -e -p 'Enter discord client token: ' -i "$DISCORD_CLIENT_TOKEN" DISCORD_CLIENT_TOKEN
export DISCORD_CLIENT_TOKEN=$DISCORD_CLIENT_TOKEN

read -e -p 'Enter telegram bot token: ' -i "$TELEGRAM_TOKEN" TELEGRAM_TOKEN
export TELEGRAM_TOKEN=$TELEGRAM_TOKEN

DISCORD_AUTHOR=${DISCORD_AUTHOR:-Wise King}
read -e -p 'Enter discord client author: ' -i "$DISCORD_AUTHOR" DISCORD_AUTHOR
export DISCORD_AUTHOR="$DISCORD_AUTHOR"

TELEGRAM_AUTHOR=${TELEGRAM_AUTHOR:-BeiruteMasterBot}
read -e -p 'Enter telegram client author: ' -i "$TELEGRAM_AUTHOR" TELEGRAM_AUTHOR
export TELEGRAM_AUTHOR="$TELEGRAM_AUTHOR"

#define the template.
cat << EOF > .env
DB=user='postgres' host='postgres'
DISCORD_CLIENT_TOKEN=$DISCORD_CLIENT_TOKEN
TELEGRAM_TOKEN=$TELEGRAM_TOKEN
DISCORD_AUTHOR=$DISCORD_AUTHOR
TELEGRAM_AUTHOR=$TELEGRAM_AUTHOR
EOF

# monta ambientes
docker-compose build
# sobe banco
docker-compose up -d postgres
# sobe container para registrar conta no telegram-cli
docker-compose run --no-deps telegram /tg/bin/telegram-cli -s /register.lua
# sobe demais containers
docker-compose up -d
