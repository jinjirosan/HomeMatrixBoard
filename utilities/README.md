# Utilities Monitoring System

This directory contains the MQTT-to-Splunk integration for utilities monitoring (heating, cold water, hot water, and energy).

## Important: Python Version

⚠️ **This script requires Python 3.6+ (system Python)**

**Splunk Environment Considerations:**
- Splunk 8.2.4 ships with Python 2.7 internally
- This script **must use system Python 3**, not Splunk's Python
- On Debian systems, system Python 3 is typically at `/usr/bin/python3`
- The script includes version checks to prevent running on Python 2.7

**Verified to work with:** Python 3.9.7 on Debian Stretch

## Contents

- **`mqtt_to_splunk.py`** - Main Python script that subscribes to MQTT and forwards to Splunk HEC
- **`splunk_credentials.py.template`** - Configuration template (copy to `splunk_credentials.py`)
- **`mqtt-to-splunk.service`** - Systemd service file for running as daemon
- **`mqtt_topic_utilities.md`** - Complete documentation for MQTT integration
- **`SPLUNK_SETUP.md`** - Splunk configuration guide

## Quick Start

### 1. Install Dependencies

**Important:** Install for system Python 3, not Splunk's Python:

```bash
# Use system Python 3 explicitly
/usr/bin/python3 -m pip install paho-mqtt requests

# Or if pip3 is available:
pip3 install paho-mqtt requests

# Or using the requirements file:
/usr/bin/python3 -m pip install -r requirements.txt
```

**Verify Python version:**
```bash
/usr/bin/python3 --version
# Should show: Python 3.9.7 or higher
```

### 2. Configure Credentials

```bash
cp splunk_credentials.py.template splunk_credentials.py
nano splunk_credentials.py
```

Fill in:
- MQTT broker credentials
- Splunk HEC URL and token
- Splunk index name

### 3. Test the Script

**Always run with system Python 3:**

```bash
cd utilities
/usr/bin/python3 mqtt_to_splunk.py
```

You should see:
```
====================================================================
Starting MQTT to Splunk Forwarder for Utilities Monitoring
====================================================================
Python Version: 3.9.7 (default, ...)
Python Executable: /usr/bin/python3
MQTT Broker: 172.16.234.55:1883
...
Connected to MQTT broker successfully
Subscribed to topic: utilities/heating/#
Subscribed to topic: utilities/hotwater/#
Subscribed to topic: utilities/coldwater/#
Subscribed to topic: utilities/energy/#
```

**If you see Python 2.7 in the output, you're using the wrong Python!**

### 4. Install as Service

**Edit the service file to use system Python 3:**

```bash
# Edit service file
sudo nano mqtt-to-splunk.service

# Update these lines:
# User=root (or your user)
# Group=root (or your group)
# WorkingDirectory=/opt/HomeMatrixBoard/utilities
# ExecStart=/usr/bin/python3 /opt/HomeMatrixBoard/utilities/mqtt_to_splunk.py

# Copy to systemd
sudo cp mqtt-to-splunk.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable mqtt-to-splunk
sudo systemctl start mqtt-to-splunk

# Check status
sudo systemctl status mqtt-to-splunk

# Verify it's using Python 3:
sudo journalctl -u mqtt-to-splunk -n 20 | grep "Python Version"
# Should show: Python Version: 3.13.5

# View logs
sudo journalctl -u mqtt-to-splunk -f
```

**Service Dependencies:**

The service file includes HAProxy as a required dependency:
- `After=haproxy.service` - Service starts after HAProxy is running
- `Requires=haproxy.service` - If HAProxy stops, this service stops too

This ensures the service won't attempt to send data when HAProxy is unavailable.

```bash
# Test dependency behavior
sudo systemctl stop haproxy
sudo systemctl status mqtt-to-splunk
# Should show: inactive (dead) - stopped because HAProxy stopped

sudo systemctl start haproxy
sleep 2
sudo systemctl status mqtt-to-splunk
# Should show: active (running) - started with HAProxy

# View dependency chain
systemctl list-dependencies mqtt-to-splunk
# Should show haproxy.service in the tree
```

## Architecture

```
Smart Gateways (Kamstrup, Elster, EmonPi)
    ↓
MQTT Broker (172.16.234.55:1883)
    ↓
Debian 12 VM
  ├─ mqtt_to_splunk.py (subscribes to MQTT)
  └─ HAProxy (127.0.0.1:8088)
      ├─→ Indexer1 (172.16.234.48:8088)
      └─→ Indexer2 (172.16.234.49:8088)
          ↓
      Indexer Cluster (with replication)
          ↓
      utilities index
```

### High Availability Features

- **HAProxy Load Balancer** - Distributes HEC traffic across both indexers
- **Automatic Failover** - If one indexer fails, traffic routes to the other
- **Health Monitoring** - Checks indexer health every 5 seconds
- **No Single Point of Failure** - Both ingestion and storage are redundant

## Data Flow

### Sourcetype Mapping

The script maps MQTT topics to manufacturer-specific sourcetypes:

| MQTT Topic | Sourcetype | Device |
|------------|------------|--------|
| `utilities/heating/#` | `kamstrup:heating` | Kamstrup heating valve sensor |
| `utilities/hotwater/#` | `kamstrup:hotwater` | Kamstrup hot water valve sensor |
| `utilities/coldwater/#` | `elster:coldwater` | Elster cold water valve sensor |
| `utilities/energy/#` | `emonpi:energy` | EmonPi energy monitor |

### Payload Handling

The script automatically handles different payload formats:

1. **JSON Objects** - Passed through as-is
   ```json
   {"temperature": 68.5, "pressure": 3.2}
   ```

2. **Raw Values** - Wrapped with field name from topic
   - Topic: `utilities/coldwater/watermeter/reading/pulse_count`
   - Payload: `123`
   - Becomes: `{"pulse_count": 123}`

3. **Plain Text** - Wrapped with field name from topic
   - Topic: `utilities/coldwater/watermeter/smart_gateways/mac_address`
   - Payload: `E0:8C:FE:33:D5:14`
   - Becomes: `{"mac_address": "E0:8C:FE:33:D5:14"}`

All events are enriched with:
- `mqtt_topic` - Full MQTT topic path
- `received_at` - Timestamp when received by script

### Fallback Behavior

If a topic doesn't match any mapping, the event uses the default sourcetype configured in Splunk HEC (`mqtt:metrics`).

## Splunk Queries

```spl
# All utility data
index=utilities

# By device type
index=utilities sourcetype=kamstrup:heating
index=utilities sourcetype=kamstrup:hotwater
index=utilities sourcetype=elster:coldwater
index=utilities sourcetype=emonpi:energy

# All Kamstrup devices
index=utilities sourcetype=kamstrup:*

# Compare metrics across utilities
index=utilities sourcetype=kamstrup:* OR sourcetype=elster:*
| stats avg(flow_rate) by sourcetype
```

## Production Status

✅ **System is operational and ingesting data successfully**

**Stats:**
- 939+ events indexed in first 24 hours
- All sourcetypes working correctly (kamstrup:heating, kamstrup:hotwater, elster:coldwater)
- HAProxy providing HA across 2 indexers
- Zero data loss, automatic failover tested

## Troubleshooting

### Python Version Issues

**Problem: Script shows Python 2.7**

```bash
# Check which Python is being used
which python3
# Should show: /usr/bin/python3

# Verify version
/usr/bin/python3 --version
# Should show: Python 3.9.7 or higher

# Check if script has execute permissions
ls -la mqtt_to_splunk.py

# Make sure shebang is correct
head -n 1 mqtt_to_splunk.py
# Should show: #!/usr/bin/env python3

# Always run with explicit path to avoid Splunk's Python
/usr/bin/python3 mqtt_to_splunk.py
```

**Problem: Dependencies not found**

If you get `ModuleNotFoundError: No module named 'paho'`:

```bash
# Install dependencies for system Python 3
/usr/bin/python3 -m pip install --user paho-mqtt requests

# Or install system-wide (requires sudo)
sudo /usr/bin/python3 -m pip install paho-mqtt requests

# Verify installation
/usr/bin/python3 -c "import paho.mqtt.client; print('paho-mqtt OK')"
/usr/bin/python3 -c "import requests; print('requests OK')"
```

### Script won't start

**Common issues and solutions:**

1. **MQTT Client API errors** - Script uses paho-mqtt CallbackAPIVersion.VERSION2
2. **datetime.UTC errors** - Uses `timezone.utc` for compatibility
3. **SSL warnings** - Automatically suppressed when `SPLUNK_VERIFY_SSL = False`

```bash
# Check if credentials file exists
ls -la splunk_credentials.py

# Test MQTT connection manually
mosquitto_sub -h 172.16.234.55 -u splunk_forwarder -P YOUR_PASSWORD -v -t "utilities/#"

# Test Splunk HEC through HAProxy
curl -k https://127.0.0.1:8088/services/collector/event \
  -H "Authorization: Splunk YOUR-TOKEN" \
  -d '{"event": "test", "sourcetype": "mqtt:metrics", "index": "utilities"}'
```

### No data in Splunk

```bash
# Check script logs
sudo journalctl -u mqtt-to-splunk -n 100

# Check for connection errors
sudo journalctl -u mqtt-to-splunk | grep -i error

# Verify MQTT messages are arriving
# (Run script in foreground with debug logging)
```

### SSL Certificate Errors

If you get SSL verification errors with self-signed certificates:

```python
# In splunk_credentials.py (development only!)
SPLUNK_VERIFY_SSL = False
```

**Note:** In production, use proper SSL certificates and keep `SPLUNK_VERIFY_SSL = True`.

## Security

- **Credentials:** Never commit `splunk_credentials.py` to version control (it's in `.gitignore`)
- **HEC Token:** Treat as a password, rotate regularly
- **MQTT Password:** Use strong password for `splunk_forwarder` user
- **SSL/TLS:** Always use SSL in production (`SPLUNK_VERIFY_SSL = True`)

## Maintenance

### Update Dependencies

```bash
pip3 install --upgrade paho-mqtt requests
```

### Restart Service

```bash
sudo systemctl restart mqtt-to-splunk
```

### View Real-time Logs

```bash
sudo journalctl -u mqtt-to-splunk -f
```

### Check Service Status

```bash
sudo systemctl status mqtt-to-splunk
```

## Related Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete deployment walkthrough
- [HAPROXY_SETUP.md](HAPROXY_SETUP.md) - HAProxy load balancer configuration
- [SPLUNK_SETUP.md](SPLUNK_SETUP.md) - Splunk HEC and index configuration
- [SPLUNK_DASHBOARDS.md](SPLUNK_DASHBOARDS.md) - SPL queries and dashboard layouts (all utilities)
- [SPLUNK_COLDWATER_DASHBOARD.md](SPLUNK_COLDWATER_DASHBOARD.md) - Dedicated cold water monitoring dashboard
- [mqtt_topic_utilities.md](mqtt_topic_utilities.md) - Complete MQTT integration guide
- [../documentation/mqtt_broker_setup.md](../documentation/mqtt_broker_setup.md) - MQTT broker configuration

## Support

For issues or questions:
1. Check the logs: `sudo journalctl -u mqtt-to-splunk -n 100`
2. Review the documentation
3. Test MQTT and HEC connectivity separately

