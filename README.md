# Industry-Grade Timetable Generator

A professional timetable scheduling system for educational institutions built with Python and Streamlit.

## Features

- ✅ **Unlimited Courses & Rooms**: Add as many courses and rooms as needed
- ✅ **Custom Constraints**: Define any terms and conditions for scheduling
- ✅ **Conflict Detection**: Automatic detection and reporting of scheduling conflicts
- ✅ **Professional Excel Export**: Multi-sheet Excel files with formatting
- ✅ **Priority-Based Scheduling**: Hard, soft, and preference constraints
- ✅ **Interactive UI**: User-friendly Streamlit interface

## Project Structure

```
/workspace
├── app/                    # Streamlit application
│   └── main.py            # Main UI entry point
├── src/                   # Source code
│   ├── core/              # Core scheduling engine
│   │   └── scheduler.py   # Scheduling algorithm
│   ├── models/            # Data models
│   │   └── timetable_models.py
│   ├── services/          # Business services
│   │   └── excel_exporter.py
│   └── utils/             # Utility functions
├── config/                # Configuration files
├── data/                  # Input data files
├── output/                # Generated outputs
└── tests/                 # Test files
```

## Installation

1. Install dependencies:
```bash
pip install streamlit openpyxl
```

2. Run the application:
```bash
streamlit run app/main.py
```

## Usage

1. **Add Courses**: Define courses with instructors, duration, student count, and preferences
2. **Add Rooms**: Specify available rooms with capacity and type
3. **Add Constraints**: Set up scheduling rules (terms & conditions)
4. **Generate**: Create the timetable using the scheduling engine
5. **Export**: Download professionally formatted Excel file

## Excel Output

The generated Excel file includes:
- **Timetable Sheet**: Complete schedule organized by day and time
- **Conflicts Sheet**: List of any scheduling conflicts
- **Constraints Sheet**: All applied constraints
- **Summary Sheet**: Metadata and statistics

## Constraint Types

- **No Instructor Overlap**: Prevents same instructor teaching multiple classes simultaneously
- **No Room Double-Booking**: Prevents room conflicts
- **Room Capacity**: Ensures room can accommodate students
- **Room Type Matching**: Matches course requirements (Lab, Auditorium, etc.)
- **Instructor Availability**: Respects instructor unavailable times
- **Custom**: Define your own constraint logic

## License

MIT License
