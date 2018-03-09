FROM python:latest
RUN ln -fs /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && dpkg-reconfigure -f noninteractive tzdata
RUN pip3 install requests psycopg2-binary discord python-telegram-bot
ENV PYTHONUNBUFFERED 1
CMD ["python3", "/main.py"]
ADD *.py /
