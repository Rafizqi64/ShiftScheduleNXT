import streamlit as st
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd

# Constants for scheduling logic
START_DATE = datetime(2025, 4, 28)
NUM_WEEKS = 6
DAYS_PER_WEEK = 7

# Define shift start and end hours (24-hour format)
shift_times = {
    'E': (6, 14),   # Early: 6am - 2pm
    'N': (0, 8),    # Night: 12am - 8am
    'D': (12, 20),  # Day: 12pm - 8pm
    'L': (18, 2),   # Late: 6pm - 2am next day
    'R': (9, 17)    # Regular: 9am - 5pm (Mon–Fri only)
}

# Sleep time restrictions per shift type
sleep_hours = {
    'N': set(range(9, 18)),
    'L': set(range(3, 12)),
    'E': set(range(22, 24)).union(range(0, 4))
}

# Hours generally considered free for socializing
usual_hours = set(range(10, 24)).union(range(0, 2))

# The 6-week static schedule that rotates among shifts
static_schedule = [
    {0: ['D'], 1: ['D'], 2: ['D'], 3: [], 4: ['E'], 5: ['E'], 6: ['E']},
    {0: [], 1: [], 2: [], 3: ['L'], 4: ['L'], 5: [], 6: ['N']},
    {0: ['N'], 1: ['N'], 2: [], 3: ['D'], 4: ['D'], 5: [], 6: []},
    {0: ['E'], 1: ['E'], 2: ['E'], 3: ['E'], 4: [], 5: ['L'], 6: ['L']},
    {0: ['L'], 1: [], 2: ['N'], 3: ['N'], 4: [], 5: ['D'], 6: ['D']},
    {0: [], 1: ['L'], 2: ['L'], 3: [], 4: ['N'], 5: ['N'], 6: []},
]

# Map shift labels (A–F) to their respective starting weeks
shift_to_week = {
    'A': 5,
    'B': 1,
    'C': 3,
    'D': 6,
    'E': 2,
    'F': 4
}

# Function to generate the full list of dates in the schedule
def generate_dates(start_date, num_weeks=NUM_WEEKS):
        return [start_date + timedelta(days=i) for i in range(num_weeks * DAYS_PER_WEEK)]

# Given a shift letter, rotate the static schedule to match its start week
def rotate_schedule(shift_letter, num_weeks=NUM_WEEKS):
    start_week_index = shift_to_week[shift_letter] - 1
    full_schedule = []
    for i in range(num_weeks):
        week_index = (start_week_index + i) % NUM_WEEKS
        full_schedule.append(static_schedule[week_index])
    return full_schedule

# Expand a shift into its actual working hours
def expand_shift_hours(shift_code):
    start, end = shift_times[shift_code]
    if end > start:
        return set(range(start, end))
    else:
        return set(range(start, 24)).union(range(0, end))

# Build the busy schedule map per person based on their shift rotation
def build_busy_map(person_shift_letter, start_date):
    busy_by_date = {}
    days_between = (start_date - START_DATE.date()).days
    num_weeks_to_generate = NUM_WEEKS + max(0, days_between // 7)
    dates = generate_dates(START_DATE, num_weeks=num_weeks_to_generate)

    if person_shift_letter == 'R':
        for date in dates:
            weekday = date.weekday()
            busy_hours = expand_shift_hours('R') if weekday < 5 else set()
            busy_by_date[date.date()] = {
                "shift": ['R'] if weekday < 5 else [],
                "busy": busy_hours,
                "filters": set()
            }
    else:
        schedule = rotate_schedule(person_shift_letter, num_weeks=num_weeks_to_generate)
        for week_index, week_schedule in enumerate(schedule):
            for day_index in range(DAYS_PER_WEEK):
                date_index = week_index * DAYS_PER_WEEK + day_index
                current_date = dates[date_index].date()
                shifts_today = week_schedule.get(day_index, [])

                busy_hours = set()
                for shift in shifts_today:
                    busy_hours.update(expand_shift_hours(shift))

                busy_by_date[current_date] = {
                    "shift": shifts_today,
                    "busy": busy_hours.copy(),
                    "filters": set()
                }

        for date in [d.date() for d in dates]:
            if date not in busy_by_date:
                busy_by_date[date] = {"shift": [], "busy": set(), "filters": set()}

    return busy_by_date

# Apply sleep filters and late-night overflow logic
def apply_sleep_filters(busy_map):
    dates = sorted(busy_map.keys())
    for i, date in enumerate(dates):
        shifts_today = busy_map[date]["shift"]

        if 'N' in shifts_today:
            busy_map[date]["filters"].update(sleep_hours['N'])
            if i > 0:
                busy_map[dates[i - 1]]["filters"].update(sleep_hours['N'])

        if 'L' in shifts_today:
            if i + 1 < len(dates):
                busy_map[dates[i + 1]]["filters"].update(sleep_hours['L'])
            next_day = date + timedelta(days=1)
            if next_day in busy_map:
                busy_map[next_day]["busy"].update({0, 1})

        if 'E' in shifts_today:
            if i > 0:
                busy_map[dates[i - 1]]["filters"].update(sleep_hours['E'])

        # If tomorrow is a Regular (R) shift, sleep early today
        if i + 1 < len(dates):
            shifts_tomorrow = busy_map[dates[i + 1]]["shift"]
            if 'R' in shifts_tomorrow:
                busy_map[date]["filters"].update(set(range(0, 8)))

    return busy_map

# Compute hours where all selected people are free
def compute_shared_free_times(people):
    shared_free_by_date = {}
    all_dates = sorted(next(iter(people.values())).keys())

    for date in all_dates:
        available_hours = usual_hours.copy()

        for person in people:
            busy = people[person][date]["busy"]
            filters = people[person][date]["filters"]
            unavailable = busy.union(filters)
            available_hours -= unavailable

        shared_free_by_date[date] = sorted(available_hours)

    return shared_free_by_date

# Group hours into ranges, supporting wrap-around (e.g. 22, 23, 0, 1)
def group_hours_to_ranges(hours):
    if not hours:
        return []
    hours = sorted(hours)
    if hours[0] == 0 and hours[-1] == 23:
        hours = hours + [h + 24 for h in hours if h < 2]
    ranges = []
    start = hours[0]
    for i in range(1, len(hours)):
        if hours[i] != hours[i - 1] + 1:
            end = hours[i - 1] + 1
            ranges.append(f"{start % 24}:00-{end % 24}:00")
            start = hours[i]
    ranges.append(f"{start % 24}:00-{(hours[-1] + 1) % 24}:00")
    return ranges

# Generate annotated calendar with shifts, weeks, and shared free time
def annotate_schedule_with_shifts_and_weeks(people, shared_free_times, start_from):
    annotated_output = []
    all_dates = sorted(next(iter(people.values())).keys())
    filtered_dates = [d for d in all_dates if d >= start_from]

    for i, date in enumerate(filtered_dates):
        day_record = {"Date": str(date)}
        free_time = shared_free_times.get(date, [])
        day_record["Shared Free Hours"] = ', '.join(group_hours_to_ranges(free_time)) if free_time else "No free hours"

        shifts_today = {}
        shifts_next_day = {}

        for idx, person in enumerate(people):
            shift = ', '.join(people[person][date]["shift"]) or "-"
            shift_code = person.split('(')[-1].strip(')')
            day_record[f"Shift {shift_code}"] = f"{shift}"
            if shift_code != 'R':
                person_index = (shift_to_week[shift_code] - 1 + (list(all_dates).index(date) // 7)) % 6 + 1
                day_record[f"Week {shift_code}"] = f"Week {person_index}"
            else:
                day_record[f"Week {shift_code}"] = "-"
            shifts_today[shift_code] = shift

            # Look ahead to next day for N shifts
            if i + 1 < len(filtered_dates):
                next_day = filtered_dates[i + 1]
                next_shift = ', '.join(people[person][next_day]["shift"]) or "-"
                shifts_next_day[shift_code] = next_shift

        # Sleepover logic: must include at least 20:00 and 1:00, and no N shifts next day
        sleepover_possible = (
            any(h in free_time for h in [20, 21, 22, 23, 0, 1]) and
            all('N' not in shifts_next_day.get(code, '') for code in shifts_next_day)
        )
        day_record["Sleepover?"] = "✅" if sleepover_possible else "❌"

        annotated_output.append(day_record)

    return pd.DataFrame(annotated_output)

# Streamlit user interface
st.title("thank u, NXT: Free Time Calendar")
st.image("nxt_shift_schedule.png", caption="Static 6-week Schedule", use_container_width=True)
st.write("Compare shifts and find overlapping free hours across 6 weeks.")

num_people = st.number_input("How many people?", min_value=1, max_value=6, value=2)
input_data = []

for i in range(num_people):
    shift = st.selectbox(f"Shift code for Person {i+1} (A–F or R for regular)", options=list(shift_to_week.keys()) + ['R'], key=f"shift_{i}")
    input_data.append(shift)

selected_date = st.date_input("Start from date", max(datetime.today().date(), datetime(2025, 4, 28).date()))

show_sleepover = st.checkbox("Show Sleepover Column", value=True)

if st.button("Show Shared Calendar"):
    people = {
        f"P{i+1} ({shift})": apply_sleep_filters(build_busy_map(shift, selected_date))
        for i, shift in enumerate(input_data)
    }
    shared_free_times = compute_shared_free_times(people)
    annotated_df = annotate_schedule_with_shifts_and_weeks(people, shared_free_times, selected_date)
    if not show_sleepover and "Sleepover?" in annotated_df.columns:
        annotated_df = annotated_df.drop(columns=["Sleepover?"])

    def highlight_cells(val):
        if isinstance(val, str):
            if ':00' in val:
                return 'background-color: #D0F0C0; color: #006400;'
            elif val.startswith('E'):
                return 'background-color: #ADD8E6; color: #00008B;'
            elif val.startswith('D'):
                return 'background-color: #90EE90; color: #006400;'
            elif val.startswith('L'):
                return 'background-color: #FFFF99; color: #8B8000;'
            elif val.startswith('N'):
                return 'background-color: #FFA07A; color: #8B0000;'
            elif val.startswith('R'):
                return 'background-color: #D3D3D3; color: #2F4F4F;'
        return ''

    st.dataframe(
        annotated_df.style.applymap(highlight_cells),
        use_container_width=True
    )
    st.download_button("Download CSV", annotated_df.to_csv(index=False), "shared_calendar.csv")
