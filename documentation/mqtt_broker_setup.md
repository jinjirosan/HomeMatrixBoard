# MQTT Broker Setup Guide

This guide details how to install and configure the MQTT broker on the broker VM (172.16.234.55).

## System Requirements
- Debian 12
- Root or sudo access
- Basic Linux knowledge

## Installation Steps

### 1. System Setup
```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Mosquitto and utilities
sudo apt install -y mosquitto mosquitto-clients
```

### 2. Main Configuration File
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

### 3. Access Control List (ACL)
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

### 4. User Management

#### Create Password File
```bash
# Create password file
sudo touch /etc/mosquitto/passwd

# Set proper permissions
sudo chown mosquitto:mosquitto /etc/mosquitto/passwd
sudo chmod 600 /etc/mosquitto/passwd
```

#### Add Users
```bash
# Add webserver user (can publish to all display topics)
sudo mosquitto_passwd -b /etc/mosquitto/passwd sigfoxwebhookhost <password>

# Add display users (can only subscribe to their own topics)
sudo mosquitto_passwd -b /etc/mosquitto/passwd wc_display <password>
sudo mosquitto_passwd -b /etc/mosquitto/passwd bathroom_display <password>
sudo mosquitto_passwd -b /etc/mosquitto/passwd eva_display <password>
```

**Note:** When adding additional users, don't use the `-c` flag as it will overwrite the existing file. Use:
```bash
sudo mosquitto_passwd /etc/mosquitto/passwd <username>
```

### 5. Service Management
```bash
# Restart Mosquitto to apply changes
sudo systemctl restart mosquitto

# Enable Mosquitto to start on boot
sudo systemctl enable mosquitto

# Check service status
sudo systemctl status mosquitto
```

## Security Overview

- **Authentication**: Anonymous connections are disabled
- **Access Control**: Each client requires username/password authentication
- **Topic Permissions**: 
  - Web server can only publish to display topics
  - Each display can only subscribe to its own topic
- **Password Storage**: Passwords stored in encrypted format

## Existing Users

1. **Web Server** (`sigfoxwebhookhost`)
   - Permissions: Can publish to all display topics (`home/displays/#`)

2. **Displays**
   - `wc_display`: Can only subscribe to `home/displays/wc`
   - `bathroom_display`: Can only subscribe to `home/displays/bathroom`
   - `eva_display`: Can only subscribe to `home/displays/eva`

## Testing

### Subscribe to Topics
```bash
# Test WC display topic
mosquitto_sub -h localhost -u wc_display -P <password> -t "home/displays/wc"

# Test bathroom display topic
mosquitto_sub -h localhost -u bathroom_display -P <password> -t "home/displays/bathroom"

# Test Eva display topic
mosquitto_sub -h localhost -u eva_display -P <password> -t "home/displays/eva"
```

### Publish Test Messages
```bash
# Test timer mode for WC display
mosquitto_pub -h localhost -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" -m '{"name":"WC Tijd","duration":15}'

# Test preset mode for WC display
mosquitto_pub -h localhost -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" -m '{"mode":"preset","preset_id":"on_air"}'

# Test preset with custom name and duration
mosquitto_pub -h localhost -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" -m '{"mode":"preset","preset_id":"on_air","name":"Studio 1","duration":3600}'
```

For more testing examples, see [Display Operation Guide](display_operation.md).

## Troubleshooting

### Check Logs
```bash
# View Mosquitto logs
sudo tail -f /var/log/mosquitto/mosquitto.log

# View system logs
sudo journalctl -u mosquitto -f
```

### Common Issues

1. **Connection refused**
   - Check if Mosquitto is running: `sudo systemctl status mosquitto`
   - Verify listener configuration in main config file
   - Check firewall settings: `sudo ufw status`

2. **Authentication failed**
   - Verify username and password are correct
   - Check ACL permissions match the user
   - Ensure password file is readable by Mosquitto: `sudo ls -l /etc/mosquitto/passwd`

3. **Cannot publish/subscribe**
   - Verify ACL permissions for the user
   - Check topic syntax matches ACL rules
   - Ensure client is using correct credentials

### Security Recommendations

1. Use strong passwords for all users
2. Consider enabling TLS/SSL for encrypted connections
3. Regularly monitor logs for suspicious activity
4. Keep Mosquitto updated: `sudo apt update && sudo apt upgrade mosquitto`
5. Restrict network access to trusted IPs if possible

## Log Files

- **Main log file**: `/var/log/mosquitto/mosquitto.log`
- **Check logs for troubleshooting**:
  ```bash
  sudo tail -f /var/log/mosquitto/mosquitto.log
  ```
