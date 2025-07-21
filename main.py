from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
import pymongo
from pymongo import MongoClient
import os
from datetime import datetime, timezone
import re
from dotenv import load_dotenv
import os


load_dotenv()


# Initialize FastAPI app
app = FastAPI(title="E-commerce API", description="E-commerce Application", version="1.0.0")

# Get environment variables
MONGODB_URL = os.getenv("MONGODB_URL")
PORT = os.getenv("PORT", 8000)  # Optional default value
DB_NAME = os.getenv("DB_NAME", "ecommerce")

# Verify URL exists
if not MONGODB_URL:
    raise Exception("MONGODB_URL is missing from .env file.")

# Setup MongoDB connection
client = MongoClient(MONGODB_URL)
db = client[DB_NAME]  # Uses DB_NAME from .env
products_collection = db.products
orders_collection = db.orders


# Pydantic models for Products
class Size(BaseModel):
    size: str
    quantity: int

class ProductCreate(BaseModel):
    name: str
    price: float
    sizes: List[Size]

class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    # Note: sizes are not included in the list response as per spec

class ProductListResponse(BaseModel):
    data: List[ProductResponse]
    page: dict

# Pydantic models for Orders
class OrderItem(BaseModel):
    productId: str
    qty: int

class OrderCreate(BaseModel):
    userId: str
    items: List[OrderItem]

class OrderResponse(BaseModel):
    id: str

class ProductDetails(BaseModel):
    name: str
    id: str

class OrderItemDetails(BaseModel):
    productDetails: ProductDetails
    qty: int

class OrderDetails(BaseModel):
    id: str
    items: List[OrderItemDetails]
    total: float

class OrderListResponse(BaseModel):
    data: List[OrderDetails]
    page: dict

# Helper functions to convert MongoDB ObjectId to string
def product_helper(product) -> dict:
    return {
        "id": str(product["_id"]),
        "name": product["name"],
        "price": product["price"]
    }

def order_helper(order) -> dict:
    return {
        "id": str(order["_id"]),
        "items": order["items"],
        "total": order["total"]
    }

# Root endpoint
@app.get("/")
async def root():
    return {"message": "E-commerce API is running"}

# *==================== PRODUCTS API ====================

@app.post("/products", status_code=201)
async def create_product(product: ProductCreate):
    """
    Create a new product
    """
    try:
        # Convert pydantic model to dict
        product_dict = product.model_dump()
        
        # Insert product into MongoDB
        result = products_collection.insert_one(product_dict)
        
        # Return the created product ID
        return {"id": str(result.inserted_id)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products", status_code=200)
async def list_products(
    name: Optional[str] = Query(None, description="Product name for partial/regex search"),
    size: Optional[str] = Query(None, description="Filter by size"),
    limit: int = Query(10, ge=1, description="Number of documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip")
):
    """
    List products with optional filtering and pagination
    """
    try:
        # Build query filter
        query_filter = {}
        
        # Name filter (partial/regex search)
        if name:
            query_filter["name"] = {"$regex": name, "$options": "i"}
        
        # Size filter
        if size:
            query_filter["sizes.size"] = size
        
        # Get total count for pagination
        total_count = products_collection.count_documents(query_filter)
        
        # Execute query with pagination
        cursor = products_collection.find(query_filter).sort("_id", 1).skip(offset).limit(limit)
        products = list(cursor)
        
        # Convert products to response format
        product_list = [product_helper(product) for product in products]
        
        # Calculate pagination info
        next_offset = offset + limit if offset + limit < total_count else None
        prev_offset = max(0, offset - limit) if offset > 0 else None
        
        # Build pagination object
        pagination = {
            "next": str(next_offset) if next_offset is not None else None,
            "limit": limit,
            "previous": str(prev_offset) if prev_offset is not None else None
        }
        
        return {
            "data": product_list,
            "page": pagination
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#* ==================== ORDERS API ====================

@app.post("/orders", status_code=201)
async def create_order(order: OrderCreate):
    """
    Create a new order
    """
    try:
        # Validate products exist and calculate total
        total_price = 0.0
        order_items = []
        
        for item in order.items:
            # Find product by ID
            try:
                product_id = ObjectId(item.productId)
            except:
                raise HTTPException(status_code=400, detail=f"Invalid product ID: {item.productId}")
                
            product = products_collection.find_one({"_id": product_id})
            if not product:
                raise HTTPException(status_code=404, detail=f"Product not found: {item.productId}")
            
            # Calculate item total
            item_total = product["price"] * item.qty
            total_price += item_total
            
            # Prepare order item with product details
            order_item = {
                "productDetails": {
                    "name": product["name"],
                    "id": item.productId
                },
                "qty": item.qty
            }
            order_items.append(order_item)
        
        # Create order document
        order_doc = {
            "userId": order.userId,
            "items": order_items,
            "total": total_price,
            "createdAt": datetime.now(timezone.utc)
        }
        
        # Insert order into MongoDB
        result = orders_collection.insert_one(order_doc)
        
        # Return the created order ID
        return {"id": str(result.inserted_id)}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders/{user_id}", status_code=200)
async def get_user_orders(
    user_id: str = Path(..., description="User ID"),
    limit: int = Query(10, ge=1, description="Number of documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip")
):
    """
    Get list of orders for a specific user
    """
    try:
        # Build query filter for user
        query_filter = {"userId": user_id}
        
        # Get total count for pagination
        total_count = orders_collection.count_documents(query_filter)
        
        # Execute query with pagination (sorted by _id)
        cursor = orders_collection.find(query_filter).sort("_id", 1).skip(offset).limit(limit)
        orders = list(cursor)
        
        # Convert orders to response format
        order_list = [order_helper(order) for order in orders]
        
        # Calculate pagination info
        next_offset = offset + limit if offset + limit < total_count else None
        prev_offset = max(0, offset - limit) if offset > 0 else None

        # Build pagination object
        pagination = {
            "next": str(next_offset) if next_offset is not None else None,
            "limit": limit,
            "previous": str(prev_offset) if prev_offset is not None else None
        }
        
        return {
            "data": order_list,
            "page": pagination
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the application
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)