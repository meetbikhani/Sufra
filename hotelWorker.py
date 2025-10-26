from typing import Annotated, TypedDict, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import requests

# MongoDB Configuration
MONGODB_URI = "Enter your MongoDB URI here"
DATABASE_NAME = "food_waste_db"
COLLECTION_NAME = "food_items"

try:
    print("🔌 Connecting to MongoDB...")
    mongo_client = MongoClient(MONGODB_URI)
    mongo_client.admin.command('ping')
    print("✓ Successfully connected to MongoDB!")
    
    db = mongo_client[DATABASE_NAME]
    food_collection = db[COLLECTION_NAME]
    
    food_collection.create_index("hotel_name")
    food_collection.create_index("price")
    food_collection.create_index("food_name")
    food_collection.create_index("is_available")
    food_collection.create_index("created_at")
    
    food_collection.create_index([("location", "2dsphere")])
    
    print(f"✓ Using database: {DATABASE_NAME}, collection: {COLLECTION_NAME}")
    print(f"✓ Geospatial indexing enabled for location-based searches")
    
except ConnectionFailure as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    print("Please make sure MongoDB is running and accessible.")
    exit(1)

# Simple in-memory conversation storage
conversation_memory = []


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_type: str  # "hotel" or "worker"

GOOGLE_GEOLOCATION_API_KEY = "your_google_api_key_here"

@tool
def get_location() -> str:
    """Get the current location coordinates of the user (hotel or worker)."""
    print("🔧 [TOOL] get_location() called")
    
    try:
        url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={GOOGLE_GEOLOCATION_API_KEY}"
        
        payload = {
            "considerIp": True
        }
        
        response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            location = data.get('location', {})
            lat = location.get('lat')
            lng = location.get('lng')
            accuracy = data.get('accuracy', 'Unknown')
            
            if lat and lng:
                coordinates = f"{lat},{lng}"
                print(f"   ✓ Retrieved coordinates: {coordinates}")
                print(f"   📍 Accuracy: {accuracy} meters")
                return coordinates
            else:
                print("   ⚠️ Could not get coordinates from API")
                return "error - coordinates not found"
        else:
            print(f"   ⚠️ API returned status code: {response.status_code}")
            return "error - coordinates not found"  
            
    except Exception as e:
        print(f"   ❌ Error getting location: {e}")
        return "error - coordinates not found"  


@tool
def store_food_in_db(hotel_name: str, food_name: str, price: float, quantity: int, hotel_location: str) -> str:
    """Store leftover food information in the MongoDB database.
    
    Args:
        hotel_name: Name of the hotel
        food_name: Name/description of the food item
        price: Price of the food
        quantity: Quantity available (e.g., "5", "2")
        hotel_location: Location coordinates of the hotel (format: "latitude,longitude")
    """
    print("🔧 [TOOL] store_food_in_db() called")
    print(f"   📝 Hotel: {hotel_name}")
    print(f"   📝 Food: {food_name}")
    print(f"   📝 Price: ${price}")
    print(f"   📝 Quantity: {quantity}")
    print(f"   📝 Location: {hotel_location}")
    
    try:
        lat, lon = map(float, hotel_location.split(','))
        
        document = {
            "hotel_name": hotel_name,
            "food_name": food_name,
            "price": float(price),  
            "quantity": int(quantity),
            "location": {
                "type": "Point",
                "coordinates": [lon, lat]  
            },
            "hotel_location": hotel_location,  
            "timestamp": datetime.now(),
            "created_at": datetime.now(),
            "is_available": True,
            "status": "active"
        }
        
        # Insert into MongoDB
        result = food_collection.insert_one(document)
        total_items = food_collection.count_documents({"is_available": True})
        
        print(f"   ✓ Successfully stored in MongoDB")
        print(f"   ✓ Document ID: {result.inserted_id}")
        print(f"   ✓ Total active items in database: {total_items}")
        
        return f"✓ Stored: {food_name} (${price}) from {hotel_name} at location {hotel_location}"
        
    except ValueError as e:
        print(f"   ❌ Error parsing location: {e}")
        return f"❌ Error: Invalid location format. Please use 'latitude,longitude'"
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return f"❌ Error storing food in database: {str(e)}"


@tool
def get_available_food(max_price: float, item_name: str = None, max_distance_km: float = None, user_location: str = None) -> str:
    """Get all available food within budget and distance, optionally filtered by item name, sorted by price (lowest to highest).
    
    Args:
        max_price: Maximum price worker is willing to pay
        item_name: Optional - specific food item name to search for (e.g., "pizza", "chicken", "pasta")
        max_distance_km: Optional - maximum distance in kilometers from user location
        user_location: Optional - user's coordinates in format "latitude,longitude" (required if max_distance_km is provided)
    """
    print("🔧 [TOOL] get_available_food() called")
    print(f"   📝 Max Price: ${max_price}")
    print(f"   📝 Item Name: {item_name if item_name else 'Any'}")
    print(f"   📝 Max Distance: {max_distance_km if max_distance_km else 'Any'} km")
    print(f"   📝 User Location: {user_location if user_location else 'Not provided'}")
    
    try:
        query = {
            "is_available": True,
            "price": {"$lte": max_price}
        }
        
        if item_name:
            query["food_name"] = {"$regex": item_name, "$options": "i"}
            print(f"   🔍 Filtering by item name: {item_name}")
        
        total_items = food_collection.count_documents({"is_available": True})
        if total_items == 0:
            print("   ⚠️ Database is empty")
            return "Sorry, no food available right now. Please check back later."
        
        print(f"   🔍 Searching in {total_items} total available items...")
        
        if max_distance_km and user_location:
            try:
                lat, lon = map(float, user_location.split(','))
                max_distance_meters = max_distance_km * 1000  
                
                query["location"] = {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]  
                        },
                        "$maxDistance": max_distance_meters
                    }
                }
                print(f"   🔍 Using geospatial query for {max_distance_km}km radius")
                
                pipeline = [
                    {
                        "$geoNear": {
                            "near": {
                                "type": "Point",
                                "coordinates": [lon, lat]
                            },
                            "distanceField": "distance",
                            "maxDistance": max_distance_meters,
                            "spherical": True
                        }
                    },
                    {
                        "$match": {
                            "is_available": True,
                            "price": {"$lte": max_price}
                        }
                    }
                ]
                
                if item_name:
                    pipeline[1]["$match"]["food_name"] = {"$regex": item_name, "$options": "i"}
                
                affordable_foods = list(food_collection.aggregate(pipeline))
                
                for food in affordable_foods:
                    food["distance_km"] = round(food["distance"] / 1000, 2)
                
                print(f"   ✓ Found {len(affordable_foods)} items within {max_distance_km}km")
                
            except ValueError as e:
                print(f"   ❌ Error parsing user location: {e}")
                return "❌ Error: Invalid location format. Please try again."
        else:
            affordable_foods = list(food_collection.find(query).sort("price", 1))  
            print(f"   ✓ Found {len(affordable_foods)} items matching criteria")
        
        if not affordable_foods:
            print("   ⚠️ No items found matching criteria")
            if item_name:
                return f"No {item_name} found under ${max_price}" + (f" within {max_distance_km}km" if max_distance_km else "") + ". Try adjusting your search criteria."
            else:
                return f"No food found under ${max_price}" + (f" within {max_distance_km}km" if max_distance_km else "") + ". Try adjusting your search criteria."
        
        if max_distance_km and user_location:
            print(f"   📊 Sorted by distance (nearest first)")
        else:
            print(f"   📊 Sorted by price (cheapest first)")
        
        search_criteria = f"{item_name} " if item_name else ""
        distance_criteria = f"within {max_distance_km}km " if max_distance_km else ""
        result = f"Found {len(affordable_foods)} {search_criteria}option(s) {distance_criteria}under ${max_price}:\n\n"
        
        for i, food in enumerate(affordable_foods, 1):
            result += f"{i}. {food['food_name']}\n"
            result += f"   🏨 Hotel: {food['hotel_name']}\n"
            result += f"   💰 Price: ${food['price']}\n"
            result += f"   📦 Quantity: {food['quantity']}\n"
            result += f"   📍 Location: {food['hotel_location']}\n"
            if "distance_km" in food:
                result += f"   📏 Distance: {food['distance_km']} km\n"
            result += f"   🕐 Posted: {food['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(food['timestamp'], datetime) else food['timestamp']}\n\n"
        
        if max_distance_km and user_location:
            result += f"💡 Nearest option: '{affordable_foods[0]['food_name']}' from {affordable_foods[0]['hotel_name']} at {affordable_foods[0]['distance_km']} km for ${affordable_foods[0]['price']}"
        else:
            result += f"💡 Best deal: '{affordable_foods[0]['food_name']}' from {affordable_foods[0]['hotel_name']} at ${affordable_foods[0]['price']}"
        
        print(f"   ✓ Returning {len(affordable_foods)} results")
        return result
        
    except Exception as e:
        print(f"   ❌ Database query error: {e}")
        return f"❌ Error searching for food: {str(e)}"


@tool
def book_food(hotel_name: str, food_name: str) -> str:
    """Book a food item from a hotel. Reduces quantity by 1 and sets availability to False if quantity reaches 0.
    
    Args:
        hotel_name: Name of the hotel
        food_name: Name of the food item to book
    """
    print("🔧 [TOOL] book_food() called")
    print(f"   📝 Hotel: {hotel_name}")
    print(f"   📝 Food: {food_name}")
    
    try:
        food_item = food_collection.find_one({
            "hotel_name": {"$regex": f"^{hotel_name}$", "$options": "i"},
            "food_name": {"$regex": f"^{food_name}$", "$options": "i"},
            "is_available": True
        })
        
        if not food_item:
            print(f"   ❌ Food item not found or not available")
            return f"❌ Sorry, '{food_name}' from {hotel_name} is not available. It may have been booked already."
        
        current_quantity = food_item['quantity']
        print(f"   📦 Current quantity: {current_quantity}")
        
        new_quantity = current_quantity - 1
        
        update_data = {
            "quantity": new_quantity,
            "last_booked": datetime.now()
        }
        
        if new_quantity <= 0:
            update_data["is_available"] = False
            update_data["status"] = "sold_out"
            print(f"   ⚠️ Quantity reached 0 - marking as unavailable")
        
        result = food_collection.update_one(
            {"_id": food_item["_id"]},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print(f"   ✓ Successfully booked!")
            print(f"   ✓ New quantity: {new_quantity}")
            
            if new_quantity <= 0:
                return f"✓ Successfully booked '{food_name}' from {hotel_name} for ${food_item['price']}!\n🎉 This was the last item available!"
            else:
                return f"✓ Successfully booked '{food_name}' from {hotel_name} for ${food_item['price']}!\n📦 Remaining quantity: {new_quantity}"
        else:
            print(f"   ❌ Failed to update database")
            return f"❌ Failed to book the item. Please try again."
            
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return f"❌ Error booking food: {str(e)}"


def calculate_distance_between_coords(coord1: str, coord2: str) -> float:
    """Calculate distance between two coordinates using Haversine formula.
    
    Args:
        coord1: First coordinate in format "latitude,longitude"
        coord2: Second coordinate in format "latitude,longitude"
    
    Returns:
        Distance in kilometers
    """
    from math import radians, sin, cos, sqrt, atan2
    
    lat1, lon1 = map(float, coord1.split(','))
    lat2, lon2 = map(float, coord2.split(','))
    
    R = 6371.0
    
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    return distance


tools = [get_location, store_food_in_db, get_available_food, book_food]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key="Enter your Google API key here",
).bind_tools(tools)


def model_call(state: AgentState) -> AgentState:
    user_type = state.get("user_type", "unknown")
    
    print(f"\n🤖 [MODEL] Processing message for user_type: {user_type}")
    
    system_prompt = SystemMessage(content=f"""You are a helpful AI assistant for a food waste management system.

CURRENT USER TYPE: {user_type.upper()}

**If user is a HOTEL:**
When a hotel tells you about leftover food, you must ALWAYS follow these steps:
1. Call get_location() first to get their GPS coordinates (format: "latitude,longitude")
2. Extract the following information from their message:
   - hotel_name: The name of the hotel (e.g., "Taj Hotel", "Grand Plaza", "Marriott")
   - food_name: The name or description of the food item
   - price: The price per item/portion (as a number)
   - quantity: How much food is available (e.g., "5", "2", "3") as number
3. Take above details from user strictly, if he doesn't provide them, ask him to repeat
4. Call store_food_in_db() with all the details: hotel_name, food_name, price, quantity, and hotel_location (coordinates from step 1)
5. Confirm the storage with a friendly message to the hotel

Example:
Hotel: "I'm from Taj Hotel. We have 5 pasta portions for $8 each"
You: Call get_location() → get coordinates → Call store_food_in_db("Taj Hotel", "pasta", 8, 5, coordinates) → Confirm

**If user is a WORKER:**
When a worker asks for food, you must ALWAYS follow these steps:

STEP 1 - Check for PRICE:
- If the worker mentioned a price limit (e.g., "under $10", "below $5", "max $7"), note it
- If NO price mentioned, ask politely: "What's your budget? How much are you willing to spend?"
- If they STILL don't provide a price after asking, set max_price to 999999 (show everything)

STEP 2 - Check for ITEM NAME:
- Check if they mentioned a specific food item (e.g., "pizza", "chicken", "pasta", "burger", "sandwich")
- If yes, note the item_name
- If no, leave item_name as None

STEP 3 - Check for DISTANCE:
- Check if they mentioned distance/radius keywords like:
  * "within Xkm", "under Xkm", "X kilometers"
  * "nearby", "near me", "close", "closest"
  * "in my area", "around me"
- If distance mentioned:
  * Extract the number (e.g., "within 5km" → 5)
  * If they say "nearby/close" without number, assume 3km as default
  * Note max_distance_km
- If NO distance mentioned, leave max_distance_km as None

STEP 4 - Get Location (when needed):
- Call get_location() to get worker's GPS coordinates
- You ALWAYS need this, whether they mention distance or not

STEP 5 - Search for Food:
- Call get_available_food() with appropriate parameters:
  * max_price (from STEP 1)
  * item_name (from STEP 2, or None)
  * max_distance_km (from STEP 3, or None)
  * user_location (from STEP 4, only if max_distance_km is provided)

STEP 6 - Present Results:
- Show the results clearly
- If distance search: Results are sorted by nearest first
- If no distance: Results are sorted by cheapest first
- Be friendly and helpful

STEP 7 - Booking (when requested):
- If worker wants to book/order/reserve a specific item:
  * They must provide: hotel name and food name
  * If missing info, ask: "Which food from which hotel would you like to book?"
  * Once you have both, call book_food(hotel_name, food_name)
  * Confirm the booking with price and remaining quantity
- Booking keywords: "book", "order", "reserve", "take", "I want this", "get this", "I'll take"

Examples:
Worker: "Show me food under $10"
You: Call get_location() → Call get_available_food(10, None, None, None) → Present results

Worker: "I want pizza within 5km under $15"
You: Call get_location() → get coordinates → Call get_available_food(15, "pizza", 5, coordinates) → Present results

Worker: "Book the pasta from Taj Hotel"
You: Call book_food("Taj Hotel", "pasta") → Confirm booking with price and quantity

Worker: "I want the chicken from Grand Plaza"
You: Call book_food("Grand Plaza", "chicken") → Confirm booking

Worker: "I'll take the first option"
You: [identify hotel and food from previous results] → Call book_food(hotel_name, food_name) → Confirm

Worker: "I want something nearby"
You: "What's your budget?" → [if they say "$8"] → Call get_location() → get coordinates → Call get_available_food(8, None, 3, coordinates) → Present results

Worker: "Show me chicken"
You: "What's your budget?" → [if they don't answer] → Call get_location() → Call get_available_food(999999, "chicken", None, None) → Present results

Be concise, friendly, and helpful. You are currently helping a {user_type}.""")
    
    all_messages = [system_prompt] + conversation_memory + state["messages"]
    
    print(f"   📤 Sending {len(all_messages)} messages to LLM")
    response = llm.invoke(all_messages)
    print(f"   📥 Received response from LLM")
    
    conversation_memory.extend(state["messages"])
    conversation_memory.append(response)
    
    if len(conversation_memory) > 10:
        del conversation_memory[:len(conversation_memory) - 10]
        print(f"   🗑️ Trimmed conversation memory to last 10 messages")
    
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    print(f"\n🔀 [DECISION] Checking if should continue...")
    
    if not last_message.tool_calls:
        print(f"   ✓ No tool calls found - ending conversation")
        return "end"
    else:
        print(f"   ✓ Tool calls found: {len(last_message.tool_calls)} call(s)")
        for i, tool_call in enumerate(last_message.tool_calls, 1):
            print(f"      {i}. {tool_call['name']}()")
        return "continue"


# Build graph
graph = StateGraph(AgentState)
graph.add_node("our_agent", model_call)
tool_node = ToolNode(tools=tools)
graph.add_node("tools", tool_node)
graph.set_entry_point("our_agent")
graph.add_conditional_edges("our_agent", should_continue, {
    "continue": "tools",
    "end": END
})
graph.add_edge("tools", "our_agent")
app = graph.compile()


def print_stream(stream):
    """Print stream output nicely."""
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()



def hotel_interactive():
    """Interactive mode for hotels to continuously add food."""
    print("\n" + "="*60)
    print("🏨 HOTEL MODE - Interactive Session Started")
    print("="*60)
    print("Instructions:")
    print("- Enter your food details (include hotel name, food, quantity, price)")
    print("- Type 'exit' to quit")
    print("="*60)
    
    while True:
        message = input("\n🏨 Hotel Input: ").strip()
        
        if message.lower() == 'exit':
            print("\n✓ Exiting hotel mode. Goodbye!")
            break
        
        if not message:
            print("⚠️ Please enter some text or type 'exit' to quit")
            continue
        
        print("-" * 60)
        inputs = {
            "messages": [HumanMessage(content=message)],
            "user_type": "hotel"
        }
        print_stream(app.stream(inputs, stream_mode="values"))


def worker_interactive():
    """Interactive mode for workers to continuously search for food."""
    print("\n" + "="*60)
    print("👷 WORKER MODE - Interactive Session Started")
    print("="*60)
    print("Instructions:")
    print("- Search for food by mentioning your budget, preferences, and location")
    print("- Book food by saying 'book [food] from [hotel]'")
    print("- Type 'exit' to quit")
    print("="*60)
    
    while True:
        message = input("\n👷 Worker Input: ").strip()
        
        if message.lower() == 'exit':
            print("\n✓ Exiting worker mode. Goodbye!")
            break
        
        if not message:
            print("⚠️ Please enter some text or type 'exit' to quit")
            continue
        
        print("-" * 60)
        inputs = {
            "messages": [HumanMessage(content=message)],
            "user_type": "worker"
        }
        print_stream(app.stream(inputs, stream_mode="values"))


def show_database():
    """Show current database contents."""
    print("\n" + "=" * 60)
    print("📊 CURRENT DATABASE")
    print("=" * 60)
    
    # Get all documents from MongoDB
    all_foods = list(food_collection.find())
    
    if all_foods:
        for i, food in enumerate(all_foods, 1):
            print(f"\n{i}. {food['food_name']}")
            print(f"   Hotel: {food['hotel_name']}")
            print(f"   Price: ${food['price']}")
            print(f"   Quantity: {food['quantity']}")
            print(f"   Location: {food['hotel_location']}")
            print(f"   Available: {food['is_available']}")
            print(f"   Status: {food.get('status', 'active')}")
            print(f"   Added: {food['timestamp']}")
            if 'last_booked' in food:
                print(f"   Last Booked: {food['last_booked']}")
            print(f"   MongoDB ID: {food['_id']}")
    else:
        print("No food items in database")
    print("=" * 60)


# ============== MAIN EXECUTION ==============

if __name__ == "__main__":
    
    # ========== CHOOSE ONE MODE ==========
    
    # MODE 1: Interactive Hotel Mode
    hotel_interactive()
    
    # MODE 2: Interactive Worker Mode
    # worker_interactive()
    
    # Close MongoDB connection
    print("\n🔌 Closing MongoDB connection...")
    mongo_client.close()
    print("✓ MongoDB connection closed.")