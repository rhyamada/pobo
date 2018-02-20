FROM python:latest
RUN ln -fs /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && dpkg-reconfigure -f noninteractive tzdata
RUN pip3 install psycopg2-binary discord python-telegram-bot
CMD ["python3", "/main.py"]
ADD *.py /
