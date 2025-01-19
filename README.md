# Shift Schedule Free Time Finder
Hello beautiful people!
This Python script helps you find free time between two people based on their shift schedules. The program uses a predefined 6-week shift schedule which can be edited and takes into account specific shifts such as Day, Night, and Late shifts. Additionally, the program adjusts for sleeping hours based on shift types and finds common free hours for both people.

### Features
- **Input**: Allows the user to input the start week and date in the GMP format `DD-MMM-YY`.
- **Free Time Calculation**: Computes the common free hours between two shifts based on their shift schedules.
- **Shift Adjustments**: Accounts for overnight shifts (e.g., `L` 18:00-02:00) and sleeping hours for each shift.
- **Usual Hours Filter**: Filters out non-typical hours, such as early morning or late night, for a better overview of the available free time.
- **Date Display**: The script shows the exact date for each day of the week.

---

### Shift Types
The following shifts are used in the script:
- **V (Day Shift)**: 06:00 - 14:00
- **N (Night Shift)**: 00:00 - 08:00
- **D (Day Shift)**: 12:00 - 20:00
- **L (Late Shift)**: 18:00 - 02:00 (next day)


### Installation if you want to be fancy

1. Clone the repository:
   ```bash
   git clone https://github.com/Rafizqi64/ShiftScheduleNXT.git
   
