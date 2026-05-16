"""
Data models for the timetable scheduling system.
These models represent the core entities used in timetable generation.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class DayOfWeek(Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


@dataclass
class Course:
    """Represents a course/subject to be scheduled."""
    id: str
    name: str
    instructor: str
    duration: int  # in hours
    students_count: int
    required_room_type: Optional[str] = None
    preferred_days: List[DayOfWeek] = field(default_factory=list)
    unavailable_times: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.preferred_days, list) and len(self.preferred_days) > 0:
            if not isinstance(self.preferred_days[0], DayOfWeek):
                self.preferred_days = [DayOfWeek(d) if isinstance(d, str) else d for d in self.preferred_days]


@dataclass
class Room:
    """Represents a classroom or venue."""
    id: str
    name: str
    capacity: int
    room_type: str = "General"  # General, Lab, Auditorium, etc.
    available_days: List[DayOfWeek] = field(default_factory=lambda: list(DayOfWeek))
    unavailable_times: List[str] = field(default_factory=list)


@dataclass
class TimeSlot:
    """Represents a time slot in the schedule."""
    day: DayOfWeek
    start_time: str
    end_time: str
    
    def __str__(self):
        return f"{self.day.value} {self.start_time}-{self.end_time}"


@dataclass
class Constraint:
    """Represents a scheduling constraint (term/condition)."""
    id: str
    name: str
    description: str
    constraint_type: str  # hard, soft, preference
    priority: int = 1  # 1-10, higher is more important
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


@dataclass
class ScheduledClass:
    """Represents a scheduled class session."""
    course: Course
    room: Room
    time_slot: TimeSlot
    instructor: str
    status: str = "scheduled"  # scheduled, conflicted, tentative


@dataclass
class Timetable:
    """Represents a complete timetable/schedule."""
    id: str
    name: str
    academic_term: str
    scheduled_classes: List[ScheduledClass] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_class(self, scheduled_class: ScheduledClass):
        self.scheduled_classes.append(scheduled_class)
    
    def add_constraint(self, constraint: Constraint):
        self.constraints.append(constraint)
    
    def get_conflicts(self) -> List[Dict[str, Any]]:
        return self.conflicts
