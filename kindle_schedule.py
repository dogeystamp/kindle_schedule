# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "mergecal==0.5.0",
#     "recurring-ical-events==3.*",
#     "typst==0.13.2",
# ]
# ///


import dataclasses
import functools
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Self, cast

import icalendar
import recurring_ical_events
import tomllib
from icalendar import Calendar
from mergecal import merge_calendars


@dataclass
class Configuration:
    """See config.toml.example for information."""

    ics_directory: Path
    start_time: time
    end_time: time
    schedule_days: int
    max_days: int


def get_config(location: Path | None=None) -> Configuration:
    """Read and parse configuration for this script."""

    if location is None:
        config_dir_str = os.environ.get("KINDLE_SCHEDULE_DIR", None)
        config_dir = (
            Path(config_dir_str)
            if config_dir_str
            else Path.home() / ".config/kindle_schedule"
        )

        config_file = config_dir / "config.toml"
    else:
        config_file = location

    try:
        config = tomllib.loads(config_file.read_text())
    except FileNotFoundError as e:
        raise FileNotFoundError(
            "Configuration file is missing. Create one by copying `config.toml.example` from the source repo."
        ) from e

    ics_directory_str = config.get("ics_directory", None)
    if ics_directory_str is None:
        raise ValueError("Missing `ics_directory` setting.")
    ics_directory = Path(ics_directory_str).expanduser()

    return Configuration(
        ics_directory=ics_directory,
        start_time=config.get("start_time", time(8, 0, 0)),
        end_time=config.get("end_time", time(22, 0, 0)),
        schedule_days=config.get("schedule_days", 5),
        max_days=config.get("max_days", 33),
    )


def read_calendars(ics_directory: Path) -> Calendar:
    """Read all .ics files in the directory and merge them into a single Calendar."""

    return merge_calendars(
        [Calendar.from_ical(f.read_text()) for f in ics_directory.glob("**/*.ics")]  # type: ignore
    )


@functools.total_ordering
@dataclass
class Event:
    """
    Helper type to wrap an event.

    This can be compared (<) to other events to determine which has higher priority.
    """

    inner: icalendar.Event
    hidden: bool = False
    n_overlaps: int = 0

    def __lt__(self, other: Self):
        status_map = dict(CANCELLED=0, TENTATIVE=1, CONFIRMED=2)
        self_priority = status_map.get(self.inner.get("STATUS"), -1)
        other_priority = status_map.get(other.inner.get("STATUS"), -1)

        return self_priority < other_priority


def get_day_events(calendar: Calendar, date: date):
    """Filter and parse the events at a date."""
    evs: list[icalendar.Event] = recurring_ical_events.of(calendar).at(date)  # type: ignore

    regular_evs: list[Event] = []
    all_day_evs: list[Event] = []

    for ev in evs:
        if ev.get("STATUS") == "CANCELLED":
            # discard event
            continue

        # all day events have just a date, not a datetime
        if isinstance(ev.DTSTART, datetime) and isinstance(ev.DTEND, datetime):
            regular_evs.append(Event(inner=ev))
        else:
            all_day_evs.append(Event(inner=ev))

    # do a sweep-line algorithm to clear up overlapping events.

    @functools.total_ordering
    @dataclass
    class SweepMarker:
        """Event start/end marker."""

        # sorts chronologically. fall back on decreasing order of priority.
        PRIORITY: int = dataclasses.field(init=False)

        marker_time: datetime

        idx: int
        """The index of the event in our array."""

        def __lt__(self, other: Self):
            if other.marker_time != self.marker_time:
                return self.marker_time < other.marker_time
            return self.PRIORITY

        def __eq__(self, other):
            return (
                isinstance(other, SweepMarker) and other.marker_time == self.marker_time
            )

    class SweepStart(SweepMarker):
        PRIORITY = 0

    class SweepEnd(SweepMarker):
        # process end before start so that events that touch don't overlap
        PRIORITY = 1

    sweep_events: list[SweepStart | SweepEnd] = []
    for idx, ev in enumerate(regular_evs):
        # TYPE CAST: we established above that regular_evs use datetime for both start and end
        sweep_events.append(SweepStart(cast(datetime, ev.inner.DTSTART), idx))
        sweep_events.append(SweepEnd(cast(datetime, ev.inner.DTEND), idx))
    sweep_events.sort()

    for i, sweep in enumerate(sweep_events):
        if regular_evs[sweep.idx].hidden:
            continue

        if isinstance(sweep, SweepEnd):
            continue

        # peek overlapping events.

        overlap_idxes: set[int] = set()
        for overlap_sweep in sweep_events[i + 1 :]:
            if isinstance(overlap_sweep, SweepEnd) and overlap_sweep.idx == sweep.idx:
                # this is the end of this current event
                break

            overlap_idxes.add(overlap_sweep.idx)

        # - if this event has higher priority than all overlaps, this event
        #   will be marked "x other events" and the rest will be hidden.
        # - otherwise, this event will be hidden.

        for overlap_idx in overlap_idxes:
            if regular_evs[sweep.idx] < regular_evs[overlap_idx]:
                break
        else:
            # this event has higher priority than all the overlapping events
            for overlap_idx in overlap_idxes:
                regular_evs[overlap_idx].hidden = True
            regular_evs[sweep.idx].n_overlaps = len(overlap_idxes)

    return ([ev for ev in regular_evs if not ev.hidden], all_day_evs)


def serialize_date(dt: date) -> dict:
    """Serialize a date. (Typst can't parse datetimes.)"""
    return dict(
        year=dt.year,
        month=dt.month,
        day=dt.day,
    )


def serialize_time(dt: time) -> dict:
    """Serialize a time. (Typst can't parse datetimes.)"""
    return dict(
        hour=dt.hour,
        minute=dt.minute,
        second=dt.second,
    )


def serialize_datetime(dt: datetime) -> dict:
    """Serialize a datetime. (Typst can't parse datetimes.)"""
    return dict(
        **serialize_date(dt),
        **serialize_time(dt.time()),
    )


def serialize_evs(regular_evs: list[Event], all_day_evs: list[Event]) -> dict:
    """Convert event lists to a daily format."""

    def serialize_regular_ev(ev: Event):
        assert isinstance(ev.inner.DTSTART, datetime) and isinstance(
            ev.inner.DTEND, datetime
        )

        return dict(
            name=ev.inner.get("SUMMARY", ""),
            start=serialize_datetime(ev.inner.DTSTART),
            end=serialize_datetime(ev.inner.DTEND),
            extra=dict(
                n_overlaps=ev.n_overlaps,
                description=ev.inner.get("DESCRIPTION"),
            ),
        )

    def serialize_all_day_ev(ev: Event):
        return dict(
            name=ev.inner.get("SUMMARY", ""),
        )

    return dict(
        regular=list(map(serialize_regular_ev, regular_evs)),
        all_day=list(map(serialize_all_day_ev, all_day_evs)),
    )


def generate_data(
    config: Configuration,
    start_date: date | None = None,
) -> dict:
    """Main function that combines all the data into a single dictionary for Typst to read."""

    start_date = start_date or date.today()

    calendar = read_calendars(config.ics_directory)

    events = []
    for i in range(config.max_days):
        events.append(
            serialize_evs(*get_day_events(calendar, start_date + timedelta(days=1) * i))
        )

    return dict(
        start_date=serialize_date(start_date),
        start_time=serialize_time(config.start_time),
        end_time=serialize_time(config.end_time),
        schedule_days=config.schedule_days,
        events=events,
    )


def generate_schedule(
    data: dict,
    **kwargs,
) -> bytes | list[bytes]:
    """Generate schedule from the data, and returns the bytes."""
    import typst

    template_file = Path(__file__).parent / "template.typ"
    return typst.compile(
        template_file, sys_inputs={"schedule": json.dumps(data)}, **kwargs
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a neat schedule from ICS calendar files."
    )
    parser.add_argument("output", help="File to output the schedule to.", type=Path)
    parser.add_argument(
        "--start-date",
        help="Date for the first page of the schedule. (Use ISO date format).",
        type=date.fromisoformat,
    )
    parser.add_argument(
        "--config",
        help="Custom configuration file location.",
        type=Path,
    )

    args = parser.parse_args()

    config = get_config(args.config)
    data = generate_data(config, start_date=args.start_date)

    generate_schedule(data, output=str(args.output))


if __name__ == "__main__":
    main()
