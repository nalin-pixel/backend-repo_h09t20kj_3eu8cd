import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone

from database import db, create_document, get_documents
from schemas import Shoe

app = FastAPI(title="Shoe Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Shoe Store Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# -----------------
# Shoe Endpoints
# -----------------

class ShoeCreate(BaseModel):
    name: str
    brand: str
    price: float
    description: Optional[str] = None
    images: List[str] = []
    colors: List[str] = []
    sizes: List[float] = []
    featured: bool = False
    rating: Optional[float] = None
    in_stock: bool = True

@app.get("/api/shoes")
def list_shoes(brand: Optional[str] = None, featured: Optional[bool] = None, limit: int = 50):
    filter_dict = {}
    if brand:
        filter_dict["brand"] = brand
    if featured is not None:
        filter_dict["featured"] = featured
    docs = get_documents("shoe", filter_dict, limit)
    for d in docs:
        if "_id" in d:
            d["id"] = str(d["_id"])  # expose as id
            del d["_id"]
    return {"items": docs}

@app.post("/api/shoes", status_code=201)
def create_shoe(payload: ShoeCreate):
    shoe = Shoe(**payload.model_dump())
    inserted_id = create_document("shoe", shoe)
    return {"id": inserted_id}

@app.get("/api/brands")
def list_brands():
    brands = db["shoe"].distinct("brand") if db is not None else []
    return {"items": brands}

@app.post("/api/seed")
def seed_demo_data():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    count = db["shoe"].count_documents({})
    if count > 0:
        return {"message": "Already seeded", "count": count}

    now = datetime.now(timezone.utc)
    demo_items = [
        {
            "name": "Air Zoom Bolt",
            "brand": "Nike",
            "price": 139.99,
            "description": "Responsive cushioning with a sleek, breathable upper.",
            "images": [
                "https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1200&auto=format&fit=crop",
            ],
            "colors": ["Black", "White", "Volt"],
            "sizes": [7, 8, 9, 10, 11, 12],
            "featured": True,
            "rating": 4.6,
            "in_stock": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "UltraRide Blaze",
            "brand": "Puma",
            "price": 119.0,
            "description": "Lightweight ride with energetic foam for daily training.",
            "images": [
                "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?q=80&w=1200&auto=format&fit=crop",
            ],
            "colors": ["Red", "Black"],
            "sizes": [6, 7, 8, 9, 10, 11],
            "featured": True,
            "rating": 4.4,
            "in_stock": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "Air Max Nova",
            "brand": "Nike",
            "price": 159.5,
            "description": "Iconic Air unit comfort remixed for modern lifestyle.",
            "images": [
                "https://images.unsplash.com/photo-1519741497674-611481863552?q=80&w=1200&auto=format&fit=crop",
            ],
            "colors": ["Blue", "White"],
            "sizes": [7, 8, 9, 9.5, 10, 11],
            "featured": False,
            "rating": 4.7,
            "in_stock": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "name": "RS-Fast Flux",
            "brand": "Puma",
            "price": 99.99,
            "description": "Bold DNA with next-gen cushioning and street-ready looks.",
            "images": [
                "https://images.unsplash.com/photo-1542291020-23006e0e2f87?q=80&w=1200&auto=format&fit=crop",
            ],
            "colors": ["White", "Teal"],
            "sizes": [6, 7, 8, 9, 10],
            "featured": False,
            "rating": 4.2,
            "in_stock": True,
            "created_at": now,
            "updated_at": now,
        },
    ]
    res = db["shoe"].insert_many(demo_items)
    return {"inserted": len(res.inserted_ids)}

