# Quick Deployment Guide - Heavy Forwarder

## Prerequisites Check

```bash
# Verify system Python 3
/usr/bin/python3 --version
# Expected: Python 3.9.7

# Verify pip is available
/usr/bin/python3 -m pip --version

# Check Splunk's Python (DO NOT USE THIS)
/opt/splunk/bin/python --version
# Expected: Python 2.7.x (we're NOT using this!)
```

## Installation Steps

### 1. Clone/Copy Repository to Heavy Forwarder

```bash
cd /opt/splunk/etc/apps/
# Or wherever you want to install
git clone https://github.com/jinjirosan/HomeMatrixBoard.git
cd HomeMatrixBoard/utilities
```

### 2. Install Python Dependencies

```bash
# Install for system Python 3 (NOT Splunk's Python)
/usr/bin/python3 -m pip install --user -r requirements.txt

# Verify installation
/usr/bin/python3 -c "import paho.mqtt.client; print('✓ paho-mqtt')"
/usr/bin/python3 -c "import requests; print('✓ requests')"
```

### 3. Configure Credentials

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

SPLUNK_HEC_URL = "https://indexer1.yourdomain.com:8088/services/collector/event"
SPLUNK_HEC_TOKEN = "b85b95be-8aa0-49d3-b367-21d9e9192af0"
SPLUNK_INDEX = "utilities"
SPLUNK_VERIFY_SSL = True  # False for self-signed certs (dev only)
```

### 4. Test the Script

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

### 5. Configure Systemd Service

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

### 6. Install and Start Service

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

### 7. Monitor Logs

```bash
# Real-time logs
sudo journalctl -u mqtt-to-splunk -f

# Last 100 lines
sudo journalctl -u mqtt-to-splunk -n 100

# Check for errors
sudo journalctl -u mqtt-to-splunk | grep -i error
```

### 8. Verify Data in Splunk

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

### ❌ Python 2.7 Error

**Symptom:** Script fails with "This script requires Python 3.6 or higher"

**Solution:** 
- Always use `/usr/bin/python3` explicitly
- Check systemd service file uses `/usr/bin/python3`
- Never use `/opt/splunk/bin/python`

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

- [ ] System Python 3.9.7+ installed and verified
- [ ] Dependencies installed (`paho-mqtt`, `requests`)
- [ ] `splunk_credentials.py` configured
- [ ] Script runs successfully in foreground
- [ ] Python version shows 3.9.7 (not 2.7) in logs
- [ ] MQTT connection successful
- [ ] Systemd service configured with correct paths
- [ ] Service starts and stays running
- [ ] Data appears in Splunk `utilities` index
- [ ] Sourcetypes are correct (kamstrup:*, elster:*)

## Success Indicators

✅ **Script is working if you see:**
- Python Version: 3.9.7 in logs
- "Connected to MQTT broker successfully"
- "Subscribed to topic: utilities/..." messages
- No error messages in journalctl

✅ **Splunk integration working if:**
- `index=utilities | stats count` returns events
- `index=utilities | stats count by sourcetype` shows kamstrup:*, elster:*
- Events have proper timestamps and fields
- Data is flowing continuously (check last 5 minutes)

## Support

For issues:
1. Check logs: `sudo journalctl -u mqtt-to-splunk -n 100`
2. Verify Python version in logs
3. Test MQTT connection separately
4. Test HEC connection with curl
5. Review [README.md](README.md) and [SPLUNK_SETUP.md](SPLUNK_SETUP.md)

