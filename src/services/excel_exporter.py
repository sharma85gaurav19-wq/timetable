"""
Excel export service for timetables.
Generates professional Excel files with multiple sheets and formatting.
"""
from typing import List, Dict, Any
from datetime import datetime
import io

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, Color
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.table import Table, TableStyleInfo
except ImportError:
    raise ImportError("Please install openpyxl: pip install openpyxl")

from src.models.timetable_models import Timetable, ScheduledClass, DayOfWeek


class ExcelExportService:
    """
    Service for exporting timetables to professionally formatted Excel files.
    """
    
    def __init__(self):
        self.wb = None
        self.styles = self._define_styles()
    
    def _define_styles(self) -> Dict[str, Dict[str, Any]]:
        """Define reusable cell styles."""
        return {
            'header': {
                'font': Font(bold=True, color="FFFFFF", size=12),
                'fill': PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid"),
                'alignment': Alignment(horizontal='center', vertical='center'),
                'border': Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
            },
            'title': {
                'font': Font(bold=True, size=16, color="1F4E78"),
                'alignment': Alignment(horizontal='center', vertical='center'),
            },
            'subtitle': {
                'font': Font(bold=True, size=12, color="2E75B6"),
                'alignment': Alignment(horizontal='left', vertical='center'),
            },
            'data': {
                'font': Font(size=11),
                'alignment': Alignment(horizontal='left', vertical='center', wrap_text=True),
                'border': Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
            },
            'conflict': {
                'font': Font(size=11, color="9C0006"),
                'fill': PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid"),
                'alignment': Alignment(horizontal='left', vertical='center'),
                'border': Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
            },
            'metadata': {
                'font': Font(size=10, italic=True, color="595959"),
                'alignment': Alignment(horizontal='left', vertical='center'),
            }
        }
    
    def _apply_style(self, cell, style_name: str):
        """Apply a predefined style to a cell."""
        if style_name not in self.styles:
            return
        
        style = self.styles[style_name]
        if 'font' in style:
            cell.font = style['font']
        if 'fill' in style:
            cell.fill = style['fill']
        if 'alignment' in style:
            cell.alignment = style['alignment']
        if 'border' in style:
            cell.border = style['border']
    
    def create_timetable_sheet(self, timetable: Timetable):
        """Create the main timetable sheet."""
        ws = self.wb.active
        ws.title = "Timetable"
        
        # Title
        ws.merge_cells('A1:H1')
        title_cell = ws['A1']
        title_cell.value = f"{timetable.name}"
        self._apply_style(title_cell, 'title')
        ws.row_dimensions[1].height = 30
        
        # Subtitle
        ws.merge_cells('A2:H2')
        subtitle_cell = ws['A2']
        subtitle_cell.value = f"Academic Term: {timetable.academic_term} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self._apply_style(subtitle_cell, 'subtitle')
        ws.row_dimensions[2].height = 20
        
        # Group schedule by day and time
        schedule_data = {}
        for scheduled_class in timetable.scheduled_classes:
            day = scheduled_class.time_slot.day.value
            time = scheduled_class.time_slot.start_time
            
            if day not in schedule_data:
                schedule_data[day] = {}
            if time not in schedule_data[day]:
                schedule_data[day][time] = []
            
            schedule_data[day][time].append(scheduled_class)
        
        # Create summary table
        row = 4
        headers = ["Day", "Time", "Course", "Instructor", "Room", "Students", "Duration", "Status"]
        
        # Write headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            self._apply_style(cell, 'header')
        ws.row_dimensions[row].height = 25
        
        row += 1
        
        # Sort days
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        sorted_days = sorted(schedule_data.keys(), key=lambda x: day_order.index(x) if x in day_order else 99)
        
        # Write data
        for day in sorted_days:
            times = sorted(schedule_data[day].keys())
            for time in times:
                classes = schedule_data[day][time]
                for idx, sc in enumerate(classes):
                    if idx > 0:
                        # Merge cells for same day/time
                        ws.merge_cells(f'A{row}:B{row}')
                    
                    data = [
                        day if idx == 0 else "",
                        time if idx == 0 else "",
                        sc.course.name,
                        sc.instructor,
                        sc.room.name,
                        sc.course.students_count,
                        f"{sc.course.duration}h",
                        sc.status.upper()
                    ]
                    
                    for col, value in enumerate(data, 1):
                        cell = ws.cell(row=row, column=col, value=value)
                        if sc.status == "conflicted":
                            self._apply_style(cell, 'conflict')
                        else:
                            self._apply_style(cell, 'data')
                    
                    ws.row_dimensions[row].height = 20
                    row += 1
        
        # Auto-adjust column widths
        column_widths = [12, 10, 25, 20, 15, 10, 10, 12]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Add table formatting
        table_ref = f"A4:H{row-1}"
        table = Table(displayName="TimetableTable", ref=table_ref)
        style = TableStyleInfo(
            name="TableStyleMedium9",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False
        )
        table.tableStyleInfo = style
        ws.add_table(table)
    
    def create_conflicts_sheet(self, timetable: Timetable):
        """Create a sheet listing all conflicts."""
        ws = self.wb.create_sheet("Conflicts")
        
        # Title
        ws.merge_cells('A1:E1')
        title_cell = ws['A1']
        title_cell.value = "Scheduling Conflicts"
        self._apply_style(title_cell, 'title')
        ws.row_dimensions[1].height = 30
        
        if not timetable.conflicts:
            ws.merge_cells('A3:E3')
            no_conflict_cell = ws['A3']
            no_conflict_cell.value = "✓ No conflicts detected!"
            no_conflict_cell.font = Font(size=14, color="008000", bold=True)
            ws.row_dimensions[3].height = 25
            return
        
        # Headers
        row = 3
        headers = ["Course", "Instructor", "Room", "Time Slot", "Violated Constraints"]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            self._apply_style(cell, 'header')
        ws.row_dimensions[row].height = 25
        
        row += 1
        
        # Write conflicts
        for conflict in timetable.conflicts:
            data = [
                conflict.get("course", "N/A"),
                conflict.get("instructor", "N/A"),
                conflict.get("room", "N/A"),
                conflict.get("time_slot", "N/A"),
                ", ".join(conflict.get("violated_constraints", ["No suitable slot"]))
            ]
            
            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row, column=col, value=value)
                self._apply_style(cell, 'conflict')
            
            ws.row_dimensions[row].height = 20
            row += 1
        
        # Auto-adjust column widths
        column_widths = [25, 20, 15, 20, 40]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
    
    def create_constraints_sheet(self, timetable: Timetable):
        """Create a sheet listing all constraints."""
        ws = self.wb.create_sheet("Constraints")
        
        # Title
        ws.merge_cells('A1:F1')
        title_cell = ws['A1']
        title_cell.value = "Applied Constraints"
        self._apply_style(title_cell, 'title')
        ws.row_dimensions[1].height = 30
        
        # Headers
        row = 3
        headers = ["ID", "Name", "Type", "Priority", "Description", "Active"]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            self._apply_style(cell, 'header')
        ws.row_dimensions[row].height = 25
        
        row += 1
        
        # Write constraints
        for constraint in timetable.constraints:
            data = [
                constraint.id,
                constraint.name,
                constraint.constraint_type,
                constraint.priority,
                constraint.description,
                "Yes" if constraint.is_active else "No"
            ]
            
            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row, column=col, value=value)
                self._apply_style(cell, 'data')
            
            ws.row_dimensions[row].height = 20
            row += 1
        
        # Auto-adjust column widths
        column_widths = [10, 25, 20, 10, 40, 10]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
    
    def create_summary_sheet(self, timetable: Timetable):
        """Create a summary/metadata sheet."""
        ws = self.wb.create_sheet("Summary")
        
        # Title
        ws.merge_cells('A1:B1')
        title_cell = ws['A1']
        title_cell.value = "Timetable Summary"
        self._apply_style(title_cell, 'title')
        ws.row_dimensions[1].height = 30
        
        # Metadata
        row = 3
        metadata_items = [
            ("Timetable ID:", timetable.id),
            ("Name:", timetable.name),
            ("Academic Term:", timetable.academic_term),
            ("Total Courses:", timetable.metadata.get("total_courses", 0)),
            ("Total Rooms:", timetable.metadata.get("total_rooms", 0)),
            ("Total Time Slots:", timetable.metadata.get("total_slots", 0)),
            ("Scheduled Classes:", timetable.metadata.get("total_scheduled", 0)),
            ("Conflicts:", timetable.metadata.get("total_conflicts", 0)),
            ("Generated At:", timetable.metadata.get("generated_at", "N/A")),
        ]
        
        for label, value in metadata_items:
            label_cell = ws.cell(row=row, column=1, value=label)
            label_cell.font = Font(bold=True, size=11)
            label_cell.alignment = Alignment(horizontal='right')
            
            value_cell = ws.cell(row=row, column=2, value=value)
            value_cell.font = Font(size=11)
            value_cell.alignment = Alignment(horizontal='left')
            
            ws.row_dimensions[row].height = 18
            row += 1
        
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 40
    
    def export_to_excel(self, timetable: Timetable, filename: str = None) -> bytes:
        """
        Export timetable to Excel file.
        Returns bytes that can be downloaded or saved.
        """
        self.wb = Workbook()
        
        # Create all sheets
        self.create_timetable_sheet(timetable)
        self.create_conflicts_sheet(timetable)
        self.create_constraints_sheet(timetable)
        self.create_summary_sheet(timetable)
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        self.wb.save(buffer)
        buffer.seek(0)
        
        return buffer.getvalue()
    
    def export_to_file(self, timetable: Timetable, filepath: str):
        """
        Export timetable to Excel file and save to disk.
        """
        excel_data = self.export_to_excel(timetable)
        with open(filepath, 'wb') as f:
            f.write(excel_data)
        return filepath
