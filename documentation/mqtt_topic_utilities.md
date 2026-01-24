# MQTT Utilities Integration Guide

This guide documents the MQTT integration for utility monitoring gateways (heating, cold water, and hot water valve sensors).

## Overview

Three Smart Gateway devices monitor valves on the home's utility systems:
- **Heating system** valve monitoring
- **Cold water** valve monitoring  
- **Hot water** valve monitoring

These gateways publish real-time metrics via MQTT to:
1. Provide real-time monitoring and alerting
2. Forward data to Splunk's `utilities` index for analysis

## Topic Structure

### Topic Hierarchy

```
utilities/heating/#
utilities/coldwater/#
utilities/hotwater/#
```

Each gateway uses its own topic prefix to publish telemetry data. The `#` wildcard covers any subtopics the gateways might publish (metrics, status, alerts, etc.).

### Topic Purpose

Depending on what the Smart Gateways support, topics may be structured as:

**Option 1: With subtopics**
- `utilities/heating/metrics` - Real-time telemetry (valve position, flow rate, pressure, temperature)
- `utilities/heating/status` - Gateway health (connectivity, battery, signal strength)
- `utilities/heating/alerts` - Alarms and anomaly detection

**Option 2: Flat structure**
- `utilities/heating` - All data published to base topic with message type in payload

### Example Message Formats

**Metrics:**
```json
{
  "timestamp": "2026-01-24T10:30:45Z",
  "gateway_id": "heating-gw-001",
  "valve_position": 75,
  "flow_rate": 2.5,
  "pressure": 3.2,
  "temperature": 68.5,
  "unit": "fahrenheit"
}
```

**Status:**
```json
{
  "timestamp": "2026-01-24T10:30:45Z",
  "gateway_id": "heating-gw-001",
  "state": "online",
  "signal_strength": -65,
  "battery": 87,
  "uptime_seconds": 86400
}
```

**Alerts:**
```json
{
  "timestamp": "2026-01-24T10:30:45Z",
  "gateway_id": "coldwater-gw-001",
  "alert_type": "high_flow",
  "severity": "warning",
  "message": "Flow rate exceeded 5.0 L/min",
  "value": 5.3
}
```

## Gateway Configuration

### Smart Gateway MQTT Settings

Each gateway is configured through its web interface with the following parameters:

#### Heating Gateway
```
MQTT server (host or ip):    172.16.234.55
MQTT port:                    1883
MQTT username:                heating_gateway
MQTT password:                [secure-password]
MQTT prefix:                  utilities/heating
MQTT interval (seconds):      30
Enable encryption (tls):      ☐ (unchecked)
```

#### Cold Water Gateway
```
MQTT server (host or ip):    172.16.234.55
MQTT port:                    1883
MQTT username:                coldwater_gateway
MQTT password:                [secure-password]
MQTT prefix:                  utilities/coldwater
MQTT interval (seconds):      30
Enable encryption (tls):      ☐ (unchecked)
```

#### Hot Water Gateway
```
MQTT server (host or ip):    172.16.234.55
MQTT port:                    1883
MQTT username:                hotwater_gateway
MQTT password:                [secure-password]
MQTT prefix:                  utilities/hotwater
MQTT interval (seconds):      30
Enable encryption (tls):      ☐ (unchecked)
```

### Configuration Notes

- **MQTT prefix**: Defines the base topic path for all messages from that gateway
- **MQTT interval**: How frequently the gateway publishes data (30 seconds recommended)
- **TLS encryption**: Disabled for now (can be enabled later if broker supports it)
- **Separate credentials**: Each gateway has its own username for security and tracking

## Broker Configuration

### User Management

Create MQTT users for the three gateways and Splunk forwarder:

```bash
# Create gateway users
sudo mosquitto_passwd /etc/mosquitto/passwd heating_gateway
sudo mosquitto_passwd /etc/mosquitto/passwd coldwater_gateway
sudo mosquitto_passwd /etc/mosquitto/passwd hotwater_gateway

# Create Splunk forwarder user
sudo mosquitto_passwd /etc/mosquitto/passwd splunk_forwarder
```

### Access Control List (ACL)

Update `/etc/mosquitto/acl` to include utility gateway permissions:

```conf
# Existing display users (keep these)
user sigfoxwebhookhost
topic write home/displays/#

user wc_display
topic read home/displays/wc

user bathroom_display
topic read home/displays/bathroom

user eva_display
topic read home/displays/eva

# Utility gateway users (each can only publish to their own topics)
user heating_gateway
topic write utilities/heating/#

user coldwater_gateway
topic write utilities/coldwater/#

user hotwater_gateway
topic write utilities/hotwater/#

# Splunk forwarder (subscribes to all utility topics)
user splunk_forwarder
topic read utilities/#

# Optional: monitoring system (read everything)
user monitor_system
topic read home/displays/#
topic read utilities/#
```

### Apply Configuration Changes

After updating the ACL file, restart Mosquitto:

```bash
sudo systemctl restart mosquitto
sudo systemctl status mosquitto
```

**Important:** ACL changes always require a restart to take effect.

## Testing and Monitoring

### Monitor Specific Gateway

```bash
# Monitor heating gateway
mosquitto_sub -h 172.16.234.55 -u splunk_forwarder -P <password> -v -t "utilities/heating/#"

# Monitor cold water gateway
mosquitto_sub -h 172.16.234.55 -u splunk_forwarder -P <password> -v -t "utilities/coldwater/#"

# Monitor hot water gateway
mosquitto_sub -h 172.16.234.55 -u splunk_forwarder -P <password> -v -t "utilities/hotwater/#"
```

### Monitor All Utility Gateways

```bash
# Subscribe to all utility topics at once
mosquitto_sub -h 172.16.234.55 -u splunk_forwarder -P <password> -v -t "utilities/#"
```

### Test Gateway Authentication

Test if a gateway can connect with its credentials:

```bash
# From broker or local machine
mosquitto_sub -h 172.16.234.55 -u hotwater_gateway -P <password> -t "utilities/hotwater/#" -v
```

If successful, you'll see `(waiting for messages)` and the connection stays open.

### Test Publishing

Test if a gateway can publish messages:

```bash
# Publish test message
mosquitto_pub -h 172.16.234.55 -u heating_gateway -P <password> \
  -t "utilities/heating/test" -m '{"test": true, "timestamp": "2026-01-24T10:30:45Z"}'

# Subscribe to verify (in another terminal)
mosquitto_sub -h 172.16.234.55 -u splunk_forwarder -P <password> \
  -v -t "utilities/heating/#"
```

### Monitor Mosquitto Logs

Watch connection attempts and errors in real-time:

```bash
# On broker VM
sudo tail -f /var/log/mosquitto/mosquitto.log
```

Look for:
- `New client connected from X.X.X.X as heating_gateway` → Success
- `Bad username or password` → Password incorrect
- `Not authorized` → ACL permission issue

## Troubleshooting

### Gateway Shows "Error, check connection"

**Step 1: Verify user exists**
```bash
sudo cat /etc/mosquitto/passwd | grep hotwater_gateway
```

**Step 2: Verify ACL permissions**
```bash
sudo cat /etc/mosquitto/acl | grep -A 1 hotwater
```

Should show:
```
user hotwater_gateway
topic write utilities/hotwater/#
```

**Step 3: Test authentication manually**
```bash
mosquitto_sub -h 172.16.234.55 -u hotwater_gateway -P <password> -t "utilities/hotwater/#" -v
```

**Step 4: Check Mosquitto logs**
```bash
sudo tail -f /var/log/mosquitto/mosquitto.log
```

Then trigger reconnect on gateway and observe error messages.

### Common Issues

1. **Missing ACL entry**
   - Symptom: "Not authorized" in logs
   - Solution: Add user to `/etc/mosquitto/acl` and restart Mosquitto

2. **Wrong password**
   - Symptom: "Bad username or password" in logs
   - Solution: Recreate password with `sudo mosquitto_passwd /etc/mosquitto/passwd username`

3. **Typo in gateway configuration**
   - Symptom: Connection error on gateway
   - Solution: Double-check IP address, username, password (no extra spaces!)

4. **ACL changes not applied**
   - Symptom: Still getting authorization errors after ACL update
   - Solution: Restart Mosquitto (`sudo systemctl restart mosquitto`)

### Password Management

To change password for existing user:

```bash
# Interactive (prompts for password)
sudo mosquitto_passwd /etc/mosquitto/passwd heating_gateway

# Non-interactive
sudo mosquitto_passwd -b /etc/mosquitto/passwd heating_gateway NewPassword123

# Restart after password change
sudo systemctl restart mosquitto
```

**Warning:** Never use `-c` flag when updating - it will erase all existing users!

## Splunk Integration

### Topic to Index Mapping

All utility topics are routed to the `utilities` index in Splunk.

**Sourcetype mapping:**
- `utilities/heating/#` → sourcetype: `utilities:heating`
- `utilities/coldwater/#` → sourcetype: `utilities:coldwater`
- `utilities/hotwater/#` → sourcetype: `utilities:hotwater`

### MQTT to Splunk Forwarder

A subscriber process (MQTT-to-Splunk forwarder) subscribes to `utilities/#` and forwards all messages to Splunk's `utilities` index.

Required credentials:
- **Username:** `splunk_forwarder`
- **Topic:** `utilities/#` (read access)

### Splunk Queries

Example queries for the utilities index:

```spl
# All utility data
index=utilities

# Specific utility
index=utilities sourcetype=utilities:heating

# High flow alerts
index=utilities alert_type=high_flow

# Gateway health monitoring
index=utilities message_type=status state=offline
```

## Security Considerations

### Current Security Model

1. **Authentication required** - Anonymous connections disabled
2. **Unique credentials** - Each gateway has its own username/password
3. **Least privilege access** - Gateways can only publish to their own topics
4. **Read segregation** - Only Splunk forwarder and monitoring user can read utility topics

### Future Enhancements

1. **TLS/SSL encryption** - Encrypt MQTT traffic in transit
2. **Certificate-based auth** - Replace passwords with client certificates
3. **Network segmentation** - Isolate utility network from display network
4. **Rate limiting** - Prevent gateway flooding
5. **Alert thresholds** - Set up automated alerts for anomalies

## Architecture Integration

### System Components

```
┌─────────────────┐       ┌──────────────────┐       ┌─────────────┐
│ Heating Gateway │──────▶│                  │──────▶│             │
│ (Smart Gateway) │       │   MQTT Broker    │       │   Splunk    │
└─────────────────┘       │  172.16.234.55   │       │  utilities  │
                          │    Port 1883      │       │    index    │
┌─────────────────┐       │                  │       │             │
│Coldwater Gateway│──────▶│                  │──────▶│             │
└─────────────────┘       └──────────────────┘       └─────────────┘
                                    │
┌─────────────────┐                 │
│Hotwater Gateway │─────────────────┘
└─────────────────┘
```

### Topic Isolation

The utility topics (`utilities/#`) are completely separate from display topics (`home/displays/#`):

- **Display system**: Home automation displays showing timers and presets
- **Utility system**: Valve monitoring and telemetry collection
- **No overlap**: Different users, different topics, different purposes

### Data Flow

1. Smart Gateways measure valve metrics (every 30 seconds)
2. Gateways publish JSON messages to MQTT broker
3. MQTT broker authenticates and authorizes based on ACL
4. Splunk forwarder subscribes to `utilities/#`
5. Forwarder writes messages to Splunk `utilities` index
6. Data available for real-time monitoring and historical analysis

## Maintenance

### Regular Tasks

1. **Monitor gateway connectivity**
   ```bash
   mosquitto_sub -h 172.16.234.55 -u monitor_system -P <password> -v -t "utilities/+/status"
   ```

2. **Review logs for errors**
   ```bash
   sudo journalctl -u mosquitto --since "1 hour ago" | grep -i error
   ```

3. **Check Splunk ingestion**
   - Verify data is flowing to `utilities` index
   - Check for gaps in telemetry

4. **Update gateway firmware**
   - Check Smart Gateway manufacturer for updates
   - Test on one gateway before updating all

### Backup Configuration

Important files to backup:
- `/etc/mosquitto/passwd` - User credentials (encrypted)
- `/etc/mosquitto/acl` - Access control list
- `/etc/mosquitto/mosquitto.conf` - Main broker config

```bash
# Backup command
sudo tar -czf mosquitto-config-backup-$(date +%Y%m%d).tar.gz \
  /etc/mosquitto/passwd \
  /etc/mosquitto/acl \
  /etc/mosquitto/mosquitto.conf
```

## Related Documentation

- [MQTT Broker Setup](mqtt_broker_setup.md) - Main broker configuration
- [MQTT Setup Guide](mqtt_setup.md) - General MQTT setup and testing
- [Architecture Overview](architecture.md) - Complete system architecture
- [Security Guide](security.md) - Security best practices

## Support

For issues with:
- **MQTT broker**: Check logs at `/var/log/mosquitto/mosquitto.log`
- **Smart Gateways**: Consult Smart Gateway documentation
- **Splunk integration**: Verify forwarder service and index configuration

