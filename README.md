# thank u, NXT – *Free Time Calendar* 🕒

**Hey beautiful people!**  
Tired of shift work getting in the way of hanging out with your favorite operators?  
This little Python + Streamlit app helps you **find shared free time** in or across rotating shifts.

Whether you're trying to plan a group dinner, some well-earned parties, or just need to vibe out with your crew — this tool finds when **you’re all actually free**.

---

## 💡 What Does It Do?

- ⌛ **Compares shift rotations** (A–F) based on a rolling 6-week schedule
- 🛌 **Considers sleep hours** for Night, Late, and Early shifts
- 🔍 **Highlights only social-friendly hours** (no 4am nonsense here)
- 🗑️ **Displays a calendar** of days, showing when you're all available
- 🎨 **Color-coded shifts** so you can read the table at a glance
- 🗓️ **Shows sleepover possibilities** wherever possible

---

## 👀 Schedule

![Shift Schedule Preview](nxt_shift_schedule.png)

Our full 6-week rotation in living color:

| Code | Name       | Time Range   | Color     |
|------|------------|--------------|-----------|
| E    | Early      | 06:00–14:00  | 🔵 Blue    |
| D    | Day        | 12:00–20:00  | 🟢 Green   |
| L    | Late       | 18:00–02:00* | 🟡 Yellow  |
| N    | Night      | 00:00–08:00  | 🔶 Orange  |

> *Late shifts actually roll over to the next day!  
> ~~such a f@$%ing headache.~~

### 🛋️ Sleep Filters Used

These hours are automatically marked as unavailable ("sleep zones") based on shift type:

| Shift | Sleep Hours (Applied)              |
|-------|------------------------------------|
| N     | 09:00 – 18:00 (before & after)     |
| L     | 03:00 – 12:00 (after)              |
| E     | 22:00 – 04:00 (night before only) |

---

## ✨ How to Run It

1. 📦 Install dependencies:
   ```bash
   pip install streamlit pandas
   ```

2. ▶️ Launch the app:
   ```bash
   streamlit run shift_free_time_week_restructured.py
   ```

3. 🌐 A browser will open — choose how many people to compare and their shift codes. Done!

Or try it deployed at: [thankunxt.streamlit.app](https://thankunxt.streamlit.app)

---

## 📈 How It Works

- ⌚ Uses a predefined 6-week repeating schedule (editable in the code)
- ⏳ Rotates shift weeks based on the selected letter (A-F)
- 🛌 Applies realistic sleep hours so you're not "free" when you should be recovering
- 🔍 Compares everyone's time and finds the shared overlapping free time
- 🗓️ Outputs an easy-to-read, color-coded schedule

---

## 🎨 For You
Cause these shifts are not an excuse to lose contact with your traumabond friends

Made with love, sleep deprivation & logic ♥️

---

Want to suggest improvements or add new features? Pull requests are welcome on GitHub!
