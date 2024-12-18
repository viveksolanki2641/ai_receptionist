from fastapi import HTTPException
from mongodb import appointments_collection, users_collection

def check_appointment_availability(user_id: str, appointment_date: str, start_time: str, end_time: str) -> bool:
    """
    Check if the user already has an overlapping appointment.
    
    Args:
        user_id (str): The unique identifier of the user.
        appointment_date (str): The date of the appointment.
        start_time (str): The start time of the appointment.
        end_time (str): The end time of the appointment.

    Returns:
        bool: True if there is an overlapping appointment, False otherwise.
    """
    
    # Find an existing appointment that overlaps with the requested time
    overlapping_appointment = appointments_collection.find_one({
        "user_id": user_id,
        "appointment_date": appointment_date,
        "$or": [
            # Check if the start time of the new appointment overlaps with the existing one
            {"start_time": {"$lte": start_time}, "end_time": {"$gte": start_time}},
            # Check if the end time of the new appointment overlaps with the existing one
            {"start_time": {"$lte": end_time}, "end_time": {"$gte": end_time}}
        ]
    })
    
    # If an overlapping appointment is found, return True
    return overlapping_appointment is not None


def create_appointment(user_id: str, appointment_date: str, start_time: str, end_time: str):
    """
    Create a new appointment for the user.

    Args:
        user_id (str): The unique identifier of the user.
        appointment_date (str): The date of the appointment.
        start_time (str): The start time of the appointment.
        end_time (str): The end time of the appointment.

    Raises:
        HTTPException: If the user does not exist or if there is an overlapping appointment.
    """
    
    # Validate if the user exists in the database
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check for overlapping appointments before creating the new one
    if check_appointment_availability(user_id, appointment_date, start_time, end_time):
        raise HTTPException(status_code=400, detail="Overlapping appointment exists")

    # Insert the new appointment into the appointments collection
    appointments_collection.insert_one({
        "user_id": user_id,
        "appointment_date": appointment_date,
        "start_time": start_time,
        "end_time": end_time
    })
