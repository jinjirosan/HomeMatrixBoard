# MQTT broker setup — Spotify topics

This guide extends your Mosquitto broker so the Spotify bridge can **publish** to `home/spotify/#` and lyrics clients (Mac Mini, Raspberry Pi, etc.) can **subscribe**.

It assumes you already followed the main [MQTT broker setup](../mqtt_broker_setup.md) (listeners, `passwd`, `acl`, `allow_anonymous false`).

## Topic layout

```
home/spotify/
  now_playing      # retained JSON — current track + progress snapshot
  lyrics/
    track          # retained JSON — full timed lyric lines for current track
    current        # non-retained JSON — current line / neighbors (updated ~1 Hz)
```

## Option A — reuse the webhook publisher (simplest)

If the same host that runs the bridge already uses `sigfoxwebhookhost` for `home/displays/#`, extend that user so it can also publish Spotify data.

Edit `/etc/mosquitto/acl` and add the second line under `sigfoxwebhookhost`:

```conf
user sigfoxwebhookhost
topic write home/displays/#
topic write home/spotify/#
```

No new password entry is required. Restart Mosquitto (see below).

Use this MQTT user only on trusted machines (the bridge runs with these credentials).

## Option B — dedicated bridge and viewer users

Use separate credentials so viewers never get write access.

### 1. Create passwords

```bash
sudo mosquitto_passwd /etc/mosquitto/passwd spotify_bridge
sudo mosquitto_passwd /etc/mosquitto/passwd spotify_viewer
```

Do **not** use `-c` on the second command (it would wipe the file).

### 2. Extend the ACL

Add to `/etc/mosquitto/acl` (keep your existing `sigfoxwebhookhost` and display users):

```conf
user spotify_bridge
topic write home/spotify/#

user spotify_viewer
topic read home/spotify/#
```

### 3. Apply configuration

```bash
sudo systemctl restart mosquitto
sudo systemctl status mosquitto
```

## Verify from any machine with mosquitto clients

Replace host, user, and password with your values.

**Subscribe (viewer-style):**

```bash
mosquitto_sub -h 172.16.234.55 -u spotify_viewer -P '<password>' -v -t 'home/spotify/#'
```

If you only added Option A and have no `spotify_viewer` user yet, use an account that has **read** on `home/spotify/#` (you can temporarily grant your own admin test user read access for debugging).

**Expected behavior:** With the bridge running, you should see messages on `home/spotify/now_playing`, `home/spotify/lyrics/track` (on track changes), and `home/spotify/lyrics/current` roughly once per second while playing.

## Utilities topics

If you use `utilities/#` gateways, those ACLs are unrelated. The Spotify bridge only needs `home/spotify/#` as above. See [MQTT utilities guide](../../utilities/mqtt_topic_utilities.md) for heating/water topics.

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Connection refused | Broker firewall, `listener` in `mosquitto.conf`, correct IP/port |
| Not authorized | ACL typo, wrong username, forgot `systemctl restart mosquitto` |
| No messages | Bridge not running, Spotify not playing, invalid/expired `.spotify_cache` |
| Sub sees nothing retained | Connect after bridge has published at least once; check `now_playing` / `lyrics/track` with `mosquitto_sub` |

## Security notes

- Prefer **TLS** on the broker in the long term if exposing MQTT beyond your LAN.
- Treat MQTT passwords like any other secret; rotate if leaked.
- `spotify_viewer` should have **read-only** topics as in Option B.
