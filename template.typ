// number of days per schedule
#let SCHEDULE_DAYS = 5

// global start time (e.g. morning)
#let START_TIME = datetime(hour: 8, minute: 0, second: 0)
// global end time (e.g. evening)
#let END_TIME = datetime(hour: 22, minute: 0, second: 0)

#let schedule_length = (END_TIME - START_TIME).hours()
#let hour_height = (1 / schedule_length) * 100%

#let datetime_to_date(dt) = {
  return datetime(year: dt.year(), month: dt.month(), day: dt.day())
}

#let all_day_cell(
  summary,
) = {
  rect(
    width: 100%,
    fill: luma(90%),
    inset: 0.5em,
    align(
      horizon + center,
      [
        #set text(size: 0.9em)
        #summary
      ],
    ),
  )
}

/// Compute the positioning and scaling of the cell for a single event.
#let event_cell(
  // the date the cell is on
  current_date,
  start_time,
  end_time,
  // Event's title.
  event_name,
  // Optional settings.
  extra: (:),
) = {
  let n_overlaps = extra.at("n_overlaps", default: 0)
  let description = extra.at("description", default: [])

  let cell_fill = if n_overlaps > 0 {
    luma(90%)
  } else {
    luma(100%)
  }

  let today_start = datetime(
    year: current_date.year(),
    month: current_date.month(),
    day: current_date.day(),
    hour: START_TIME.hour(),
    minute: START_TIME.minute(),
    second: START_TIME.second(),
  )

  let today_end = datetime(
    year: current_date.year(),
    month: current_date.month(),
    day: current_date.day(),
    hour: END_TIME.hour(),
    minute: END_TIME.minute(),
    second: END_TIME.second(),
  )

  let effective_start = calc.max(start_time, today_start)
  let effective_end = calc.min(end_time, today_end)

  let time_msg = (start, end, today_date) => {
    let start_label = if datetime_to_date(start) == today_date {
      [#start.display("[hour]:[minute]")]
    } else {
      []
    }

    let end_label = if datetime_to_date(end) == today_date {
      [#end.display("[hour]:[minute]")]
    } else {
      []
    }

    parbreak()
    [#start_label -- #end_label]
  }

  let others_msg = count => {
    if count > 0 {
      parbreak()
      if count > 1 [
        _(#count other events)_
      ] else [
        _(#count other event)_
      ]
    }
  }

  place(
    top + left,
    dx: 0%,
    dy: (effective_start - today_start).hours() * hour_height,
    rect(
      height: calc.max(0, (effective_end - effective_start).hours()) * hour_height,
      fill: cell_fill,
      stroke: 1pt + black,
      inset: 0.5em,
      width: 100%,
    )[
      #event_name
      #set text(size: 0.8em)
      #time_msg(start_time, end_time, current_date)

      #emph(description)
      #others_msg(n_overlaps)
    ],
  )
}

#let schedule(start_date, events) = {
  set par(leading: 0.20em, spacing: 0.4em)
  grid(
    // columns:
    // - hour indicators
    // - timetable
    columns: (auto, auto),
    // rows:
    // - days of the week
    // - all day events
    // - timetable
    rows: (auto, auto, 1fr),

    // note above that `auto` means "use just enough space", while `1fr` means
    // "use all remaining space".

    // corner area (idk what to put here)
    block(),

    // day of the week indicators
    block(
      height: auto,
      width: 100%,
      grid(
        columns: SCHEDULE_DAYS,
        ..range(SCHEDULE_DAYS).map(i => {
          let current_date = start_date + duration(days: i)
          rect(
            width: 100%,
            stroke: none,
            inset: (left: 0em, right: 0em, top: 0.5em, bottom: 0.5em),
            align(
              center + top,
              [
                #set par(leading: 0.4em)
                #current_date.display("[weekday]")
                \
                #set text(size: 1.4em)
                *#current_date.display("[day]")*
              ],
            ),
          )
        })
      ),
    ),

    // dummy (corner)
    block(),

    // all day event blocks
    block(
      height: auto,
      width: 100%,
      {
        grid(
          columns: SCHEDULE_DAYS,
          ..range(SCHEDULE_DAYS).map(i => {
            let today_events = events.at(i, default: (:)).at("all_day", default: ())
            if today_events.len() > 0 {
              grid(
                inset: 0.15em,
                ..today_events
              )
            } else {
              block(width: 100%)
            }
          })
        )
        v(0.4em)
      },
    ),

    // hour indicators
    block(height: 100%, width: auto, inset: (right: 1em))[
      #let current_time = START_TIME
      #while current_time < END_TIME {
        // zero height to avoid displacing the other labels
        let time_label = box(height: 0em, text(current_time.display("[hour]")))

        place(
          top,
          float: true,
          clearance: 0em,
          dy: (current_time - START_TIME).hours() * hour_height - 0.375em,
          time_label,
        )
        current_time += duration(hours: 1)
      }
    ],

    // main calendar element
    block(
      height: 100%,
      width: 100%,
      {
        // hour line markers
        let current_time = START_TIME
        while current_time < END_TIME {
          let time_label = text(current_time.display("[hour]:[minute]"))

          place(
            dx: -1%,
            dy: (current_time - START_TIME).hours() * hour_height,
            line(length: 102%, stroke: 0.5pt + gray),
          )
          current_time += duration(hours: 1)
        }


        // events
        grid(
          columns: range(SCHEDULE_DAYS).map(_ => 1fr),
          rows: 1fr,
          ..range(SCHEDULE_DAYS).map(i => {
            let today_events = events.at(i, default: (:)).at("regular", default: ())
            block(width: 100%, height: 100%, for event in today_events { event })
          })
        )
      },
    ),
  )
}

/// Render schedules on multiple pages, one schedule per day
#let calendar(start_date, events) = {
  let n_days = events.len()

  // generate this amount of pages
  let n_schedules = calc.max(1, 1 + n_days - SCHEDULE_DAYS)

  for page_idx in range(n_schedules) {
    schedule(start_date + duration(days: 1) * page_idx, events.slice(page_idx))
    if page_idx != n_schedules - 1 {
      pagebreak()
    }
  }
}


// kindle settings
#set page(
  width: 3.6in,
  height: 4.7666667in,
  flipped: false,
  margin: (top: 1em, bottom: 1em, left: 1.0em, right: 1.5em),
)
#set text(font: "Liberation Sans", size: 6pt)


/// Parse a date from JSON (Typst doesn't support this natively).
#let parse_date(date) = {
  datetime(
    year: date.at("year"),
    month: date.at("month"),
    day: date.at("day"),
  )
}
/// Parse a datetime from JSON.
#let parse_datetime(date) = {
  datetime(
    year: date.at("year"),
    month: date.at("month"),
    day: date.at("day"),
    hour: date.at("hour"),
    minute: date.at("minute"),
    second: date.at("second"),
  )
}


// parse events from JSON
#let data = json("data.json")
#let start_date = parse_date(data.start_date)
#let events = (
  data
    .events
    .enumerate()
    .map(elem => {
      let (i, ev) = elem
      let current_date = start_date + duration(days: 1) * i

      (
        regular: ev.regular.map(regular_ev => {
          let start = parse_datetime(regular_ev.start)
          let end = parse_datetime(regular_ev.end)
          event_cell(
            current_date,
            start,
            end,
            [*#regular_ev.name*],
            extra: regular_ev.at("extra", default: (:)),
          )
        }),
        all_day: ev.all_day.map(all_day_ev => {
          all_day_cell(all_day_ev.name)
        }),
      )
    })
)
#calendar(start_date, events)
