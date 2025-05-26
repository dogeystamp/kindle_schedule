# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.
#
# © 2025 dogeystamp <dogeystamp@disroot.org>

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "mergecal==0.5.0",
#     "pillow==11.2.1",
#     "recurring-ical-events==3.7.0",
#     "typst==0.13.2",
#     "watchdog==6.0.0",
# ]
# ///

"""
Quick experimental cells to play with the functions interactively.

Run this with [marimo](https://github.com/marimo-team/marimo).
"""

import marimo

__generated_with = "0.13.11"
app = marimo.App(width="medium")

with app.setup:
    import marimo as mo
    import kindle_schedule as ks

    config = ks.get_config()
    calendar = ks.read_calendars(config)


@app.cell
def _():
    config
    return


@app.cell
def _():
    from datetime import date
    ks.recurring_ical_events.of(calendar).at(date(2025, 5, 11))
    return (date,)


@app.cell
def _(date):
    data = ks.generate_data(config, start_date=date(2025, 5, 5))
    data
    return (data,)


@app.cell
def _(data):
    import json
    json.dumps(data)
    return


@app.cell
def _(data):
    img = ks.generate_schedule(data, format="png")
    type(img)
    return (img,)


@app.cell
def _(img):
    from io import BytesIO
    [mo.image(BytesIO(img)) for img in img]
    return


if __name__ == "__main__":
    app.run()
