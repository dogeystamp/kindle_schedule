# kindle schedule display

This is a "smart" schedule display that can be placed on your desk, so you can
always see your schedule. Because it uses e-paper, the battery could probably
last at least a month.

The display can be synchronized with your cloud calendar semi-automatically, as
long as you can get the events in ICS format.

## how it works

The schedule display itself is just a re-purposed e-reader.

1. On a laptop, events are synced from the cloud using [vdirsyncer](https://github.com/pimutils/vdirsyncer).
2. A Python script filters and processes the events.
3. [Typst](https://github.com/typst/typst) is used to render the calendar to PDF.
4. The calendar is transferred wirelessly to the display via SSH/SFTP.

## installation & usage

_This project is not intended for production use_, so everything in this
section is very convoluted and not suitable for users without much technical
knowledge (sorry).

Theoretically, this project can be used on any e-reader device where you can
sideload books, but the schedule display is intended to run on a device with
[KOReader](https://github.com/koreader/koreader) installed.

The following steps are designed for Linux, although everything should work on
MacOS. This script itself should work on Windows, but `vdirsyncer` doesn't.

- Install and set up [vdirsyncer](https://vdirsyncer.pimutils.org/en/stable/tutorial.html)
    on your computer. `vdirsyncer` is a command-line utility that synchronizes ICS files
    between your computer and a cloud calendar.

- Clone this repository:

    ```
    git clone https://github.com/dogeystamp/kindle_schedule.git
    cd kindle_schedule
    ```

- Create a configuration file:

    ```
    mkdir -p ~/.config/kindle_schedule/
    cp config.toml.example ~/.config/kindle_schedule/config.toml
    ```

- Tweak the configuration. The main thing you need to change is
    `ics_directory`, which should be set to the directory where vdirsyncer stores
    its ICS files.

    ```
    # use your preferred editor
    nano ~/.config/kindle_schedule/config.toml
    ```

- Install [KOReader](https://github.com/koreader/koreader) on an e-reader device.

- Ensure that your Wi-Fi is connected in KOReader.

- [Enable the SSH server](https://github.com/koreader/koreader/wiki/SSH) in KOReader.
    - Set up [public-key based authentication](https://www.baeldung.com/linux/ssh-setup-public-key-auth)
        by selecting `Settings → Network → SSH server → SSH public key.` in the top menu.
        This will show a file path (on my device, `/mnt/us/koreader/settings/SSH/authorized_keys`)
        where you can enter your public key.
    - To edit the authorized keys file, you can use the built-in terminal:
        `Tools → More tools → Terminal emulator → Open terminal session` in the
        top menu. The terminal includes `vi` and a POSIX shell.
    - Alternatively, at least on Kindle devices, you can exit KOReader and plug
        the device into your computer with USB. You can then mount the filesystem
        and copy the authorized key file. You will not see the `/mnt/us` part
        of the file path.

- Back on your computer, install [uv](https://docs.astral.sh/uv/).
    (Alternatively, install all the dependencies in pip manually.)

- You can now synchronize everything in one long command (which you should bind to an alias or script):

    ```
    vdirsyncer sync \
        && kindle_schedule/kindle_schedule.py ~/.schedule.pdf \
        && scp ~/.schedule.pdf [kindle's IP address]:/mnt/us/documents/schedule.pdf -p 2222
    ```

    KOReader turns off Wi-Fi when the device is in sleep mode, so you will have to wake it up to sync.

- In KOReader, open the file browser (the file cabinet icon) in the top menu and open `schedule.pdf`.

- In the bottom menu, set "View Mode" to "page".
    - You might also want to edit the "Zoom to" and "Fit" settings.
    - Set "Page Crop" to "none" and set "Margin" to the minimum.

- In the top menu, go to `Settings → Screen → Sleep screen`. Disable the sleep screen message, and select `Wallpaper → Leave screen as-is`.

- You can now go back to `schedule.pdf`, and press the power button. KOReader will put the device in deep sleep,
    but your schedule will stay on screen. This saves an immense amount of battery.

## development

This project is built using [uv](https://docs.astral.sh/uv/).
The Python files list their own dependencies ([PEP-0723](https://peps.python.org/pep-0723/)),
so you can install the dependencies and run the scripts with a single command:

```
uv run kindle_schedule.py
```

Or, since it has a shebang, just `./kindle_schedule.py`.

To get a virtual environment for your IDE / LSP to work with, you can do the following:

```
uv venv
source .venv/bin/activate
uv sync --active --script kindle_schedule.py
```

This will create a virtual environment with all of the script's dependencies.
