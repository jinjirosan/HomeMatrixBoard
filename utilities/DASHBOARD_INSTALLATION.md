# Splunk Dashboard Installation Guide

Quick guide to install the Cold Water Dashboard XML into Splunk.

## Installation Steps

### Method 1: Via Splunk Web UI (Recommended)

1. **Log into Splunk** Search Head
   - Navigate to your Splunk web interface
   - Default: `http://your-splunk:8000`

2. **Go to Dashboards**
   - Click **Dashboards** in the top menu
   - Or navigate to: **Settings** → **User Interface** → **Dashboards**

3. **Create New Dashboard**
   - Click **Create New Dashboard**
   - Dashboard Title: `Cold Water Consumption Dashboard`
   - Dashboard ID: `coldwater_dashboard`
   - Dashboard Permissions: Choose appropriate permissions
   - Click **Create**

4. **Edit Source**
   - Once created, click **Edit** → **Edit Source**
   - Delete all existing XML code
   - Copy the entire contents of `coldwater_dashboard.xml`
   - Paste into the source editor
   - Click **Save**

5. **Done!**
   - Your dashboard should now display with all panels

---

### Method 2: Via File System (Search Head)

1. **SSH to Splunk Search Head**
   ```bash
   ssh user@your-splunk-searchhead
   ```

2. **Navigate to Dashboards Directory**
   ```bash
   cd $SPLUNK_HOME/etc/apps/search/local/data/ui/views/
   # Or for a custom app:
   # cd $SPLUNK_HOME/etc/apps/YOUR_APP/local/data/ui/views/
   ```

3. **Create Dashboard File**
   ```bash
   sudo nano coldwater_dashboard.xml
   # Paste the XML content
   # Save and exit (Ctrl+X, Y, Enter)
   ```

4. **Set Permissions**
   ```bash
   sudo chown splunk:splunk coldwater_dashboard.xml
   sudo chmod 644 coldwater_dashboard.xml
   ```

5. **Reload Splunk** (if needed)
   ```bash
   sudo /opt/splunk/bin/splunk reload
   # Or restart:
   # sudo /opt/splunk/bin/splunk restart
   ```

6. **Access Dashboard**
   - Navigate to: `http://your-splunk:8000/app/search/coldwater_dashboard`

---

## Dashboard Features

### 🎨 Visual Elements

**Single Value Panels** (with color coding):
- Today's Total Consumption (green/yellow/red thresholds)
- Current Flow Rate (0-10 L/min)
- Leak Detection Status (green=OK, red=LEAK)
- Gateway Health (signal strength)
- Continuous Flow Detection (leak alert)
- Efficiency Score (vs 30-day average)
- Monthly Cost Estimate
- Data Freshness indicator

**Charts:**
- **Area Chart** - Real-time flow rate timeline (blue gradient)
- **Column Chart** - Daily consumption (green bars)
- **Column Chart** - Peak usage times by hour (green/red)

**Tables:**
- Hourly usage breakdown (color-coded by usage level)
- Weekly comparison (with trend indicators ⬆⬇→)

### ⚙️ Dashboard Controls

**Time Range Picker:**
- Default: Last 24 hours
- Adjustable via dropdown

**Auto Refresh:**
- 30 seconds (default)
- 1 minute
- 5 minutes
- None

### 🎨 Color Scheme

**Consumption Levels:**
- 🟢 Green (#65A637): Normal/Low
- 🔵 Blue (#6DB7C6): Moderate
- 🟡 Yellow (#F7BC38): High
- 🔴 Red (#D93F3C): Critical/Leak

**Signal Strength:**
- Green: Excellent/Good
- Yellow: Fair
- Red: Poor/Offline

---

## Customization

### Adjust Thresholds

**Edit consumption thresholds** (Panel 1 - Today's Total):
```xml
<option name="rangeValues">[200,400,600]</option>
```
Change values to match your household:
- `[150,300,450]` for lower usage
- `[300,600,900]` for higher usage

**Edit flow rate thresholds** (Panel 2 - Current Flow):
```xml
<option name="rangeValues">[0.1,1,5]</option>
```

**Edit leak detection threshold** (Panel 6 - Continuous Flow):
```xml
| eval alert_value=case(
    longest_flow > 60, 100,    ← Change to 120 for 2-hour threshold
    longest_flow > 30, 66,     ← Change to 60 for 1-hour threshold
    ...
```

### Change Water Cost Rate

**Edit cost calculation** (Panel 7 - Monthly Cost):
```xml
| eval cost_estimate=monthly_m3 * 2.50
```
Replace `2.50` with your actual rate per m³

### Add More Panels

To add custom panels:
1. Click **Edit** → **Add Panel**
2. Choose visualization type
3. Add SPL query from `SPLUNK_COLDWATER_DASHBOARD.md`
4. Configure visualization options

---

## Troubleshooting

### ❌ "No results found"

**Check:**
1. Data is flowing: `index=utilities sourcetype=elster:coldwater | head 10`
2. Time range is correct (try last 24 hours)
3. Field names match your data

### ❌ Dashboard shows errors

**Check:**
1. XML syntax is valid (no missing tags)
2. All `<` and `>` characters are properly escaped in queries
   - Use `&lt;` for `<`
   - Use `&gt;` for `>`
   - Use `&amp;` for `&`

### ❌ Panels show "Waiting for input"

**Solution:**
1. Click **Edit** → **Edit Tokens**
2. Set default values for `$time_token$` and `$refresh_token$`

### ❌ Colors not showing

**Check:**
1. `useColors` option is set to `1`
2. `rangeValues` and `rangeColors` arrays have matching lengths
3. Color hex codes are valid

### ❌ Charts show wrong data

**Verify field names:**
```spl
index=utilities sourcetype=elster:coldwater
| head 1
| transpose
```
Update field names in queries if they differ from expected

---

## Performance Optimization

### For Large Datasets

1. **Use summary indexing** for historical data
2. **Limit time ranges** on expensive queries
3. **Increase refresh intervals** (5m instead of 30s)
4. **Use search acceleration** for frequently used searches

### Enable Dashboard Cache

```bash
# In $SPLUNK_HOME/etc/system/local/web.conf
[dashboard]
dashboard_cache_enabled = true
dashboard_cache_timeout = 300
```

---

## Dashboard Permissions

### Share Dashboard

1. **Go to Dashboard** → **Edit** → **Edit Permissions**
2. Choose:
   - **Private** - Only you can see it
   - **App** - All users of the app
   - **Global** - All users (all apps)

3. Set **Read/Write** permissions for roles

---

## Export/Backup

### Export Dashboard

```bash
# From search head:
sudo cp $SPLUNK_HOME/etc/apps/search/local/data/ui/views/coldwater_dashboard.xml /path/to/backup/
```

### Import to Another Splunk Instance

1. Copy XML file to new instance
2. Place in: `$SPLUNK_HOME/etc/apps/search/local/data/ui/views/`
3. Reload or restart Splunk

---

## Related Documentation

- [SPLUNK_COLDWATER_DASHBOARD.md](SPLUNK_COLDWATER_DASHBOARD.md) - Query documentation
- [SPLUNK_DASHBOARDS.md](SPLUNK_DASHBOARDS.md) - All utilities dashboards
- [SPLUNK_SETUP.md](SPLUNK_SETUP.md) - Splunk HEC configuration

---

## Support

**Splunk Dashboard XML Reference:**
- [Splunk Dashboard Framework](https://docs.splunk.com/Documentation/Splunk/latest/Viz/PanelreferenceforSimplifiedXML)
- [Simple XML Reference](https://docs.splunk.com/Documentation/Splunk/latest/Viz/PanelreferenceforSimplifiedXML)

**Dashboard Issues:**
1. Check Splunk logs: `index=_internal sourcetype=splunkd component=dashboard`
2. Verify SPL syntax in search bar first
3. Test queries individually before adding to dashboard

---

**Last Updated:** 2026-01-26  
**Dashboard Version:** 1.0.0  
**Splunk Version:** 8.2+ (Simple XML)

