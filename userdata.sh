sudo apt update
sudo apt install python3.9 -y
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.9 get-pip.py
git clone https://github.com/joy-rosie/wedbot.git
cd wedbot
python3.9 -m pip install --upgrade pip
python3.9 -m pip install -r requirements.txt
