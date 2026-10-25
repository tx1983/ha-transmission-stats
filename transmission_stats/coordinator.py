from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from transmission_rpc import Client
from transmission_rpc.error import TransmissionAuthError, TransmissionError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, EVENT_TORRENT_COMPLETED

_LOGGER = logging.getLogger(__name__)

TORRENT_FIELDS = ["id", "name", "status", "percent_done", "hash_string", "total_size", "download_dir"]


@dataclass
class TransmissionData:
    download_speed: int  # байт/с
    upload_speed: int  # байт/с
    active_torrents: int
    paused_torrents: int
    total_torrents: int
    downloading: int
    seeding: int


def create_client(data: dict) -> Client:
    """Блокирующий вызов — запускать только в executor."""
    return Client(
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        username=data.get(CONF_USERNAME) or None,
        password=data.get(CONF_PASSWORD) or None,
    )


class TransmissionCoordinator(DataUpdateCoordinator[TransmissionData]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self._client: Client | None = None
        # id торрента -> прогресс (0..1) на прошлом опросе; None до первого опроса
        self._known: dict[int, float] | None = None

    def _fetch(self) -> tuple[TransmissionData, dict[int, dict[str, Any]]]:
        if self._client is None:
            self._client = create_client(self.config_entry.data)
        stats = self._client.session_stats()
        torrents = self._client.get_torrents(arguments=TORRENT_FIELDS)
        snapshot = {
            t.id: {
                "id": t.id,
                "name": t.name,
                "hash": t.hash_string,
                "size": t.total_size,
                "download_dir": t.download_dir,
                "progress": float(t.percent_done),
            }
            for t in torrents
        }
        data = TransmissionData(
            download_speed=stats.download_speed,
            upload_speed=stats.upload_speed,
            active_torrents=stats.active_torrent_count,
            paused_torrents=stats.paused_torrent_count,
            total_torrents=stats.torrent_count,
            downloading=sum(1 for t in torrents if t.status == "downloading"),
            seeding=sum(1 for t in torrents if t.status == "seeding"),
        )
        return data, snapshot

    async def _async_update_data(self) -> TransmissionData:
        try:
            data, snapshot = await self.hass.async_add_executor_job(self._fetch)
        except TransmissionAuthError as err:
            self._client = None
            raise ConfigEntryAuthFailed from err
        except TransmissionError as err:
            self._client = None
            raise UpdateFailed(f"Ошибка Transmission: {err}") from err

        # Первый опрос только запоминает состояние, чтобы не было ложных событий
        if self._known is not None:
            for torrent_id, info in snapshot.items():
                prev = self._known.get(torrent_id)
                if prev is not None and prev < 1 <= info["progress"]:
                    self.hass.bus.async_fire(
                        EVENT_TORRENT_COMPLETED,
                        {
                            "entry_id": self.config_entry.entry_id,
                            "id": info["id"],
                            "name": info["name"],
                            "hash": info["hash"],
                            "size": info["size"],
                            "download_dir": info["download_dir"],
                        },
                    )
        self._known = {tid: info["progress"] for tid, info in snapshot.items()}
        return data
