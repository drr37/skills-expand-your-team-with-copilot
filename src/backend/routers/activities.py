"""
Endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional, List

from ..database import activities_collection, teachers_collection

router = APIRouter(
    prefix="/activities",
    tags=["activities"]
)

@router.get("/", response_model=Dict[str, Any])
def get_activities(
    day: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get all activities with their details, with optional filtering by day and time
    
    - day: Filter activities occurring on this day (e.g., 'Monday', 'Tuesday')
    - start_time: Filter activities starting at or after this time (24-hour format, e.g., '14:30')
    - end_time: Filter activities ending at or before this time (24-hour format, e.g., '17:00')
    """
    # Query the database - for mock database, we'll get all and filter manually
    activities = {}
    for activity in activities_collection.find():
        name = activity.pop('_id')
        
        # Apply filters manually for mock database
        include_activity = True
        
        if day and 'schedule_details' in activity:
            if day not in activity['schedule_details'].get('days', []):
                include_activity = False
        
        if start_time and 'schedule_details' in activity:
            if activity['schedule_details'].get('start_time', '') < start_time:
                include_activity = False
        
        if end_time and 'schedule_details' in activity:
            if activity['schedule_details'].get('end_time', '') > end_time:
                include_activity = False
        
        if include_activity:
            activities[name] = activity
    
    return activities

@router.get("/days", response_model=List[str])
def get_available_days() -> List[str]:
    """Get a list of all days that have activities scheduled"""
    # Get unique days across all activities for mock database
    days = set()
    for activity in activities_collection.find():
        if 'schedule_details' in activity and 'days' in activity['schedule_details']:
            days.update(activity['schedule_details']['days'])
    
    return sorted(list(days))

@router.post("/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, teacher_username: Optional[str] = Query(None)):
    """Sign up a student for an activity - requires teacher authentication"""
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")
    
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")
    
    # Get the activity
    activity = activities_collection.find_one({"_id": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400, detail="Already signed up for this activity")

    # Add student to participants
    activity["participants"].append(email)
    activities_collection.update_one(
        {"_id": activity_name},
        {"$set": {"participants": activity["participants"]}}
    )
    
    return {"message": f"Signed up {email} for {activity_name}"}

@router.post("/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, teacher_username: Optional[str] = Query(None)):
    """Remove a student from an activity - requires teacher authentication"""
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")
    
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")
    
    # Get the activity
    activity = activities_collection.find_one({"_id": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400, detail="Not registered for this activity")

    # Remove student from participants
    activity["participants"].remove(email)
    activities_collection.update_one(
        {"_id": activity_name},
        {"$set": {"participants": activity["participants"]}}
    )
    
    return {"message": f"Unregistered {email} from {activity_name}"}