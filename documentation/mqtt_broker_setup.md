# MQTT Broker Setup Guide

This guide details the MQTT broker configuration on the broker VM (172.16.234.55).

## Main Configuration File
Location: `/etc/mosquitto/mosquitto.conf`

```conf
# Place your local configuration in /etc/mosquitto/conf.d/
#
# A full description of the configuration file is at
# /usr/share/doc/mosquitto/examples/mosquitto.conf.example

pid_file /run/mosquitto/mosquitto.pid

include_dir /etc/mosquitto/conf.d

# Default listener
listener 1883

# Security settings
allow_anonymous false
password_file /etc/mosquitto/passwd
acl_file /etc/mosquitto/acl

# Enable persistent session storage
persistence true
persistence_location /var/lib/mosquitto/

# Log settings
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information

# Connection settings
max_keepalive 60
connection_messages true
retry_interval 20
max_inflight_messages 20
max_queued_messages 100

# Timeout settings
socket_timeout 10
keepalive_interval 60
```

## Access Control List (ACL)
Location: `/etc/mosquitto/acl`

```conf
# Publisher (Web server)
user sigfoxwebhookhost
topic write home/displays/#

# Individual display subscribers
user wc_display
topic read home/displays/wc

user bathroom_display
topic read home/displays/bathroom

user eva_display
topic read home/displays/eva
```

## Security Overview
- Anonymous connections are disabled
- Each client requires username/password authentication
- Access control is implemented through ACL file
- Web server can only publish to display topics
- Each display can only subscribe to its own topic

## User Management

### Adding Users
```bash
# Add a new user
sudo mosquitto_passwd -c /etc/mosquitto/passwd <username>

# Add additional users (don't use -c flag as it will overwrite the file)
sudo mosquitto_passwd /etc/mosquitto/passwd <username>
```

### After Configuration Changes
Restart the Mosquitto service after any configuration changes:
```bash
sudo systemctl restart mosquitto
```

## Existing Users
1. Web Server:
   - Username: `sigfoxwebhookhost`
   - Permissions: Can publish to all display topics

2. Displays:
   - `wc_display`: Can only subscribe to `home/displays/wc`
   - `bathroom_display`: Can only subscribe to `home/displays/bathroom`
   - `eva_display`: Can only subscribe to `home/displays/eva`

## Log Files
- Main log file: `/var/log/mosquitto/mosquitto.log`
- Check logs for troubleshooting:
  ```bash
  sudo tail -f /var/log/mosquitto/mosquitto.log
  ``` 