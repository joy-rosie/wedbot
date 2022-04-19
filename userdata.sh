#!/bin/bash
sudo apt update
sudo apt install python3.9 -y
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.9 get-pip.py
git clone https://github.com/joy-rosie/wedbot.git /opt/wedbot
python3.9 -m pip install --upgrade pip
python3.9 -m pip install -r /opt/wedbot/requirements.txt
touch /opt/wedbot/.env
echo 'TELEGRAM_BOT_TOKEN=""' >> /opt/wedbot/.env
echo 'TELEGRAM_CHAT_ID=""' >> /opt/wedbot/.env
crontab -l > mycron
echo "* * * * * /usr/bin/python3.9 /opt/wedbot/main.py" >> mycron
crontab mycron
rm mycron
sudo service crond status
