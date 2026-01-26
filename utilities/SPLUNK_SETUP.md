# Splunk Configuration for Utilities Monitoring

This guide details the Splunk setup for ingesting utilities data from MQTT gateways.

## Environment

- **Splunk Version:** 8.2.4 on Debian Stretch
- **Splunk Internal Python:** 2.7 (not used by this integration)
- **System Python:** 3.9.7 (used by mqtt_to_splunk.py script)
- **Heavy Forwarder:** Runs the MQTT-to-Splunk bridge script

## Overview

**Architecture:**
- **Index:** `utilities` (stores all utility monitoring data)
- **Sourcetypes:** Device-manufacturer specific
  - `kamstrup:heating` - Kamstrup heating valve sensor
  - `kamstrup:hotwater` - Kamstrup hot water valve sensor
  - `elster:coldwater` - Elster cold water valve sensor
  - `emonpi:energy` - EmonPi energy monitor
- **Default Sourcetype:** `mqtt:metrics` (fallback for unmapped topics)
- **Sources:** Individual device identifiers (heating_main, coldwater_main, etc.)

## Indexer Cluster Configuration

### 1. Create Utilities Index

On **Cluster Master**, create index configuration app:

**Directory:** `$SPLUNK_HOME/etc/master-apps/C57_utilities_index/`

**`default/indexes.conf`:**
```ini
[utilities]
homePath = $SPLUNK_DB/utilities/db
coldPath = $SPLUNK_DB/utilities/colddb
thawedPath = $SPLUNK_DB/utilities/thaweddb
maxTotalDataSizeMB = 10240
frozenTimePeriodInSecs = 7776000
# 90 days retention (adjust as needed)

repFactor = auto
# Uses cluster replication factor
```

**Apply to cluster:**
```bash
/opt/splunk/bin/splunk apply cluster-bundle --answer-yes
```

### 2. Configure HTTP Event Collector (HEC)

On **Cluster Master**, create HEC configuration app:

**Directory:** `$SPLUNK_HOME/etc/master-apps/C57_hec_config/`

**`default/inputs.conf`:**
```ini
[http]
disabled = 0
enableSSL = 1
port = 8088
# SSL certificate paths (if using custom certs)
# serverCert = $SPLUNK_HOME/etc/auth/mycerts/server.pem
# sslPassword = <password>

[http://mqtt_ingestion]
disabled = 0
token = YOUR-HEC-TOKEN-HERE
indexes = utilities
sourcetype = mqtt:metrics
# This is the default sourcetype; script can override
```

**Important Notes:**
- Generate a strong random token (don't use the example above in production)
- Keep the token secure (treat it like a password)
- Token is shared across all indexers in the cluster

**Apply to cluster:**
```bash
/opt/splunk/bin/splunk apply cluster-bundle --answer-yes
```

### 3. Verify HEC is Enabled

On each indexer:

```bash
# Check HEC status
curl -k https://localhost:8089/services/data/inputs/http/http \
  -u admin:password

# Test HEC endpoint
curl -k https://localhost:8088/services/collector/event \
  -H "Authorization: Splunk YOUR-HEC-TOKEN-HERE" \
  -d '{"event": "test", "sourcetype": "mqtt:metrics", "index": "utilities"}'
```

Expected response:
```json
{"text":"Success","code":0}
```

## Field Extractions

### Create Field Extractions App

**Directory:** `$SPLUNK_HOME/etc/apps/TA-utilities/`

**`default/props.conf`:**
```ini
# Kamstrup Heating Sensor
[kamstrup:heating]
SHOULD_LINEMERGE = false
TRUNCATE = 0
TIME_PREFIX = "timestamp"\s*:\s*"
TIME_FORMAT = %Y-%m-%dT%H:%M:%S%Z
MAX_TIMESTAMP_LOOKAHEAD = 32
KV_MODE = json
INDEXED_EXTRACTIONS = json

# Kamstrup Hot Water Sensor
[kamstrup:hotwater]
SHOULD_LINEMERGE = false
TRUNCATE = 0
TIME_PREFIX = "timestamp"\s*:\s*"
TIME_FORMAT = %Y-%m-%dT%H:%M:%S%Z
MAX_TIMESTAMP_LOOKAHEAD = 32
KV_MODE = json
INDEXED_EXTRACTIONS = json

# Elster Cold Water Sensor
[elster:coldwater]
SHOULD_LINEMERGE = false
TRUNCATE = 0
TIME_PREFIX = "timestamp"\s*:\s*"
TIME_FORMAT = %Y-%m-%dT%H:%M:%S%Z
MAX_TIMESTAMP_LOOKAHEAD = 32
KV_MODE = json
INDEXED_EXTRACTIONS = json

# EmonPi Energy Monitor
[emonpi:energy]
SHOULD_LINEMERGE = false
TRUNCATE = 0
TIME_PREFIX = "timestamp"\s*:\s*"
TIME_FORMAT = %Y-%m-%dT%H:%M:%S%Z
MAX_TIMESTAMP_LOOKAHEAD = 32
KV_MODE = json
INDEXED_EXTRACTIONS = json

# Fallback for unmapped topics
[mqtt:metrics]
SHOULD_LINEMERGE = false
TRUNCATE = 0
TIME_PREFIX = "timestamp"\s*:\s*"
TIME_FORMAT = %Y-%m-%dT%H:%M:%S%Z
MAX_TIMESTAMP_LOOKAHEAD = 32
KV_MODE = json
INDEXED_EXTRACTIONS = json
```

**Deploy app:**
- To Cluster Master: `$SPLUNK_HOME/etc/master-apps/TA-utilities/`
- To Search Head: `$SPLUNK_HOME/etc/apps/TA-utilities/`

```bash
# On Cluster Master
/opt/splunk/bin/splunk apply cluster-bundle --answer-yes

# On Search Head
/opt/splunk/bin/splunk restart
```

## Data Model (Optional)

Create a data model for utilities monitoring to enable acceleration and dashboard building.

**`default/datamodels.conf`:**
```ini
[Utilities_Monitoring]
acceleration = 1
acceleration.earliest_time = -7d
```

## Useful Queries

### Basic Searches

```spl
# All utilities data
index=utilities

# By device type
index=utilities sourcetype=kamstrup:heating
index=utilities sourcetype=kamstrup:hotwater
index=utilities sourcetype=elster:coldwater
index=utilities sourcetype=emonpi:energy

# All Kamstrup devices
index=utilities sourcetype=kamstrup:*

# Check for parsing errors (data that fell back to default)
index=utilities sourcetype=mqtt:metrics
```

### Analytics

```spl
# Average flow rate by device
index=utilities 
| stats avg(flow_rate) as avg_flow by sourcetype
| sort - avg_flow

# Flow rate over time
index=utilities sourcetype=kamstrup:* OR sourcetype=elster:*
| timechart avg(flow_rate) by sourcetype

# Temperature monitoring (heating)
index=utilities sourcetype=kamstrup:heating
| timechart avg(temperature) span=1h

# Detect high flow anomalies
index=utilities flow_rate>5.0
| table _time sourcetype source flow_rate
| sort - flow_rate

# Gateway health monitoring
index=utilities 
| stats latest(received_at) as last_seen by sourcetype
| eval time_since = now() - strptime(last_seen, "%Y-%m-%dT%H:%M:%S.%3NZ")
| eval status = if(time_since > 300, "OFFLINE", "ONLINE")
| table sourcetype last_seen status
```

### Alerts

**High Flow Alert:**
```spl
index=utilities (sourcetype=kamstrup:* OR sourcetype=elster:*) flow_rate>5.0
| stats count by sourcetype source flow_rate
```

**Gateway Offline Alert:**
```spl
index=utilities 
| stats latest(_time) as last_seen by sourcetype
| eval minutes_since = round((now() - last_seen) / 60, 2)
| where minutes_since > 5
| table sourcetype minutes_since
```

## Dashboard Example

Create a dashboard for monitoring:

```xml
<dashboard>
  <label>Utilities Monitoring</label>
  <row>
    <panel>
      <title>Flow Rate by Device</title>
      <chart>
        <search>
          <query>index=utilities sourcetype=kamstrup:* OR sourcetype=elster:* | timechart avg(flow_rate) by sourcetype</query>
          <earliest>-60m@m</earliest>
          <latest>now</latest>
        </search>
        <option name="charting.chart">line</option>
      </chart>
    </panel>
  </row>
  <row>
    <panel>
      <title>Temperature (Heating)</title>
      <chart>
        <search>
          <query>index=utilities sourcetype=kamstrup:heating | timechart avg(temperature)</query>
          <earliest>-24h@h</earliest>
          <latest>now</latest>
        </search>
        <option name="charting.chart">area</option>
      </chart>
    </panel>
  </row>
  <row>
    <panel>
      <title>Gateway Status</title>
      <table>
        <search>
          <query>index=utilities | stats latest(_time) as last_seen by sourcetype | eval status = if((now() - last_seen) > 300, "OFFLINE", "ONLINE")</query>
          <earliest>-5m@m</earliest>
          <latest>now</latest>
        </search>
      </table>
    </panel>
  </row>
</dashboard>
```

## Security

### HEC Token Management

```bash
# Rotate HEC token (on Cluster Master)
# 1. Create new token in inputs.conf
# 2. Apply cluster bundle
# 3. Update mqtt_to_splunk script with new token
# 4. Remove old token after verification
```

### Network Security

- Restrict HEC port (8088) to known IPs (Heavy Forwarder)
- Use firewall rules on indexers
- Enable SSL/TLS on HEC (already configured)
- Use proper SSL certificates (not self-signed in production)

## Troubleshooting

### No data appearing in index

```spl
# Check if HEC is receiving data
index=_internal sourcetype=splunkd component=HttpEventCollector
| stats count by status

# Check for errors
index=_internal sourcetype=splunkd component=HttpEventCollector error
| table _time error_message
```

### Data going to wrong sourcetype

```spl
# Check what sourcetypes are being received
index=utilities | stats count by sourcetype

# If data is in mqtt:metrics instead of specific types,
# the MQTT script may not be mapping topics correctly
```

### Performance issues

```bash
# Check indexer queue sizes
/opt/splunk/bin/splunk show-queues

# Monitor HEC performance
index=_internal sourcetype=splunkd component=HttpEventCollector
| stats avg(elapsed_ms) by method
```

## Maintenance

### Index Size Monitoring

```spl
| rest /services/data/indexes/utilities
| table title currentDBSizeMB maxTotalDataSizeMB
```

### Data Retention

Adjust retention in `indexes.conf`:
```ini
[utilities]
frozenTimePeriodInSecs = 7776000  # 90 days
# Or
frozenTimePeriodInSecs = 15552000  # 180 days
```

## Related Documentation

- [mqtt_topic_utilities.md](mqtt_topic_utilities.md) - MQTT integration guide
- [README.md](README.md) - Utilities system overview
- [../documentation/mqtt_broker_setup.md](../documentation/mqtt_broker_setup.md) - MQTT broker setup

