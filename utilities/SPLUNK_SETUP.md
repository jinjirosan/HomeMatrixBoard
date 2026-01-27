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

### 1a. Create Summary Utilities Index

The `summary_utilities` index stores processed and aggregated metrics from the raw `utilities` index. This is used for energy metrics processing and other summary data.

On **Cluster Master**, add to the same index configuration app:

**Directory:** `$SPLUNK_HOME/etc/master-apps/C57_utilities_index/`

**`default/indexes.conf`** (add this section):
```ini
[summary_utilities]
homePath = $SPLUNK_DB/summary_utilities/db
coldPath = $SPLUNK_DB/summary_utilities/colddb
thawedPath = $SPLUNK_DB/summary_utilities/thaweddb
maxTotalDataSizeMB = 5120
frozenTimePeriodInSecs = 15552000
# 180 days retention (longer than raw data for historical analysis)

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

## Energy Metrics Processing (Summary Index)

### Overview

Energy data from EmonPi arrives as raw pulse counts via MQTT topic `utilities/energy/emonpi/pulsecount` and is indexed in the `utilities` index with sourcetype `emonpi:energy`. A saved search processes this raw data to calculate:

- **Power metrics**: Real-time power (kW), rolling averages, variance
- **Energy consumption**: Total power (Wh), daily kWh estimates
- **Cost calculations**: Peak/off-peak costs, total daily costs (EUR)
- **Time-of-use (TOU)**: Peak hours (7:00-23:00) vs off-peak hours
- **Demand analysis**: Daily peak power, peak demand detection
- **Environmental**: CO₂ emissions (kg)

### Create Saved Search for Energy Processing

On **Search Head**, create saved search configuration:

**Directory:** `$SPLUNK_HOME/etc/apps/TA-utilities/local/`

**`savedsearches.conf`:**
```ini
[energy_metrics_processing]
search = index=utilities sourcetype=emonpi:energy \
| spath \
| search mqtt_topic="utilities/energy/emonpi/pulsecount" \
| eval pulsecount=tonumber(mvindex(pulsecount,0)) \
| sort 0 _time \
| delta pulsecount as pulse_increment \
| eval pulse_increment=if(isnull(pulse_increment) OR pulse_increment < 0, 0, pulse_increment) \
| eval total_power_wh_pulse=pulse_increment * 0.1 \
| delta _time as time_delta \
| eval kWh_to_power=if(time_delta > 0, (total_power_wh_pulse / time_delta) * 3600, 0) \
| eval pulse_to_daily_kWh=if(time_delta > 0, (total_power_wh_pulse / time_delta) * 86400 / 1000, 0) \
| eval date_hour=tonumber(strftime(_time, "%H")) \
| eval date_wday=strftime(_time, "%A") \
| eval _day=strftime(_time, "%Y-%m-%d") \
| eval cron_TOU_peak=if(date_hour >= 7 AND date_hour < 23, 1, 0) \
| eval cron_TOU_cost=if(date_hour >= 7 AND date_hour < 23, 1, 0) \
| eval cron_TOU_off_peak=if(cron_TOU_peak=0, 1, 0) \
| eval pulse_peak_cost_increment=pulse_increment * cron_TOU_peak \
| eval pulse_total_cost_increment=pulse_increment * cron_TOU_cost \
| eval pulse_off_peak_cost_increment=pulse_increment * cron_TOU_off_peak \
| streamstats sum(pulse_peak_cost_increment) as pulse_peak_cost_accumulator by _day reset_on_change=t \
| streamstats sum(pulse_total_cost_increment) as pulse_total_cost_accumulator by _day reset_on_change=t \
| streamstats sum(pulse_off_peak_cost_increment) as pulse_off_peak_cost_accumulator by _day reset_on_change=t \
| eval pulse_peak_cost=pulse_peak_cost_accumulator * 0.1 \
| eval pulse_total_cost=pulse_total_cost_accumulator * 0.1 \
| eval pulse_off_peak_cost=pulse_off_peak_cost_accumulator * 0.1 \
| streamstats avg(kWh_to_power) as rolling_avg_power window=12 \
| eval power_variance_pct=if(rolling_avg_power > 0, ((kWh_to_power - rolling_avg_power) / rolling_avg_power) * 100, 0) \
| eventstats max(kWh_to_power) as daily_peak_power by _day \
| eval is_peak_demand=if(kWh_to_power == daily_peak_power, 1, 0) \
| eval estimated_daily_cost_eur=pulse_to_daily_kWh * 0.30 \
| eval co2_emissions_kg=(total_power_wh_pulse / 1000) * 0.475 \
| table _time pulsecount pulse_increment total_power_wh_pulse kWh_to_power pulse_to_daily_kWh rolling_avg_power power_variance_pct daily_peak_power is_peak_demand estimated_daily_cost_eur co2_emissions_kg pulse_total_cost pulse_peak_cost pulse_off_peak_cost pulse_total_cost_accumulator pulse_peak_cost_accumulator pulse_off_peak_cost_accumulator date_hour date_wday _day cron_TOU_peak cron_TOU_off_peak \
| collect index=summary_utilities sourcetype=energy_metrics addtime=true marker=""
dispatch.earliest_time = -1h@h
dispatch.latest_time = now
cron_schedule = */5 * * * *
enableSched = 1
description = Process EmonPi energy pulse counts into calculated metrics (power, cost, TOU, CO2)
```

**Key Configuration:**
- **Schedule**: Runs every 5 minutes (`*/5 * * * *`)
- **Time Range**: Processes last hour of data (`-1h@h` to `now`)
- **Output**: Sends to `summary_utilities` index with sourcetype `energy_metrics`

**Apply configuration:**
```bash
# On Search Head
/opt/splunk/bin/splunk restart
# Or reload saved searches
/opt/splunk/bin/splunk reload savedsearches
```

### Energy Metrics Fields

The saved search outputs the following calculated fields to `summary_utilities`:

| Field | Description | Unit |
|-------|-------------|------|
| `pulsecount` | Raw pulse count from EmonPi | pulses |
| `pulse_increment` | Change in pulses since last reading | pulses |
| `total_power_wh_pulse` | Energy consumed (pulse increment × 0.1) | Wh |
| `kWh_to_power` | Real-time power calculation | kW |
| `pulse_to_daily_kWh` | Projected daily consumption | kWh/day |
| `rolling_avg_power` | 12-point rolling average power | kW |
| `power_variance_pct` | Variance from rolling average | % |
| `daily_peak_power` | Maximum power for the day | kW |
| `is_peak_demand` | Flag if this is the daily peak (1/0) | boolean |
| `estimated_daily_cost_eur` | Projected daily cost (rate: €0.30/kWh) | EUR |
| `co2_emissions_kg` | CO₂ emissions (0.475 kg/kWh) | kg |
| `pulse_total_cost` | Accumulated cost (total pulses × 0.1 × rate) | EUR |
| `pulse_peak_cost` | Accumulated peak hours cost | EUR |
| `pulse_off_peak_cost` | Accumulated off-peak hours cost | EUR |
| `date_hour` | Hour of day (0-23) | hour |
| `date_wday` | Day of week | day name |
| `_day` | Date (YYYY-MM-DD) | date |
| `cron_TOU_peak` | Peak hours flag (7:00-23:00) | 1/0 |
| `cron_TOU_off_peak` | Off-peak hours flag | 1/0 |

### Querying Summary Data

```spl
# All energy metrics
index=summary_utilities sourcetype=energy_metrics

# Current power consumption
index=summary_utilities sourcetype=energy_metrics latest=now
| stats latest(kWh_to_power) as current_power_kW

# Daily cost breakdown
index=summary_utilities sourcetype=energy_metrics earliest=@d
| stats 
    latest(pulse_total_cost) as total_cost_eur,
    latest(pulse_peak_cost) as peak_cost_eur,
    latest(pulse_off_peak_cost) as off_peak_cost_eur
    by _day

# Power trend (last 24 hours)
index=summary_utilities sourcetype=energy_metrics earliest=-24h
| timechart span=15m avg(kWh_to_power) as avg_power_kW

# Peak demand detection
index=summary_utilities sourcetype=energy_metrics earliest=@d
| where is_peak_demand=1
| table _time daily_peak_power

# CO₂ emissions today
index=summary_utilities sourcetype=energy_metrics earliest=@d
| stats sum(co2_emissions_kg) as total_co2_kg
```

### Configuration Notes

**Pulse Conversion Factor:**
- Default: `0.1` Wh per pulse (adjust in saved search if your meter differs)

**Cost Rate:**
- Default: `€0.30` per kWh (adjust `estimated_daily_cost_eur` calculation if needed)

**CO₂ Emission Factor:**
- Default: `0.475` kg CO₂ per kWh (adjust for your region's grid mix)

**Time-of-Use (TOU) Hours:**
- Peak: 7:00-23:00 (16 hours)
- Off-peak: 23:00-7:00 (8 hours)
- Adjust `cron_TOU_peak` condition if your rates differ

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

