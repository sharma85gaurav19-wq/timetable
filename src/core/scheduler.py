"""
Scheduling engine that generates timetables based on constraints.
This is the core algorithm module for timetable generation.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import random

from src.models.timetable_models import (
    Course, Room, TimeSlot, Constraint, 
    ScheduledClass, Timetable, DayOfWeek
)


class SchedulingEngine:
    """
    Main scheduling engine that generates timetables.
    Supports custom constraints and terms/conditions.
    """
    
    def __init__(self):
        self.courses: List[Course] = []
        self.rooms: List[Room] = []
        self.constraints: List[Constraint] = []
        self.time_slots: List[TimeSlot] = []
        self.schedule: Dict[str, ScheduledClass] = {}
        
    def set_courses(self, courses: List[Course]):
        """Set the list of courses to schedule."""
        self.courses = courses
        
    def set_rooms(self, rooms: List[Room]):
        """Set the list of available rooms."""
        self.rooms = rooms
        
    def set_constraints(self, constraints: List[Constraint]):
        """Set scheduling constraints."""
        self.constraints = [c for c in constraints if c.is_active]
        # Sort by priority (higher priority first)
        self.constraints.sort(key=lambda x: x.priority, reverse=True)
        
    def set_time_slots(self, time_slots: List[TimeSlot]):
        """Set available time slots."""
        self.time_slots = time_slots
        
    def generate_default_time_slots(
        self, 
        days: List[DayOfWeek],
        start_hour: int = 9,
        end_hour: int = 17,
        slot_duration: int = 1
    ):
        """Generate default time slots."""
        self.time_slots = []
        for day in days:
            for hour in range(start_hour, end_hour, slot_duration):
                start_time = f"{hour:02d}:00"
                end_time = f"{hour + slot_duration:02d}:00"
                self.time_slots.append(TimeSlot(
                    day=day,
                    start_time=start_time,
                    end_time=end_time
                ))
        return self.time_slots
    
    def validate_constraint(self, constraint: Constraint, scheduled_class: ScheduledClass, 
                           existing_schedule: List[ScheduledClass]) -> bool:
        """
        Validate if a scheduled class satisfies a constraint.
        Returns True if constraint is satisfied, False otherwise.
        """
        if constraint.constraint_type == "no_overlap_instructor":
            # Check if instructor has overlapping classes
            for sc in existing_schedule:
                if (sc.instructor == scheduled_class.instructor and 
                    sc.time_slot.day == scheduled_class.time_slot.day and
                    sc.time_slot.start_time == scheduled_class.time_slot.start_time):
                    return False
                    
        elif constraint.constraint_type == "no_overlap_room":
            # Check if room is already booked
            for sc in existing_schedule:
                if (sc.room.id == scheduled_class.room.id and
                    sc.time_slot.day == scheduled_class.time_slot.day and
                    sc.time_slot.start_time == scheduled_class.time_slot.start_time):
                    return False
                    
        elif constraint.constraint_type == "room_capacity":
            # Check if room capacity is sufficient
            if scheduled_class.room.capacity < scheduled_class.course.students_count:
                return False
                
        elif constraint.constraint_type == "room_type_match":
            # Check if room type matches course requirement
            if (scheduled_class.course.required_room_type and 
                scheduled_class.room.room_type != scheduled_class.course.required_room_type):
                return False
                
        elif constraint.constraint_type == "instructor_availability":
            # Check instructor availability
            unavailable = scheduled_class.course.unavailable_times
            time_key = f"{scheduled_class.time_slot.day.value} {scheduled_class.time_slot.start_time}"
            if time_key in unavailable:
                return False
                
        elif constraint.constraint_type == "custom":
            # Custom constraint logic from parameters
            custom_func = constraint.parameters.get("validation_function")
            if custom_func and callable(custom_func):
                return custom_func(scheduled_class, existing_schedule)
                
        return True
    
    def check_all_constraints(self, scheduled_class: ScheduledClass, 
                             existing_schedule: List[ScheduledClass]) -> Tuple[bool, List[str]]:
        """
        Check all active constraints for a scheduled class.
        Returns (is_valid, list_of_violated_constraints)
        """
        violated = []
        for constraint in self.constraints:
            if not self.validate_constraint(constraint, scheduled_class, existing_schedule):
                violated.append(constraint.name)
        
        return len(violated) == 0, violated
    
    def find_best_slot(self, course: Course, existing_schedule: List[ScheduledClass]) -> Optional[Tuple[Room, TimeSlot]]:
        """
        Find the best available room and time slot for a course.
        Uses a greedy approach with constraint checking.
        """
        candidates = []
        
        for room in self.rooms:
            # Skip if room capacity is insufficient
            if room.capacity < course.students_count:
                continue
            
            # Skip if room type doesn't match (if specified)
            if course.required_room_type and room.room_type != course.required_room_type:
                continue
            
            for time_slot in self.time_slots:
                # Check if day is in preferred days (if specified)
                if course.preferred_days and time_slot.day not in course.preferred_days:
                    continue
                
                # Create tentative scheduled class
                scheduled_class = ScheduledClass(
                    course=course,
                    room=room,
                    time_slot=time_slot,
                    instructor=course.instructor
                )
                
                # Check constraints
                is_valid, violated = self.check_all_constraints(scheduled_class, existing_schedule)
                
                if is_valid:
                    candidates.append((room, time_slot, 0))  # 0 violations
                else:
                    # Still consider but with penalty
                    candidates.append((room, time_slot, len(violated)))
        
        if not candidates:
            return None
        
        # Sort by number of violations (prefer 0 violations)
        candidates.sort(key=lambda x: x[2])
        
        # Return best candidate
        best = candidates[0]
        if best[2] == 0:
            return (best[0], best[1])
        else:
            # Return best even with violations if no perfect match
            return (best[0], best[1])
    
    def generate_timetable(self, name: str = "Generated Timetable", 
                          academic_term: str = "Current Term") -> Timetable:
        """
        Generate a complete timetable for all courses.
        """
        timetable = Timetable(
            id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            name=name,
            academic_term=academic_term
        )
        
        # Add constraints to timetable
        for constraint in self.constraints:
            timetable.add_constraint(constraint)
        
        scheduled_classes = []
        conflicts = []
        
        # Sort courses by difficulty (more constraints first)
        sorted_courses = sorted(
            self.courses, 
            key=lambda c: (len(c.unavailable_times), -c.students_count)
        )
        
        for course in sorted_courses:
            # Calculate number of sessions needed
            sessions_needed = course.duration  # Assuming 1 hour per session
            
            for session in range(sessions_needed):
                best_slot = self.find_best_slot(course, scheduled_classes)
                
                if best_slot:
                    room, time_slot = best_slot
                    scheduled_class = ScheduledClass(
                        course=course,
                        room=room,
                        time_slot=time_slot,
                        instructor=course.instructor
                    )
                    
                    # Double-check constraints
                    is_valid, violated = self.check_all_constraints(scheduled_class, scheduled_classes)
                    
                    if not is_valid:
                        conflicts.append({
                            "course": course.name,
                            "instructor": course.instructor,
                            "room": room.name,
                            "time_slot": str(time_slot),
                            "violated_constraints": violated
                        })
                        scheduled_class.status = "conflicted"
                    
                    scheduled_classes.append(scheduled_class)
                    timetable.add_class(scheduled_class)
                else:
                    conflicts.append({
                        "course": course.name,
                        "instructor": course.instructor,
                        "reason": "No suitable slot found"
                    })
        
        timetable.conflicts = conflicts
        timetable.metadata = {
            "total_courses": len(self.courses),
            "total_rooms": len(self.rooms),
            "total_slots": len(self.time_slots),
            "total_scheduled": len(scheduled_classes),
            "total_conflicts": len(conflicts),
            "generated_at": datetime.now().isoformat()
        }
        
        return timetable
    
    def optimize_timetable(self, timetable: Timetable, iterations: int = 100) -> Timetable:
        """
        Optimize an existing timetable by reducing conflicts.
        Uses a simple local search approach.
        """
        # TODO: Implement optimization algorithm
        # For MVP, we'll return the timetable as-is
        return timetable
