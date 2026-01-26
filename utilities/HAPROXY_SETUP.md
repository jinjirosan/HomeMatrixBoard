# HAProxy Load Balancer Setup for Splunk HEC

This document describes the HAProxy configuration for load balancing and failover between Splunk indexers.

## Overview

HAProxy provides high availability and load balancing for the MQTT-to-Splunk forwarder by distributing HEC (HTTP Event Collector) traffic across both indexers in the cluster with automatic failover.

## Architecture

```
MQTT Gateways (Kamstrup, Elster, EmonPi)
    ↓
MQTT Broker (172.16.234.55:1883)
    ↓
mqtt_to_splunk.py
    ↓
HAProxy (127.0.0.1:8088) ← Local load balancer
    ├─→ Indexer1 (172.16.234.48:8088) [PRIMARY]
    └─→ Indexer2 (172.16.234.49:8088) [SECONDARY]
         ↓
    Indexer Cluster
         ↓
    utilities index (with replication)
```

## Benefits

✅ **High Availability** - Automatic failover if one indexer goes down  
✅ **Load Balancing** - Distributes requests across both indexers  
✅ **Health Monitoring** - Checks indexer health every 5 seconds  
✅ **No SPOF** - Eliminates single point of failure at ingestion layer  
✅ **Transparent** - Script just connects to localhost:8088  
✅ **Stats Dashboard** - Built-in monitoring at http://VM_IP:9000/stats

## Installation

### Prerequisites

- Debian 12 (Bookworm) VM
- Network connectivity to both Splunk indexers on port 8088
- Root or sudo access

### Install HAProxy

```bash
apt update
apt install -y haproxy
```

### Backup Original Configuration

```bash
cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.orig
```

## Configuration

### Complete HAProxy Configuration

Edit `/etc/haproxy/haproxy.cfg`:

```bash
nano /etc/haproxy/haproxy.cfg
```

**Configuration file:**

```
global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

defaults
    log     global
    mode    tcp
    option  tcplog
    option  dontlognull
    timeout connect 5000
    timeout client  50000
    timeout server  50000

# HEC Frontend (listen on localhost only)
frontend splunk_hec_frontend
    bind 127.0.0.1:8088
    mode tcp
    default_backend splunk_hec_backend

# HEC Backend (both indexers with health checks)
backend splunk_hec_backend
    mode tcp
    balance roundrobin
    option tcp-check
    
    # Primary indexer
    server indexer1 172.16.234.48:8088 check inter 5s rise 2 fall 3
    
    # Secondary indexer (automatic failover)
    server indexer2 172.16.234.49:8088 check inter 5s rise 2 fall 3

# Stats page for monitoring
listen stats
    bind *:9000
    mode http
    stats enable
    stats uri /stats
    stats refresh 10s
    stats admin if TRUE
```

### Configuration Explained

#### Global Section
- **chroot** - Security hardening
- **stats socket** - Admin socket for runtime commands
- **daemon** - Run in background

#### Frontend Section
- **bind 127.0.0.1:8088** - Only listen on localhost (security)
- **mode tcp** - TCP passthrough (for HTTPS)
- **default_backend** - Route to indexer backend

#### Backend Section
- **balance roundrobin** - Distribute requests evenly
- **option tcp-check** - TCP-level health checks
- **check inter 5s** - Check every 5 seconds
- **rise 2** - Mark UP after 2 successful checks
- **fall 3** - Mark DOWN after 3 failed checks

#### Stats Section
- **bind *:9000** - Listen on all interfaces port 9000
- **stats uri /stats** - Access at http://VM_IP:9000/stats
- **stats refresh 10s** - Auto-refresh every 10 seconds

## Deployment

### 1. Validate Configuration

```bash
haproxy -c -f /etc/haproxy/haproxy.cfg
```

Expected output:
```
Configuration file is valid
```

**Note:** Warnings about `httplog` vs `tcplog` are harmless.

### 2. Start HAProxy

```bash
systemctl restart haproxy
systemctl enable haproxy
systemctl status haproxy
```

Should show `active (running)` in green.

### 3. Verify HAProxy is Listening

```bash
# Check port 8088
netstat -tlnp | grep 8088

# Should show:
# tcp  0  0 127.0.0.1:8088  0.0.0.0:*  LISTEN  <pid>/haproxy
```

## Testing

### Test HEC Through HAProxy

```bash
# Test event submission
curl -k https://127.0.0.1:8088/services/collector/event \
  -H "Authorization: Splunk YOUR-HEC-TOKEN" \
  -d '{"event": "HAProxy test", "sourcetype": "mqtt:metrics", "index": "utilities"}'
```

Expected response:
```json
{"text":"Success","code":0}
```

### Check Backend Status

```bash
# Via admin socket
echo "show stat" | socat stdio /run/haproxy/admin.sock | grep indexer

# Or check stats page
curl http://localhost:9000/stats
```

### View Stats Dashboard

Open in browser:
```
http://YOUR_VM_IP:9000/stats
```

You should see:
- **Frontend stats** - Connections, sessions
- **Backend stats** - Both indexers with status (UP/DOWN)
- **Server stats** - Per-indexer metrics

## Monitoring

### Real-time Monitoring

```bash
# Watch HAProxy logs
tail -f /var/log/haproxy.log

# Or via journalctl
journalctl -u haproxy -f
```

### Check Indexer Health

```bash
# Show backend status
echo "show servers state" | socat stdio /run/haproxy/admin.sock
```

### Stats Metrics

Access stats page: `http://VM_IP:9000/stats`

**Key metrics to monitor:**
- **Status** - UP (green) or DOWN (red)
- **Session Rate** - Requests per second
- **Queue** - Queued requests (should be 0)
- **Downtime** - Time since last failure

## Failover Testing

### Test Automatic Failover

```bash
# 1. Check both indexers are UP
curl http://localhost:9000/stats | grep indexer

# 2. Stop one indexer (on indexer1)
/opt/splunk/bin/splunk stop

# 3. Check HAProxy redirects to indexer2
curl -k https://127.0.0.1:8088/services/collector/event \
  -H "Authorization: Splunk YOUR-TOKEN" \
  -d '{"event": "failover test"}'

# Should still return: {"text":"Success","code":0}

# 4. Check stats - indexer1 should be DOWN
curl http://localhost:9000/stats | grep indexer1
# Should show: DOWN

# 5. Restart indexer1
/opt/splunk/bin/splunk start

# 6. Wait 10-15 seconds for health checks
# indexer1 should return to UP status
```

## Troubleshooting

### HAProxy Won't Start

```bash
# Check configuration syntax
haproxy -c -f /etc/haproxy/haproxy.cfg

# Check logs
journalctl -u haproxy -n 50

# Common issues:
# - Port 8088 already in use
# - Invalid backend IPs
# - Syntax errors in config
```

### Both Indexers Show DOWN

```bash
# Check network connectivity
telnet 172.16.234.48 8088
telnet 172.16.234.49 8088

# Check indexers are running
# On each indexer:
/opt/splunk/bin/splunk status

# Check HEC is enabled on indexers
curl -k https://172.16.234.48:8088/services/collector/event
```

### Events Not Reaching Splunk

```bash
# 1. Check HAProxy is receiving requests
tail -f /var/log/haproxy.log

# 2. Check script is sending to HAProxy
journalctl -u mqtt-to-splunk -f

# 3. Check Splunk HEC logs
# On indexer:
/opt/splunk/bin/splunk search "index=_internal sourcetype=splunkd component=HttpEventCollector"
```

### Stats Page Not Accessible

```bash
# Check port 9000 is listening
netstat -tlnp | grep 9000

# Check firewall
ufw status

# Allow port 9000 if needed
ufw allow 9000/tcp
```

## Security Considerations

### Current Setup
- ✅ HAProxy only listens on localhost (127.0.0.1) for HEC
- ✅ Stats page accessible from any IP (port 9000)
- ✅ No SSL between HAProxy and indexers (internal network)

### Recommended Enhancements

1. **Restrict stats page access:**
```
listen stats
    bind 127.0.0.1:9000  # Only localhost
    # Or use ACLs:
    acl allowed_ips src 172.16.234.0/24
    http-request deny unless allowed_ips
```

2. **Add authentication to stats:**
```
listen stats
    stats auth admin:YOUR_SECURE_PASSWORD
```

3. **Enable SSL to indexers (if needed):**
```
backend splunk_hec_backend
    server indexer1 172.16.234.48:8088 check ssl verify none
    server indexer2 172.16.234.49:8088 check ssl verify none
```

## Performance Tuning

### For Higher Loads

If processing >1000 events/second:

```
global
    maxconn 4000
    nbproc 2  # Use 2 CPU cores

defaults
    timeout connect 3000
    timeout client  30000
    timeout server  30000

backend splunk_hec_backend
    balance leastconn  # Use least-connected instead of round-robin
```

### Monitoring Performance

```bash
# Show current sessions
echo "show sess" | socat stdio /run/haproxy/admin.sock

# Show current stats
echo "show stat" | socat stdio /run/haproxy/admin.sock | column -t -s,
```

## Maintenance

### Adding an Indexer

Edit `/etc/haproxy/haproxy.cfg`:

```
backend splunk_hec_backend
    server indexer1 172.16.234.48:8088 check inter 5s rise 2 fall 3
    server indexer2 172.16.234.49:8088 check inter 5s rise 2 fall 3
    server indexer3 172.16.234.50:8088 check inter 5s rise 2 fall 3  # NEW
```

Reload configuration:
```bash
systemctl reload haproxy
```

### Removing an Indexer

1. Mark indexer as maintenance in stats page
2. Remove from configuration
3. Reload HAProxy

### Updating HAProxy

```bash
# Update package
apt update
apt upgrade haproxy

# Restart (minimal downtime)
systemctl restart haproxy
```

## Integration with MQTT Script

The `mqtt_to_splunk.py` script connects to HAProxy transparently:

```python
# In splunk_credentials.py
SPLUNK_HEC_URL = "https://127.0.0.1:8088/services/collector/event"
```

No changes needed in the script - HAProxy handles all load balancing and failover automatically!

### Service Dependencies

The `mqtt-to-splunk.service` systemd unit includes HAProxy as a required dependency:

```ini
[Unit]
Description=MQTT to Splunk Forwarder for Utilities Monitoring
After=network-online.target haproxy.service
Requires=haproxy.service
```

**What this means:**
- mqtt-to-splunk service will **only start after** HAProxy is running
- If HAProxy stops or fails, mqtt-to-splunk will **automatically stop**
- When HAProxy restarts, mqtt-to-splunk can **automatically restart**
- Prevents connection errors and failed HEC submissions

**Testing the dependency:**

```bash
# Test 1: Stop HAProxy - mqtt-to-splunk should also stop
sudo systemctl stop haproxy
sudo systemctl status mqtt-to-splunk
# Expected: inactive (dead)

# Test 2: Start HAProxy - mqtt-to-splunk should start
sudo systemctl start haproxy
sleep 2
sudo systemctl status mqtt-to-splunk
# Expected: active (running)

# Test 3: View dependency chain
systemctl list-dependencies mqtt-to-splunk
# Should show haproxy.service in the tree

# Test 4: Check what depends on HAProxy
systemctl list-dependencies haproxy --reverse
# Should show mqtt-to-splunk.service
```

This ensures a robust startup sequence and prevents orphaned services!

## Logs

### HAProxy Logs Location

```bash
# System logs
/var/log/haproxy.log

# Or via journalctl
journalctl -u haproxy -f
```

### Log Format

```
<timestamp> <frontend> <backend>/<server> <metrics> <status>
```

Example:
```
Jan 26 10:00:00 localhost haproxy[1234]: 127.0.0.1:54321 [26/Jan/2026:10:00:00.000] splunk_hec_frontend splunk_hec_backend/indexer1 0/0/1 212 -- 1/1/0/0/0 0/0
```

## Related Documentation

- [README.md](README.md) - Utilities system overview
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete deployment walkthrough
- [SPLUNK_SETUP.md](SPLUNK_SETUP.md) - Splunk HEC configuration
- [mqtt_topic_utilities.md](mqtt_topic_utilities.md) - MQTT broker integration

## References

- [HAProxy Documentation](https://www.haproxy.org/documentation.html)
- [HAProxy TCP Mode](https://www.haproxy.com/blog/haproxy-ssl-termination/)
- [Splunk HEC Documentation](https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector)

