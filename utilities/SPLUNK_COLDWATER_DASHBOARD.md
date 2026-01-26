# Cold Water Monitoring Dashboard - Elster Gateway

Complete Splunk dashboard guide for monitoring cold water consumption using the Elster smart gateway.

## Overview

**Sourcetype:** `elster:coldwater`  
**Index:** `utilities`  
**Gateway Source:** `coldwater_main`  
**Pulse Factor:** 1 pulse = 1 liter

### Available Metrics

| Field | Description | Event Count | Units |
|-------|-------------|-------------|-------|
| `current_value` | Cumulative meter reading | 191 | pulses (liters) |
| `pulse_count` | Same as current_value | 191 | pulses (liters) |
| `pulse_factor` | Conversion factor | 191 | pulses/liter (always 1) |
| `water_used_last_minute` | Real-time flow rate | 190 | L/min |
| `leak_detect` | Leak detection flag | 187 | 0 or 1 |
| `wifi_rssi` | WiFi signal strength | 538 | dBm |
| `mac_address` | Gateway MAC address | 538 | string |
| `running_firmware_version` | Firmware version | 538 | integer |
| `startup_time` | Last boot time | 538 | timestamp |

**Important Notes:**
- `current_value` is **cumulative** (currently ~551,879 liters since installation)
- Use `water_used_last_minute` for real-time monitoring
- Calculate daily/weekly consumption using deltas of `current_value`

---

## Dashboard Layout

```
┌────────────────────────────────────────────────────────────┐
│ 💧 Cold Water Consumption Dashboard                       │
│ Time Range: Last 24 Hours                  [Refresh: 30s] │
├────────────────────────────────────────────────────────────┤
│ Current Status (Single Value Panels)                      │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│ │Today's   │ │Current   │ │Leak      │ │Gateway   │     │
│ │Usage     │ │Flow      │ │Status    │ │Status    │     │
│ │245 L     │ │1.2 L/min │ │🟢 Normal │ │🟢 Online │     │
│ │(64.7 gal)│ │(19 gal/h)│ │          │ │-45 dBm   │     │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
├────────────────────────────────────────────────────────────┤
│ Real-Time Flow Rate (Last 24 Hours) - Line Chart         │
│ [Shows L/min over time, spikes = usage events]           │
├────────────────────────────────────────────────────────────┤
│ Daily Consumption (Last 30 Days) - Column Chart          │
│ [Bar chart showing daily totals in liters]               │
├─────────────────────────┬──────────────────────────────────┤
│ Hourly Usage Today      │ Weekly Comparison                │
│ [Table showing L/hour]  │ This Week: 1,750 L (462 gal)    │
│                         │ Last Week: 1,680 L (444 gal)    │
│                         │ Change: +70 L (+4.2%)           │
└─────────────────────────┴──────────────────────────────────┘
```

---

## Panel 1: Today's Total Consumption

**Purpose:** Show total water consumed since midnight  
**Visualization:** Single Value  
**Refresh:** 1 minute  
**Time Range:** Today (@d to now)

```spl
index=utilities sourcetype=elster:coldwater current_value=*
    earliest=@d latest=now
| stats 
    earliest(current_value) as start_today,
    latest(current_value) as current_reading
| eval liters_today=current_reading - start_today
| eval gallons_today=round(liters_today * 0.264172, 1)
| eval m3_today=round(liters_today / 1000, 3)
| table liters_today, gallons_today, m3_today
| rename liters_today as "Liters Today", gallons_today as "Gallons Today", m3_today as "m³ Today"
```

**Display Format:**
- Primary: Liters (245 L)
- Secondary: Gallons (64.7 gal)

**Color Thresholds:**
- Green: < 200 L
- Yellow: 200-400 L
- Red: > 400 L

---

## Panel 2: Current Flow Rate

**Purpose:** Display real-time water flow  
**Visualization:** Single Value  
**Refresh:** 30 seconds  
**Time Range:** Last 5 minutes

```spl
index=utilities sourcetype=elster:coldwater water_used_last_minute=*
| stats latest(water_used_last_minute) as current_flow_lpm
| eval flow_lph=round(current_flow_lpm * 60, 1)
| eval flow_gph=round(current_flow_lpm * 60 * 0.264172, 1)
| eval status=case(
    current_flow_lpm = 0, "💧 No Flow",
    current_flow_lpm < 1, "🟢 Light Use",
    current_flow_lpm < 5, "🟡 Moderate Use",
    current_flow_lpm >= 5, "🔴 Heavy Use",
    1=1, "❓ Unknown"
  )
| table status, current_flow_lpm, flow_lph, flow_gph
| rename current_flow_lpm as "L/min", flow_lph as "L/hour", flow_gph as "Gal/hour"
```

**Display Format:**
- Primary: L/min (1.2 L/min)
- Secondary: Gallons/hour (19 gal/h)
- Status indicator with emoji

**Flow Rate Guide:**
- 0 L/min: No usage
- 0.5-2 L/min: Faucet, toilet
- 3-8 L/min: Shower
- 10+ L/min: Multiple fixtures or possible leak

---

## Panel 3: Leak Status

**Purpose:** Show current leak detection status  
**Visualization:** Single Value with status indicator  
**Refresh:** 30 seconds  
**Time Range:** Last 15 minutes

```spl
index=utilities sourcetype=elster:coldwater leak_detect=*
| stats 
    latest(leak_detect) as current_status,
    latest(_time) as last_check,
    count(eval(leak_detect=1)) as leak_events_total
| eval status=case(
    current_status=0, "🟢 NO LEAK",
    current_status=1, "🔴 LEAK DETECTED",
    1=1, "❓ UNKNOWN"
  )
| eval last_check_time=strftime(last_check, "%Y-%m-%d %H:%M:%S")
| eval minutes_ago=round((now() - last_check) / 60, 0)
| table status, leak_events_total, minutes_ago
| rename leak_events_total as "Total Leak Events", minutes_ago as "Last Check (min ago)"
```

**Alert:** Change panel background to red if `current_status=1`

---

## Panel 4: Gateway Health

**Purpose:** Monitor gateway connectivity and signal  
**Visualization:** Single Value  
**Refresh:** 1 minute  
**Time Range:** Last 1 hour

```spl
index=utilities sourcetype=elster:coldwater
| stats 
    latest(_time) as last_seen,
    latest(wifi_rssi) as signal_dbm,
    latest(running_firmware_version) as firmware,
    count as message_count
| eval time_since=now() - last_seen
| eval status=case(
    time_since < 120, "🟢 ONLINE",
    time_since < 600, "🟡 DELAYED",
    1=1, "🔴 OFFLINE"
  )
| eval signal_quality=case(
    signal_dbm > -50, "Excellent",
    signal_dbm > -60, "Good",
    signal_dbm > -70, "Fair",
    1=1, "Poor"
  )
| eval last_seen_friendly=strftime(last_seen, "%H:%M:%S")
| table status, signal_dbm, signal_quality, message_count, firmware
| rename signal_dbm as "Signal (dBm)", signal_quality as "Signal Quality", message_count as "Messages (1h)", firmware as "Firmware"
```

**WiFi Signal Guide:**
- -30 to -50 dBm: Excellent
- -51 to -60 dBm: Good
- -61 to -70 dBm: Fair
- -71+ dBm: Poor (consider relocating gateway)

---

## Panel 5: Flow Rate Timeline (Last 24 Hours)

**Purpose:** Show flow rate over time to identify usage patterns  
**Visualization:** Line Chart  
**Refresh:** 5 minutes  
**Time Range:** Last 24 hours

```spl
index=utilities sourcetype=elster:coldwater water_used_last_minute=*
    earliest=-24h latest=now
| timechart span=5m avg(water_used_last_minute) as avg_flow_lpm
| eval flow_lph=round(avg_flow_lpm * 60, 1)
| eval flow_gph=round(flow_lph * 0.264172, 1)
| fields _time, avg_flow_lpm, flow_lph, flow_gph
| rename avg_flow_lpm as "Flow (L/min)", flow_lph as "Flow (L/hour)", flow_gph as "Flow (gal/hour)"
```

**Chart Settings:**
- X-axis: Time (5-minute intervals)
- Y-axis: Flow rate (L/min)
- Line color: Blue
- Area fill: Light blue (20% opacity)
- Show peaks for usage events

**Overlay Options:**
Add a threshold line at 5 L/min to highlight high usage

---

## Panel 6: Daily Consumption (Last 30 Days)

**Purpose:** Show daily water consumption trends  
**Visualization:** Column Chart  
**Refresh:** 1 hour  
**Time Range:** Last 30 days

```spl
index=utilities sourcetype=elster:coldwater current_value=*
    earliest=-30d latest=now
| bucket _time span=1d
| stats 
    earliest(current_value) as start_of_day,
    latest(current_value) as end_of_day
    by _time
| where isnotnull(start_of_day) AND isnotnull(end_of_day)
| eval daily_liters=end_of_day - start_of_day
| eval daily_gallons=round(daily_liters * 0.264172, 1)
| eval daily_m3=round(daily_liters / 1000, 3)
| eval date=strftime(_time, "%m/%d")
| table _time, date, daily_liters, daily_gallons, daily_m3
| sort - _time
| fields - _time
| rename daily_liters as "Liters", daily_gallons as "Gallons", daily_m3 as "m³"
```

**Chart Settings:**
- X-axis: Date (MM/DD format)
- Y-axis: Liters
- Bar color: Gradient (green to yellow to red based on volume)
- Show average line

**Thresholds:**
- Green: < 200 L/day (normal)
- Yellow: 200-400 L/day (higher than usual)
- Red: > 400 L/day (investigate)

---

## Panel 7: Hourly Usage Today

**Purpose:** Breakdown of water usage by hour today  
**Visualization:** Table  
**Refresh:** 5 minutes  
**Time Range:** Today (@d to now)

```spl
index=utilities sourcetype=elster:coldwater water_used_last_minute=*
    earliest=@d latest=now
| eval hour=strftime(_time, "%H:00")
| stats sum(water_used_last_minute) as hourly_liters by hour
| eval hourly_gallons=round(hourly_liters * 0.264172, 1)
| eval hourly_liters=round(hourly_liters, 1)
| table hour, hourly_liters, hourly_gallons
| sort hour
| rename hour as "Hour", hourly_liters as "Liters", hourly_gallons as "Gallons"
```

**Table Format:**
```
Hour    | Liters | Gallons
--------|--------|--------
07:00   | 45.3   | 12.0
08:00   | 89.7   | 23.7
09:00   | 12.1   | 3.2
...
```

---

## Panel 8: Weekly Comparison

**Purpose:** Compare this week vs last week consumption  
**Visualization:** Single Value or Table  
**Refresh:** 1 hour  
**Time Range:** Last 14 days

```spl
index=utilities sourcetype=elster:coldwater current_value=*
    earliest=-14d latest=now
| eval week=if(_time > relative_time(now(), "-7d"), "This Week", "Last Week")
| bucket _time span=1d
| stats 
    earliest(current_value) as start_reading,
    latest(current_value) as end_reading
    by _time, week
| eval daily_liters=end_reading - start_reading
| stats sum(daily_liters) as total_liters by week
| eval gallons=round(total_liters * 0.264172, 0)
| eval m3=round(total_liters / 1000, 2)
| table week, total_liters, gallons, m3
| transpose 0 header_field=week
| eval change_liters=round('This Week' - 'Last Week', 0)
| eval change_percent=round((('This Week' - 'Last Week') / 'Last Week') * 100, 1)
| eval change_status=case(
    change_percent > 20, "🔴 High Increase",
    change_percent > 10, "🟡 Moderate Increase",
    change_percent > -10, "🟢 Similar",
    change_percent > -20, "🟢 Moderate Decrease",
    1=1, "🟢 Significant Decrease"
  )
| table "Last Week", "This Week", change_liters, change_percent, change_status
```

**Display:**
```
Last Week:   1,680 L (444 gal)
This Week:   1,750 L (462 gal)
Change:      +70 L (+4.2%) 🟡 Moderate Increase
```

---

## Panel 9: Peak Usage Times (Last 7 Days)

**Purpose:** Identify which hours have highest usage  
**Visualization:** Heatmap or Column Chart  
**Refresh:** 6 hours  
**Time Range:** Last 7 days

```spl
index=utilities sourcetype=elster:coldwater water_used_last_minute=*
    earliest=-7d latest=now
| eval hour=strftime(_time, "%H")
| eval day_of_week=strftime(_time, "%A")
| stats 
    avg(water_used_last_minute) as avg_flow,
    max(water_used_last_minute) as max_flow,
    sum(water_used_last_minute) as total_flow,
    count as samples
    by hour
| eval avg_flow=round(avg_flow, 2)
| eval max_flow=round(max_flow, 1)
| eval total_flow=round(total_flow, 0)
| sort hour
| rename hour as "Hour", avg_flow as "Avg Flow (L/min)", max_flow as "Max Flow (L/min)", total_flow as "Total (L)", samples as "Samples"
```

**Typical Usage Pattern:**
- 06:00-09:00: Morning peak (showers, coffee, breakfast)
- 12:00-13:00: Lunch peak
- 18:00-21:00: Evening peak (dinner, dishes, showers)
- 22:00-06:00: Minimal (toilets only)

---

## Panel 10: Continuous Flow Detection (Leak Alert)

**Purpose:** Detect sustained water flow (potential leak)  
**Visualization:** Single Value with alert status  
**Refresh:** 5 minutes  
**Time Range:** Last 2 hours

```spl
index=utilities sourcetype=elster:coldwater water_used_last_minute=*
    earliest=-2h latest=now
| where water_used_last_minute > 0.1
| streamstats count as consecutive_minutes reset_on_change=f
| stats 
    max(consecutive_minutes) as longest_flow,
    latest(water_used_last_minute) as current_flow
| eval alert=case(
    longest_flow > 60, "🔴 LEAK SUSPECTED (>1hr continuous)",
    longest_flow > 30, "🟡 INVESTIGATE (>30min continuous)",
    longest_flow > 15, "🟢 NORMAL (but extended use)",
    1=1, "🟢 NORMAL"
  )
| eval message=case(
    longest_flow > 60, "Water has been flowing continuously for " . longest_flow . " minutes. Possible leak!",
    longest_flow > 30, "Water flowing for " . longest_flow . " minutes. Check for running fixtures.",
    1=1, "No continuous flow detected."
  )
| table alert, longest_flow, current_flow, message
| rename longest_flow as "Longest Continuous Flow (min)", current_flow as "Current Flow (L/min)"
```

**Alert Logic:**
- > 60 minutes: RED - Likely leak
- 30-60 minutes: YELLOW - Investigate (might be dishwasher, laundry, or leak)
- 15-30 minutes: GREEN - Probably normal (shower, bath)
- < 15 minutes: GREEN - Normal usage

---

## Advanced Queries

### Query: Consumption by Day of Week

**Purpose:** Identify which days have highest usage

```spl
index=utilities sourcetype=elster:coldwater current_value=*
    earliest=-30d latest=now
| bucket _time span=1d
| stats 
    earliest(current_value) as start,
    latest(current_value) as end
    by _time
| eval daily_liters=end - start
| eval day_of_week=strftime(_time, "%A")
| stats 
    avg(daily_liters) as avg_liters,
    count as sample_days
    by day_of_week
| eval avg_liters=round(avg_liters, 0)
| eval avg_gallons=round(avg_liters * 0.264172, 0)
| sort - avg_liters
| rename day_of_week as "Day", avg_liters as "Avg Liters", avg_gallons as "Avg Gallons", sample_days as "Days Sampled"
```

**Expected Results:**
- Weekdays: Higher usage (laundry, dishes, showers before work)
- Weekends: Lower usage (people away) or higher (home projects)

---

### Query: Water Usage Efficiency Score

**Purpose:** Rate current week vs historical average

```spl
index=utilities sourcetype=elster:coldwater current_value=*
    earliest=-60d latest=now
| bucket _time span=1d
| stats 
    earliest(current_value) as start,
    latest(current_value) as end
    by _time
| eval daily_liters=end - start
| eval is_this_week=if(_time > relative_time(now(), "-7d"), 1, 0)
| stats 
    avg(eval(if(is_this_week=0, daily_liters, null()))) as historical_avg,
    avg(eval(if(is_this_week=1, daily_liters, null()))) as this_week_avg
| eval efficiency_score=case(
    this_week_avg < (historical_avg * 0.8), "⭐⭐⭐⭐⭐ Excellent",
    this_week_avg < (historical_avg * 0.9), "⭐⭐⭐⭐ Good",
    this_week_avg < historical_avg, "⭐⭐⭐ Average",
    this_week_avg < (historical_avg * 1.1), "⭐⭐ Below Average",
    1=1, "⭐ Poor"
  )
| eval savings_liters=round(historical_avg - this_week_avg, 0)
| eval savings_percent=round(((historical_avg - this_week_avg) / historical_avg) * 100, 1)
| eval historical_avg=round(historical_avg, 0)
| eval this_week_avg=round(this_week_avg, 0)
| table efficiency_score, this_week_avg, historical_avg, savings_liters, savings_percent
```

---

### Query: Unusual Usage Detection

**Purpose:** Detect days with abnormal water usage

```spl
index=utilities sourcetype=elster:coldwater current_value=*
    earliest=-30d latest=now
| bucket _time span=1d
| stats 
    earliest(current_value) as start,
    latest(current_value) as end
    by _time
| eval daily_liters=end - start
| eventstats 
    avg(daily_liters) as avg_usage,
    stdev(daily_liters) as stdev_usage
| eval upper_threshold=avg_usage + (2 * stdev_usage)
| eval lower_threshold=avg_usage - (2 * stdev_usage)
| eval anomaly=case(
    daily_liters > upper_threshold, "🔴 HIGH",
    daily_liters < lower_threshold, "🟡 LOW",
    1=1, "🟢 NORMAL"
  )
| where anomaly!="🟢 NORMAL"
| eval date=strftime(_time, "%Y-%m-%d %A")
| eval daily_gallons=round(daily_liters * 0.264172, 0)
| eval avg_usage=round(avg_usage, 0)
| table date, daily_liters, daily_gallons, avg_usage, anomaly
| sort - _time
| head 20
```

**Use Case:** Identify potential leaks, meter errors, or days when you had guests

---

## Alert Configurations

### Alert 1: Continuous Flow > 1 Hour

**Search:**
```spl
index=utilities sourcetype=elster:coldwater water_used_last_minute=*
    earliest=-2h latest=now
| where water_used_last_minute > 0.1
| streamstats count as consecutive_minutes reset_on_change=f
| stats max(consecutive_minutes) as longest_flow
| where longest_flow > 60
```

**Trigger:** When water flows continuously for > 60 minutes  
**Throttle:** 30 minutes  
**Action:** Email, SMS, Webhook  
**Priority:** Critical

---

### Alert 2: High Flow Rate (Possible Burst)

**Search:**
```spl
index=utilities sourcetype=elster:coldwater water_used_last_minute=*
| stats max(water_used_last_minute) as max_flow
| where max_flow > 10
```

**Trigger:** When flow > 10 L/min  
**Throttle:** 15 minutes  
**Action:** Email, SMS  
**Priority:** High

**Context:** Normal shower = 5-8 L/min, so >10 L/min suggests multiple fixtures or burst

---

### Alert 3: Leak Detected by Gateway

**Search:**
```spl
index=utilities sourcetype=elster:coldwater leak_detect=1
```

**Trigger:** Immediate when leak_detect flag = 1  
**Throttle:** 5 minutes  
**Action:** Email, SMS, Push notification  
**Priority:** Critical

---

### Alert 4: Gateway Offline

**Search:**
```spl
index=utilities sourcetype=elster:coldwater
| stats latest(_time) as last_seen
| eval minutes_since=round((now() - last_seen) / 60, 0)
| where minutes_since > 15
```

**Trigger:** No data received for > 15 minutes  
**Throttle:** 1 hour  
**Action:** Email  
**Priority:** Medium

---

### Alert 5: Abnormal Daily Usage

**Search:**
```spl
index=utilities sourcetype=elster:coldwater current_value=*
    earliest=@d latest=now
| stats 
    earliest(current_value) as start,
    latest(current_value) as current
| eval liters_today=current - start
| where liters_today > 500
```

**Trigger:** When daily usage > 500 liters (adjust based on household)  
**Throttle:** Daily at 20:00  
**Action:** Email summary  
**Priority:** Low

---

## Cost Tracking

### Monthly Water Cost Estimate

**Purpose:** Calculate estimated water bill based on consumption

```spl
index=utilities sourcetype=elster:coldwater current_value=*
    earliest=-30d latest=now
| bucket _time span=1mon
| stats 
    earliest(current_value) as start_month,
    latest(current_value) as end_month
    by _time
| eval monthly_liters=end_month - start_month
| eval monthly_m3=monthly_liters / 1000
| eval monthly_gallons=round(monthly_liters * 0.264172, 0)
| eval cost_estimate=monthly_m3 * 2.50
| eval month=strftime(_time, "%B %Y")
| eval monthly_m3=round(monthly_m3, 2)
| eval cost_estimate=round(cost_estimate, 2)
| table month, monthly_liters, monthly_m3, monthly_gallons, cost_estimate
| rename monthly_liters as "Liters", monthly_m3 as "Cubic Meters", monthly_gallons as "Gallons", cost_estimate as "Estimated Cost ($)"
```

**Note:** Adjust `* 2.50` to your actual water rate per m³

---

## Maintenance & Troubleshooting

### Check Data Freshness

```spl
index=utilities sourcetype=elster:coldwater
| stats 
    latest(_time) as last_event,
    count as total_events
| eval seconds_ago=now() - last_event
| eval minutes_ago=round(seconds_ago / 60, 1)
| eval status=case(
    seconds_ago < 300, "🟢 Data is fresh",
    seconds_ago < 900, "🟡 Data is delayed",
    1=1, "🔴 No recent data"
  )
| eval last_event_time=strftime(last_event, "%Y-%m-%d %H:%M:%S")
| table status, last_event_time, minutes_ago, total_events
```

---

### Verify Pulse Factor

```spl
index=utilities sourcetype=elster:coldwater pulse_factor=*
| stats 
    latest(pulse_factor) as current_factor,
    dc(pulse_factor) as unique_values,
    count as total_events
| eval note=if(current_factor=1, "✓ Correct (1 pulse = 1 liter)", "⚠ Unexpected value")
| table current_factor, unique_values, total_events, note
```

---

### Field Availability Report

```spl
index=utilities sourcetype=elster:coldwater
    earliest=-24h latest=now
| stats 
    count(eval(isnotnull(current_value))) as has_current_value,
    count(eval(isnotnull(pulse_count))) as has_pulse_count,
    count(eval(isnotnull(water_used_last_minute))) as has_flow_rate,
    count(eval(isnotnull(leak_detect))) as has_leak_detect,
    count(eval(isnotnull(wifi_rssi))) as has_wifi_signal,
    count as total_events
| transpose 0
| rename "row 1" as count, column as field
```

---

## Performance Tips

1. **Use summary indexing** for historical data:
   ```spl
   | collect index=summary_coldwater sourcetype=coldwater:daily
   ```

2. **Limit time ranges** for real-time panels:
   - Flow rate: Last 5 minutes
   - Today's usage: @d to now
   - Trends: Last 24h or 7d

3. **Use data models** for frequently accessed queries

4. **Schedule expensive queries** to run hourly and cache results

---

## Related Documentation

- [SPLUNK_DASHBOARDS.md](SPLUNK_DASHBOARDS.md) - All utilities dashboards
- [SPLUNK_SETUP.md](SPLUNK_SETUP.md) - Splunk HEC configuration
- [mqtt_topic_utilities.md](mqtt_topic_utilities.md) - MQTT broker integration
- [README.md](README.md) - Utilities system overview

---

**Last Updated:** 2026-01-26  
**Version:** 1.0.0  
**Data Source:** Elster Smart Gateway (coldwater_main)  
**Total Events Analyzed:** 16,711 (across all utilities)  
**Cold Water Events:** 191 (current_value, pulse_count, pulse_factor)

