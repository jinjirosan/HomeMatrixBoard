# MQTT Broker Setup Guide

## System Requirements
- Debian 12
- Mosquitto MQTT Broker
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

### 2. Broker Configuration
Create main configuration file (/etc/mosquitto/conf.d/default.conf):

```conf
# Network settings
listener 1883
allow_anonymous false

# Authentication
password_file /etc/mosquitto/passwd
acl_file /etc/mosquitto/conf.d/acl

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information

# Performance
max_queued_messages 1000
max_inflight_messages 20
```

### 3. Access Control Configuration
Create ACL file (/etc/mosquitto/conf.d/acl):

```conf
# Webserver permissions (can publish to all display topics)
user sigfoxwebhookhost
topic write home/displays/#

# Individual display permissions (can only read their own topics)
user wc_display
topic read home/displays/wc

user bathroom_display
topic read home/displays/bathroom

user eva_display
topic read home/displays/eva
```

### 4. User Management
```bash
# Create password file
sudo touch /etc/mosquitto/passwd

# Add users with passwords
sudo mosquitto_passwd -b /etc/mosquitto/passwd sigfoxwebhookhost <password>
sudo mosquitto_passwd -b /etc/mosquitto/passwd wc_display <password>
sudo mosquitto_passwd -b /etc/mosquitto/passwd bathroom_display <password>
sudo mosquitto_passwd -b /etc/mosquitto/passwd eva_display <password>

# Set proper permissions
sudo chown mosquitto:mosquitto /etc/mosquitto/passwd
sudo chmod 600 /etc/mosquitto/passwd
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

## Testing

### 1. Subscribe to Topics
```bash
# Test WC display topic
mosquitto_sub -h localhost -u wc_display -P <password> -t "home/displays/wc"

# Test bathroom display topic
mosquitto_sub -h localhost -u bathroom_display -P <password> -t "home/displays/bathroom"

# Test Eva display topic
mosquitto_sub -h localhost -u eva_display -P <password> -t "home/displays/eva"
```

### 2. Publish Test Messages
```bash
# Test publishing to WC display
mosquitto_pub -h localhost -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" -m '{"name":"WC Tijd","duration":15}'

# Test publishing to bathroom display
mosquitto_pub -h localhost -u sigfoxwebhookhost -P <password> \
    -t "home/displays/bathroom" -m '{"name":"Bathroom Tijd","duration":30}'

# Test publishing to Eva display
mosquitto_pub -h localhost -u sigfoxwebhookhost -P <password> \
    -t "home/displays/eva" -m '{"name":"Eva Tijd","duration":45}'
```

## Troubleshooting

### 1. Check Logs
```bash
# View Mosquitto logs
sudo tail -f /var/log/mosquitto/mosquitto.log

# View system logs
sudo journalctl -u mosquitto
```

### 2. Common Issues
1. Connection refused
   - Check if Mosquitto is running
   - Verify listener configuration
   - Check firewall settings

2. Authentication failed
   - Verify username and password
   - Check ACL permissions
   - Ensure password file is readable by Mosquitto

3. Cannot publish/subscribe
   - Verify ACL permissions
   - Check topic syntax
   - Ensure client is using correct credentials

### 3. Security Recommendations
1. Use strong passwords
2. Consider enabling TLS/SSL
3. Regularly monitor logs
4. Keep Mosquitto updated
5. Restrict network access to trusted IPs
