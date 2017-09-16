#!/bin/bash

# Take a copy of the appdaemon configuration and sed out the password
sed -r 's/ha_key.+$/ha_key: IllNeverTell/gm' /home/pi/appdaemon/conf/appdaemon.yaml > /home/homeassistant/.homeassistant/appdaemon-apps/appdaemon.yaml
cp /home/pi/appdaemon/conf/apps.yaml /home/homeassistant/.homeassistant/appdaemon-apps/apps.yaml
cp -r /home/pi/appdaemon/conf/custom_css/* /home/homeassistant/.homeassistant/appdaemon-apps/custom_css/
cp -r /home/pi/appdaemon/conf/custom_widgets/* /home/homeassistant/.homeassistant/appdaemon-apps/custom_widgets/

# Commit the latest version
git add .
MESSAGE=$(printf "%s: Committing latest configurations" `date +%Y-%m-%d`)
echo $MESSAGE
git commit -m "$MESSAGE"
git push
