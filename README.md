
# AI Receptionist - README

This project, **AI Receptionist**, is a Minimum Viable Product (MVP) designed as an AI-powered assistant for handling customer inquiries and scheduling appointments. The system integrates with Google Calendar for appointment scheduling and uses MongoDB for data storage. Additionally, it supports multiple languages (English, Hindi, and Gujarati) through a translator SDK.

---

## Features
- AI-powered assistant for customer inquiries.
- Appointment booking functionality integrated with Google Calendar.
- MongoDB is used for data storage.
- Multi-language support using a Translation API (currently supporting English, Hindi, and Gujarati).
- FastAPI backend with RESTful APIs to manage user interactions.

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/viveksolanki2641/ai_receptionist.git
cd ai_receptionist
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
- Copy `.env-example` to `.env`:
  ```bash
  cp .env-example .env
  ```
- Update `.env` with appropriate values for your setup.

### 5. Setup MongoDB
- Install MongoDB from [MongoDB Official Website](https://www.mongodb.com/try/download/community).
- Start MongoDB locally

### 6. Setup Google Calendar API
- Visit the [Google Cloud Console](https://console.cloud.google.com/) to create a project.
- Enable the **Google Calendar API** for your project.
- Create credentials for an OAuth 2.0 Client ID and download the `credentials.json` file.
- Save `credentials.json` in the root directory of the project.

For more information, refer to the [Google Calendar API Quickstart Guide](https://developers.google.com/calendar/quickstart/python).

---

## Running the Application
- Navigate to the `app` folder:
  ```bash
  cd app
  ```
- Start the application using Uvicorn:
  ```bash
  uvicorn main:app --reload
  ```

### Access the API Documentation
Once the application is running, you can access the interactive API documentation at:
```
http://127.0.0.1:8000/docs
```

This will provide you with an interactive interface to test the available endpoints.

## File Explanation

- `app/main.py`: The main FastAPI application that initializes the server and defines all the routes/endpoints.
- `app/schemas.py`: Contains Pydantic models for validating request and response bodies.
- `app/chat.py`: Handles logic for processing user queries and interacting with OpenAI's API.
- `app/appointments.py`: Manages the appointment booking process and integration with Google Calendar.
- `app/google_calendar.py`: Contains functions for Google Calendar authentication, checking existing meetings, and scheduling new appointments.
- `app/mongodb.py`: Handles MongoDB connection and manages data across various collections.
- `app/translator.py`: Provides functionality to detect and translate user queries into different languages.
- `.env-example`: Example configuration file for sensitive environment variables (API keys, database URIs, etc.).
- `requirements.txt`: Contains the list of Python dependencies required to run the application.

## MongoDB Collections
There are 5 collections in MongoDB used for storing data:
1. **business_data**: Stores business-related information such as services, operating hours, and contact details.
2. **users**: Stores user-related information (name, user_id, etc.).
3. **queries**: Stores user queries and the respective assistant responses.
4. **appointments**: Stores appointment details for users.
5. **custom_responses**: Stores pre-defined custom responses for frequently asked questions.

## Translation Support
This application uses a translation SDK to support English, Hindi, and Gujarati. If a user queries in any language other than English, the assistant will automatically detect and translate the query to English for processing.

---

## Technologies Used:
- FastAPI (for building the API)
- OpenAI (for generating responses)
- Google Calendar API (for scheduling appointments)
- MongoDB (for data storage)
- Translator API (for multi-language support)
