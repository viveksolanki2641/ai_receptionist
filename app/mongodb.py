from pymongo import MongoClient, ASCENDING

# MongoDB connection setup
mongo_client = MongoClient("mongodb://localhost:27017/")

# Database and collections
db = mongo_client["business_database"]
business_collection = db["business_data"]
users_collection = db["users"]
queries_collection = db["queries"]
appointments_collection = db["appointments"]
custom_responses_collection = db["custom_responses"]

def initialize_collections():
    """
    Setup collections with required indexes and sample data.
    
    This function creates indexes for the collections to optimize queries and ensures 
    that the necessary sample data is inserted into the collections if they are empty.
    """
    
    # Create an index for the appointments collection to optimize overlapping queries
    appointments_collection.create_index(
        [("user_id", ASCENDING), 
         ("appointment_date", ASCENDING), 
         ("start_time", ASCENDING), 
         ("end_time", ASCENDING)],
        name="appointment_index"
    )
    
    # Create an index for custom_responses on query_type with a unique constraint
    custom_responses_collection.create_index("query_type", unique=True, name="query_type_index")
    
    # Insert sample custom responses if the collection is empty
    if custom_responses_collection.count_documents({}) == 0:
        custom_responses_collection.insert_many([
            {"query_type": "service_inquiry", "response_template": "We offer {service_name} for ${price}."},
            {"query_type": "operating_hours", "response_template": "Our operating hours are {operating_hours}."},
        ])
    
    print("Indexes created for appointments collection.")

def insert_sample_data_if_empty():
    """
    Insert sample business data into the collection if it's empty.
    
    This function checks if the business data collection is empty and, if so, inserts 
    a predefined set of sample data related to the business services and contact information.
    """
    
    # Sample business data
    sample_data = {
        "business_name": "Tech Solutions",
        "services_offered": [
            {"service_name": "Web Development", "description": "Building modern websites", "price": 500},
            {"service_name": "App Development", "description": "Creating mobile applications", "price": 1000},
            {"service_name": "SEO Optimization", "description": "Improving website rankings", "price": 300}
        ],
        "operating_hours": "Mon-Fri: 9am - 6pm",
        "contact_information": {
            "phone": "123-456-7890",
            "email": "contact@techsolutions.com"
        }
    }

    # Insert sample data if the business collection is empty
    if business_collection.count_documents({}) == 0:
        business_collection.insert_one(sample_data)

# Initialize collections (run once on import)
initialize_collections()

# Export collections for reuse in other parts of the app
__all__ = [
    "business_collection",
    "users_collection",
    "queries_collection",
    "appointments_collection",
    "custom_responses_collection",
]
