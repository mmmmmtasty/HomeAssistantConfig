#!/bin/bash

# Take a copy of the appdaemon configuration and sed out the password
sed -r 's/ha_key.+$/ha_key: IllNeverTell/gm' /home/pi/appdaemon/conf/apps.yaml > /home/homeassistant/.homeassistant/appdaemon-apps/apps.yaml

# Commit the latest version
git add .
MESSAGE=$(printf "%s: Committing latest configurations" `date +%Y-%m-%d`)
echo $MESSAGE
git commit -m "$MESSAGE"
git push
