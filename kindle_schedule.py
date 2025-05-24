# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "recurring-ical-events==3.*",
# ]
# ///


import os
from pathlib import Path
from dataclasses import dataclass

import tomllib


@dataclass
class Configuration:
    ics_directory: Path


def get_config() -> Configuration:
    config_dir_str = os.environ.get("KINDLE_SCHEDULE_DIR", None)
    config_dir = (
        Path(config_dir_str)
        if config_dir_str
        else Path.home() / ".config/kindle_schedule"
    )

    config_file = config_dir / "config.toml"

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

    return Configuration(ics_directory=ics_directory)


def main() -> None:
    config = get_config()
    print(config)


if __name__ == "__main__":
    main()
