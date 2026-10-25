# Transmission Stats for Home Assistant

A custom Home Assistant integration that exposes [Transmission](https://transmissionbt.com/) statistics as sensors and fires an event when a torrent finishes downloading.

## Features

- Sensors:
  - Download speed and upload speed
  - Active, paused and total torrents
  - Torrents currently downloading and seeding
- `transmission_stats_torrent_completed` event, fired when a torrent finishes downloading
- Configuration through the UI (no YAML needed)
- English and Russian translations

## Installation

### HACS (custom repository)

1. Open HACS, click the three-dot menu and choose **Custom repositories**.
2. Add the URL of this repository and select the **Integration** category.
3. Install **Transmission Stats** and restart Home Assistant.

### Manual

Copy the `custom_components/transmission_stats` folder into your Home Assistant `<config>/custom_components/` directory and restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & services → Add integration**.
2. Search for **Transmission Stats**.
3. Enter the host and port of your Transmission RPC interface (default port: `9091`) and, if authentication is enabled, the username and password.

The integration polls Transmission every 30 seconds.

## Sensors

| Sensor | Description |
| --- | --- |
| Download speed | Current download speed (shown in MB/s) |
| Upload speed | Current upload speed (shown in MB/s) |
| Active torrents | Torrents that are currently transferring data |
| Paused torrents | Torrents that are paused |
| Total torrents | All torrents in Transmission |
| Downloading | Torrents in the downloading state |
| Seeding | Torrents in the seeding state |

## Download completion notifications

When a torrent goes from incomplete to 100%, the integration fires the `transmission_stats_torrent_completed` event on the Home Assistant event bus.

Event data:

| Field | Description |
| --- | --- |
| `name` | Torrent name |
| `hash` | Torrent info hash |
| `size` | Total size in bytes |
| `download_dir` | Download directory |
| `id` | Transmission torrent ID |
| `entry_id` | Config entry ID of the integration |

### Example automation

```yaml
alias: Transmission - download complete
triggers:
  - trigger: event
    event_type: transmission_stats_torrent_completed
actions:
  - action: notify.mobile_app_your_phone
    data:
      title: "Download complete"
      message: "{{ trigger.event.data.name }}"
```

Replace `notify.mobile_app_your_phone` with any notify service you use. You can watch the event live under **Developer tools → Events** by listening to `transmission_stats_torrent_completed`.

## Limitations

- The polling interval is 30 seconds. A torrent that is added and completed between two polls will not trigger the event.
- After a Home Assistant restart, the first poll only records the current state, so no false events are fired.

## Troubleshooting

- **Cannot connect:** check that the Transmission RPC interface is enabled and reachable from the Home Assistant host, and that the host and port are correct.
- **Invalid authentication:** verify the RPC username and password in your Transmission settings.
- **Sensors have generic names:** make sure the `translations` folder is present in `custom_components/transmission_stats/`, then restart Home Assistant.

For other problems, check the Home Assistant logs and open an issue in this repository.

## License

This project is licensed under the [MIT License](LICENSE).
