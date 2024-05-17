from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from bson import ObjectId
from pymongo import MongoClient

# Initialize FastAPI app
app = FastAPI()

# MongoDB client setup
client = MongoClient("mongodb://localhost:27017/")
db = client.property_management


# Models
class Property(BaseModel):
    property_name: str
    address: str
    city: str
    state: str


class UpdateProperty(BaseModel):
    property_id: str
    property_name: str
    address: str
    city: str
    state: str


def property_helper(property) -> dict:

    return {
        "id": str(property["_id"]),
        "property_name": property["property_name"],
        "address": property["address"],
        "city": property["city"],
        "state": property["state"]
    }


@app.post("/create_new_property", response_model=List[dict])
async def create_new_property(property: Property):
    property_dict = property.dict()
    db.properties.insert_one(property_dict)
    properties = [property_helper(prop) for prop in db.properties.find()]
    return properties


@app.get("/fetch_property_details", response_model=List[dict])
async def fetch_property_details(city: str):
    properties = [property_helper(prop) for prop in db.properties.find({"city": city})]
    if not properties:
        raise HTTPException(status_code=404, detail="No properties found for this city")
    return properties


@app.put("/update_property_details", response_model=List[dict])
async def update_property_details(update_property: UpdateProperty):
    property_id = update_property.property_id
    if not ObjectId.is_valid(property_id):
        raise HTTPException(status_code=400, detail="Invalid property ID")
    updated_data = update_property.dict()
    del updated_data["property_id"]
    result = db.properties.update_one({"_id": ObjectId(property_id)}, {"$set": updated_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Property not found")
    properties = [property_helper(prop) for prop in db.properties.find()]
    return properties


@app.get("/find_cities_by_state", response_model=List[str])
async def find_cities_by_state(state: str):
    cities = db.properties.distinct("city", {"state": state})
    if not cities:
        raise HTTPException(status_code=404, detail="No cities found for this state")
    return cities


@app.get("/find_similar_properties", response_model=List[dict])
async def find_similar_properties(property_id: str):
    if not ObjectId.is_valid(property_id):
        raise HTTPException(status_code=400, detail="Invalid property ID")
    property = db.properties.find_one({"_id": ObjectId(property_id)})
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    city = property["city"]
    properties = [property_helper(prop) for prop in db.properties.find({"city": city})]
    return properties


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)
