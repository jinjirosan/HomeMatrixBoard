# MDGi App Integration Guide - Utilities Dashboards

## Overview

This guide provides step-by-step instructions to integrate the utilities monitoring dashboards into your existing **MDGi** Splunk app with drill-down navigation.

---

## Integration Architecture

### Dashboard Hierarchy

```
MDGi App Navigation
├── Overall Status (default)
├── Environment
├── Power Grid
├── ... (existing dashboards)
└── 🏠 Utilities (NEW)
    ├── Overview Dashboard (main landing)
    ├── 🔥 Heating Dashboard
    ├── 💧 Hot Water Dashboard
    └── 🚰 Cold Water Dashboard
```

### Drill-Down Flow

```
Overview Dashboard
    │
    ├─[Click Heating Panel]──────> Heating Dashboard
    │
    ├─[Click Hot Water Panel]────> Hot Water Dashboard
    │
    └─[Click Cold Water Panel]───> Cold Water Dashboard
```

---

## Prerequisites

- Splunk app **MDGi** already deployed
- Access to Splunk deployment server or direct access to search head
- Admin/power user permissions in Splunk
- All 4 dashboard XML files ready:
  - `utilities_overview_dashboard.xml`
  - `heating_dashboard.xml`
  - `hotwater_dashboard.xml`
  - `coldwater_dashboard.xml`

---

## Installation Steps

### Step 1: Copy Dashboard Files to MDGi App

#### Option A: Deployment Server Method (Recommended)

```bash
# On your deployment server
cd /opt/splunk/etc/deployment-apps/MDGi/local/data/ui/views/

# Copy all 4 dashboard XML files
sudo cp /path/to/utilities_overview_dashboard.xml .
sudo cp /path/to/heating_dashboard.xml .
sudo cp /path/to/hotwater_dashboard.xml .
sudo cp /path/to/coldwater_dashboard.xml .

# Set ownership
sudo chown -R splunk:splunk /opt/splunk/etc/deployment-apps/MDGi/

# Deploy to search head(s)
sudo /opt/splunk/bin/splunk reload deploy-server
```

#### Option B: Direct Search Head Installation

```bash
# On your search head
cd /opt/splunk/etc/apps/MDGi/local/data/ui/views/

# If the directory doesn't exist, create it
sudo mkdir -p /opt/splunk/etc/apps/MDGi/local/data/ui/views/

# Copy all 4 dashboard XML files
sudo cp /path/to/utilities_overview_dashboard.xml .
sudo cp /path/to/heating_dashboard.xml .
sudo cp /path/to/hotwater_dashboard.xml .
sudo cp /path/to/coldwater_dashboard.xml .

# Set ownership
sudo chown -R splunk:splunk /opt/splunk/etc/apps/MDGi/

# Reload Splunk (dashboards usually auto-detect, but this ensures it)
sudo /opt/splunk/bin/splunk reload
```

---

### Step 2: Update Navigation Menu

#### Update default.xml

```bash
# On deployment server (or directly on search head)
cd /opt/splunk/etc/apps/MDGi/local/data/ui/nav/

# Backup existing navigation
sudo cp default.xml default.xml.backup

# Edit the navigation file
sudo nano default.xml
```

**Add the Utilities collection** (insert between existing collections):

```xml
<nav search_view="search" color="#dd6600">
  <view name="search"/>
  <view name="reports"/>
  <view name="overall_status" default='true'/>
  <view name="environment"/>
  <view name="power_grid"/>
  <view name="nodes"/>
  <view name="storage"/>
  <view name="firewalls"/>
  <view name="steppingstones"/>
  <view name="splunk_ops"/>
  <view name="wifi"/>
  
  <!-- NEW: Utilities Monitoring -->
  <collection label="Utilities">
    <view name="utilities_overview_dashboard" />
    <view name="heating_dashboard" />
    <view name="hotwater_dashboard" />
    <view name="coldwater_dashboard" />
  </collection>
  
  <!-- Existing collections below -->
  <collection label="Splunk Health">
    <a href="http://splunkds.flinkerbusch.intranet:8000/splunkds/en-US/app/splunk_monitoring_console/monitoringconsole_overview">Overview</a>
    <a href="http://splunkds.flinkerbusch.intranet:8000/splunkds/en-US/app/splunk_monitoring_console/resource_usage_deployment">Resource Usage</a>
    <a href="http://splunkds.flinkerbusch.intranet:8000/splunkds/en-US/app/splunk_monitoring_console/indexing_performance_deployment">Indexing performance</a>
    <a href="http://splunkds.flinkerbusch.intranet:8000/splunkds/en-US/app/splunk_monitoring_console/license_usage_30days">License Usage</a>
  </collection>
  
  <collection label="Splunk">  
    <view name="datasets" />
    <view name="alerts" />
    <view name="dashboards" />
    <view name="analysis_workspace" />
  </collection>
</nav>
```

**Save and set permissions:**

```bash
sudo chown splunk:splunk default.xml
```

---

### Step 3: Verify Dashboard Permissions

Ensure the dashboards are visible in the app:

```bash
# Check file permissions
ls -la /opt/splunk/etc/apps/MDGi/local/data/ui/views/*.xml

# All should be owned by splunk:splunk with 644 permissions
```

**Expected output:**
```
-rw-r--r-- 1 splunk splunk 51234 Jan 26 10:30 coldwater_dashboard.xml
-rw-r--r-- 1 splunk splunk 58374 Jan 26 10:30 heating_dashboard.xml
-rw-r--r-- 1 splunk splunk 54829 Jan 26 10:30 hotwater_dashboard.xml
-rw-r--r-- 1 splunk splunk 64238 Jan 26 10:30 utilities_overview_dashboard.xml
```

---

### Step 4: Set Dashboard Metadata (Optional)

Create metadata for better dashboard descriptions:

```bash
# Create metadata directory if it doesn't exist
sudo mkdir -p /opt/splunk/etc/apps/MDGi/metadata/

# Edit default.meta
sudo nano /opt/splunk/etc/apps/MDGi/metadata/default.meta
```

**Add these entries:**

```ini
# Utilities Dashboards
[views/utilities_overview_dashboard]
owner = admin
version = 1.0
modtime = 1706262000
export = system

[views/heating_dashboard]
owner = admin
version = 1.0
modtime = 1706262000
export = system

[views/hotwater_dashboard]
owner = admin
version = 1.0
modtime = 1706262000
export = system

[views/coldwater_dashboard]
owner = admin
version = 1.0
modtime = 1706262000
export = system
```

---

### Step 5: Reload and Test

#### Reload Splunk

```bash
# On deployment server (if using)
sudo /opt/splunk/bin/splunk reload deploy-server

# On search head
sudo /opt/splunk/bin/splunk reload
# OR just restart web interface
sudo /opt/splunk/bin/splunk restart splunkweb
```

#### Access and Test

1. **Open MDGi App:**
   ```
   http://your-splunk:8000/app/MDGi/overall_status
   ```

2. **Navigate to Utilities:**
   - Look for new "Utilities" dropdown in navigation bar
   - Click to expand
   - Click "utilities_overview_dashboard"

3. **Test Drill-Downs:**
   - Click on "🔥 Heating System" panel → should open Heating Dashboard in new tab
   - Click on "💧 Hot Water" panel → should open Hot Water Dashboard
   - Click on "🚰 Cold Water" panel → should open Cold Water Dashboard

---

## URL Structure

After integration, your dashboards will be accessible at:

| Dashboard | URL |
|-----------|-----|
| **Overview** | `http://splunk:8000/app/MDGi/utilities_overview_dashboard` |
| **Heating** | `http://splunk:8000/app/MDGi/heating_dashboard` |
| **Hot Water** | `http://splunk:8000/app/MDGi/hotwater_dashboard` |
| **Cold Water** | `http://splunk:8000/app/MDGi/coldwater_dashboard` |

---

## Customization Options

### Option 1: Custom Dashboard Titles in Navigation

Edit the dashboard XML files to customize titles shown in nav menu:

```xml
<!-- In each dashboard XML, update the label -->
<label>🏠 Utilities Overview</label>  <!-- Instead of long title -->
```

### Option 2: Change Navigation Icon/Color

Edit `default.xml` to add emoji or custom labels:

```xml
<collection label="🏠 Utilities">
  <view name="utilities_overview_dashboard" label="Overview" />
  <view name="heating_dashboard" label="🔥 Heating" />
  <view name="hotwater_dashboard" label="💧 Hot Water" />
  <view name="coldwater_dashboard" label="🚰 Cold Water" />
</collection>
```

### Option 3: Make Utilities Overview the Default Dashboard

If you want utilities overview to be the landing page:

```xml
<nav search_view="search" color="#dd6600">
  <view name="search"/>
  <view name="reports"/>
  <view name="utilities_overview_dashboard" default='true'/>  <!-- NEW DEFAULT -->
  <view name="overall_status"/>  <!-- Remove default='true' from here -->
  <!-- ... rest of navigation ... -->
</nav>
```

### Option 4: Add Breadcrumb Navigation

Add a note panel at the top of each sub-dashboard to link back to overview:

```xml
<!-- Add this row at the top of heating/hotwater/coldwater dashboards -->
<row>
  <panel>
    <html>
      <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; text-align: center;">
        <a href="/app/MDGi/utilities_overview_dashboard" style="font-size: 14px; color: #0066cc;">
          ⬅ Back to Utilities Overview
        </a>
      </div>
    </html>
  </panel>
</row>
```

---

## Troubleshooting

### Issue 1: Dashboards Not Showing in Navigation

**Symptoms:** Utilities collection visible but dashboards are empty/missing

**Solution:**
```bash
# Check if dashboard files exist
ls -la /opt/splunk/etc/apps/MDGi/local/data/ui/views/utilities*.xml
ls -la /opt/splunk/etc/apps/MDGi/local/data/ui/views/*water*.xml
ls -la /opt/splunk/etc/apps/MDGi/local/data/ui/views/heating*.xml

# Verify file permissions
sudo chown -R splunk:splunk /opt/splunk/etc/apps/MDGi/

# Reload
sudo /opt/splunk/bin/splunk restart splunkweb
```

### Issue 2: Drill-Down Links Not Working

**Symptoms:** Clicking panels doesn't navigate to sub-dashboards

**Check:**
1. Verify app name in XML is correct (`/app/MDGi/...`)
2. Check that dashboards exist in the MDGi app
3. Verify user has permissions to access dashboards

**Fix drill-down links:**
```xml
<!-- Ensure the app name matches your actual app name -->
<drilldown>
  <link target="_blank">/app/MDGi/heating_dashboard?form.time_token.earliest=$time_token.earliest$&amp;form.time_token.latest=$time_token.latest$</link>
</drilldown>
```

### Issue 3: Navigation Menu Not Updating

**Symptoms:** New Utilities collection not appearing

**Solution:**
```bash
# Clear browser cache
# Then restart Splunk web

# On search head
sudo /opt/splunk/bin/splunk restart splunkweb

# If using deployment server, force a deployment
sudo /opt/splunk/bin/splunk reload deploy-server
```

### Issue 4: Dashboard Shows "No results found"

**Symptoms:** Dashboards load but show no data

**Check:**
1. Verify data is in the `utilities` index:
   ```spl
   index=utilities | stats count by sourcetype
   ```

2. Check HEC is receiving data (see DEPLOYMENT_GUIDE.md)

3. Verify time range includes data:
   - Try expanding time range to "Last 7 days"

---

## File Structure Reference

After integration, your MDGi app structure should look like:

```
/opt/splunk/etc/apps/MDGi/
├── local/
│   ├── data/
│   │   └── ui/
│   │       ├── nav/
│   │       │   └── default.xml (UPDATED)
│   │       └── views/
│   │           ├── utilities_overview_dashboard.xml (NEW)
│   │           ├── heating_dashboard.xml (NEW)
│   │           ├── hotwater_dashboard.xml (NEW)
│   │           └── coldwater_dashboard.xml (NEW)
│   └── metadata/
│       └── default.meta (OPTIONAL)
└── ... (existing MDGi app files)
```

---

## Deployment Checklist

- [ ] Copy 4 dashboard XML files to MDGi app views directory
- [ ] Update navigation default.xml with Utilities collection
- [ ] Set file permissions (splunk:splunk, 644)
- [ ] Reload Splunk web interface
- [ ] Test navigation menu shows "Utilities"
- [ ] Test overview dashboard loads with data
- [ ] Test drill-down from Heating panel
- [ ] Test drill-down from Hot Water panel
- [ ] Test drill-down from Cold Water panel
- [ ] Verify time range tokens pass correctly to sub-dashboards
- [ ] Test auto-refresh functionality
- [ ] Bookmark utilities_overview_dashboard for quick access

---

## Rollback Procedure

If you need to revert the integration:

```bash
# On deployment server or search head
cd /opt/splunk/etc/apps/MDGi/local/data/ui/

# Restore navigation backup
sudo cp nav/default.xml.backup nav/default.xml

# Remove dashboard files
sudo rm -f views/utilities_overview_dashboard.xml
sudo rm -f views/heating_dashboard.xml
sudo rm -f views/hotwater_dashboard.xml
sudo rm -f views/coldwater_dashboard.xml

# Reload
sudo /opt/splunk/bin/splunk restart splunkweb
```

---

## Additional Configuration

### Enable Dashboard Sharing

To make dashboards accessible to all MDGi app users:

1. Go to each dashboard in Splunk Web
2. Click **Edit** → **Edit Permissions**
3. Select **Shared in App**
4. Set appropriate read/write permissions for roles
5. Click **Save**

### Create Scheduled Reports

Convert dashboard queries to scheduled reports for email delivery:

1. Open any dashboard panel search
2. Click **Save As** → **Report**
3. Set schedule (e.g., daily at 6 AM)
4. Configure email delivery
5. Save

### Add to Home Dashboard

Create shortcuts on MDGi home screen:

```xml
<!-- In overall_status.xml or home dashboard -->
<row>
  <panel>
    <html>
      <h2>Quick Links</h2>
      <ul>
        <li><a href="/app/MDGi/utilities_overview_dashboard">🏠 Utilities Overview</a></li>
        <li><a href="/app/MDGi/heating_dashboard">🔥 Heating System</a></li>
        <li><a href="/app/MDGi/hotwater_dashboard">💧 Hot Water</a></li>
        <li><a href="/app/MDGi/coldwater_dashboard">🚰 Cold Water</a></li>
      </ul>
    </html>
  </panel>
</row>
```

---

## Performance Considerations

- **Auto-refresh:** Default is 1 minute; increase to 5 minutes if experiencing performance issues
- **Time range:** Shorter ranges (6-12 hours) load faster than 24 hours
- **Concurrent users:** Monitor Splunk search load if many users access utilities dashboards
- **Summary indexing:** For historical data (>30 days), consider summary indexing

---

## Support

For issues with:
- **Dashboard functionality:** Check SPLUNK_*_DASHBOARD.md documentation files
- **Data ingestion:** See DEPLOYMENT_GUIDE.md and HAPROXY_SETUP.md
- **MQTT connectivity:** See mqtt_topic_utilities.md
- **Splunk app integration:** This document (MDGI_APP_INTEGRATION.md)

---

## Version History

- **v1.0** (2026-01-26) - Initial MDGi integration
  - 4 dashboards integrated
  - Drill-down navigation implemented
  - Utilities collection in nav menu

---

**✅ Integration Complete! Your utilities monitoring is now part of the MDGi app!**

