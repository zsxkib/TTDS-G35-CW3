echo "START BACK-END"
sudo apt update;
sudo apt install mongodb -y;
pip3 install -r "back_end/requirments.txt";
python3 back_end/manage.py runserver;