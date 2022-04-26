#!/usr/bin/env bash

sudo pip3 install -r requirements.txt

sudo cp install/services/*.service /lib/systemd/system/
mkdir /usr/share/Tidepool-frontend
sudo cp -r * /usr/share/Tidepool-frontend/

sudo systemctl daemon-reload
sudo systemctl restart tidepool-api.service
sudo systemctl enable tidepool-api.service