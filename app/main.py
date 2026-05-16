"""
Streamlit UI for the Timetable Generator.
Provides an interactive interface for creating and managing timetables.
"""
import streamlit as st
from typing import List, Dict, Any
import json
import io

from src.models.timetable_models import (
    Course, Room, Constraint, DayOfWeek, TimeSlot
)
from src.core.scheduler import SchedulingEngine
from src.services.excel_exporter import ExcelExportService


def initialize_session_state():
    """Initialize session state variables."""
    if 'courses' not in st.session_state:
        st.session_state.courses = []
    if 'rooms' not in st.session_state:
        st.session_state.rooms = []
    if 'constraints' not in st.session_state:
        st.session_state.constraints = []
    if 'timetable' not in st.session_state:
        st.session_state.timetable = None
    if 'excel_data' not in st.session_state:
        st.session_state.excel_data = None


def render_sidebar():
    """Render sidebar navigation."""
    st.sidebar.title("📅 Timetable Generator")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio(
        "Navigation",
        ["Home", "Add Courses", "Add Rooms", "Add Constraints", "Generate Timetable", "View/Export"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        f"""
        **Current Status:**
        - Courses: {len(st.session_state.courses)}
        - Rooms: {len(st.session_state.rooms)}
        - Constraints: {len(st.session_state.constraints)}
        """
    )
    
    return menu


def render_home():
    """Render home page."""
    st.title("🎓 Industry-Grade Timetable Generator")
    st.markdown("""
    Welcome to the **Professional Timetable Scheduling System**!
    
    This tool helps educational institutions create optimal timetables based on custom constraints and requirements.
    
    ### Features:
    - ✅ Support for unlimited courses and rooms
    - ✅ Custom constraints (terms & conditions)
    - ✅ Conflict detection and resolution
    - ✅ Professional Excel export with multiple sheets
    - ✅ Priority-based constraint handling
    
    ### Getting Started:
    1. Add your courses using the "Add Courses" tab
    2. Define available rooms in "Add Rooms"
    3. Set up constraints in "Add Constraints"
    4. Generate your timetable
    5. View and export results
    
    ---
    """)
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Courses", len(st.session_state.courses))
    with col2:
        st.metric("Rooms", len(st.session_state.rooms))
    with col3:
        st.metric("Constraints", len(st.session_state.constraints))


def render_add_courses():
    """Render course addition form."""
    st.title("📚 Add Courses")
    st.markdown("Define the courses that need to be scheduled.")
    
    with st.form("course_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            course_id = st.text_input("Course ID*", placeholder="e.g., CS101")
            course_name = st.text_input("Course Name*", placeholder="e.g., Introduction to Programming")
            instructor = st.text_input("Instructor Name*", placeholder="e.g., Dr. John Smith")
            duration = st.number_input("Duration (hours)*", min_value=1, max_value=10, value=2)
        
        with col2:
            students_count = st.number_input("Number of Students*", min_value=1, value=30)
            room_type = st.selectbox("Required Room Type", ["General", "Lab", "Auditorium", "Any"])
            preferred_days = st.multiselect(
                "Preferred Days",
                [day.value for day in DayOfWeek]
            )
        
        unavailable_times = st.text_area(
            "Unavailable Times (optional)",
            placeholder="Enter unavailable times, one per line. Format: 'Day HH:MM' (e.g., Monday 09:00)"
        )
        
        submitted = st.form_submit_button("➕ Add Course", use_container_width=True)
        
        if submitted:
            if not all([course_id, course_name, instructor, duration, students_count]):
                st.error("Please fill in all required fields marked with *")
            else:
                # Parse unavailable times
                unavail_list = [t.strip() for t in unavailable_times.split('\n') if t.strip()]
                
                # Convert preferred days to enum
                pref_days_enum = [DayOfWeek(d) for d in preferred_days]
                
                course = Course(
                    id=course_id,
                    name=course_name,
                    instructor=instructor,
                    duration=duration,
                    students_count=students_count,
                    required_room_type=room_type if room_type != "Any" else None,
                    preferred_days=pref_days_enum,
                    unavailable_times=unavail_list
                )
                
                st.session_state.courses.append(course)
                st.success(f"✅ Course '{course_name}' added successfully!")
    
    # Display existing courses
    if st.session_state.courses:
        st.markdown("---")
        st.subheader(f"Added Courses ({len(st.session_state.courses)})")
        
        for idx, course in enumerate(st.session_state.courses):
            with st.expander(f"{course.id} - {course.name}"):
                st.write(f"**Instructor:** {course.instructor}")
                st.write(f"**Duration:** {course.duration} hours")
                st.write(f"**Students:** {course.students_count}")
                st.write(f"**Room Type:** {course.required_room_type or 'Any'}")
                st.write(f"**Preferred Days:** {', '.join([d.value for d in course.preferred_days]) or 'Any'}")
                
                if st.button("🗑️ Remove", key=f"remove_course_{idx}"):
                    st.session_state.courses.pop(idx)
                    st.rerun()


def render_add_rooms():
    """Render room addition form."""
    st.title("🏫 Add Rooms")
    st.markdown("Define the available rooms/classrooms.")
    
    with st.form("room_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            room_id = st.text_input("Room ID*", placeholder="e.g., R101")
            room_name = st.text_input("Room Name*", placeholder="e.g., Main Classroom A")
            capacity = st.number_input("Capacity*", min_value=1, value=50)
        
        with col2:
            room_type = st.selectbox("Room Type", ["General", "Lab", "Auditorium", "Computer Lab", "Seminar Hall"])
        
        submitted = st.form_submit_button("➕ Add Room", use_container_width=True)
        
        if submitted:
            if not all([room_id, room_name, capacity]):
                st.error("Please fill in all required fields marked with *")
            else:
                room = Room(
                    id=room_id,
                    name=room_name,
                    capacity=capacity,
                    room_type=room_type
                )
                
                st.session_state.rooms.append(room)
                st.success(f"✅ Room '{room_name}' added successfully!")
    
    # Display existing rooms
    if st.session_state.rooms:
        st.markdown("---")
        st.subheader(f"Added Rooms ({len(st.session_state.rooms)})")
        
        for idx, room in enumerate(st.session_state.rooms):
            with st.expander(f"{room.id} - {room.name}"):
                st.write(f"**Capacity:** {room.capacity}")
                st.write(f"**Type:** {room.room_type}")
                
                if st.button("🗑️ Remove", key=f"remove_room_{idx}"):
                    st.session_state.rooms.pop(idx)
                    st.rerun()


def render_add_constraints():
    """Render constraint addition form."""
    st.title("⚙️ Add Constraints")
    st.markdown("""
    Define scheduling constraints (terms & conditions).
    
    **Constraint Types:**
    - **Hard**: Must be satisfied (priority 10)
    - **Soft**: Should be satisfied if possible (priority 5)
    - **Preference**: Nice to have (priority 2)
    """)
    
    constraint_types = {
        "no_overlap_instructor": "No Instructor Overlap",
        "no_overlap_room": "No Room Double-Booking",
        "room_capacity": "Room Capacity Check",
        "room_type_match": "Room Type Matching",
        "instructor_availability": "Instructor Availability",
        "custom": "Custom Constraint"
    }
    
    with st.form("constraint_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            constraint_id = st.text_input("Constraint ID*", placeholder="e.g., C001")
            constraint_name = st.text_input("Constraint Name*", placeholder="e.g., No Morning Classes")
            constraint_type_key = st.selectbox(
                "Constraint Type",
                options=list(constraint_types.keys()),
                format_func=lambda x: constraint_types[x]
            )
        
        with col2:
            priority_level = st.selectbox("Priority Level", ["Hard", "Soft", "Preference"])
            is_active = st.checkbox("Active", value=True)
        
        description = st.text_area("Description*", placeholder="Describe what this constraint enforces...")
        
        submitted = st.form_submit_button("➕ Add Constraint", use_container_width=True)
        
        if submitted:
            if not all([constraint_id, constraint_name, description]):
                st.error("Please fill in all required fields marked with *")
            else:
                priority_map = {"Hard": 10, "Soft": 5, "Preference": 2}
                
                constraint = Constraint(
                    id=constraint_id,
                    name=constraint_name,
                    description=description,
                    constraint_type=constraint_type_key,
                    priority=priority_map[priority_level],
                    is_active=is_active
                )
                
                st.session_state.constraints.append(constraint)
                st.success(f"✅ Constraint '{constraint_name}' added successfully!")
    
    # Display existing constraints
    if st.session_state.constraints:
        st.markdown("---")
        st.subheader(f"Added Constraints ({len(st.session_state.constraints)})")
        
        for idx, constraint in enumerate(st.session_state.constraints):
            priority_badge = "🔴 Hard" if constraint.priority >= 8 else "🟡 Soft" if constraint.priority >= 4 else "🟢 Preference"
            
            with st.expander(f"{constraint.id} - {constraint.name} [{priority_badge}]"):
                st.write(f"**Type:** {constraint.constraint_type}")
                st.write(f"**Priority:** {constraint.priority}/10")
                st.write(f"**Description:** {constraint.description}")
                st.write(f"**Active:** {'Yes' if constraint.is_active else 'No'}")
                
                if st.button("🗑️ Remove", key=f"remove_constraint_{idx}"):
                    st.session_state.constraints.pop(idx)
                    st.rerun()


def render_generate():
    """Render timetable generation page."""
    st.title("🚀 Generate Timetable")
    st.markdown("Configure and generate your timetable.")
    
    # Validation
    if not st.session_state.courses:
        st.warning("⚠️ Please add at least one course before generating.")
        return
    
    if not st.session_state.rooms:
        st.warning("⚠️ Please add at least one room before generating.")
        return
    
    # Configuration
    with st.expander("⚙️ Advanced Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            timetable_name = st.text_input("Timetable Name", value="Academic Timetable 2024")
            academic_term = st.text_input("Academic Term", value="Spring 2024")
        
        with col2:
            start_hour = st.slider("Start Hour", 6, 12, 9)
            end_hour = st.slider("End Hour", 14, 22, 17)
            slot_duration = st.selectbox("Slot Duration", [1, 2], index=0)
        
        working_days = st.multiselect(
            "Working Days",
            [day.value for day in DayOfWeek],
            default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        )
    
    if st.button("🎯 Generate Timetable", type="primary", use_container_width=True):
        with st.spinner("Generating timetable... This may take a moment."):
            try:
                # Initialize engine
                engine = SchedulingEngine()
                
                # Set data
                engine.set_courses(st.session_state.courses)
                engine.set_rooms(st.session_state.rooms)
                engine.set_constraints(st.session_state.constraints)
                
                # Generate time slots
                working_days_enum = [DayOfWeek(d) for d in working_days]
                engine.generate_default_time_slots(
                    days=working_days_enum,
                    start_hour=start_hour,
                    end_hour=end_hour,
                    slot_duration=slot_duration
                )
                
                # Generate timetable
                timetable = engine.generate_timetable(
                    name=timetable_name,
                    academic_term=academic_term
                )
                
                # Export to Excel
                exporter = ExcelExportService()
                excel_data = exporter.export_to_excel(timetable)
                
                # Store in session
                st.session_state.timetable = timetable
                st.session_state.excel_data = excel_data
                
                # Show results
                st.success("✅ Timetable generated successfully!")
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Scheduled Classes", timetable.metadata['total_scheduled'])
                with col2:
                    st.metric("Total Conflicts", timetable.metadata['total_conflicts'])
                with col3:
                    st.metric("Success Rate", 
                             f"{100 - (timetable.metadata['total_conflicts'] / max(timetable.metadata['total_scheduled'], 1) * 100):.1f}%")
                with col4:
                    st.metric("Constraints Applied", len(timetable.constraints))
                
                if timetable.conflicts:
                    st.warning(f"⚠️ {len(timetable.conflicts)} conflict(s) detected. Check the 'View/Export' tab for details.")
                
            except Exception as e:
                st.error(f"❌ Error generating timetable: {str(e)}")


def render_view_export():
    """Render view and export page."""
    st.title("📊 View & Export Timetable")
    
    if not st.session_state.timetable:
        st.info("📝 No timetable generated yet. Please go to 'Generate Timetable' first.")
        return
    
    timetable = st.session_state.timetable
    
    # Display summary
    st.subheader("📋 Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Name:** {timetable.name}")
        st.write(f"**Term:** {timetable.academic_term}")
        st.write(f"**Generated:** {timetable.metadata.get('generated_at', 'N/A')}")
    
    with col2:
        st.write(f"**Courses:** {timetable.metadata.get('total_courses', 0)}")
        st.write(f"**Rooms:** {timetable.metadata.get('total_rooms', 0)}")
        st.write(f"**Scheduled:** {timetable.metadata.get('total_scheduled', 0)}")
    
    # Display schedule
    st.subheader("📅 Schedule Overview")
    
    if timetable.scheduled_classes:
        # Create DataFrame-like display
        schedule_data = []
        for sc in timetable.scheduled_classes:
            schedule_data.append({
                "Day": sc.time_slot.day.value,
                "Time": sc.time_slot.start_time,
                "Course": sc.course.name,
                "Instructor": sc.instructor,
                "Room": sc.room.name,
                "Status": sc.status
            })
        
        st.dataframe(schedule_data, use_container_width=True)
    
    # Display conflicts
    if timetable.conflicts:
        st.subheader("⚠️ Conflicts")
        for conflict in timetable.conflicts:
            with st.expander(f"Conflict: {conflict.get('course', 'Unknown')}"):
                st.write(conflict)
    
    # Export options
    st.subheader("💾 Export Options")
    
    if st.session_state.excel_data:
        st.download_button(
            label="📥 Download Excel File",
            data=st.session_state.excel_data,
            file_name=f"{timetable.name.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.markdown("""
        **Excel file includes:**
        - 📄 **Timetable** - Complete schedule with all classes
        - ⚠️ **Conflicts** - List of any scheduling conflicts
        - ⚙️ **Constraints** - All applied constraints
        - 📊 **Summary** - Metadata and statistics
        """)
    
    # JSON export
    st.markdown("---")
    st.subheader("📄 Alternative Formats")
    
    if st.button("Export as JSON"):
        timetable_dict = {
            "id": timetable.id,
            "name": timetable.name,
            "academic_term": timetable.academic_term,
            "metadata": timetable.metadata,
            "scheduled_classes": [
                {
                    "course": sc.course.name,
                    "instructor": sc.instructor,
                    "room": sc.room.name,
                    "day": sc.time_slot.day.value,
                    "time": sc.time_slot.start_time,
                    "status": sc.status
                }
                for sc in timetable.scheduled_classes
            ],
            "conflicts": timetable.conflicts
        }
        
        json_str = json.dumps(timetable_dict, indent=2)
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"{timetable.name.replace(' ', '_')}.json",
            mime="application/json"
        )


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Timetable Generator",
        page_icon="📅",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    initialize_session_state()
    menu = render_sidebar()
    
    if menu == "Home":
        render_home()
    elif menu == "Add Courses":
        render_add_courses()
    elif menu == "Add Rooms":
        render_add_rooms()
    elif menu == "Add Constraints":
        render_add_constraints()
    elif menu == "Generate Timetable":
        render_generate()
    elif menu == "View/Export":
        render_view_export()


if __name__ == "__main__":
    main()
