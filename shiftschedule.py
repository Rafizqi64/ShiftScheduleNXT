from collections import defaultdict
from datetime import datetime, timedelta

# Define the shift times as hour ranges (in 24-hour format)
shift_times = {
    'V': (6, 14),    # 6:00-14:00
    'N': (0, 8),     # 00:00-08:00
    'D': (12, 20),   # 12:00-20:00
    'L': (18, 2)     # 18:00-02:00 (next day)
}

def get_shift_hours(shift_type):
    start, end = shift_times[shift_type]

    today_hours = set()
    next_day_hours = set()

    if start < end:
        # Normal shift that ends the same day
        today_hours = set(range(start, end))
    else:
        # Shift that crosses over midnight
        today_hours = set(range(start, 24))   # e.g., 18:00 - 23:00
        next_day_hours = set(range(0, end))   # e.g., 00:00 - 02:00 (on next day)

    return today_hours, next_day_hours

# Static 6-week schedule (same for everyone)
# Each week is a list of shifts for each day (7 days per week)
static_schedule = [
    {0: ['D'], 1: ['D'], 2: ['D'], 3: [], 4: ['V'], 5: ['V'], 6: ['V']},  # Week 1
    {0: [], 1: [], 2: [], 3: ['L'], 4: ['L'], 5: [], 6: ['N']},  # Week 2
    {0: ['N'], 1: ['N'], 2: [], 3: ['D'], 4: ['D'], 5: [], 6: []},  # Week 3
    {0: ['V'], 1: ['V'], 2: ['V'], 3: ['V'], 4: [], 5: ['L'], 6: ['L']},  # Week 4
    {0: ['L'], 1: [], 2: ['N'], 3: ['N'], 4: [], 5: ['D'], 6: ['D']},  # Week 5
    {0: [], 1: ['L'], 2: ['L'], 3: [], 4: ['N'], 5: ['N'], 6: []},  # Week 6
]

# Map shifts A-F to week numbers 1-5 
shift_to_week = {
    'A': 5,
    'B': 1,
    'C': 3,
    'D': 6,
    'E': 2,
    'F': 4
}

def find_free_time(start_weeks, start_date):
    num_people = len(start_weeks)
    
    # free_times[week_offset_and_weeks][day] = set of hours free
    free_times = defaultdict(lambda: defaultdict(set))
    
    # Reference date (28-Apr-2025)
    reference_date = datetime.strptime("28-apr-2025", "%d-%b-%Y")
    
    # Week offset from the reference date
    week_offset = (start_date - reference_date).days // 7
    
    for offset in range(6):  # 6 weeks of comparison
        # Calculate current week number for each person
        weeks = [(shift_to_week[start_week] + week_offset + offset) % 6 for start_week in start_weeks]
        
        # Initialize busy hours for all days in the week for all people
        busy_hours_by_day = {day: [set() for _ in range(num_people)] for day in range(7)}
        
        for i in range(num_people):
            for day in range(7):
                shifts = static_schedule[weeks[i]].get(day, [])
                
                for shift in shifts:
                    today_hours, next_day_hours = get_shift_hours(shift)
                    
                    # Add busy hours for today
                    busy_hours_by_day[day][i].update(today_hours)
                    
                    # Add busy hours for the next day (cross-midnight part)
                    next_day = (day + 1) % 7
                    busy_hours_by_day[next_day][i].update(next_day_hours)
        
        # Now calculate free hours (common between all people)
        for day in range(7):
            # Full 24-hour set minus busy hours for each person
            free_hours_per_person = [set(range(24)) - busy_hours_by_day[day][i] for i in range(num_people)]
            
            # Common free hours = intersection of everyone’s free hours
            common_free = set.intersection(*free_hours_per_person)
            
            if common_free:
                free_times[(offset, *weeks)][day] = common_free

    return free_times

def filter_unusual_times(free_times):
    usual_hours = set(range(10, 24)).union(set(range(0, 2)))  # 10 AM - 2 AM

    sleeping_hours_n = set(range(9, 18))   # 9 AM - 6 PM
    sleeping_hours_l = set(range(3, 12))   # 3 AM - 12 PM
    sleeping_hours_v_today = set(range(22, 24))  # 10 PM - 12 AM (today)
    sleeping_hours_v_next = set(range(0, 4))     # 12 AM - 4 AM (next day)

    filtered_free_times = {}

    for (week_offset, *weeks), days in free_times.items():
        filtered_free_times[(week_offset, *weeks)] = {}

        # Prepare a temporary structure to hold any "overflow" hours crossing days
        day_results = defaultdict(set)

        for day in range(7):
            hours = days.get(day, set()).copy()
            if not hours:
                continue

            # Step 1: Filter by usual hours (we don't want weird times)
            filtered_hours = hours.intersection(usual_hours)

            # Step 2: Remove sleep hours for shifts happening the same day
            for week in weeks:
                shifts_today = static_schedule[week].get(day, [])

                if 'N' in shifts_today:
                    filtered_hours -= sleeping_hours_n
                if 'L' in shifts_today:
                    filtered_hours -= sleeping_hours_l
                if 'V' in shifts_today:
                    filtered_hours -= sleeping_hours_v_today

            # Step 3: Handle the **next** day recovery from V shift today
            next_day = (day - 1) % 7
            for week in weeks:
                shifts_today = static_schedule[week].get(day, [])
                if 'V' in shifts_today:
                    # Sleep continues into next day
                    if next_day not in day_results:
                        next_day_hours = days.get(next_day, set()).intersection(usual_hours)
                        day_results[next_day] = next_day_hours
                    day_results[next_day] -= sleeping_hours_v_next

            # Step 4: Handle the **previous** day shifts (recovery)
            prev_day = (day + 1) % 7
            for week in weeks:
                shifts_prev_day = static_schedule[week].get(prev_day, [])

                if 'L' in shifts_prev_day:
                    filtered_hours -= sleeping_hours_l
                if 'V' in shifts_prev_day:
                    filtered_hours -= sleeping_hours_v_next  # Sleep in early hours of the day

            for hour in filtered_hours:
                if hour < 24:
                    day_results[day].add(hour)
                else:
                    adj_day = (day + 1) % 7
                    if adj_day not in day_results:
                        next_day_hours = days.get(adj_day, set()).intersection(usual_hours)
                        day_results[adj_day] = next_day_hours
                    day_results[adj_day].add(hour - 24)

        # Step 6: Save the results back into filtered_free_times
        for result_day, hours_set in day_results.items():
            if hours_set:  # Only add non-empty results
                filtered_free_times[(week_offset, *weeks)][result_day] = hours_set

    return filtered_free_times


# Get user input for the start weeks and start date
while True:
    try:
        num_people = int(input("Enter the number of people: "))
        if num_people > 1:
            break  # Exit the loop since input is valid
        else:
            print("Invalid input. Please enter more than one.")
    except ValueError:
        print("Invalid input. Please enter a valid integer.")

start_weeks = []
for i in range(num_people):
    while True:
        start_week = input(f"Enter the shift for Person {i + 1} (A-F): ").upper()
        if start_week in shift_to_week:
            start_weeks.append(start_week)
            break
        else:
            print("Invalid input. Please enter a valid shift (A-F).")

while True:
    start_date_str = input("Enter the start date GMP wise (DD-MMM-YY): ")
    start_date = datetime.strptime(start_date_str, "%d-%b-%y")
    reference_date = datetime.strptime("28-Apr-2025", "%d-%b-%Y")
    if start_date >= reference_date:
        break
    else:
        print("Invalid date. Please enter a date on or after 5th May 2025.")

# Adjust the input date to the nearest Monday
start_date = start_date - timedelta(days=start_date.weekday())

# Example: Finding free time between multiple people
free_time = find_free_time(start_weeks, start_date)
filtered_free_time = filter_unusual_times(free_time)
#cleaned_free_time = filter_short_periods(filtered_free_time)

# Display the filtered results with dates in a "prettier" format
print("\n=== Free Time Schedule ===\n")
#for (week_offset, *weeks), days in cleaned_free_time.items():
for (week_offset, *weeks), days in filtered_free_time.items():
    weeks_str = ', '.join([f"P{i + 1} Week {week + 1}" for i, week in enumerate(weeks)])
    print(f"--- Week {week_offset + 1} ({weeks_str}) ---")
    for day in range(7):  # Ensure all days are displayed
        day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day]
        current_date = start_date + timedelta(days=day + week_offset * 7)
        formatted_date = current_date.strftime("%d-%b-%y")
        
        # Display shifts for each person
        shifts_info = []
        for i, week in enumerate(weeks):
            shifts = static_schedule[week].get(day, [])
            shifts_info.append(f"P{i + 1}: {', '.join(shifts) if shifts else 'No shift'}")
        print(f"  {day_name} ({formatted_date}): {' | '.join(shifts_info)}")
        
        if day in days:
            formatted_hours = [f"{hour:02}:00" for hour in sorted(days[day])]
            print(f"    Free hours: {', '.join(formatted_hours)}")
        else:
            print(f"    Free hours: No common free hours")
    print("\n")