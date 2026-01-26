# Utilities MQTT-to-Splunk Integration - Changelog

## Version 1.0.1 - Service Dependencies (2026-01-26)

### Service Improvements

#### Systemd Service Dependencies
- ✅ Added HAProxy as required dependency in systemd service file
- ✅ Service now ensures HAProxy is running before starting
- ✅ Automatic shutdown if HAProxy stops (prevents failed ingestion attempts)
- ✅ Proper startup ordering: network → HAProxy → mqtt-to-splunk

**Changes:**
```ini
[Unit]
After=network-online.target haproxy.service
Requires=haproxy.service
```

**Benefits:**
- Prevents service from starting without HAProxy
- Eliminates connection errors during startup
- Clean dependency chain visible in `systemctl list-dependencies`
- Automatic lifecycle management (both services start/stop together)

### Documentation Updates
- Updated DEPLOYMENT_GUIDE.md with service dependency notes
- Updated README.md with dependency testing commands
- Updated HAPROXY_SETUP.md with service integration details

---

## Version 1.0.0 - Production Release (2026-01-26)

### Initial Deployment

**Environment:**
- Platform: Dedicated Debian 12 (Bookworm) VM
- Python: 3.13.5
- Splunk: 8.2.4 (2-node indexer cluster)
- MQTT Broker: Mosquitto on 172.16.234.55:1883

### Features Implemented

#### Core Functionality
- ✅ MQTT subscriber connects to utilities/* topics
- ✅ Automatic payload handling (JSON objects, raw values, plain text)
- ✅ Manufacturer-specific sourcetype mapping:
  - utilities/heating → kamstrup:heating
  - utilities/hotwater → kamstrup:hotwater
  - utilities/coldwater → elster:coldwater
  - utilities/energy → emonpi:energy
- ✅ Field name extraction from MQTT topic structure
- ✅ Metadata enrichment (mqtt_topic, received_at)

#### High Availability
- ✅ HAProxy load balancer (localhost:8088)
- ✅ Dual indexer support (172.16.234.48, 172.16.234.49)
- ✅ Automatic health checks every 5 seconds
- ✅ Automatic failover on indexer failure
- ✅ Round-robin load distribution
- ✅ Stats dashboard on port 9000

#### Python Compatibility
- ✅ Python 3.13.5 support (Debian 12 default)
- ✅ paho-mqtt CallbackAPIVersion.VERSION2
- ✅ Modern datetime with timezone.utc
- ✅ SSL warning suppression for self-signed certs
- ✅ Python 3.6+ version checking at startup

### Issues Resolved During Deployment

#### 1. Non-JSON Payload Handling
**Problem:** Gateways publish raw values (integers, floats, strings) not JSON objects  
**Solution:** Auto-wrap values with field name from last part of MQTT topic
- Example: Topic `utilities/coldwater/reading/pulse_count` payload `123` → `{"pulse_count": 123}`

#### 2. MQTT Client API Deprecation
**Problem:** paho-mqtt deprecated CallbackAPIVersion.VERSION1  
**Solution:** Updated to VERSION2 with corrected callback signatures:
- `on_connect(client, userdata, flags, reason_code, properties)`
- `on_subscribe(client, userdata, mid, reason_codes, properties)`

#### 3. datetime.UTC Compatibility
**Problem:** `datetime.UTC` not available in Python 3.10 and earlier  
**Solution:** Use `timezone.utc` instead for broader compatibility

#### 4. SSL Warning Spam
**Problem:** urllib3 InsecureRequestWarning flooding logs  
**Solution:** Added `urllib3.disable_warnings()` when SPLUNK_VERIFY_SSL = False

#### 5. Python Environment on Debian 12
**Problem:** pip requires --break-system-packages flag  
**Solution:** Documented proper installation method for Debian 12 externally-managed environment

### Architecture Decisions

#### Why Separate VM vs Heavy Forwarder
- Splunk Heavy Forwarder runs Splunk 8.2.4 with Python 2.7 internally
- Python 3 installation on HF had lsb_release issues (Debian Stretch EOL)
- Dedicated Debian 12 VM provides:
  - Modern Python 3.13.5 with working pip
  - No risk to production Splunk installation
  - Clean separation of concerns
  - Easy to rebuild/replace

#### Why HAProxy vs Single Indexer
- Eliminates single point of failure at ingestion layer
- Transparent to application (script connects to localhost)
- Built-in health monitoring and failover
- No external dependencies (runs on same VM)

### Performance

**Production Metrics (First 24 Hours):**
- Events Indexed: 939+
- Data Loss: 0
- Average Latency: <100ms end-to-end
- Indexer Failover: Tested successfully
- CPU Usage: <5% (1 vCPU VM)
- Memory Usage: <200MB (512MB VM)

### File Structure

```
utilities/
├── mqtt_to_splunk.py (334 lines)      - Main script
├── splunk_credentials.py.template     - Configuration template
├── mqtt-to-splunk.service             - Systemd service file
├── requirements.txt                   - Python dependencies
├── README.md                          - Quick reference
├── DEPLOYMENT_GUIDE.md                - Complete deployment walkthrough
├── HAPROXY_SETUP.md                   - HAProxy configuration guide
├── SPLUNK_SETUP.md                    - Splunk HEC and index setup
├── mqtt_topic_utilities.md            - MQTT broker integration
└── CHANGELOG.md (this file)           - Version history
```

### Dependencies

**Python Packages:**
- paho-mqtt >= 1.6.1 (MQTT client)
- requests >= 2.31.0 (HTTP client for HEC)
- urllib3 (included with requests)

**System Packages:**
- haproxy (load balancer)
- python3 (3.11+)
- python3-pip
- git
- socat (for HAProxy admin socket)

### Configuration

**MQTT Settings:**
- Broker: 172.16.234.55:1883
- User: splunk_forwarder
- Topics: utilities/heating/#, utilities/hotwater/#, utilities/coldwater/#, utilities/energy/#

**Splunk Settings:**
- HEC URL: https://127.0.0.1:8088/services/collector/event (via HAProxy)
- Index: utilities
- Default Sourcetype: mqtt:metrics (overridden by script)

**HAProxy:**
- Frontend: 127.0.0.1:8088
- Backend: 172.16.234.48:8088, 172.16.234.49:8088
- Stats: *:9000

### Known Limitations

1. **No TLS to MQTT Broker** - Connection is unencrypted (internal network only)
2. **Self-Signed Certs** - SSL verification disabled for Splunk HEC
3. **No Message Queuing** - If both indexers fail, data is lost (mitigated by cluster HA)
4. **Single Gateway Support** - Script runs on one VM (can run multiple instances if needed)

### Future Enhancements

**Planned:**
- [ ] Prometheus metrics export
- [ ] Grafana dashboard integration
- [ ] Alert rules for gateway offline detection
- [ ] TLS encryption to MQTT broker
- [ ] Proper SSL certificate for Splunk HEC
- [ ] Message queue buffering (Redis/RabbitMQ)

**Under Consideration:**
- [ ] Docker container deployment
- [ ] Kubernetes deployment
- [ ] Multi-region support
- [ ] Data transformation pipeline
- [ ] Custom field extractions

### Deployment Checklist

- [x] Debian 12 VM provisioned
- [x] Python 3.13 and dependencies installed
- [x] HAProxy configured and tested
- [x] MQTT credentials configured
- [x] Splunk HEC token generated
- [x] Script tested in foreground
- [x] Systemd service installed
- [x] Service set to start on boot
- [x] Data verified in Splunk
- [x] Sourcetypes validated
- [x] Failover tested
- [x] Documentation completed

### Support

For issues or questions:
- Check logs: `sudo journalctl -u mqtt-to-splunk -n 100`
- Review documentation in utilities/ folder
- Test components separately (MQTT, HAProxy, HEC)
- Check HAProxy stats: http://VM_IP:9000/stats

### Contributors

- Initial implementation and deployment: January 2026
- Platform: HomeMatrixBoard utilities monitoring system

### License

See LICENSE file in project root.

---

## Version History

### v1.0.0 (2026-01-26)
- Initial production release
- Core functionality complete
- All major issues resolved
- 939+ events indexed successfully
- HAProxy HA confirmed working

