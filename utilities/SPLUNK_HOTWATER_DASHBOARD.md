# 💧 Hot Water Monitoring Dashboard - Splunk Queries & Insights

## Overview

This document provides comprehensive Splunk queries for monitoring your **Kamstrup Hot Water** system. The hot water gateway provides detailed metrics including volume, flow rate, temperature, and power consumption.

---

## Field Reference - Kamstrup Hot Water

Based on actual data from `sourcetype=kamstrup:hotwater`:

| Field Name | Description | Unit | Example Value |
|-----------|-------------|------|---------------|
| `volume` | Total hot water volume | m³ | 8.254 |
| `flow` | Current flow rate | L/h | 45.2 |
| `temp1` | Supply temperature (hot) | °C | 55.4 |
| `temp2` | Return temperature | °C | 48.2 |
| `power` | Current thermal power | kW | 2.4 |
| `heat_energy` | Total heat energy delivered | MWh | 1.234 |
| `cooling_energy` | Total cooling energy (if applicable) | MWh | 0.001 |
| `mqtt_topic` | MQTT topic path | string | utilities/hotwater/metrics |
| `received_at` | Timestamp received | ISO8601 | 2026-01-26T10:15:00Z |
| `wifi_rssi` | WiFi signal strength | dBm | -52 |

---

## Dashboard Panels - Top 10 Queries

### 1. Today's Hot Water Consumption

**Purpose:** Track daily hot water usage in liters

```spl
index=utilities sourcetype=kamstrup:hotwater volume=*
| bucket _time span=1d
| stats 
    earliest(volume) as start_volume,
    latest(volume) as end_volume
    by _time
| eval consumption_m3 = end_volume - start_volume
| eval consumption_liters = consumption_m3 * 1000
| eval date = strftime(_time, "%Y-%m-%d")
| table date, consumption_liters, consumption_m3
| eval consumption_liters = round(consumption_liters, 1)
| eval consumption_m3 = round(consumption_m3, 3)
```

**Expected Output:**
- Date, consumption in liters and m³
- Typical range: 150-400 L/day per household

---

### 2. Current Flow Rate (Real-Time)

**Purpose:** Monitor live hot water flow

```spl
index=utilities sourcetype=kamstrup:hotwater flow=*
| stats latest(flow) as current_flow_lph
| eval current_flow_lpm = current_flow_lph / 60
| eval status = case(
    current_flow_lpm = 0, "No Flow",
    current_flow_lpm < 2, "Light Use",
    current_flow_lpm < 5, "Normal Use",
    current_flow_lpm < 10, "High Use",
    1=1, "Very High"
)
| eval current_flow_lpm = round(current_flow_lpm, 2)
| table current_flow_lpm, current_flow_lph, status
```

**Expected Output:**
- Current flow in L/min and L/h
- Status indicator based on flow rate

---

### 3. Supply Temperature Monitoring

**Purpose:** Track hot water temperature at supply

```spl
index=utilities sourcetype=kamstrup:hotwater temp1=*
| timechart span=10m 
    avg(temp1) as avg_temp,
    min(temp1) as min_temp,
    max(temp1) as max_temp
| eval avg_temp = round(avg_temp, 1)
| eval min_temp = round(min_temp, 1)
| eval max_temp = round(max_temp, 1)
```

**Expected Output:**
- Average, min, max supply temperatures over time
- Typical range: 50-60°C for hot water systems

---

### 4. Temperature Differential (Supply vs Return)

**Purpose:** Calculate heat loss in distribution

```spl
index=utilities sourcetype=kamstrup:hotwater (temp1=* AND temp2=*)
| eval temp_diff = temp1 - temp2
| timechart span=15m 
    avg(temp_diff) as avg_diff,
    avg(temp1) as avg_supply,
    avg(temp2) as avg_return
| eval avg_diff = round(avg_diff, 1)
| eval avg_supply = round(avg_supply, 1)
| eval avg_return = round(avg_return, 1)
```

**Expected Output:**
- Temperature differential (°C)
- Lower diff = less heat loss = better insulation
- Typical diff: 5-15°C depending on usage

---

### 5. Flow Rate Timeline (24 Hours)

**Purpose:** Visualize flow patterns throughout the day

```spl
index=utilities sourcetype=kamstrup:hotwater flow=*
| eval flow_lpm = flow / 60
| timechart span=5m avg(flow_lpm) as avg_flow_lpm
| eval avg_flow_lpm = round(avg_flow_lpm, 2)
```

**Expected Output:**
- Time-series of flow rates
- Shows peak usage times (morning showers, evening dishes)

---

### 6. Power Consumption Tracking

**Purpose:** Monitor thermal power usage

```spl
index=utilities sourcetype=kamstrup:hotwater power=*
| timechart span=15m 
    avg(power) as avg_power_kw,
    max(power) as peak_power_kw
| eval avg_power_kw = round(avg_power_kw, 2)
| eval peak_power_kw = round(peak_power_kw, 2)
```

**Expected Output:**
- Average and peak power consumption
- Higher power = more heat demand = colder incoming water or high flow

---

### 7. Daily Consumption Trend (Last 30 Days)

**Purpose:** Compare daily usage over a month

```spl
index=utilities sourcetype=kamstrup:hotwater volume=*
    earliest=-30d latest=now
| bucket _time span=1d
| stats 
    earliest(volume) as start_volume,
    latest(volume) as end_volume
    by _time
| eval daily_consumption_liters = (end_volume - start_volume) * 1000
| eval date = strftime(_time, "%m/%d")
| table date, daily_consumption_liters
| eval daily_consumption_liters = round(daily_consumption_liters, 1)
| sort _time
```

**Expected Output:**
- Daily consumption for last 30 days
- Helps identify trends and anomalies

---

### 8. Peak Usage Times (Hourly Breakdown)

**Purpose:** Identify when hot water is used most

```spl
index=utilities sourcetype=kamstrup:hotwater flow=*
| eval hour = strftime(_time, "%H")
| eval flow_lpm = flow / 60
| stats 
    avg(flow_lpm) as avg_flow,
    max(flow_lpm) as max_flow,
    count as data_points
    by hour
| eval avg_flow = round(avg_flow, 2)
| eval max_flow = round(max_flow, 2)
| sort hour
```

**Expected Output:**
- Average and max flow by hour of day
- Typical peaks: 6-9 AM (showers), 6-9 PM (cooking/dishes)

---

### 9. Efficiency: Energy per Volume

**Purpose:** Calculate energy efficiency (kWh per m³)

```spl
index=utilities sourcetype=kamstrup:hotwater (heat_energy=* AND volume=*)
| stats 
    latest(heat_energy) as total_energy_mwh,
    latest(volume) as total_volume_m3
| eval energy_kwh = total_energy_mwh * 1000
| eval efficiency_kwh_per_m3 = energy_kwh / total_volume_m3
| eval efficiency_kwh_per_m3 = round(efficiency_kwh_per_m3, 2)
| table total_volume_m3, energy_kwh, efficiency_kwh_per_m3
```

**Expected Output:**
- Total volume and energy consumption
- Efficiency metric (typically 40-80 kWh/m³ depending on incoming water temp)

---

### 10. System Health & Gateway Status

**Purpose:** Monitor gateway connectivity and metrics

```spl
index=utilities sourcetype=kamstrup:hotwater
| stats 
    count as total_events,
    latest(_time) as last_seen,
    latest(wifi_rssi) as signal_strength,
    latest(running_firmware_version) as firmware,
    dc(mqtt_topic) as unique_topics
| eval last_seen_time = strftime(last_seen, "%Y-%m-%d %H:%M:%S")
| eval time_since = now() - last_seen
| eval status = case(
    time_since < 120, "🟢 ONLINE",
    time_since < 600, "🟡 DELAYED",
    1=1, "🔴 OFFLINE"
)
| eval signal_quality = case(
    signal_strength > -50, "Excellent",
    signal_strength > -60, "Good",
    signal_strength > -70, "Fair",
    1=1, "Poor"
)
| table status, total_events, last_seen_time, signal_strength, signal_quality, firmware, unique_topics
```

**Expected Output:**
- Gateway status, event count, signal strength
- Helps diagnose connectivity issues

---

## Critical Alerts - Top 5

### Alert 1: Continuous Flow Detected (Potential Leak)

**Trigger:** Flow rate > 0 for more than 2 hours

```spl
index=utilities sourcetype=kamstrup:hotwater flow=*
| eval flow_lpm = flow / 60
| streamstats time_window=2h count(eval(flow_lpm > 0)) as continuous_flow_count
| where continuous_flow_count > 120
| stats 
    latest(flow_lpm) as current_flow,
    latest(continuous_flow_count) as minutes_flowing
| eval alert_level = case(
    minutes_flowing > 240, "🔴 CRITICAL - Possible Leak",
    minutes_flowing > 120, "🟡 WARNING - Extended Flow",
    1=1, "✅ NORMAL"
)
| table alert_level, current_flow, minutes_flowing
```

**Action:** Investigate for running taps, leaking fixtures, or recirculation pump issues

---

### Alert 2: Abnormally High Daily Consumption

**Trigger:** Today's consumption > 150% of 30-day average

```spl
index=utilities sourcetype=kamstrup:hotwater volume=*
| bucket _time span=1d
| stats 
    earliest(volume) as start_volume,
    latest(volume) as end_volume
    by _time
| eval daily_consumption = (end_volume - start_volume) * 1000
| eventstats avg(daily_consumption) as avg_consumption
| eval threshold = avg_consumption * 1.5
| where daily_consumption > threshold
| eval alert = "⚠️ HIGH CONSUMPTION - " + round(daily_consumption, 0) + " L (avg: " + round(avg_consumption, 0) + " L)"
| table _time, alert, daily_consumption, avg_consumption, threshold
```

**Action:** Check for unusual usage, guests, or system malfunction

---

### Alert 3: Supply Temperature Too Low

**Trigger:** Supply temp < 45°C (risk of legionella growth)

```spl
index=utilities sourcetype=kamstrup:hotwater temp1=*
| where temp1 < 45
| stats 
    latest(temp1) as current_temp,
    min(temp1) as lowest_temp,
    count as low_temp_events
| eval alert = "🔴 CRITICAL - Low Supply Temperature (" + round(current_temp, 1) + "°C)"
| table alert, current_temp, lowest_temp, low_temp_events
```

**Action:** Check water heater settings, heating element, or thermostat

---

### Alert 4: Temperature Differential Too High

**Trigger:** Temp diff > 20°C (excessive heat loss)

```spl
index=utilities sourcetype=kamstrup:hotwater (temp1=* AND temp2=*)
| eval temp_diff = temp1 - temp2
| where temp_diff > 20
| stats 
    latest(temp_diff) as current_diff,
    max(temp_diff) as max_diff,
    avg(temp_diff) as avg_diff,
    count as high_diff_events
| eval alert = "⚠️ HIGH HEAT LOSS - " + round(current_diff, 1) + "°C differential"
| table alert, current_diff, max_diff, avg_diff, high_diff_events
```

**Action:** Check for circulation issues, poor insulation, or system imbalance

---

### Alert 5: Gateway Offline

**Trigger:** No data received in last 10 minutes

```spl
index=utilities sourcetype=kamstrup:hotwater
| stats latest(_time) as last_seen
| eval time_since = now() - last_seen
| where time_since > 600
| eval minutes_offline = round(time_since / 60, 0)
| eval alert = "🔴 GATEWAY OFFLINE - No data for " + minutes_offline + " minutes"
| table alert, last_seen, minutes_offline
```

**Action:** Check gateway power, WiFi connection, MQTT broker status

---

## Advanced Queries

### Hourly Consumption Pattern Analysis

**Purpose:** Deep dive into usage patterns by hour and day of week

```spl
index=utilities sourcetype=kamstrup:hotwater volume=*
| bucket _time span=1h
| stats 
    earliest(volume) as start_vol,
    latest(volume) as end_vol
    by _time
| eval hourly_consumption_l = (end_vol - start_vol) * 1000
| eval hour = strftime(_time, "%H")
| eval day_of_week = strftime(_time, "%A")
| stats avg(hourly_consumption_l) as avg_consumption by hour, day_of_week
| eval avg_consumption = round(avg_consumption, 2)
| sort day_of_week, hour
```

---

### Cost Estimation (Hot Water Energy)

**Purpose:** Estimate hot water heating cost

```spl
index=utilities sourcetype=kamstrup:hotwater heat_energy=*
| bucket _time span=1d
| stats 
    earliest(heat_energy) as start_energy,
    latest(heat_energy) as end_energy
    by _time
| eval daily_energy_kwh = (end_energy - start_energy) * 1000
| eval daily_cost = daily_energy_kwh * 0.15
| eval date = strftime(_time, "%Y-%m-%d")
| table date, daily_energy_kwh, daily_cost
| eval daily_energy_kwh = round(daily_energy_kwh, 2)
| eval daily_cost = "$" + round(daily_cost, 2)
| sort - _time
| head 30
```

**Note:** Adjust `0.15` to your local electricity rate ($/kWh)

---

### Flow Duration Analysis

**Purpose:** How long does water flow during each usage event?

```spl
index=utilities sourcetype=kamstrup:hotwater flow=*
| eval flow_lpm = flow / 60
| eval is_flowing = if(flow_lpm > 0.5, 1, 0)
| streamstats current=f window=0 
    sum(is_flowing) as flow_session
    reset_on_change=true 
    reset_after="(is_flowing=0)"
| where is_flowing=1
| stats 
    count as duration_minutes,
    avg(flow_lpm) as avg_flow
    by flow_session
| eval duration_category = case(
    duration_minutes < 2, "Quick (< 2 min)",
    duration_minutes < 5, "Short (2-5 min)",
    duration_minutes < 10, "Medium (5-10 min)",
    duration_minutes < 30, "Long (10-30 min)",
    1=1, "Very Long (> 30 min)"
)
| stats count by duration_category
| sort - count
```

---

### Temperature Stability Analysis

**Purpose:** Check how stable supply temperature is

```spl
index=utilities sourcetype=kamstrup:hotwater temp1=*
| bucket _time span=1h
| stats 
    avg(temp1) as avg_temp,
    stdev(temp1) as temp_variance,
    min(temp1) as min_temp,
    max(temp1) as max_temp
    by _time
| eval temp_range = max_temp - min_temp
| eval stability = case(
    temp_variance < 1, "Very Stable",
    temp_variance < 2, "Stable",
    temp_variance < 5, "Moderate",
    1=1, "Unstable"
)
| eval hour = strftime(_time, "%Y-%m-%d %H:00")
| table hour, avg_temp, temp_variance, temp_range, stability
| eval avg_temp = round(avg_temp, 1)
| eval temp_variance = round(temp_variance, 2)
| eval temp_range = round(temp_range, 1)
```

---

### Weekly Consumption Comparison

**Purpose:** Compare this week vs last week

```spl
index=utilities sourcetype=kamstrup:hotwater volume=*
    earliest=-14d latest=now
| eval week = if(_time >= relative_time(now(), "-7d@d"), "This Week", "Last Week")
| bucket _time span=1d
| stats 
    earliest(volume) as start_vol,
    latest(volume) as end_vol
    by _time, week
| eval daily_consumption_l = (end_vol - start_vol) * 1000
| stats sum(daily_consumption_l) as total_consumption by week
| eval total_consumption = round(total_consumption, 1)
```

---

## Key Insights & Interpretations

### 1. **Volume Metrics**
- **Total Volume (`volume`)**: Cumulative meter reading in m³
- **Daily Consumption**: Typically 150-400 L/day for household
- **High consumption**: Check for leaks, guests, or unusual usage

### 2. **Flow Rate Patterns**
- **Morning Peak (6-9 AM)**: Showers, typically 4-8 L/min
- **Evening Peak (6-9 PM)**: Dishes, baths, typically 2-6 L/min
- **Continuous Low Flow**: May indicate recirculation pump or small leak

### 3. **Temperature Insights**
- **Supply Temp (temp1)**: Should be 50-60°C for safety and efficiency
- **Return Temp (temp2)**: Typically 5-15°C lower than supply
- **Large Differential**: Heat loss in distribution (check insulation)

### 4. **Power Consumption**
- **Higher Power**: More heat needed (cold inlet water or high flow)
- **Power vs Flow Correlation**: Power should increase with flow
- **Constant Power + No Flow**: Recirculation or heat loss

### 5. **Energy Efficiency**
- **Typical Range**: 40-80 kWh/m³
- **Lower is Better**: Warmer inlet water = less heating needed
- **Seasonal Variation**: Higher in winter (colder inlet water)

---

## Dashboard Best Practices

### Data Refresh Recommendations
- **Real-time Monitoring**: 30-second refresh
- **Daily Review**: 5-minute refresh
- **Historical Analysis**: Manual refresh

### Alert Thresholds (Customize to Your Usage)
- **Daily Consumption**: Your avg ± 50%
- **Flow Duration**: > 120 minutes continuous
- **Supply Temperature**: < 45°C or > 65°C
- **Temp Differential**: > 20°C

### Time Ranges for Different Views
- **Real-time Status**: Last 15 minutes
- **Daily Patterns**: Last 24 hours
- **Weekly Trends**: Last 7 days
- **Monthly Analysis**: Last 30 days
- **Seasonal Comparison**: Last 365 days

---

## Troubleshooting Common Issues

### Issue 1: No Flow Data Despite Usage

**Symptoms:** Flow rate shows 0 but you know water is being used

**Possible Causes:**
- Flow sensor malfunction
- Gateway not reading flow meter
- MQTT topic mismatch

**Diagnostic Query:**
```spl
index=utilities sourcetype=kamstrup:hotwater
| stats count by mqtt_topic
```

---

### Issue 2: Temperature Reading Errors

**Symptoms:** temp1 or temp2 showing 0, -999, or unrealistic values

**Diagnostic Query:**
```spl
index=utilities sourcetype=kamstrup:hotwater (temp1=* OR temp2=*)
| stats 
    min(temp1) as min_t1,
    max(temp1) as max_t1,
    min(temp2) as min_t2,
    max(temp2) as max_t2
```

**Action:** If min < 0 or max > 100, sensor may be faulty

---

### Issue 3: Inconsistent Volume Readings

**Symptoms:** Volume decreases or jumps unexpectedly

**Diagnostic Query:**
```spl
index=utilities sourcetype=kamstrup:hotwater volume=*
| sort _time
| autoregress volume as previous_volume
| eval volume_change = volume - previous_volume
| where volume_change < 0 OR volume_change > 1
| table _time, previous_volume, volume, volume_change
```

**Action:** Meter reset or communication error

---

## Export & Reporting

### Monthly Consumption Report

```spl
index=utilities sourcetype=kamstrup:hotwater volume=*
    earliest=-30d@d latest=now
| bucket _time span=1mon
| stats 
    earliest(volume) as start_volume,
    latest(volume) as end_volume,
    earliest(_time) as period_start,
    latest(_time) as period_end
| eval consumption_m3 = end_volume - start_volume
| eval consumption_liters = consumption_m3 * 1000
| eval month = strftime(period_start, "%B %Y")
| table month, consumption_liters, consumption_m3
| eval consumption_liters = round(consumption_liters, 0)
| eval consumption_m3 = round(consumption_m3, 3)
```

**Use:** Save as scheduled search, export to CSV, or email

---

## Integration with Other Dashboards

### Compare Hot Water vs Cold Water

```spl
index=utilities (sourcetype=kamstrup:hotwater OR sourcetype=elster:coldwater)
| eval utility = if(sourcetype="kamstrup:hotwater", "Hot Water", "Cold Water")
| eval consumption = if(sourcetype="kamstrup:hotwater", volume * 1000, current_value)
| timechart span=1d latest(consumption) as reading by utility
```

---

## Next Steps

1. ✅ Deploy hot water dashboard XML (see `hotwater_dashboard.xml`)
2. ✅ Set up critical alerts as scheduled searches
3. ✅ Customize thresholds based on your usage patterns
4. ✅ Create monthly reports for trend analysis
5. ✅ Integrate with cold water and heating dashboards for full home view

---

**📊 Ready to visualize? See `hotwater_dashboard.xml` for the complete Splunk dashboard!**

