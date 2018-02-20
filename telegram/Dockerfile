FROM python:latest
RUN ln -fs /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && dpkg-reconfigure -f noninteractive tzdata
WORKDIR /
RUN apt-get update && \
apt-get install -y gcc make git zlib1g-dev libevent-dev libreadline-dev  libjansson-dev libconfig-dev \
lua5.2 liblua5.2-dev lua-sql-postgres lua-cjson
RUN git clone --recursive https://github.com/vysheng/tg.git
WORKDIR /tg
RUN ./configure && make
ADD .telegram-cli /root/.telegram-cli
ADD *.lua /
CMD ["bin/telegram-cli","-s","/bot.lua"]

