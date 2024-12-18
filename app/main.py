from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from mongodb import (
    insert_sample_data_if_empty,
    business_collection,
    users_collection,
    queries_collection,
    appointments_collection,
    custom_responses_collection
)
from chat import generate_answer
from appointments import create_appointment
import os
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import json
from google_calendar import authenticate_google_calendar, check_existing_meetings, schedule_meeting
from translator import convert_language, detected_que_language

# Initialize FastAPI app
app = FastAPI()

# List of allowed origins (adjust based on where the frontend is served from)
origins = [
    "*",  # Allow all origins (for now, adjust as needed for production)
    # "http://localhost:3000",  # Frontend URL if have
    # "http://127.0.0.1:5500",  # Possible other frontend URL
]

# Add CORS middleware to handle cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specific origins
    allow_credentials=True,  # Allows credentials (cookies, etc.)
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Insert sample data if empty
insert_sample_data_if_empty()

# Pydantic models for request and response validation
class Service(BaseModel):
    service_name: str
    description: str
    price: float

class BusinessData(BaseModel):
    business_name: str
    services_offered: List[Service]
    operating_hours: str
    contact_information: Dict[str, str]

class User(BaseModel):
    name: str
    mobile_number: str
    user_id: str

class QueryData(BaseModel):
    user_id: str
    query: str
    answer: str

class Appointment(BaseModel):
    user_id: str
    appointment_date: str
    start_time: str
    end_time: str

# API Endpoints

class ChatRequest(BaseModel):
    user_id: str  # user_id should be a string
    query: str

class ChatResponse(BaseModel):
    answer: str

@app.post("/user", response_model=User)
def create_user(user: User):
    """Create a new user and store the data."""
    users_collection.insert_one(user.dict())
    return user

@app.get("/business", response_model=BusinessData)
def get_business_information():
    """Fetches all business information (name, services, operating hours, and contact)."""
    
    # Retrieve business data
    business_data = business_collection.find_one()
    if not business_data:
        raise HTTPException(status_code=404, detail="Business information not found")
    
    return BusinessData(
        business_name=business_data["business_name"],
        services_offered=business_data["services_offered"],
        operating_hours=business_data["operating_hours"],
        contact_information=business_data["contact_information"]
    )

@app.post("/query/", response_model=ChatResponse)
def process_query(query_data: ChatRequest):
    """
    Process a user's query, fetch previous messages, pass it to OpenAI, and update chat history.
    
    Steps:
    - Retrieve business data and custom responses.
    - Detect query language, translate if needed.
    - Process the query and generate response using OpenAI.
    - Handle appointment booking or conflicts.
    """
    
    # Retrieve business data and custom responses
    business_data = business_collection.find_one()
    custom_responses_documents = custom_responses_collection.find()

    if not business_data:
        raise HTTPException(status_code=404, detail="Business information not found")
    
    current_datetime = datetime.now()
    formatted_current_date = current_datetime.strftime("%Y-%m-%d")
    formatted_current_time = current_datetime.strftime("%H:%M:%S")
    user_question = query_data.query

    # Detect query language and translate if necessary
    detected_language = detected_que_language(user_question)
    if detected_language != "en":
        user_question = convert_language(user_query=user_question, current_language=detected_language, dest_language="en")

    system_prompt = f"""
        You are the AI Receptionist for Tech Solutions company. Your role is to act as an assistant, maintaining a cheerful tone for happy queries and an apologetic tone for complaints. You are responsible for assisting users with information about services and for booking appointments.
        Allow only those questions that are related to being an assistant for Tech Solutions company, focusing on services and appointments.
        Instructions:
        1. **Always respond in JSON format with a single set of brackets only.** 
        - Every response must strictly follow the JSON format. For all queries except confirmed appointments, use the format:
            {{ "answer": "" }}
        - Only use the appointment JSON format for confirmed bookings as described below.
        
        2. **Service Validation:**
        - Only use the service name provided by the user. If the service name is invalid or not in the service details, inform the user politely in the `{{ "answer": "" }}` format.
        - Do not suggest or use random service names.

        3. **Appointment Booking Process:**
        - Collect all necessary details: user name, service name, and appointment date and time.
        - Once all details are collected, explicitly clarify and confirm the following with the user:
            - User name
            - Service name
            - Appointment date
            - Appointment time
        - Use the response format strictly as for confirm:
            {{ "answer": "" }}
        - Only after receiving explicit confirmation from the user, generate the final JSON output in the following format:
            {{
                "user_name": "",
                "service_name": "",
                "appointment_date": "",
                "appointment_time": ""
            }}

        4. **General Queries:**
        - For all general questions, including service information or incomplete appointment details, respond strictly using:
            {{ "answer": "" }}
        
        5. **Appointment Queries:**
        - If the user wants to check an appointment, interpret the query to determine the desired date and time.
        - Use the current date and time: {formatted_current_date}, {formatted_current_time}.
        - Extract the date and time from the user’s query {user_question} and format them as:
            "appointment_date": "YYYY-MM-DD", "appointment_time": "HH:MM:SS".
        - Use the response format:
            {{ "answer": "" }}
        
        6. **Query Type if match:**
        - Whenever you detect a question that matches a custom response type, respond using the pre-defined template from the custom responses collection.
            {{ "answer": "" ,"custom_response_type": ""}}
        
        Always adhere strictly to these guidelines and formats.
    """

    # Construct the business prompt
    prompt = (
        f"Business Name: {business_data['business_name']}\n"
        f"Services Offered:\n" + "\n".join(
            [f"- {service['service_name']}: {service['description']} (Price: ${service['price']})"
             for service in business_data['services_offered']]
        ) + "\n"
        f"Operating Hours: {business_data['operating_hours']}\n"
        f"Contact Info: Phone - {business_data['contact_information']['phone']}, "
        f"Email - {business_data['contact_information']['email']}\n"
    )

    # Generate custom response F-strings
    custom_responses = "\n".join(
        [f"Custom Response for {response['query_type']}: f\"{response['response_template']}\""
         for response in custom_responses_documents]
    )

    # Combine the prompts into a single system prompt
    system_prompt = f"{system_prompt}\n\n{prompt}\n{custom_responses}"
        
    # Fetch previous chat history for the user
    chat_history = queries_collection.find_one({"user_id": query_data.user_id})
    
    if not chat_history:
        # If no previous history exists, initialize a new chat history for the user
        chat_history = {
            "user_id": query_data.user_id,
            "messages": [{"role": "system", "content": system_prompt}]  # Stores user/assistant message pairs
        }
        queries_collection.insert_one(chat_history)

    query_prompt = f"Use answer json for all the queries. If you confirm with the user for appointment, then respond with that JSON.\n\nUser question: {user_question}"
    
    queries_collection.update_one(
        {"user_id": query_data.user_id},
        {"$push": {"messages": {"role": "user", "content": query_prompt}}}
    )
    
    # Fetch updated chat history
    chat_history = queries_collection.find_one({"user_id": query_data.user_id})
    print(chat_history["messages"])
    print(type(chat_history["messages"]))

    # Generate the response using OpenAI
    response = generate_answer(chat_history["messages"], query_prompt)
    print(response)
    response_json = json.loads(response)

    if response_json.get("answer"):
        answer = response_json.get("answer")
        print("Normal answer")
    else:
        try:
            # Parse OpenAI's JSON response for appointment details
            user_name = response_json.get("user_name")
            user_email = "test@gmail.com"  # Replace with actual email retrieval logic
            service_name = response_json.get("service_name")
            appointment_date = response_json.get("appointment_date")
            appointment_time = response_json.get("appointment_time")

            if not appointment_date or not appointment_time:
                raise ValueError("Incomplete appointment details")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse appointment details: {str(e)}")

        # Check for existing appointment conflicts
        existing_appointment = appointments_collection.find_one({
            "appointment_date": appointment_date,
            "$or": [
                {"start_time": {"$lte": appointment_time}, "end_time": {"$gte": appointment_time}}
            ]
        })
        
        calendar_service = authenticate_google_calendar()

        if existing_appointment:
            existing_meetings = check_existing_meetings(calendar_service, appointment_date, appointment_time)
            if existing_meetings:
                return {"answer": f"Conflict detected! Existing meeting at {appointment_date} {appointment_time}. Please choose another time."}

            if existing_appointment["user_id"] == query_data.user_id:
                result = {
                    "query": user_question,
                    "answer": "You already have an appointment at this time. No double booking is required.",
                    "appointment_details": {
                        "user_id": existing_appointment["user_id"],
                        "appointment_date": existing_appointment["appointment_date"],
                        "start_time": existing_appointment["start_time"],
                        "end_time": existing_appointment["end_time"]
                    }
                }
            else:
                appointment_info = {
                    "user_id": existing_appointment["user_id"],
                    "appointment_date": existing_appointment["appointment_date"],
                    "start_time": existing_appointment["start_time"],
                    "end_time": existing_appointment["end_time"]
                }
                result = {
                    "query": user_question,
                    "answer": f"An appointment is already scheduled for {appointment_info['appointment_date']} "
                            f"from {appointment_info['start_time']} to {appointment_info['end_time']}.",
                    "appointment_details": appointment_info
                }

            answer = result['answer']
        else:
            # No conflict; create a new appointment
            new_appointment = {
                "user_id": query_data.user_id,
                "appointment_date": appointment_date,
                "start_time": appointment_time,
                "end_time": (datetime.strptime(appointment_time, "%H:%M:%S") + timedelta(hours=1)).strftime("%H:%M:%S")
            }
            meeting_link = schedule_meeting(calendar_service, user_name, user_email, service_name, appointment_date, appointment_time)

            appointments_collection.insert_one(new_appointment)

            result = {
                "query": user_question,
                "answer": f"Your appointment has been successfully booked for {new_appointment['appointment_date']} "
                        f"from {new_appointment['start_time']} to {new_appointment['end_time']}.",
                "appointment_details": new_appointment
            }
            answer = result['answer']

    # Append the assistant's response to the chat history
    queries_collection.update_one(
        {"user_id": query_data.user_id},
        {"$push": {"messages": {"role": "assistant", "content": answer}}}
    )

    # Translate the answer back to the user's language if needed
    if detected_language != "en":
        answer = convert_language(user_query=answer, current_language="en", dest_language=detected_language)

    return QueryData(user_id=query_data.user_id, query=user_question, answer=answer)


@app.get("/chat_history/{user_id}")
def get_chat_history(user_id: str):
    """
    Retrieve the chat history for a specific user.
    
    Args:
    - user_id (str): The user ID for which to fetch the chat history.
    
    Returns:
    - chat history for the user.
    """
    chat_history = queries_collection.find_one({"user_id": user_id}, {"_id": 0, "messages": 1})
    if not chat_history:
        raise HTTPException(status_code=404, detail="No chat history found for the given user_id")
    return {"user_id": user_id, "messages": chat_history["messages"]}
