echo 'Setting up digikala_history'
git clone https://github.com/jadijadi/digikala_history/
cd digikala_history
sudo pip3 install -r requirements.txt
sudo apt install python-stdeb
python setup.py --command-packages=stdeb.command bdist_deb
echo 'Setup finished'
