# Quick Deployment Guide - mdgi Integration

**Note:** App name is `mdgi` (lowercase) - case-sensitive in URLs!

## 🚀 5-Minute Integration Checklist

### Step 1: Copy Dashboard Files (2 minutes)

```bash
# On your Splunk search head or deployment server
cd /opt/splunk/etc/apps/mdgi/local/data/ui/views/

# Copy all 4 dashboards
sudo cp ~/github/HomeMatrixBoard/utilities/utilities_overview_dashboard.xml .
sudo cp ~/github/HomeMatrixBoard/utilities/utilities_heating_dashboard.xml .
sudo cp ~/github/HomeMatrixBoard/utilities/utilities_hotwater_dashboard.xml .
sudo cp ~/github/HomeMatrixBoard/utilities/utilities_coldwater_dashboard.xml .

# Fix permissions
sudo chown -R splunk:splunk /opt/splunk/etc/apps/mdgi/
```

---

### Step 2: Update Navigation (2 minutes)

```bash
# Backup current navigation
cd /opt/splunk/etc/apps/mdgi/local/data/ui/nav/
sudo cp default.xml default.xml.backup

# Edit navigation
sudo nano default.xml
```

**Add this section** (after line 11, before "Splunk Health"):

```xml
  <!-- Utilities Monitoring -->
  <collection label="Utilities">
    <view name="utilities_overview_dashboard" />
    <view name="utilities_heating_dashboard" />
    <view name="utilities_hotwater_dashboard" />
    <view name="utilities_coldwater_dashboard" />
  </collection>
```

Save and exit (Ctrl+X, Y, Enter)

---

### Step 3: Reload Splunk (1 minute)

```bash
# Reload web interface
sudo /opt/splunk/bin/splunk restart splunkweb

# OR if using deployment server
sudo /opt/splunk/bin/splunk reload deploy-server
```

---

### Step 4: Test (30 seconds)

1. Open: `http://your-splunk:8000/app/mdgi/`
2. Look for **"Utilities"** in navigation bar
3. Click **"utilities_overview_dashboard"**
4. Click on **"🔥 Heating System"** panel → should open heating dashboard
5. ✅ Done!

---

## Quick URLs

After deployment, access dashboards at:

```
http://your-splunk:8000/app/mdgi/utilities_overview_dashboard
http://your-splunk:8000/app/mdgi/utilities_heating_dashboard
http://your-splunk:8000/app/mdgi/utilities_hotwater_dashboard
http://your-splunk:8000/app/mdgi/utilities_coldwater_dashboard
```

---

## Troubleshooting

### Dashboards not showing?

```bash
# Check files exist
ls -la /opt/splunk/etc/apps/mdgi/local/data/ui/views/utilities_*.xml

# Fix permissions if needed
sudo chown -R splunk:splunk /opt/splunk/etc/apps/mdgi/
sudo chmod 644 /opt/splunk/etc/apps/mdgi/local/data/ui/views/*.xml
```

### Navigation not updating?

```bash
# Clear browser cache, then:
sudo /opt/splunk/bin/splunk restart splunkweb
```

### Drill-downs not working?

Check that app name in URLs matches your app name (should be "MDGi")

---

## Rollback

If something goes wrong:

```bash
# Restore navigation
cd /opt/splunk/etc/apps/mdgi/local/data/ui/nav/
sudo cp default.xml.backup default.xml

# Remove dashboards
cd /opt/splunk/etc/apps/mdgi/local/data/ui/views/
sudo rm -f utilities_overview_dashboard.xml
sudo rm -f utilities_heating_dashboard.xml  
sudo rm -f utilities_hotwater_dashboard.xml
sudo rm -f utilities_coldwater_dashboard.xml

# Reload
sudo /opt/splunk/bin/splunk restart splunkweb
```

---

## Full Documentation

For detailed instructions, see:
- **[MDGI_APP_INTEGRATION.md](MDGI_APP_INTEGRATION.md)** - Complete integration guide
- **[OVERVIEW_DASHBOARD_INSTALLATION.md](OVERVIEW_DASHBOARD_INSTALLATION.md)** - Dashboard details

---

**✅ That's it! Your utilities monitoring is now integrated into MDGi!**

