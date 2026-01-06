# Security Guide

This document outlines security considerations and best practices for the HomeMatrixBoard system.

## MQTT Security

### Authentication
- **No anonymous access**: Anonymous connections are disabled on the MQTT broker
- **Unique credentials**: Each client has unique username/password credentials
- **Password storage**: Passwords stored in encrypted format using Mosquitto's password hashing
- **Password file**: Located at `/etc/mosquitto/passwd` with restricted permissions (600)

### Authorization
- **ACL controls**: Access control lists (ACL) control topic access
- **Publisher restrictions**: Publishers limited to specific topics
- **Subscriber restrictions**: Subscribers can only read assigned topics
- **Topic isolation**: Each display can only access its own topic

### Network Security
- **Internal network**: MQTT broker only accessible within internal network
- **Port restrictions**: Port 1883 restricted to known IPs (via firewall if configured)
- **No external exposure**: MQTT broker not exposed to internet

## Webserver Security

### Access Control
- **Nginx reverse proxy**: Nginx acts as reverse proxy protecting Flask application
- **Limited user permissions**: Service runs as non-root user
- **Port binding**: Flask binds to localhost, Nginx handles external connections

### Input Validation
- **Parameter validation**: Validates all webhook parameters
- **Data sanitization**: Sanitizes input data before processing
- **Error handling**: Graceful error handling for invalid requests
- **JSON validation**: Validates JSON structure for POST requests

### Network Security
- **Internal network**: Webserver accessible within internal network
- **Optional external access**: Can be configured for external access if needed
- **Firewall**: Consider firewall rules to restrict access

## Display Security

### Credential Management
- **Separate credentials**: Each display has unique MQTT credentials
- **Secure storage**: Credentials stored in `secrets.py` (not in git)
- **Read-only filesystem**: CIRCUITPY drive is read-only, reducing risk of credential exposure

### Network Security
- **WiFi encryption**: Uses WPA2/WPA3 encrypted WiFi network
- **MQTT authentication**: All MQTT connections require authentication
- **Topic isolation**: Each display can only subscribe to its own topic

## Spotify Integration Security

### OAuth Security
- **OAuth 2.0**: Uses standard OAuth 2.0 flow
- **Token storage**: OAuth tokens stored in `.spotify_cache` file (not in git)
- **Token refresh**: Tokens automatically refreshed by spotipy library
- **Redirect URI validation**: Redirect URI must match exactly in Spotify dashboard

### Credential Management
- **Separate file**: Spotify credentials in `spotify_credentials.py` (not in git)
- **No hardcoding**: Credentials never hardcoded in source code
- **Environment variables**: Consider using environment variables for production

## General Security Recommendations

### 1. Password Management
- Use strong, unique passwords for all users
- Rotate passwords regularly
- Never commit passwords to version control
- Use password managers for credential storage

### 2. Network Security
- Keep all systems on internal network when possible
- Use firewall rules to restrict access
- Consider VPN for remote access
- Monitor network traffic for anomalies

### 3. System Updates
- Keep all packages updated: `sudo apt update && sudo apt upgrade`
- Monitor security advisories
- Apply security patches promptly
- Keep CircuitPython and libraries updated on displays

### 4. Monitoring and Logging
- Regularly monitor system logs
- Check MQTT broker logs for suspicious activity
- Monitor webserver logs for errors
- Review display serial console for connection issues

### 5. TLS/SSL (Future Enhancement)
- Consider enabling TLS/SSL for MQTT connections
- Use HTTPS for webserver if external access is needed
- Obtain SSL certificates from trusted CA
- Configure certificate validation

### 6. Access Control
- Limit SSH access to webserver and broker
- Use SSH keys instead of passwords
- Disable root login
- Implement fail2ban for brute force protection

### 7. Backup and Recovery
- Regularly backup configuration files
- Backup secrets.py files (securely)
- Document recovery procedures
- Test backup restoration

## Security Checklist

- [ ] All MQTT users have strong passwords
- [ ] Anonymous MQTT access is disabled
- [ ] ACL permissions are correctly configured
- [ ] No credentials in version control
- [ ] Nginx reverse proxy is configured
- [ ] Service runs as non-root user
- [ ] Firewall rules are in place
- [ ] System packages are up to date
- [ ] Logs are being monitored
- [ ] Backup procedures are in place

## Incident Response

If a security issue is detected:

1. **Immediate Actions**
   - Disconnect affected systems from network if necessary
   - Change compromised credentials
   - Review logs for unauthorized access

2. **Investigation**
   - Identify the scope of the issue
   - Review access logs
   - Check for unauthorized changes

3. **Remediation**
   - Apply security patches
   - Update credentials
   - Strengthen security measures

4. **Documentation**
   - Document the incident
   - Update security procedures
   - Review and improve security measures

## Related Documentation

- [MQTT Broker Setup](mqtt_broker_setup.md) - MQTT security configuration
- [Webserver Setup](webserver_setup.md) - Webserver security configuration
- [Display Setup](display_setup.md) - Display credential management
