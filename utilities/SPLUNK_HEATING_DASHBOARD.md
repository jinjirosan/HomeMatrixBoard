# 🔥 Heating System Monitoring Dashboard - Splunk Queries & Insights

## Overview

This document provides comprehensive Splunk queries for monitoring your **Kamstrup Heating** system. The heating gateway provides detailed metrics including heat energy, volume, flow rate, supply/return temperatures, and power consumption for your central heating system.

---

## Field Reference - Kamstrup Heating

Based on actual data from `sourcetype=kamstrup:heating`:

| Field Name | Description | Unit | Example Value |
|-----------|-------------|------|---------------|
| `heat_energy` | Total heat energy delivered | MWh | 12.456 |
| `cooling_energy` | Total cooling energy (if applicable) | MWh | 0.001 |
| `volume` | Total heating water volume | m³ | 245.78 |
| `flow` | Current flow rate | L/h | 180.5 |
| `temp1` | Supply temperature (flow) | °C | 72.4 |
| `temp2` | Return temperature | °C | 55.2 |
| `power` | Current thermal power | kW | 8.5 |
| `mqtt_topic` | MQTT topic path | string | utilities/heating/metrics |
| `received_at` | Timestamp received | ISO8601 | 2026-01-26T10:15:00Z |
| `wifi_rssi` | WiFi signal strength | dBm | -48 |

---

## Dashboard Panels - Top 10 Queries

### 1. Today's Heat Energy Consumption

**Purpose:** Track daily heat energy usage for cost calculation

```spl
index=utilities sourcetype=kamstrup:heating heat_energy=*
| bucket _time span=1d
| stats 
    earliest(heat_energy) as start_energy,
    latest(heat_energy) as end_energy
    by _time
| eval consumption_mwh = end_energy - start_energy
| eval consumption_kwh = consumption_mwh * 1000
| eval date = strftime(_time, "%Y-%m-%d")
| table date, consumption_kwh, consumption_mwh
| eval consumption_kwh = round(consumption_kwh, 2)
| eval consumption_mwh = round(consumption_mwh, 4)
```

**Expected Output:**
- Date, consumption in kWh and MWh
- Typical range: 50-300 kWh/day (varies by season and home size)
- Winter usage is significantly higher than summer

---

### 2. Current Heating Power Output

**Purpose:** Monitor real-time thermal power delivery

```spl
index=utilities sourcetype=kamstrup:heating power=*
| stats latest(power) as current_power_kw
| eval status = case(
    current_power_kw = 0, "Idle",
    current_power_kw < 3, "Low Demand",
    current_power_kw < 8, "Normal",
    current_power_kw < 15, "High Demand",
    1=1, "Peak Load"
)
| eval current_power_kw = round(current_power_kw, 2)
| table current_power_kw, status
```

**Expected Output:**
- Current power in kW
- Status indicator based on power level
- 0 kW = heating off, >5 kW = active heating

---

### 3. Supply Temperature (Flow)

**Purpose:** Monitor heating system supply temperature

```spl
index=utilities sourcetype=kamstrup:heating temp1=*
| timechart span=10m 
    avg(temp1) as avg_supply_temp,
    min(temp1) as min_supply_temp,
    max(temp1) as max_supply_temp
| eval avg_supply_temp = round(avg_supply_temp, 1)
| eval min_supply_temp = round(min_supply_temp, 1)
| eval max_supply_temp = round(max_supply_temp, 1)
```

**Expected Output:**
- Average, min, max supply temperatures over time
- Typical range: 60-80°C for radiator systems, 30-45°C for underfloor heating
- Weather-compensated systems adjust temp based on outdoor temperature

---

### 4. Temperature Differential (ΔT)

**Purpose:** Calculate system efficiency via supply-return differential

```spl
index=utilities sourcetype=kamstrup:heating (temp1=* AND temp2=*)
| eval delta_t = temp1 - temp2
| timechart span=15m 
    avg(delta_t) as avg_delta,
    avg(temp1) as avg_supply,
    avg(temp2) as avg_return
| eval avg_delta = round(avg_delta, 1)
| eval avg_supply = round(avg_supply, 1)
| eval avg_return = round(avg_return, 1)
```

**Expected Output:**
- Temperature differential (°C)
- Ideal ΔT: 15-20°C for efficient operation
- Higher ΔT = more heat extracted = better efficiency
- Lower ΔT = poor heat extraction or high flow rate

---

### 5. Flow Rate Timeline (24 Hours)

**Purpose:** Visualize heating water circulation patterns

```spl
index=utilities sourcetype=kamstrup:heating flow=*
| eval flow_lpm = flow / 60
| timechart span=10m avg(flow_lpm) as avg_flow_lpm
| eval avg_flow_lpm = round(avg_flow_lpm, 2)
```

**Expected Output:**
- Time-series of flow rates
- Correlates with heating demand
- Should vary with thermostat settings and outdoor temperature

---

### 6. Power Consumption Over Time

**Purpose:** Track thermal power delivery throughout the day

```spl
index=utilities sourcetype=kamstrup:heating power=*
| timechart span=15m 
    avg(power) as avg_power_kw,
    max(power) as peak_power_kw
| eval avg_power_kw = round(avg_power_kw, 2)
| eval peak_power_kw = round(peak_power_kw, 2)
```

**Expected Output:**
- Average and peak power consumption
- Shows heating cycles and demand patterns
- Higher morning/evening peaks align with occupancy

---

### 7. Daily Energy Trend (Last 30 Days)

**Purpose:** Compare daily heating usage over a month

```spl
index=utilities sourcetype=kamstrup:heating heat_energy=*
    earliest=-30d latest=now
| bucket _time span=1d
| stats 
    earliest(heat_energy) as start_energy,
    latest(heat_energy) as end_energy
    by _time
| eval daily_kwh = (end_energy - start_energy) * 1000
| eval date = strftime(_time, "%m/%d")
| table date, daily_kwh
| eval daily_kwh = round(daily_kwh, 1)
| sort _time
```

**Expected Output:**
- Daily consumption for last 30 days
- Clear seasonal trends visible
- Helps identify unusual consumption days

---

### 8. Hourly Power Distribution

**Purpose:** Identify heating demand patterns by time of day

```spl
index=utilities sourcetype=kamstrup:heating power=*
| eval hour = strftime(_time, "%H")
| stats 
    avg(power) as avg_power,
    max(power) as max_power,
    count as data_points
    by hour
| eval avg_power = round(avg_power, 2)
| eval max_power = round(max_power, 2)
| sort hour
```

**Expected Output:**
- Average and max power by hour of day
- Typical peaks: 5-8 AM (pre-wake), 5-10 PM (evening)
- Overnight lows if night setback is enabled

---

### 9. System Efficiency Metrics

**Purpose:** Calculate overall heating system efficiency

```spl
index=utilities sourcetype=kamstrup:heating (heat_energy=* AND volume=*)
| stats 
    latest(heat_energy) as total_energy_mwh,
    latest(volume) as total_volume_m3
| eval energy_kwh = total_energy_mwh * 1000
| eval efficiency_kwh_per_m3 = energy_kwh / total_volume_m3
| eval efficiency_kwh_per_m3 = round(efficiency_kwh_per_m3, 1)
| table total_volume_m3, energy_kwh, efficiency_kwh_per_m3
```

**Expected Output:**
- Total volume and energy consumption
- Efficiency metric (kWh per m³ of water circulated)
- Consistent ratio indicates stable system performance

---

### 10. Gateway Health & Connectivity

**Purpose:** Monitor heating system gateway status

```spl
index=utilities sourcetype=kamstrup:heating
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
- Critical for ensuring continuous monitoring

---

## Critical Alerts - Top 5

### Alert 1: System Running Continuously (No Cycling)

**Trigger:** Power > 3 kW for more than 3 hours straight

```spl
index=utilities sourcetype=kamstrup:heating power=*
| streamstats time_window=3h count(eval(power > 3)) as continuous_heating_count
| where continuous_heating_count > 180
| stats 
    latest(power) as current_power,
    latest(continuous_heating_count) as minutes_running,
    avg(power) as avg_power
| eval alert_level = case(
    minutes_running > 360, "🔴 CRITICAL - System Not Cycling",
    minutes_running > 180, "🟡 WARNING - Extended Run Time",
    1=1, "✅ NORMAL"
)
| eval current_power = round(current_power, 1)
| eval avg_power = round(avg_power, 1)
| table alert_level, current_power, avg_power, minutes_running
```

**Action:** Check for:
- Undersized heating system
- Extreme cold weather
- Thermostat malfunction
- Heat loss (insulation issues)

---

### Alert 2: Abnormally High Daily Energy Use

**Trigger:** Today's consumption > 150% of 30-day average

```spl
index=utilities sourcetype=kamstrup:heating heat_energy=*
| bucket _time span=1d
| stats 
    earliest(heat_energy) as start_energy,
    latest(heat_energy) as end_energy
    by _time
| eval daily_kwh = (end_energy - start_energy) * 1000
| eventstats avg(daily_kwh) as avg_consumption
| eval threshold = avg_consumption * 1.5
| where daily_kwh > threshold
| eval alert = "⚠️ HIGH CONSUMPTION - " + round(daily_kwh, 0) + " kWh (avg: " + round(avg_consumption, 0) + " kWh)"
| table _time, alert, daily_kwh, avg_consumption, threshold
```

**Action:** Investigate unusual weather, heating schedule changes, or system malfunction

---

### Alert 3: Low Temperature Differential (Poor Efficiency)

**Trigger:** ΔT < 10°C while heating is running

```spl
index=utilities sourcetype=kamstrup:heating (temp1=* AND temp2=* AND power=*)
| where power > 1
| eval delta_t = temp1 - temp2
| where delta_t < 10
| stats 
    latest(delta_t) as current_delta,
    min(delta_t) as lowest_delta,
    avg(power) as avg_power,
    count as low_delta_events
| eval alert = "⚠️ LOW ΔT - Inefficient Operation (" + round(current_delta, 1) + "°C)"
| table alert, current_delta, lowest_delta, avg_power, low_delta_events
```

**Action:** Check for:
- Flow rate too high
- Radiators/emitters undersized
- System imbalance
- Pump speed settings

---

### Alert 4: Supply Temperature Out of Range

**Trigger:** Supply temp > 85°C (too high) or < 40°C when heating (too low)

```spl
index=utilities sourcetype=kamstrup:heating temp1=*
| where temp1 > 85 OR (temp1 < 40 AND power > 1)
| stats 
    latest(temp1) as current_temp,
    min(temp1) as lowest_temp,
    max(temp1) as highest_temp,
    latest(power) as current_power
| eval alert = case(
    current_temp > 85, "🔴 CRITICAL - Temperature Too High (" + round(current_temp, 1) + "°C)",
    current_temp < 40, "🔴 CRITICAL - Temperature Too Low (" + round(current_temp, 1) + "°C)",
    1=1, "✅ Normal"
)
| table alert, current_temp, lowest_temp, highest_temp, current_power
```

**Action:**
- Too high: Risk of damage, check boiler/heat source
- Too low: Insufficient heating, check heat source operation

---

### Alert 5: Gateway Offline

**Trigger:** No data received in last 10 minutes

```spl
index=utilities sourcetype=kamstrup:heating
| stats latest(_time) as last_seen
| eval time_since = now() - last_seen
| where time_since > 600
| eval minutes_offline = round(time_since / 60, 0)
| eval alert = "🔴 GATEWAY OFFLINE - No data for " + minutes_offline + " minutes"
| table alert, last_seen, minutes_offline
```

**Action:** Check gateway power, WiFi, MQTT broker

---

## Advanced Queries

### Weather-Correlated Energy Analysis

**Purpose:** Correlate heating usage with outdoor temperature (if available)

```spl
index=utilities sourcetype=kamstrup:heating heat_energy=*
| bucket _time span=1h
| stats 
    earliest(heat_energy) as start_energy,
    latest(heat_energy) as end_energy
    by _time
| eval hourly_kwh = (end_energy - start_energy) * 1000
| eval hour = strftime(_time, "%Y-%m-%d %H:00")
| table hour, hourly_kwh
| eval hourly_kwh = round(hourly_kwh, 2)
| sort - hourly_kwh
| head 20
```

**Note:** Enhance by joining with outdoor temperature data if available

---

### Heating Cycle Analysis

**Purpose:** Identify heating on/off cycles per day

```spl
index=utilities sourcetype=kamstrup:heating power=*
| eval is_heating = if(power > 3, 1, 0)
| autoregress is_heating as previous_heating
| eval cycle_start = if(is_heating=1 AND previous_heating=0, 1, 0)
| bucket _time span=1d
| stats sum(cycle_start) as cycles_per_day by _time
| eval date = strftime(_time, "%Y-%m-%d")
| table date, cycles_per_day
| sort - _time
```

**Insight:** Too many cycles = short cycling (inefficient), too few = long runs (may indicate sizing issue)

---

### Cost Estimation (Gas/Oil Heating)

**Purpose:** Estimate heating fuel cost

```spl
index=utilities sourcetype=kamstrup:heating heat_energy=*
| bucket _time span=1d
| stats 
    earliest(heat_energy) as start_energy,
    latest(heat_energy) as end_energy
    by _time
| eval daily_kwh = (end_energy - start_energy) * 1000
| eval boiler_efficiency = 0.85
| eval fuel_kwh = daily_kwh / boiler_efficiency
| eval daily_cost = fuel_kwh * 0.08
| eval date = strftime(_time, "%Y-%m-%d")
| table date, daily_kwh, fuel_kwh, daily_cost
| eval daily_kwh = round(daily_kwh, 1)
| eval fuel_kwh = round(fuel_kwh, 1)
| eval daily_cost = "$" + round(daily_cost, 2)
| sort - _time
| head 30
```

**Note:** Adjust `0.85` for boiler efficiency and `0.08` for fuel cost ($/kWh)

---

### System Performance Score

**Purpose:** Calculate daily performance metric

```spl
index=utilities sourcetype=kamstrup:heating (temp1=* AND temp2=* AND power=*)
| eval delta_t = temp1 - temp2
| eval efficiency_score = case(
    delta_t >= 18 AND power > 0, 100,
    delta_t >= 15 AND power > 0, 85,
    delta_t >= 12 AND power > 0, 70,
    delta_t >= 10 AND power > 0, 50,
    power = 0, null(),
    1=1, 30
)
| bucket _time span=1d
| stats avg(efficiency_score) as daily_score by _time
| eval date = strftime(_time, "%Y-%m-%d")
| eval daily_score = round(daily_score, 0)
| table date, daily_score
| sort - _time
```

---

### Flow Rate vs Power Correlation

**Purpose:** Verify proper system balance

```spl
index=utilities sourcetype=kamstrup:heating (flow=* AND power=*)
| eval flow_lpm = flow / 60
| eval power_kw = power
| chart avg(flow_lpm) as avg_flow over power_kw
| eval avg_flow = round(avg_flow, 1)
```

**Insight:** Flow should increase with power (variable speed pump) or remain constant (fixed speed)

---

## Key Insights & Interpretations

### 1. **Heat Energy Metrics**
- **Total Energy (`heat_energy`)**: Cumulative MWh from heat meter
- **Daily Range**: 50-300 kWh depending on season and home size
- **Seasonal Variation**: Winter consumption 5-10x higher than summer

### 2. **Temperature Analysis**
- **Supply Temp (temp1)**: Radiators 60-80°C, Underfloor 30-45°C
- **Return Temp (temp2)**: Should be 15-20°C lower than supply
- **ΔT Efficiency**: Higher ΔT = better heat extraction = more efficient

### 3. **Power Patterns**
- **Cycling Behavior**: System should cycle on/off, not run continuously
- **Typical Cycles**: 3-6 cycles per hour in moderate weather
- **Load Matching**: Power should match demand (thermostat settings)

### 4. **Flow Rate Insights**
- **Constant Flow**: Fixed-speed circulation pump
- **Variable Flow**: Weather-compensated or modulating system
- **No Flow + Power**: Heat source firing but circulation stopped (pump issue)

### 5. **System Efficiency**
- **Ideal ΔT**: 15-20°C
- **Flow Balance**: Proper flow ensures even heat distribution
- **Cycling Frequency**: Optimal cycling indicates proper sizing

---

## Dashboard Best Practices

### Alert Thresholds (Customize to Your System)
- **Daily Energy**: Your avg ± 50% (account for weather)
- **ΔT**: < 10°C = alert, 15-20°C = ideal
- **Supply Temp**: System-specific (radiator vs underfloor)
- **Continuous Run**: > 3 hours without cycling

### Time Ranges for Different Views
- **Real-time Status**: Last 15 minutes
- **Heating Cycles**: Last 24 hours
- **Daily Patterns**: Last 7 days
- **Seasonal Trends**: Last 365 days

### Correlation with External Factors
- **Outdoor Temperature**: Inverse correlation
- **Occupancy Patterns**: Morning/evening peaks
- **Thermostat Settings**: Direct impact on supply temp

---

## Troubleshooting Common Issues

### Issue 1: High Energy Use Despite Mild Weather

**Diagnostic Query:**
```spl
index=utilities sourcetype=kamstrup:heating heat_energy=*
| bucket _time span=1d
| stats 
    earliest(heat_energy) as start,
    latest(heat_energy) as end,
    avg(power) as avg_power
    by _time
| eval daily_kwh = (end - start) * 1000
| where daily_kwh > 200 AND avg_power > 5
| eval date = strftime(_time, "%Y-%m-%d")
| table date, daily_kwh, avg_power
```

**Possible Causes:** Heat loss, thermostat issues, system short-cycling

---

### Issue 2: Low ΔT (Poor Heat Extraction)

**Diagnostic Query:**
```spl
index=utilities sourcetype=kamstrup:heating (temp1=* AND temp2=*)
| eval delta_t = temp1 - temp2
| stats 
    avg(delta_t) as avg_delta,
    min(delta_t) as min_delta,
    avg(flow) as avg_flow
| eval avg_delta = round(avg_delta, 1)
| eval avg_flow = round(avg_flow, 0)
```

**Possible Causes:** Flow rate too high, radiators undersized, system imbalance

---

### Issue 3: Temperature Fluctuations

**Diagnostic Query:**
```spl
index=utilities sourcetype=kamstrup:heating temp1=*
| bucket _time span=1h
| stats stdev(temp1) as temp_variance by _time
| where temp_variance > 5
| eval hour = strftime(_time, "%Y-%m-%d %H:00")
| table hour, temp_variance
```

**Possible Causes:** Weather compensation issues, thermostat cycling, boiler modulation problems

---

## Export & Reporting

### Monthly Heating Report

```spl
index=utilities sourcetype=kamstrup:heating heat_energy=*
    earliest=-30d@d latest=now
| bucket _time span=1mon
| stats 
    earliest(heat_energy) as start_energy,
    latest(heat_energy) as end_energy,
    avg(temp1) as avg_supply_temp
| eval consumption_kwh = (end_energy - start_energy) * 1000
| eval estimated_cost = consumption_kwh * 0.08
| eval month = strftime(_time, "%B %Y")
| table month, consumption_kwh, avg_supply_temp, estimated_cost
| eval consumption_kwh = round(consumption_kwh, 0)
| eval avg_supply_temp = round(avg_supply_temp, 1) + "°C"
| eval estimated_cost = "$" + round(estimated_cost, 2)
```

---

## Next Steps

1. ✅ Deploy heating dashboard XML (see `heating_dashboard.xml`)
2. ✅ Configure alerts for your system specifications
3. ✅ Baseline your "normal" consumption for comparison
4. ✅ Monitor ΔT for efficiency optimization
5. ✅ Correlate with outdoor temperature for better insights

---

**🔥 Ready to monitor your heating? See `heating_dashboard.xml` for the complete Splunk dashboard!**

