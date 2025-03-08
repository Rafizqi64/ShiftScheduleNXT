from collections import defaultdict
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox

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
        return set(range(start, 24)) | set(range(0, end))

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

# Map shifts A-F to week numbers 0-5
shift_to_week = {
    'A': 0,
    'B': 1,
    'C': 2,
    'D': 3,
    'E': 4,
    'F': 5
}

# Function to calculate free time between multiple people
def find_free_time(start_weeks, start_date):
    num_people = len(start_weeks)
    free_times = defaultdict(lambda: defaultdict(set))
    
    # Calculate the reference date (5th of May)
    reference_date = datetime.strptime("05-May-2025", "%d-%b-%Y")
    
    # Calculate the week offset from the reference date
    week_offset = (start_date - reference_date).days // 7
    
    for offset in range(6):  # Compare 6 weeks
        weeks = [(shift_to_week[start_week] + week_offset + offset) % 6 for start_week in start_weeks]
        
        for day in range(7):
            busy_hours = [set() for _ in range(num_people)]
            
            for i in range(num_people):
                shifts = static_schedule[weeks[i]].get(day, [])
                for shift in shifts:
                    busy_hours[i].update(get_shift_hours(shift))
            
            # Find the free hours for all persons
            free_hours = [set(range(24)) - busy_hours[i] for i in range(num_people)]
            
            # Find the common free hours between all persons
            common_free = set.intersection(*free_hours)

            if common_free:
                free_times[(offset, *weeks)][day] = common_free

    return free_times

def filter_unusual_times(free_times):
    # Define usual hours (e.g., 10 AM to 2 AM)
    usual_hours = set(range(10, 24)).union(set(range(0, 2)))  # 10 AM - 2 AM 
    
    # Define sleeping hours for N and L shifts (before and after their shifts)
    # N shift (00:00-08:00) => sleeping hours after their shift, 9 AM - 6 PM
    sleeping_hours_n = set(range(9, 18))  # 9 AM - 6 PM
    
    # L shift (18:00-02:00) => sleeping hours before their shift, 3 AM - 12 PM
    sleeping_hours_l = set(range(3, 12))  # 3 AM - 12 PM
    
    # V shift (06:00-14:00) => sleeping hours before their shift, 10 PM - 4 AM
    sleeping_hours_v = set(range(22, 28))  # 10 PM - 4 AM    
    
    filtered_free_times = {}
    for (week_offset, *weeks), days in free_times.items():
        filtered_free_times[(week_offset, *weeks)] = {}
        for day, hours in days.items():
            # Start with the usual hours filter
            filtered_hours = hours.intersection(usual_hours)
            
            # Check if any person is working a night shift (N, L, or V)
            for week in weeks:
                shifts = static_schedule[week].get(day, [])
                if 'N' in shifts:
                    filtered_hours -= sleeping_hours_n  # Remove 9 AM - 6 PM for N shift
                if 'L' in shifts:
                    filtered_hours -= sleeping_hours_l  # Remove 3 AM - 12 PM for L shift

            # Check if any person has a morning shift the next day
            next_day = (day + 1) % 7
            for week in weeks:
                shifts_next_day = static_schedule[week].get(next_day, [])
                if 'V' in shifts_next_day:
                    filtered_hours -= set(range(22, 24))  # Remove 10 PM - 12 AM for V shift
                    if next_day not in filtered_free_times[(week_offset, *weeks)]:
                        filtered_free_times[(week_offset, *weeks)][next_day] = set()
                    filtered_free_times[(week_offset, *weeks)][next_day].update(set(range(0, 4)))  # Remove 12 AM - 4 AM for V shift

            # Adjust for overnight shifts properly
            result = defaultdict(set)
            for hour in filtered_hours:
                if hour < 24:
                    result[day].add(hour)  # Regular hours for the current day
                else:
                    # For hours like 24:00-28:00, adjust to the next day (e.g., 24:00 is day + 1)
                    result[next_day].add(hour - 24)

            # Combine results into filtered_free_times
            for next_day, hours in result.items():
                if next_day not in filtered_free_times[(week_offset, *weeks)]:
                    filtered_free_times[(week_offset, *weeks)][next_day] = set()
                filtered_free_times[(week_offset, *weeks)][next_day].update(hours)

    return filtered_free_times

def filter_short_periods(filtered_free_times):
    cleaned_free_times = {}
    for key, days in filtered_free_times.items():
        cleaned_free_times[key] = {}
        for day, hours in days.items():
            sorted_hours = sorted(hours)
            consecutive_hours = []
            temp = []

            for i in range(len(sorted_hours)):
                if i == 0 or sorted_hours[i] == sorted_hours[i - 1] + 1:
                    temp.append(sorted_hours[i])
                else:
                    if len(temp) > 2:
                        consecutive_hours.extend(temp)
                    temp = [sorted_hours[i]]
            if len(temp) > 2:
                consecutive_hours.extend(temp)

            if consecutive_hours:
                cleaned_free_times[key][day] = set(consecutive_hours)

    return cleaned_free_times

def calculate_free_time():
    try:
        num_people = int(num_people_entry.get())
        start_weeks = []
        for i in range(num_people):
            start_week = start_weeks_entries[i].get().upper()
            if start_week not in shift_to_week:
                raise ValueError(f"Invalid shift for Person {i + 1}. Please enter a valid shift (A-F).")
            start_weeks.append(start_week)

        start_date_str = start_date_entry.get()
        start_date = datetime.strptime(start_date_str, "%d-%b-%y")
        reference_date = datetime.strptime("05-May-2025", "%d-%b-%Y")
        if start_date < reference_date:
            raise ValueError("Invalid date. Please enter a date on or after 5th May 2025.")

        # Adjust the input date to the nearest Monday
        start_date = start_date - timedelta(days=start_date.weekday())

        # Calculate free time
        free_time = find_free_time(start_weeks, start_date)
        filtered_free_time = filter_unusual_times(free_time)
        cleaned_free_time = filter_short_periods(filtered_free_time)

        # Display the results
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "\n=== Free Time Schedule ===\n")
        for (week_offset, *weeks), days in cleaned_free_time.items():
            weeks_str = ', '.join([f"P{i + 1} Week {week + 1}" for i, week in enumerate(weeks)])
            result_text.insert(tk.END, f"--- Week {week_offset + 1} ({weeks_str}) ---\n")
            for day in range(7):  # Ensure all days are displayed
                day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day]
                current_date = start_date + timedelta(days=day + week_offset * 7)
                formatted_date = current_date.strftime("%d-%b-%y")
                
                if day in days:
                    formatted_hours = [f"{hour:02}:00" for hour in sorted(days[day])]
                    result_text.insert(tk.END, f"  {day_name} ({formatted_date}): {', '.join(formatted_hours)}\n")
                else:
                    result_text.insert(tk.END, f"  {day_name} ({formatted_date}): No common free hours\n")
            result_text.insert(tk.END, "\n")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Create the main window
root = tk.Tk()
root.title("Free Time Scheduler")

# Create and place the widgets
tk.Label(root, text="Enter the number of people:").grid(row=0, column=0, padx=10, pady=5)
num_people_entry = tk.Entry(root)
num_people_entry.grid(row=0, column=1, padx=10, pady=5)

start_weeks_entries = []
for i in range(6):  # Assuming a maximum of 6 people
    tk.Label(root, text=f"Enter the start week for Person {i + 1} (A-F):").grid(row=i + 1, column=0, padx=10, pady=5)
    entry = tk.Entry(root)
    entry.grid(row=i + 1, column=1, padx=10, pady=5)
    start_weeks_entries.append(entry)

tk.Label(root, text="Enter the start date GMP wise (DD-MMM-YY):").grid(row=7, column=0, padx=10, pady=5)
start_date_entry = tk.Entry(root)
start_date_entry.grid(row=7, column=1, padx=10, pady=5)

calculate_button = tk.Button(root, text="Calculate Free Time", command=calculate_free_time)
calculate_button.grid(row=8, column=0, columnspan=2, padx=10, pady=10)

result_text = tk.Text(root, width=80, height=20)
result_text.grid(row=9, column=0, columnspan=2, padx=10, pady=10)

# Run the main loop
root.mainloop()