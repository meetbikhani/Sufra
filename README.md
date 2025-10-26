# 🍽️ Sufra - Food Waste Management Platform

> **Bridging surplus food with those who need it most**

An AI-powered platform connecting hotels with surplus food to low-income citizens seeking affordable meals, reducing food waste while addressing food insecurity globally.

---

## 📖 About Sufra

**Sufra** addresses two critical global challenges:
1. **Food Waste**: Hotels, weddings, and celebrations generate large quantities of edible food that are discarded daily
2. **Food Insecurity**: Low-income citizens and daily wage workers struggle to afford regular meals

By leveraging GENAI (LangChain, LangGraph) reasoning and geolocation, Sufra creates a transparent, real-time link between food surplus and those who need it most.

### 🎯 Our Mission
Promote zero food waste, ensure access to affordable meals, and support the UN Sustainable Development Goals.

---

## 👥 Target Users

- **Low-income citizens** who struggle to afford regular meals
- **Daily wage workers** who often skip meals due to high food prices
- **Hotels & Restaurants** with surplus food after service hours
- **NGOs & Community Organizations** tracking and redistributing excess meals

---

## 💡 Problem Statement

### Pain Points:

1. **Massive Food Waste**: Hotels, weddings, and celebrations discard large quantities of edible food daily due to lack of efficient redistribution systems.

2. **No Connection**: No transparent, real-time link between food surplus and those who need it most.

3. **Food Insecurity**: Daily wage workers often skip meals due to high food prices and limited access to affordable options.

### Why It's Urgent:
- ✅ Promotes zero food waste
- ✅ Ensures access to meals at lower prices
- ✅ Supports UN Sustainable Development Goals
- ✅ Creates immediate humanitarian impact
- ✅ Fosters long-term food security

---

## ✨ Features

### 🏨 For Hotels
- Upload surplus food with name, quantity, and price
- Automatic location detection
- Real-time inventory management
- Reduce waste while earning revenue

### 👷 For Workers
- Budget-based food search
- Location filtering (within 5km, 10km, etc.)
- Distance display for each option
- Instant booking with QR code

### 🤖 AI-Powered
- Natural language chat interface
- Smart recommendations based on budget, distance, and preferences
- Context-aware responses
- Multilingual support (future)

---

## 🎬 Demo Story

> **Abdul's Story**: Abdul, a worker in Dubai, often skipped meals to save money for his family in India. Through Sufra, he found surplus hotel meals at low prices. That night, his first warm dinner showed how technology and kindness can nourish hope.

**Watch Demo**: [https://tinyurl.com/mr3auy8r](https://tinyurl.com/mr3auy8r)

---

## 🏗️ System Architecture

**Architecture Diagram**: [View Here](https://tinyurl.com/2dje3d8t)

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Hotels    │────────▶│  AI Agent    │◀────────│   Workers   │
│  (Input)    │         │  (Gemini)    │         │  (Search)   │
└─────────────┘         └──────┬───────┘         └─────────────┘
                               │
                        ┌──────┴──────┐
                        ▼             ▼
                  ┌─────────┐   ┌────────┐
                  │Location │   │MongoDB │
                  │   API   │   │   DB   │
                  └─────────┘   └────────┘
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React & React Native |
| **Backend** | FastAPI + Django + MongoDB |
| **AI Layer** | Gemini (Google) + LangChain + LangGraph |
| **APIs** | Google Maps / Geolocation APIs |
| **Deployment** | AWS |

---

## 🚀 User Flow

**User Flow Diagram**: [View Here](https://tinyurl.com/pye39amd)

### For Hotels:
1. Upload surplus food (name, quantity, price, location)
2. Data stored in MongoDB database
3. Food becomes available for workers

### For Workers:
1. Enter budget and preferences
2. AI fetches GPS location and filters results
3. View ranked recommendations by distance/price
4. Book food and receive QR code for pickup

**Detailed Flow**: [View Diagram](https://tinyurl.com/5n8ae36k)

---

## 🤖 Why AI?

### AI Capabilities:

1. **Advanced Reasoning**: Matches user budget and preferences with nearby food
2. **Natural Language Processing**: Easy, human-like communication
3. **Smart Ranking**: Optimizes by distance, budget, and availability
4. **Multilingual Support**: Accessible worldwide (future)
5. **Real-time Processing**: Instant geolocation and matching

---

## 📦 Prerequisites

- **Python 3.8+**
- **MongoDB** (Local or [MongoDB Atlas](https://www.mongodb.com/cloud/atlas))
- **Google API Key** (Free tier: 1,500 requests/day)

---

## 🚀 Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/sufra-food-waste-management.git
cd sufra-food-waste-management
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**requirements.txt:**
```txt
langchain>=0.1.0
langchain-google-genai>=0.0.6
langgraph>=0.0.20
langchain-core>=0.1.0
pymongo>=4.6.0
requests>=2.31.0
python-dotenv>=1.0.0
```

---

## ⚙️ Configuration

### 1. MongoDB Setup

**MongoDB Atlas (Recommended - Free):**
1. Create account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create free cluster (M0)
3. Get connection string from "Connect" → "Connect your application"

### 2. Google API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key

### 3. Configure Application

Open `main.py` and update:

```python
MONGODB_URI = "your_mongodb_connection_string_here"
GOOGLE_API_KEY = "your_google_api_key_here"
DATABASE_NAME = "food_waste_db"
COLLECTION_NAME = "food_items"
```

---

## 🎮 Usage

### Hotel Mode (Add Food)
```bash
python main.py
```

Uncomment in `main.py`:
```python
hotel_interactive()
```

**Example:**
```
🏨 Hotel Input: I'm from Taj Hotel with 5 pasta portions for $8 each
✓ Stored: pasta ($8) from Taj Hotel, Quantity: 5
```

### Worker Mode (Search & Book)
```bash
python main.py
```

Uncomment in `main.py`:
```python
worker_interactive()
```

**Example:**
```
👷 Worker Input: Show me food under $10 within 5km

Found 2 options under $10:
1. pasta - Taj Hotel - $8 (2.8 km)
2. chicken - Grand Plaza - $7 (2.1 km)

👷 Worker Input: Book pasta from Taj Hotel
✓ Successfully booked 'pasta' for $8! Remaining: 4
```

---

## 🛠️ Troubleshooting

**MongoDB Connection Error:**
- Check connection string is correct
- Verify IP whitelist in MongoDB Atlas

**Google API Key Error:**
- Verify API key has no spaces
- Check "Generative Language API" is enabled

**Location API 403 Error:**
- Code automatically uses free fallback APIs (ipapi.co, ip-api.com)

**Module Not Found:**
```bash
source venv/bin/activate  # Activate virtual environment first
pip install -r requirements.txt
```

---

## 📈 Future Scope

- ✅ Validation & rating system for authenticity
- ✅ Multilingual support for global accessibility
- ✅ NGO partnerships for community redistribution
- ✅ Payment integration and mobile app
- ✅ Real-time notifications and analytics dashboard

---

## 🌍 Impact

- **Environmental**: Reduces food waste and carbon footprint
- **Social**: Provides affordable meals to vulnerable communities
- **Economic**: Revenue for hotels, cost savings for workers

---

**Made with ❤️ to reduce food waste and nourish hope**
