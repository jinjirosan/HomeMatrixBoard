# 🏠 Utilities Overview Dashboard - Installation Guide

## Overview

The **Utilities Overview Dashboard** provides a comprehensive monitoring view of all your home utilities:
- 🔥 **Heating System** (Kamstrup)
- 💧 **Hot Water** (Kamstrup)  
- 🚰 **Cold Water** (Elster)
- ⚡ **Energy** (EmonPi)

This is your **central command center** for monitoring all utilities in one place!

---

## Dashboard Features

### 🎯 **10 Rows × 19 Panels**

#### **Row 1: Current Readings (4 Panels)**
- 🔥 Heating Volume (m³) - Color-coded
- 💧 Hot Water Volume (m³) - Color-coded
- 🚰 Cold Water Total (m³) - Color-coded
- ⚡ Energy Power (kW) - Color-coded

#### **Row 2: System Health**
- 📊 **Health Table** - Shows all 4 utilities with:
  - Status: 🟢 ONLINE / 🟡 DELAYED / 🔴 OFFLINE
  - Message count, last seen time
  - WiFi signal (dBm) with quality rating
  - Firmware version

#### **Row 3: 24-Hour Usage Trends**
- 📈 **Stacked Area Chart** - All utilities usage over 24h
  - Red gradient: Heating
  - Blue gradient: Hot Water
  - Cyan gradient: Cold Water
  - Beautiful transparency effects

#### **Row 4: Flow & Power Monitoring (2 Panels)**
- 💨 **Flow Rates** - Multi-line chart (L/h)
  - Orange: Hot Water
  - Blue: Cold Water
  - Red: Heating
- ⚡ **Power Consumption** - Area chart (kW)
  - Yellow: Hot Water power
  - Red: Heating power

#### **Row 5: Temperature Monitoring**
- 🌡️ **Temperature Chart** - 4 lines
  - Pink: Heating Supply
  - Purple: Heating Return
  - Orange: Hot Water Supply
  - Red: Hot Water Return

#### **Row 6: Daily Consumption**
- 📊 **Column Chart** - Last 7 days comparison
  - Shows daily readings for all 3 water/heating utilities
  - Side-by-side columns for easy comparison

#### **Row 7: Cost Estimation (2 Panels)**
- 💰 **7-Day Cost Breakdown** - Stacked column chart
  - Shows daily costs split by utility
  - Data labels on min/max values
- 💵 **30-Day Total** - Single value panel
  - Shows total estimated cost
  - Color-coded by amount

#### **Row 8: Anomaly Detection**
- ⚠️ **High Flow/Power Alerts** - Table
  - Calculates avg, max, and threshold (2σ above avg)
  - Alert levels: ✅ NORMAL / ⚡ ELEVATED / ⚠️ HIGH
  - Automatically flags unusual activity

#### **Row 9: Leak Detection & Events (2 Panels)**
- 🚨 **Leak Status** - All systems leak detection
  - Tracks burst/leak sensors
  - Flow anomaly detection
  - Total leak events counter
- 📊 **Event Summary** - Last hour statistics
  - Total events per utility
  - Data rate (events/min)
  - Unique topics count

#### **Row 10: Efficiency Metrics (4 Panels)**
- ⭐ **Heating Efficiency** - kWh per m³
- 📈 **Data Ingestion Rate** - Events per minute
- 🔌 **Active Gateways** - Count of online gateways
- 📡 **Average Signal Strength** - WiFi dBm

---

## Installation

### **Method 1: Splunk Web UI** (Recommended)

1. **Log into Splunk Web**
   ```
   http://your-splunk-server:8000
   ```

2. **Navigate to Dashboards**
   - Click **Dashboards** in the top menu
   - Click **Create New Dashboard**

3. **Configure Dashboard**
   - **Title:** `Utilities Monitoring - Overview Dashboard`
   - **ID:** `utilities_overview_dashboard`
   - **Description:** `Comprehensive monitoring of all home utilities`
   - **Permissions:** Shared in App (or Private if preferred)
   - Click **Create**

4. **Add Dashboard XML**
   - Click **Edit** (top right)
   - Click **Source** (switch to source mode)
   - **Delete all existing XML**
   - **Copy entire contents** of `utilities_overview_dashboard.xml`
   - **Paste into editor**
   - Click **Save**

5. **Access Dashboard**
   ```
   http://your-splunk-server:8000/app/search/utilities_overview_dashboard
   ```

---

### **Method 2: File System Deployment**

#### **On Splunk Search Head:**

```bash
# Copy dashboard to Splunk views directory
sudo cp utilities_overview_dashboard.xml \
  /opt/splunk/etc/apps/search/local/data/ui/views/utilities_overview_dashboard.xml

# Set ownership
sudo chown splunk:splunk \
  /opt/splunk/etc/apps/search/local/data/ui/views/utilities_overview_dashboard.xml

# Reload Splunk (optional, usually auto-detected)
sudo /opt/splunk/bin/splunk reload
```

#### **On Deployment Server (for managed search heads):**

```bash
# Create app structure
sudo mkdir -p /opt/splunk/etc/deployment-apps/utilities_dashboards/local/data/ui/views/

# Copy dashboard
sudo cp utilities_overview_dashboard.xml \
  /opt/splunk/etc/deployment-apps/utilities_dashboards/local/data/ui/views/

# Set permissions
sudo chown -R splunk:splunk /opt/splunk/etc/deployment-apps/utilities_dashboards/

# Deploy to search head(s)
sudo /opt/splunk/bin/splunk reload deploy-server
```

---

## Dashboard Controls

### **Time Range Picker**
- Default: Last 24 hours
- Change to: Last 7 days, Last 30 days, etc.
- Affects most panels (some have fixed time ranges)

### **Auto-Refresh Selector**
- **30 seconds** - For active monitoring
- **1 minute** - Default, good balance
- **5 minutes** - Light refresh load
- **None** - Manual refresh only

---

## Customization

### **Adjust Cost Rates**

Edit the cost calculation queries in the dashboard XML:

```xml
<!-- Heating cost rate (per MWh) -->
heat_energy * 100  ← Change 100 to your rate

<!-- Hot water cost rate (per m³) -->
volume * 0.08  ← Change 0.08 to your rate

<!-- Cold water cost rate (per pulse/liter) -->
current_value * 0.000005  ← Adjust to your rate
```

### **Modify Alert Thresholds**

#### **Volume thresholds (Row 1):**
```xml
<option name="rangeValues">[10,20,30]</option>
<!-- Green: <10m³, Yellow: 10-20m³, Orange: 20-30m³, Red: >30m³ -->
```

#### **Flow rate thresholds:**
```xml
<option name="rangeValues">[1,3,5]</option>
<!-- Adjust for your expected flow rates -->
```

#### **Anomaly detection sensitivity:**
```xml
| eval threshold=avg_flow + (2 * stdev_flow)
<!-- Change "2" to adjust sensitivity (1=sensitive, 3=less sensitive) -->
```

### **Add More Utilities**

If you have additional utilities (e.g., gas, electricity from other sources):

1. Add a new single value panel in Row 1
2. Update the sourcetype filters:
   ```
   sourcetype IN (kamstrup:*, elster:*, emonpi:*, your:newtype)
   ```
3. Add color mappings for the new utility

---

## Troubleshooting

### **No Data Showing**

1. **Check index:**
   ```spl
   index=utilities | head 10
   ```
   - Verify data is being ingested

2. **Check sourcetypes:**
   ```spl
   index=utilities | stats count by sourcetype
   ```
   - Should show: `kamstrup:heating`, `kamstrup:hotwater`, `elster:coldwater`, `emonpi:energy`

3. **Check time range:**
   - Ensure you have data within the selected time range
   - Try expanding to "Last 7 days"

### **Missing Panels or Blank Charts**

1. **Field name mismatch:**
   - Dashboard expects specific field names (e.g., `volume`, `flow`, `power`)
   - Run field discovery:
     ```spl
     index=utilities sourcetype=kamstrup:heating | fieldsummary
     ```

2. **Update field names in queries:**
   - If your fields are named differently, edit the XML searches

### **"No results found"**

- **Likely cause:** No data for that specific utility
- **Solution:** 
  - Check MQTT gateway is publishing
  - Verify `mqtt_to_splunk.py` is running
  - Check HAProxy status

### **Slow Dashboard Performance**

1. **Reduce time range:**
   - Use "Last 6 hours" instead of "Last 24 hours"

2. **Increase auto-refresh interval:**
   - Change from 30s to 5m

3. **Optimize searches:**
   - Add specific time ranges to individual panels
   - Use summary indexing for historical data

4. **Enable search acceleration:**
   ```bash
   # On Search Head
   sudo /opt/splunk/bin/splunk enable app-acceleration utilities
   ```

### **Colors Not Showing**

- **Issue:** Thresholds may not match your data ranges
- **Solution:** Adjust `rangeValues` in the XML to match your actual data

---

## Performance Optimization

### **Summary Indexing** (for large datasets)

If you have months of data and the dashboard is slow:

```spl
# Create a summary index
index=utilities sourcetype IN (kamstrup:*, elster:*)
| bucket _time span=1h
| stats 
    latest(volume) as volume,
    latest(flow) as flow,
    latest(power) as power,
    avg(temp1) as avg_temp1
    by _time, sourcetype
| collect index=utilities_summary
```

Schedule this as a saved search to run every hour.

### **Data Model Acceleration**

Create a data model for utilities and enable acceleration:

1. Settings → Data models → New Data Model
2. Build the model with your fields
3. Enable acceleration (1 day, 7 days, or 30 days)
4. Update dashboard searches to use the data model

---

## Integration with Other Dashboards

### **Drill-down to Detail Dashboards**

You can add drill-down from the overview to specific utility dashboards:

1. Edit dashboard XML
2. For each panel, add:
   ```xml
   <option name="drilldown">all</option>
   <drilldown>
     <link target="_blank">/app/search/utilities_coldwater_dashboard?form.time.earliest=$earliest$&amp;form.time.latest=$latest$</link>
   </drilldown>
   ```

### **Link from Navigation Menu**

Create a navigation menu entry:

**File:** `/opt/splunk/etc/apps/search/local/data/ui/nav/default.xml`

```xml
<nav>
  <collection label="Utilities">
    <view name="utilities_overview_dashboard" default="true" />
    <view name="utilities_coldwater_dashboard" />
    <divider />
    <saved source="unclassified" />
  </collection>
</nav>
```

---

## Dashboard Access & Permissions

### **Make Dashboard the Default View**

```bash
# Edit user preferences
/opt/splunk/etc/users/admin/user-prefs/local/user-prefs.conf

[general]
default_namespace = search
display.page.home.dashboardId = utilities_overview_dashboard
```

### **Share Dashboard with Team**

1. In Splunk Web, open the dashboard
2. Click **Edit** → **Edit Permissions**
3. Select **Shared in App**
4. Set read/write permissions for roles
5. Click **Save**

### **Export Dashboard**

To share with other Splunk instances:

1. Open dashboard in Splunk Web
2. Click **Edit** → **Edit Source**
3. Copy entire XML
4. Save to file or share via version control

---

## Key Insights from This Dashboard

### **At a Glance:**
- ✅ All systems online and healthy
- 📊 24-hour usage patterns
- 💰 Cost tracking and estimation
- ⚠️ Immediate anomaly alerts
- 🚨 Leak detection status

### **Use Cases:**

1. **Morning Check** - Verify all systems are online and no leaks
2. **Weekly Review** - Compare daily consumption trends
3. **Monthly Billing** - Review cost estimates before bills arrive
4. **Troubleshooting** - Quickly identify which utility has issues
5. **Optimization** - Spot usage patterns to reduce consumption

---

## Next Steps

### **After Installation:**

1. ✅ Verify all panels are showing data
2. ✅ Adjust color thresholds to match your usage patterns
3. ✅ Set up email alerts based on anomaly detection
4. ✅ Create a scheduled PDF report for weekly summaries
5. ✅ Bookmark the dashboard for quick access

### **Advanced Features:**

- **Mobile View:** Dashboard is responsive and works on tablets
- **TV Display:** Set auto-refresh to 30s and display on wall monitor
- **Alerts:** Create scheduled searches based on dashboard queries
- **Reports:** Schedule PDF delivery of dashboard snapshots

---

## Support

### **Documentation:**
- `SPLUNK_DASHBOARDS.md` - Query reference
- `SPLUNK_COLDWATER_DASHBOARD.md` - Cold water specific guide
- `README.md` - Overall project documentation

### **Related Dashboards:**
- `utilities_coldwater_dashboard.xml` - Detailed cold water monitoring
- `utilities_heating_dashboard.xml` - Heating system details
- `utilities_hotwater_dashboard.xml` - Hot water system details
- (Future) `energy_dashboard.xml` - Energy consumption analysis

---

## Dashboard Statistics

- **Total Panels:** 19
- **Total Rows:** 10
- **Chart Types:** 8 different types
  - Single Value (8)
  - Table (4)
  - Area Chart (3)
  - Line Chart (2)
  - Column Chart (2)
- **Auto-refresh:** Configurable (30s - 5m)
- **Time Range:** Configurable (default 24h)
- **Color Themes:** 5 distinct color palettes

---

## Version History

- **v1.0** (2026-01-26) - Initial release
  - 19 panels across 10 rows
  - Support for 4 utility types
  - Anomaly detection and leak alerts
  - Cost estimation and efficiency metrics

---

**🎉 Enjoy your comprehensive utilities monitoring dashboard!** 🎉

