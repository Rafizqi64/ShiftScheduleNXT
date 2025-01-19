from collections import defaultdict
from datetime import datetime, timedelta

# Define the shift times as hour ranges (in 24-hour format)
shift_times = {
    'V': (6, 14),    # 6:00-14:00
    'N': (0, 8),     # 00:00-08:00
    'D': (12, 20),   # 12:00-20:00
    'L': (18, 2)     # 18:00-02:00 (next day)
}

# Function to convert shifts into a 24-hour representation 
def get_shift_hours(shift_type):
    start, end = shift_times[shift_type]
    if start < end:
        return set(range(start, end))  # Normal shift time (same day)
    else:
        # For shifts that cross midnight (like 'L' 18:00-02:00)
        return set(range(start, 24)) | set(range(24, 24+end))

# Static 6-week schedule (same for everyone)
# Each week is a list of shifts for each day (7 days per week)
static_schedule = [
    {0: ['L'], 1: ['L'], 2: [], 3: ['N'], 4: ['N'], 5: ['N'], 6: ['N']},  # Week 1
    {0: [], 1: [], 2: ['D'], 3: ['D'], 4: ['D'], 5: [], 6: []},  # Week 2
    {0: ['V'], 1: ['V'], 2: ['V'], 3: ['V'], 4: [], 5: ['L'], 6: ['L']},  # Week 3
    {0: ['N'], 1: ['N'], 2: ['N'], 3: [], 4: [], 5: ['D'], 6: ['D']},  # Week 4
    {0: ['D'], 1: ['D'], 2: [], 3: [], 4: ['V'], 5: ['V'], 6: ['V']},  # Week 5
    {0: [], 1: [], 2: ['L'], 3: ['L'], 4: ['L'], 5: [], 6: []},  # Week 6
]

# Function to calculate free time between two people
def find_free_time(start_week1, start_week2):
    free_times = defaultdict(lambda: defaultdict(set))
    
    for week_offset in range(6):
        week_p1 = (start_week1 + week_offset) % 6
        week_p2 = (start_week2 + week_offset) % 6
        
        for day in range(7):
            shifts_p1 = static_schedule[week_p1].get(day, [])
            busy_hours_p1 = set()
            for shift in shifts_p1:
                busy_hours_p1.update(get_shift_hours(shift))

            shifts_p2 = static_schedule[week_p2].get(day, [])
            busy_hours_p2 = set()
            for shift in shifts_p2:
                busy_hours_p2.update(get_shift_hours(shift))

            # Find the free hours for both persons
            free_hours_p1 = set(range(24)) - busy_hours_p1
            free_hours_p2 = set(range(24)) - busy_hours_p2

            # Find the common free hours between both
            common_free = free_hours_p1.intersection(free_hours_p2)

            if common_free:
                free_times[(week_offset, week_p1, week_p2)][day] = common_free

    return free_times
def filter_unusual_times(free_times):
    # Define usual hours (e.g., 10 AM to 2 AM)
    usual_hours = set(range(0, 24))  # 12 AM - 2 AM 
    
    # Define sleeping hours for N and L shifts (before and after their shifts)
    sleeping_hours_n = set(range(9, 18))  # 9 AM - 6 PM
    sleeping_hours_l = set(range(3, 12))  # 3 AM - 12 PM
    sleeping_hours_v = set(range(22, 28))  # 10 PM - 4 AM
    
    filtered_free_times = {}
    for (week_offset, week_p1, week_p2), days in free_times.items():
        filtered_free_times[(week_offset, week_p1, week_p2)] = {}
        for day, hours in days.items():
            # Start with the usual hours filter
            filtered_hours = hours.intersection(usual_hours)
            
            # Check if Person 1 is working a night shift (N, L, or V)
            shifts_p1 = static_schedule[week_p1].get(day, [])
            if 'N' in shifts_p1:
                filtered_hours -= sleeping_hours_n  # Remove 9 AM - 6 PM for N shift
            if 'L' in shifts_p1:
                filtered_hours -= sleeping_hours_l  # Remove 3 AM - 12 PM for L shift

            # Check if Person 2 is working a night shift (N, L, or V)
            shifts_p2 = static_schedule[week_p2].get(day, [])
            if 'N' in shifts_p2:
                filtered_hours -= sleeping_hours_n  # Remove 9 AM - 6 PM for N shift
            if 'L' in shifts_p2:
                filtered_hours -= sleeping_hours_l  # Remove 3 AM - 12 PM for L shift 

            # Adjust for Person 1's next day morning shift (V shift)
            next_day = (day + 1) % 7
            shifts_p1_next_day = static_schedule[week_p1].get(next_day, [])
            if 'V' in shifts_p1_next_day:
                # Remove early morning hours from the current day (10 PM to 12 AM)
                filtered_hours -= set(range(22, 24))
                if next_day not in filtered_free_times[(week_offset, week_p1, week_p2)]:
                    filtered_free_times[(week_offset, week_p1, week_p2)][next_day] = set()
                # Remove hours for V shift from 12 AM to 4 AM for the next day
                filtered_free_times[(week_offset, week_p1, week_p2)][next_day] -= set(range(0, 4))

            # Adjust for Person 2's next day morning shift (V shift)
            shifts_p2_next_day = static_schedule[week_p2].get(next_day, [])
            if 'V' in shifts_p2_next_day:
                # Remove early morning hours from the current day (10 PM to 12 AM)
                filtered_hours -= set(range(22, 24))
                if next_day not in filtered_free_times[(week_offset, week_p1, week_p2)]:
                    filtered_free_times[(week_offset, week_p1, week_p2)][next_day] = set()
                # Remove hours for V shift from 12 AM to 4 AM for the next day
                filtered_free_times[(week_offset, week_p1, week_p2)][next_day] -= set(range(0, 4))

            # Adjust for overnight shifts properly
            result = defaultdict(set)
            for hour in filtered_hours:
                if hour < 24:
                    result[day].add(hour)
                else:
                    result[next_day].add(hour - 24)

            # Combine results into filtered_free_times
            for next_day, hours in result.items():
                if next_day not in filtered_free_times[(week_offset, week_p1, week_p2)]:
                    filtered_free_times[(week_offset, week_p1, week_p2)][next_day] = set()
                filtered_free_times[(week_offset, week_p1, week_p2)][next_day].update(hours)

    return filtered_free_times

# Get user input for the start week and start date
start_week1 = int(input("Enter the start week for Person 1: ")) - 1
start_week2 = int(input("Enter the start week for Person 2: ")) - 1
start_date_str = input("Enter the start date GMP wise (DD-MMM-YY): ")

# Convert the start date string to a datetime object
start_date = datetime.strptime(start_date_str, "%d-%b-%y")

# Example: Finding free time between Person 1 starting at week 0 and Person 2 starting at week 1
free_time = find_free_time(start_week1=start_week1, start_week2=start_week2)
filtered_free_time = filter_unusual_times(free_time)

# Display the filtered results with dates in a "prettier" format
print("\n=== Free Time Schedule ===\n")
for (week_offset, week_p1, week_p2), days in filtered_free_time.items():
    print(f"--- Week {week_offset + 1} (P1 Week {week_p1 + 1}, P2 Week {week_p2 + 1}) ---")
    for day in range(7):  # Ensure all days are displayed
        day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day]
        current_date = start_date + timedelta(days=day + week_offset * 7)
        formatted_date = current_date.strftime("%d-%b-%y")
        
        if day in days:
            formatted_hours = [f"{hour:02}:00" for hour in sorted(days[day])]
            print(f"  {day_name} ({formatted_date}): {', '.join(formatted_hours)}")
        else:
            print(f"  {day_name} ({formatted_date}): No common free hours")
    print("\n")