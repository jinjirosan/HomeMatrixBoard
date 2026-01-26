# Quick Deployment Guide - Debian 12 VM

## Overview

This guide walks through deploying the MQTT-to-Splunk forwarder on a **dedicated Debian 12 (Bookworm) VM** with HAProxy for high availability.

## Architecture

```
MQTT Broker (172.16.234.55)
    ↓
Debian 12 VM (mqtt_to_splunk.py + HAProxy)
    ↓
HAProxy Load Balancer (127.0.0.1:8088)
    ├─→ Indexer1 (172.16.234.48:8088)
    └─→ Indexer2 (172.16.234.49:8088)
```

## Prerequisites

- Fresh Debian 12 (Bookworm) VM
- Minimum specs: 1 vCPU, 512MB RAM, 10GB disk
- Network access to MQTT broker and Splunk indexers
- Root or sudo access

## Prerequisites Check

```bash
# Verify OS version
cat /etc/debian_version
# Expected: 12.x

# Verify system Python 3
/usr/bin/python3 --version
# Expected: Python 3.11.x or higher

# Verify pip is available
/usr/bin/python3 -m pip --version
```

## Installation Steps

### 1. Update System and Install Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip git haproxy socat
```

### 2. Clone Repository

```bash
cd /opt
git clone https://github.com/jinjirosan/HomeMatrixBoard.git
cd HomeMatrixBoard/utilities
```

### 3. Install Python Dependencies

```bash
# Debian 12 uses externally-managed environment
# Install with --break-system-packages flag (safe for dedicated VM)
pip3 install -r requirements.txt --break-system-packages

# Verify installation
/usr/bin/python3 -c "import paho.mqtt.client; print('✓ paho-mqtt')"
/usr/bin/python3 -c "import requests; print('✓ requests')"
```

### 4. Configure HAProxy Load Balancer

See [HAPROXY_SETUP.md](HAPROXY_SETUP.md) for complete details.

**Quick setup:**

```bash
# Backup original config
cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.orig

# Create HAProxy config
nano /etc/haproxy/haproxy.cfg
```

Add the frontend and backend configuration (see HAPROXY_SETUP.md for full config), using your indexer IPs:
- Indexer1: 172.16.234.48:8088
- Indexer2: 172.16.234.49:8088

```bash
# Validate config
haproxy -c -f /etc/haproxy/haproxy.cfg

# Start HAProxy
systemctl restart haproxy
systemctl enable haproxy
systemctl status haproxy
```

**Test HAProxy:**
```bash
curl -k https://127.0.0.1:8088/services/collector/event \
  -H "Authorization: Splunk YOUR-HEC-TOKEN" \
  -d '{"event": "test", "index": "utilities"}'
```

### 5. Configure Script Credentials

```bash
cp splunk_credentials.py.template splunk_credentials.py
nano splunk_credentials.py
```

Fill in:
```python
MQTT_BROKER = "172.16.234.55"
MQTT_PORT = 1883
MQTT_USER = "splunk_forwarder"
MQTT_PASSWORD = "your_actual_password"

# Use HAProxy on localhost
SPLUNK_HEC_URL = "https://127.0.0.1:8088/services/collector/event"
SPLUNK_HEC_TOKEN = "b85b95be-8aa0-49d3-b367-21d9e9192af0"
SPLUNK_INDEX = "utilities"
SPLUNK_VERIFY_SSL = False  # False for self-signed certs
```

### 6. Test the Script

```bash
# Test run (Ctrl+C to stop)
/usr/bin/python3 mqtt_to_splunk.py

# Expected output:
# ============================================================
# Starting MQTT to Splunk Forwarder for Utilities Monitoring
# ============================================================
# Python Version: 3.9.7 ...
# Python Executable: /usr/bin/python3
# MQTT Broker: 172.16.234.55:1883
# Connected to MQTT broker successfully
# Subscribed to topic: utilities/heating/#
# ...
```

### 7. Configure Systemd Service

```bash
# Edit service file
nano mqtt-to-splunk.service
```

Update these values:
```ini
User=splunk
Group=splunk
WorkingDirectory=/opt/splunk/etc/apps/HomeMatrixBoard/utilities
ExecStart=/usr/bin/python3 /opt/splunk/etc/apps/HomeMatrixBoard/utilities/mqtt_to_splunk.py
```

### 8. Install and Start Service

```bash
# Copy to systemd
sudo cp mqtt-to-splunk.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable (start on boot)
sudo systemctl enable mqtt-to-splunk

# Start service
sudo systemctl start mqtt-to-splunk

# Check status
sudo systemctl status mqtt-to-splunk

# Verify Python version in logs
sudo journalctl -u mqtt-to-splunk -n 30 | grep "Python Version"
# Expected: Python Version: 3.9.7
```

### 9. Monitor Logs

```bash
# Real-time logs
sudo journalctl -u mqtt-to-splunk -f

# Last 100 lines
sudo journalctl -u mqtt-to-splunk -n 100

# Check for errors
sudo journalctl -u mqtt-to-splunk | grep -i error
```

### 10. Verify Data in Splunk

On Splunk Search Head:

```spl
# Check for any utilities data (last 5 minutes)
index=utilities earliest=-5m

# Check by sourcetype
index=utilities | stats count by sourcetype
# Expected: kamstrup:heating, kamstrup:hotwater, elster:coldwater

# Check raw events
index=utilities | head 10 | table _time sourcetype source mqtt_topic
```

## Common Issues

### ❌ MQTT Callback API Errors

**Symptom:** `TypeError: on_connect() takes 4 positional arguments but 5 were given`

**Solution:** Script now uses paho-mqtt API VERSION2 with correct callback signatures:
- `on_connect(client, userdata, flags, reason_code, properties)`
- `on_subscribe(client, userdata, mid, reason_codes, properties)`

This is already fixed in the latest version.

### ❌ datetime.UTC Errors

**Symptom:** `AttributeError: type object 'datetime.datetime' has no attribute 'UTC'`

**Solution:** Uses `timezone.utc` instead of `datetime.UTC` for compatibility.

Already fixed in the latest version.

### ❌ Python 2.7 Error

**Symptom:** Script fails with "This script requires Python 3.6 or higher"

**Solution:** 
- Always use `/usr/bin/python3` explicitly
- Check systemd service file uses `/usr/bin/python3`
- Debian 12 uses Python 3.13.5 by default

### ❌ Module Not Found

**Symptom:** `ModuleNotFoundError: No module named 'paho'`

**Solution:**
```bash
# Install for system Python 3 (with --user flag)
/usr/bin/python3 -m pip install --user paho-mqtt requests

# Or system-wide
sudo /usr/bin/python3 -m pip install paho-mqtt requests
```

### ❌ MQTT Connection Failed

**Symptom:** "Failed to connect to MQTT broker. Return code: 4"

**Solution:**
- Code 4 = Bad username or password
- Verify credentials in `splunk_credentials.py`
- Test manually: `mosquitto_sub -h 172.16.234.55 -u splunk_forwarder -P password -t "utilities/#"`

### ❌ HEC Connection Failed

**Symptom:** "Failed to send to Splunk. Status: 403"

**Solution:**
- Verify HEC token is correct
- Check HEC is enabled on indexer
- Test: `curl -k https://indexer:8088/services/collector/event -H "Authorization: Splunk YOUR-TOKEN" -d '{"event":"test"}'`

### ❌ No Data in Splunk

**Symptom:** Script runs but no data appears in Splunk

**Solution:**
1. Check script logs: `sudo journalctl -u mqtt-to-splunk -n 100`
2. Check MQTT messages are arriving: Run script in foreground
3. Check Splunk HEC logs: `index=_internal sourcetype=splunkd component=HttpEventCollector`
4. Verify index exists: `| rest /services/data/indexes | search title=utilities`

## Service Management

```bash
# Start
sudo systemctl start mqtt-to-splunk

# Stop
sudo systemctl stop mqtt-to-splunk

# Restart
sudo systemctl restart mqtt-to-splunk

# Status
sudo systemctl status mqtt-to-splunk

# Disable (don't start on boot)
sudo systemctl disable mqtt-to-splunk

# Enable (start on boot)
sudo systemctl enable mqtt-to-splunk

# View logs
sudo journalctl -u mqtt-to-splunk -f
```

## Testing Checklist

- [x] System Python 3.11+ installed and verified (Python 3.13.5 confirmed)
- [x] Dependencies installed (`paho-mqtt`, `requests`)
- [x] HAProxy configured and running
- [x] HAProxy stats page accessible (port 9000)
- [x] Both indexers showing UP in HAProxy
- [x] `splunk_credentials.py` configured
- [x] Script runs successfully in foreground
- [x] Python version shows 3.13.x (not 2.7) in logs
- [x] MQTT connection successful
- [x] MQTT callback API VERSION2 working
- [x] No SSL warnings in logs
- [x] Systemd service configured with correct paths
- [x] Service starts and stays running
- [x] Data appears in Splunk `utilities` index
- [x] Sourcetypes are correct (kamstrup:heating, kamstrup:hotwater, elster:coldwater)
- [x] 900+ events indexed successfully

## Success Indicators

✅ **Script is working if you see:**
- Python Version: 3.13.x in logs
- "Connected to MQTT broker successfully"
- "Subscribed to topic: utilities/..." messages
- No error messages, SSL warnings, or deprecation warnings in logs
- Clean output with only INFO level messages

✅ **HAProxy is working if:**
- Stats page shows both indexers UP (green) at http://VM_IP:9000/stats
- Can send test events through localhost:8088
- Failover works when one indexer is stopped

✅ **Splunk integration working if:**
- `index=utilities | stats count` returns 900+ events
- `index=utilities | stats count by sourcetype` shows kamstrup:heating, kamstrup:hotwater, elster:coldwater
- Events have proper timestamps and fields (mqtt_topic, received_at)
- Raw values are properly wrapped (e.g., `{"pulse_count": 123}`)
- Data is flowing continuously (check last 5 minutes)

**Production Stats (26 Jan 2026):**
- 939 events in first 24 hours
- 3 sourcetypes active (kamstrup:heating, kamstrup:hotwater, elster:coldwater)
- Zero data loss
- HAProxy providing automatic failover

## Support

For issues:
1. Check logs: `sudo journalctl -u mqtt-to-splunk -n 100`
2. Verify Python version in logs
3. Test MQTT connection separately
4. Test HEC connection with curl
5. Review [README.md](README.md) and [SPLUNK_SETUP.md](SPLUNK_SETUP.md)

