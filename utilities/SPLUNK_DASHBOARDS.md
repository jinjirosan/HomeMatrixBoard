# Splunk Dashboards for Utilities Monitoring

This document provides SPL (Search Processing Language) queries for creating comprehensive dashboards to monitor heating, water, and energy utilities.

## Overview

The queries in this document work with data from:
- **Heating**: Kamstrup heating valve sensor (`sourcetype=kamstrup:heating`)
- **Hot Water**: Kamstrup hot water valve sensor (`sourcetype=kamstrup:hotwater`)
- **Cold Water**: Elster cold water valve sensor (`sourcetype=elster:coldwater`)
- **Energy**: EmonPi energy monitor (`sourcetype=emonpi:energy`)

All data is indexed in the `utilities` index.

---

## Field Reference by Sourcetype

### Kamstrup (Heating & Hot Water)
**Key fields** (348 events each):
- `volume` - Total volume in m³
- `flow` - Current flow rate in L/h (liters per hour)
- `power` - Current power in kW
- `heat_energy` - Heat energy in MWh
- `cooling_energy` - Cooling energy in MWh
- `temp1` - Temperature 1 (supply) in °C
- `temp2` - Temperature 2 (return) in °C
- `tempdiff` - Temperature difference in °C
- `temp1xm3`, `temp2xm3` - Temperature × volume
- `water_temp` - Water temperature in °C
- `meter_temp` - Meter internal temperature in °C
- `hourcounter` - Operating hours
- `device_date`, `device_time` - Device timestamp
- `battery_days_left` - Battery life remaining
- `leak_burst` - Leak detection flag (0/1)
- `infoevent` - Information event code
- `avgtemp1_m`, `avgtemp1_y` - Average temp1 (month/year)
- `avgtemp2_m`, `avgtemp2_y` - Average temp2 (month/year)
- `maxflow_m`, `maxflow_y` - Max flow (month/year)
- `maxflowdate_m`, `maxflowdate_y` - Max flow date
- `maxpower_y`, `maxpowerdate_m`, `maxpowerdate_y` - Max power stats
- `minflow_m`, `minflow_y`, `minflowdate_m`, `minflowdate_y` - Min flow stats
- `minpower_y`, `minpowerdate_m`, `minpowerdate_y` - Min power stats

### Elster (Cold Water)
**Key fields** (191 events):
- `current_value` - Current meter reading (total pulses)
- `pulse_count` - Pulse count
- `pulse_factor` - Pulses per unit (conversion factor)
- `water_used_last_minute` - Water usage in last minute (L/min)
- `leak_detect` - Leak detection flag (187 events)

### Common Fields (All Sourcetypes)
- `mqtt_topic` - Full MQTT topic path (16,711 events)
- `received_at` - Timestamp when received by script (16,710 events)
- `source` - Gateway identifier (heating_main, hotwater_main, coldwater_main)
- `wifi_rssi` - WiFi signal strength in dBm (538 events)
- `mac_address` - Gateway MAC address (538 events)
- `running_firmware_version` - Current firmware (538 events)
- `available_firmware_version` - Available firmware update (538 events)
- `update_available` - Update flag (527 events)
- `startup_time` - Gateway boot time (538 events)

**Important Notes:**
1. Each metric is published as a **separate MQTT message** (not combined JSON)
2. Kamstrup uses **L/h** (liters per hour) for flow
3. Elster uses **L/min** (liters per minute) for water_used_last_minute
4. Total events in 24h period: **16,711 events**

---

## Query 1: Real-Time Utility Consumption Overview

**Purpose:** Display current readings for all utilities in single-value tiles

**Visualization:** Single Value / Table  
**Refresh:** 30 seconds  
**Time Range:** Last 15 minutes

```spl
index=utilities sourcetype IN (kamstrup:*, elster:*, emonpi:*)
| eval utility_type=case(
    sourcetype=="kamstrup:heating", "Heating",
    sourcetype=="kamstrup:hotwater", "Hot Water",
    sourcetype=="elster:coldwater", "Cold Water",
    sourcetype=="emonpi:energy", "Energy",
    1=1, "Other"
  )
| stats 
    latest(volume) as "Volume (m³)",
    latest(current_value) as "Current Value",
    latest(flow) as "Flow (L/h)",
    latest(power) as "Power (kW)",
    latest(temp1) as "Temp1 (°C)",
    latest(temp2) as "Temp2 (°C)",
    latest(heat_energy) as "Heat Energy (MWh)",
    latest(water_used_last_minute) as "Water Used (L/min)"
    by utility_type
| eval "Volume (m³)"=round('Volume (m³)', 2)
| eval "Flow (L/h)"=round('Flow (L/h)', 1)
| eval "Power (kW)"=round('Power (kW)', 2)
| eval "Temp1 (°C)"=round('Temp1 (°C)', 1)
| eval "Temp2 (°C)"=round('Temp2 (°C)', 1)
| eval "Heat Energy (MWh)"=round('Heat Energy (MWh)', 3)
```

**Expected Output:**
```
utility_type  | Volume (m³) | Flow (L/h) | Power (kW) | Temp1 (°C) | Temp2 (°C) | Heat Energy (MWh) | Current Value | Water Used (L/min)
Heating       | 23.45       | 156.0      | 5.2        | 52.0       | 35.0       | 1.234             | -             | -
Hot Water     | 15.67       | 89.0       | 3.8        | 48.0       | 38.0       | 0.987             | -             | -
Cold Water    | -           | -          | -          | -          | -          | -                 | 551879.00     | 0.5
```

---

## Query 2: Hourly Usage Comparison (Last 24 Hours)

**Purpose:** Show usage trends over the last 24 hours for all utilities

**Visualization:** Line Chart / Area Chart  
**Refresh:** 5 minutes  
**Time Range:** Last 24 hours

```spl
index=utilities sourcetype IN (kamstrup:hotwater, elster:coldwater, kamstrup:heating)
    earliest=-24h latest=now
| eval utility=case(
    sourcetype=="kamstrup:hotwater", "Hot Water",
    sourcetype=="elster:coldwater", "Cold Water",
    sourcetype=="kamstrup:heating", "Heating",
    1=1, "Unknown"
  )
| eval usage_value=coalesce(volume, current_value, pulse_count)
| timechart span=1h 
    latest(usage_value) as hourly_reading
    by utility
| eval "Hot Water"=round('Hot Water', 2)
| eval "Cold Water"=round('Cold Water', 2)
| eval "Heating"=round('Heating', 2)
```

**Chart Settings:**
- X-axis: Time (hourly buckets)
- Y-axis: Total Usage
- Series: Hot Water, Cold Water, Heating
- Colors: Red (Hot Water), Blue (Cold Water), Orange (Heating)

**Alternative - Flow Rate Trend:**
```spl
index=utilities (flow=* OR water_used_last_minute=*)
    earliest=-24h latest=now
| eval flow_metric=coalesce(flow, water_used_last_minute)
| eval utility=case(
    match(mqtt_topic, "hotwater"), "Hot Water",
    match(mqtt_topic, "coldwater"), "Cold Water",
    match(mqtt_topic, "heating"), "Heating",
    1=1, "Unknown"
  )
| timechart span=1h 
    avg(flow_metric) as avg_flow 
    by utility
| eval "Hot Water"=round('Hot Water', 1)
| eval "Cold Water"=round('Cold Water', 1)
| eval "Heating"=round('Heating', 1)
```

---

## Query 3: Anomaly Detection - High Flow Rate Alerts

**Purpose:** Detect abnormal flow rates that could indicate leaks or malfunctions

**Visualization:** Table with color indicators  
**Refresh:** 1 minute  
**Time Range:** Last 1 hour

```spl
index=utilities (flow=* OR water_used_last_minute=*)
| eval flow_metric=coalesce(flow, water_used_last_minute)
| eval utility=case(
    sourcetype=="kamstrup:hotwater", "Hot Water",
    sourcetype=="elster:coldwater", "Cold Water",
    sourcetype=="kamstrup:heating", "Heating",
    1=1, mqtt_topic
  )
| stats 
    avg(flow_metric) as avg_flow,
    max(flow_metric) as max_flow,
    stdev(flow_metric) as stdev_flow,
    count as sample_count
    by utility
| eval threshold=avg_flow + (2 * stdev_flow)
| eval alert_level=case(
    max_flow > threshold, "⚠️ HIGH",
    max_flow > (threshold * 0.75), "⚡ ELEVATED",
    1=1, "✅ NORMAL"
  )
| table utility, avg_flow, max_flow, threshold, alert_level, sample_count
| eval avg_flow=round(avg_flow, 2), max_flow=round(max_flow, 2), threshold=round(threshold, 2)
```

**Alert Configuration:**
```spl
| where alert_level="⚠️ HIGH"
```
**Trigger:** When max_flow exceeds threshold (2 standard deviations above average)  
**Action:** Send email/webhook notification

**Expected Output:**
```
utility     | avg_flow | max_flow | threshold | alert_level  | sample_count
Cold Water  | 0.52     | 5.23     | 1.04      | ⚠️ HIGH      | 190
Hot Water   | 125.50   | 250.00   | 200.00    | ⚡ ELEVATED  | 348
Heating     | 180.00   | 210.00   | 240.00    | ✅ NORMAL    | 348
```

**Note:** Kamstrup `flow` is in L/h (liters per hour), while Elster `water_used_last_minute` is in L/min. Consider normalizing units.

---

## Query 4: Gateway Health & Connectivity Status

**Purpose:** Monitor gateway connectivity, signal strength, and firmware versions

**Visualization:** Table / Status Indicator  
**Refresh:** 1 minute  
**Time Range:** Last 1 hour

```spl
index=utilities 
| eval gateway=case(
    match(mqtt_topic, "heating"), "Heating Gateway",
    match(mqtt_topic, "hotwater"), "Hot Water Gateway",
    match(mqtt_topic, "coldwater"), "Cold Water Gateway",
    match(mqtt_topic, "energy"), "Energy Gateway",
    1=1, "Unknown"
  )
| stats 
    count as message_count,
    latest(_time) as last_seen,
    earliest(_time) as first_seen,
    latest(wifi_rssi) as signal_strength,
    latest(running_firmware_version) as firmware
    by gateway
| eval time_since_last_seen=now() - last_seen
| eval status=case(
    time_since_last_seen < 120, "🟢 ONLINE",
    time_since_last_seen < 600, "🟡 DELAYED",
    1=1, "🔴 OFFLINE"
  )
| eval last_seen_friendly=strftime(last_seen, "%Y-%m-%d %H:%M:%S")
| table gateway, status, message_count, last_seen_friendly, signal_strength, firmware
| sort - last_seen
```

**Color Rules:**
- 🟢 ONLINE: Green (< 2 minutes since last message)
- 🟡 DELAYED: Yellow (2-10 minutes since last message)
- 🔴 OFFLINE: Red (> 10 minutes since last message)

**Alert on Offline:**
```spl
| where status="🔴 OFFLINE"
```

**Expected Output:**
```
gateway            | status       | message_count | last_seen_friendly    | signal_strength | firmware
Heating Gateway    | 🟢 ONLINE    | 345          | 2026-01-26 12:34:56   | -45             | 2
Hot Water Gateway  | 🟢 ONLINE    | 298          | 2026-01-26 12:34:50   | -52             | 2
Cold Water Gateway | 🟢 ONLINE    | 312          | 2026-01-26 12:34:45   | -48             | 2
Energy Gateway     | 🟡 DELAYED   | 45           | 2026-01-26 12:29:30   | -65             | 1
```

---

## Query 5: Daily Cost Estimation & Comparison (7-Day Trend)

**Purpose:** Estimate daily costs for each utility and show 7-day trend

**Visualization:** Stacked Bar Chart / Column Chart  
**Refresh:** 1 hour  
**Time Range:** Last 7 days

```spl
index=utilities sourcetype IN (kamstrup:*, elster:*, emonpi:*)
    earliest=-7d latest=now
| eval utility=case(
    sourcetype=="kamstrup:heating", "Heating",
    sourcetype=="kamstrup:hotwater", "Hot Water",
    sourcetype=="elster:coldwater", "Cold Water",
    sourcetype=="emonpi:energy", "Energy",
    1=1, "Other"
  )
| eval usage=coalesce(heat_energy, cooling_energy, volume, current_value, pulse_count, power)
| eval estimated_cost=case(
    utility=="Heating" AND isnotnull(heat_energy), heat_energy * 100,
    utility=="Hot Water" AND isnotnull(volume), volume * 0.08,
    utility=="Cold Water" AND isnotnull(current_value), current_value * 0.000005,
    utility=="Energy", power * 0.15,
    1=1, 0
  )
| timechart span=1d 
    sum(estimated_cost) as daily_cost 
    by utility
| addtotals fieldname=total_daily_cost
| eval total_daily_cost=round(total_daily_cost, 2)
```

**Cost Multipliers (Adjust these to your rates):**
- Heating: $100 per MWh (heat_energy field)
- Hot Water: $0.08 per m³ (volume field)
- Cold Water: $0.000005 per pulse (current_value field, adjust based on pulse_factor)
- Energy: $0.15 per kW (power field)

**Alternative - Show Total Only:**
```spl
index=utilities sourcetype IN (kamstrup:*, elster:*, emonpi:*)
    earliest=-7d latest=now
| eval usage=coalesce(current_value, pulse_count, power)
| eval utility=case(
    sourcetype=="kamstrup:heating", "Heating",
    sourcetype=="kamstrup:hotwater", "Hot Water",
    sourcetype=="elster:coldwater", "Cold Water",
    sourcetype=="emonpi:energy", "Energy",
    1=1, "Other"
  )
| eval estimated_cost=case(
    utility=="Heating", usage * 0.10,
    utility=="Hot Water", usage * 0.08,
    utility=="Cold Water", usage * 0.005,
    utility=="Energy", usage * 0.15,
    1=1, 0
  )
| timechart span=1d sum(estimated_cost) as total_daily_cost
| eval total_daily_cost=round(total_daily_cost, 2)
```

---

## Query 6: System Health & Ingestion Rate

**Purpose:** Monitor overall system health and data ingestion rate

**Visualization:** Single Value tiles  
**Refresh:** 30 seconds  
**Time Range:** Last 1 hour

```spl
index=utilities earliest=-1h
| stats 
    count as events_last_hour,
    dc(sourcetype) as active_sourcetypes,
    dc(mqtt_topic) as unique_topics,
    dc(source) as active_gateways
| eval health=case(
    events_last_hour > 100, "Excellent",
    events_last_hour > 50, "Good",
    events_last_hour > 10, "Low",
    1=1, "Critical"
  )
```

**Separate Panels:**

**Panel 1 - Events per Hour:**
```spl
index=utilities earliest=-1h | stats count
```

**Panel 2 - Active Gateways:**
```spl
index=utilities earliest=-15m | stats dc(source) as count
```

**Panel 3 - Data Freshness:**
```spl
index=utilities 
| stats latest(_time) as last_event 
| eval seconds_ago=now() - last_event
| eval freshness=if(seconds_ago < 60, "Fresh", if(seconds_ago < 300, "Stale", "Old"))
| table freshness, seconds_ago
```

---

## Dashboard Layout Recommendation

### Main Dashboard: "Utilities Overview"

```
┌─────────────────────────────────────────────────────────────────┐
│  🏠 Utilities Monitoring Dashboard                              │
│  Time Range: Last 24 Hours                    [Refresh: 30s]    │
├─────────────────────────────────────────────────────────────────┤
│  System Health                                                  │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐      │
│  │Events/Hr  │ │ Gateways  │ │  Topics   │ │  Health   │      │
│  │   345     │ │     3     │ │    12     │ │  Excellent│      │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘      │
│                                                (Query 6)        │
├─────────────────────────────────────────────────────────────────┤
│  Current Readings                                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ 🔥 Heating   │ │ 💧 Hot Water │ │ 🚰 Cold Water│            │
│  │ 1234.56 L    │ │  8765.43 L   │ │  5432.10 L   │            │
│  │ 72.0°F       │ │  68.5°F      │ │  58.0°F      │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                (Query 1)        │
├─────────────────────────────────────────────────────────────────┤
│  📈 24-Hour Usage Trend                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │     Line chart showing usage over time                  │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                (Query 2)        │
├───────────────────────────────┬─────────────────────────────────┤
│  ⚠️ Anomaly Alerts            │  🔌 Gateway Health             │
│  ┌────────────────────────┐   │  ┌────────────────────────┐    │
│  │ Utility  | Status      │   │  │ Gateway | Status       │    │
│  │ Cold     | ⚠️ HIGH     │   │  │ Heating | 🟢 ONLINE    │    │
│  │ Hot      | ✅ NORMAL   │   │  │ HotWater| 🟢 ONLINE    │    │
│  │ Heating  | ✅ NORMAL   │   │  │ Cold    | 🟢 ONLINE    │    │
│  └────────────────────────┘   │  └────────────────────────┘    │
│           (Query 3)            │           (Query 4)            │
├───────────────────────────────┴─────────────────────────────────┤
│  💰 7-Day Cost Comparison                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │     Stacked bar chart showing daily costs              │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                (Query 5)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Drilldown Dashboard: "Detailed Utility View"

Create a separate dashboard for each utility with detailed metrics.

### Example: "Heating System Detail"

```spl
index=utilities sourcetype=kamstrup:heating earliest=-7d
| timechart span=1h
    avg(temperature) as "Avg Temperature",
    avg(flow_rate) as "Avg Flow Rate",
    avg(pressure) as "Avg Pressure",
    max(current_value) as "Max Reading"
```

### Statistical Summary:
```spl
index=utilities sourcetype=kamstrup:heating earliest=-7d
| stats 
    avg(temperature) as avg_temp,
    min(temperature) as min_temp,
    max(temperature) as max_temp,
    avg(flow_rate) as avg_flow,
    max(flow_rate) as max_flow,
    avg(pressure) as avg_pressure,
    count as total_readings
| eval avg_temp=round(avg_temp, 1)
| eval avg_flow=round(avg_flow, 2)
| eval avg_pressure=round(avg_pressure, 2)
```

---

## Alert Configurations

### Alert 1: Gateway Offline

**Search:**
```spl
index=utilities 
| stats latest(_time) as last_seen by source
| eval time_since=now() - last_seen
| where time_since > 600
| eval gateway=source
| table gateway, time_since
```

**Trigger:** When time_since > 600 seconds (10 minutes)  
**Throttle:** 15 minutes  
**Action:** Email, Webhook

---

### Alert 2: High Flow Rate (Potential Leak)

**Search:**
```spl
index=utilities (flow=* OR water_used_last_minute=*)
| eval flow_metric=case(
    isnotnull(flow), flow,
    isnotnull(water_used_last_minute), water_used_last_minute * 60,
    1=1, 0
  )
| eval utility=case(
    sourcetype=="kamstrup:hotwater", "Hot Water",
    sourcetype=="elster:coldwater", "Cold Water",
    sourcetype=="kamstrup:heating", "Heating",
    1=1, "Unknown"
  )
| stats max(flow_metric) as max_flow by utility
| where max_flow > 300
| eval max_flow=round(max_flow, 1)
```

**Trigger:** When max_flow > 300 L/h (normalized)  
**Throttle:** 30 minutes  
**Action:** Email, SMS, Webhook

**Note:** Flow is normalized to L/h (Kamstrup `flow` is already L/h, Elster `water_used_last_minute` is converted from L/min to L/h)

---

### Alert 3: Temperature Anomaly

**Search:**
```spl
index=utilities temperature=*
| stats 
    avg(temperature) as avg_temp,
    stdev(temperature) as stdev_temp
    by sourcetype
| eval threshold_high=avg_temp + (3 * stdev_temp)
| eval threshold_low=avg_temp - (3 * stdev_temp)
| appendcols 
    [search index=utilities temperature=* 
    | stats latest(temperature) as current_temp by sourcetype]
| where current_temp > threshold_high OR current_temp < threshold_low
```

**Trigger:** Temperature exceeds 3 standard deviations  
**Throttle:** 1 hour  
**Action:** Email

---

## Advanced Queries

### Query 7: Pulse Count Rate of Change (Detect Sudden Spikes)

**Purpose:** Detect sudden increases in cold water pulse count (potential burst pipe)

```spl
index=utilities sourcetype=elster:coldwater pulse_count=*
    earliest=-1h latest=now
| sort 0 _time
| streamstats window=2 current=f last(pulse_count) as prev_pulse
| eval rate_of_change=pulse_count - prev_pulse
| where rate_of_change > 10
| stats 
    count as spike_count,
    avg(rate_of_change) as avg_spike,
    max(rate_of_change) as max_spike,
    latest(_time) as last_spike_time
| eval last_spike=strftime(last_spike_time, "%Y-%m-%d %H:%M:%S")
| table spike_count, avg_spike, max_spike, last_spike
```

**Alert Threshold:** rate_of_change > 10 pulses in consecutive readings

---

### Query 8: Weekly Comparison (This Week vs Last Week)

**Purpose:** Compare total consumption between this week and last week

```spl
index=utilities sourcetype IN (kamstrup:*, elster:*)
    earliest=-14d latest=now
| eval week=if(_time > relative_time(now(), "-7d"), "This Week", "Last Week")
| eval utility=case(
    sourcetype=="kamstrup:heating", "Heating",
    sourcetype=="kamstrup:hotwater", "Hot Water",
    sourcetype=="elster:coldwater", "Cold Water",
    1=1, "Other"
  )
| eval usage_metric=coalesce(volume, current_value, heat_energy)
| stats 
    max(usage_metric) as max_reading
    by week, utility
| eval usage_diff=case(
    week=="This Week", max_reading
  )
| stats 
    values(max_reading) as readings,
    list(week) as weeks
    by utility
| eval "This Week"=mvindex(readings, mvfind(weeks, "This Week"))
| eval "Last Week"=mvindex(readings, mvfind(weeks, "Last Week"))
| eval "Change %"=round((('This Week' - 'Last Week') / 'Last Week') * 100, 1)
| table utility, "Last Week", "This Week", "Change %"
```

---

### Query 9: Peak Usage Hours

```spl
index=utilities current_value=* OR pulse_count=*
    earliest=-7d latest=now
| eval hour=strftime(_time, "%H")
| eval usage=coalesce(current_value, pulse_count)
| stats sum(usage) as total_usage by hour
| sort - total_usage
| head 10
```

---

### Query 10: MAC Address & Device Inventory

```spl
index=utilities mac_address=* OR wifi_rssi=*
| stats 
    latest(mac_address) as MAC,
    latest(wifi_rssi) as "Signal (dBm)",
    latest(running_firmware_version) as Firmware,
    latest(startup_time) as "Last Startup",
    count as "Message Count"
    by source
| rename source as "Gateway"
```

---

### Query 11: Temperature Monitoring (Kamstrup Only)

**Purpose:** Monitor supply/return temperatures and temperature differences

```spl
index=utilities sourcetype IN (kamstrup:*) (temp1=* OR temp2=* OR tempdiff=*)
| eval utility=case(
    sourcetype=="kamstrup:heating", "Heating",
    sourcetype=="kamstrup:hotwater", "Hot Water",
    1=1, "Unknown"
  )
| timechart span=10m
    avg(temp1) as "Supply Temp (°C)",
    avg(temp2) as "Return Temp (°C)",
    avg(tempdiff) as "Temp Diff (°C)"
    by utility
```

**Use:** Line chart showing temperature trends over time

---

### Query 12: Leak Detection Alerts

**Purpose:** Detect leaks from either Kamstrup or Elster gateways

```spl
index=utilities (leak_burst=1 OR leak_detect=1)
| eval utility=case(
    sourcetype=="kamstrup:heating", "Heating",
    sourcetype=="kamstrup:hotwater", "Hot Water",
    sourcetype=="elster:coldwater", "Cold Water",
    1=1, "Unknown"
  )
| eval leak_type=if(isnotnull(leak_burst), "Burst", "Detect")
| stats 
    count as leak_events,
    latest(_time) as last_leak_time,
    earliest(_time) as first_leak_time
    by utility, leak_type
| eval last_leak=strftime(last_leak_time, "%Y-%m-%d %H:%M:%S")
| eval first_leak=strftime(first_leak_time, "%Y-%m-%d %H:%M:%S")
| table utility, leak_type, leak_events, first_leak, last_leak
```

---

### Query 13: Energy Efficiency (Heating Performance)

**Purpose:** Calculate heating efficiency based on energy and volume

```spl
index=utilities sourcetype=kamstrup:heating (heat_energy=* OR volume=*)
| stats 
    latest(heat_energy) as energy_mwh,
    latest(volume) as volume_m3
| eval efficiency=if(volume_m3 > 0, (energy_mwh * 1000) / volume_m3, 0)
| eval efficiency=round(efficiency, 2)
| table energy_mwh, volume_m3, efficiency
| rename energy_mwh as "Heat Energy (MWh)", volume_m3 as "Volume (m³)", efficiency as "kWh per m³"
```

---

### Query 14: Water Consumption Rate (Last Hour)

**Purpose:** Calculate actual water consumption in liters for the last hour

```spl
index=utilities sourcetype=elster:coldwater water_used_last_minute=*
    earliest=-1h latest=now
| stats sum(water_used_last_minute) as total_liters
| eval gallons=round(total_liters * 0.264172, 2)
| table total_liters, gallons
| rename total_liters as "Liters (Last Hour)", gallons as "Gallons (Last Hour)"
```

---

### Query 15: Power Demand Chart (Kamstrup)

**Purpose:** Show real-time power demand for heating systems

```spl
index=utilities sourcetype IN (kamstrup:*) power=*
    earliest=-24h latest=now
| eval utility=case(
    sourcetype=="kamstrup:heating", "Heating",
    sourcetype=="kamstrup:hotwater", "Hot Water",
    1=1, "Unknown"
  )
| timechart span=15m
    avg(power) as avg_power,
    max(power) as max_power
    by utility
```

**Alert:** Set threshold for `max_power > 10` kW for demand alerts

---

## Performance Tips

1. **Use time ranges wisely:**
   - Real-time panels: Last 15 minutes
   - Trend charts: Last 24 hours or 7 days
   - Historical analysis: Last 30 days

2. **Leverage summary indexing:**
   ```spl
   | collect index=summary_utilities sourcetype=utilities:hourly
   ```

3. **Use data models** for frequently accessed data

4. **Index-time field extraction** for high-volume fields

5. **Scheduled searches** for expensive queries (run hourly, store results)

---

## Next Steps

1. **Create the main dashboard** using queries 1-6
2. **Set up alerts** for gateway offline and high flow rates
3. **Build drilldown dashboards** for each utility
4. **Customize cost multipliers** in Query 5 to match your actual utility rates
5. **Test anomaly detection** thresholds and adjust as needed

---

## Related Documentation

- [README.md](README.md) - Utilities system overview
- [SPLUNK_SETUP.md](SPLUNK_SETUP.md) - Splunk HEC configuration
- [mqtt_topic_utilities.md](mqtt_topic_utilities.md) - MQTT broker integration
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete deployment walkthrough

---

## Support

For questions about these dashboards or queries:
1. Test queries in Splunk Search & Reporting first
2. Adjust time ranges based on your data volume
3. Modify field names if your gateways publish different field names
4. Check `index=utilities | head 10` to see actual field names in your data

**Last Updated:** 2026-01-26  
**Version:** 1.0.0

