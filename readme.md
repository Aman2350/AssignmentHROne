# E-commerce FastAPI Application

A FastAPI-based e-commerce backend application with MongoDB integration, featuring products and orders management.

## Features

- **Products API**: Create and list products with filtering and pagination
- **Orders API**: Create orders and retrieve user-specific orders
- **MongoDB Integration**: Using PyMongo for database operations
- **Automatic Documentation**: FastAPI auto-generated API docs
- **Ready for Deployment**: Configured for Render and Railway platforms

## API Endpoints

### Products
- `POST /products` - Create a new product
- `GET /products` - List products with optional filtering (name, size) and pagination

### Orders
- `POST /orders` - Create a new order
- `GET /orders/{user_id}` - Get orders for a specific user

## Tech Stack

- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database with PyMongo driver
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI server

## Local Development Setup


### Installation

1. **Clone the repository**
```bash
git clone <my repo-url>
cd <application name>
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp .env.example .env
# Edit .env file with your MongoDB connection string
```

5. **Run the application**
```bash
python main.py
# Or using uvicorn directly:
uvicorn main:app --reload
```

6. **Access the application**
- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

## MongoDB Atlas Setup

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/atlas)

Example connection string:
```
mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/ecommerce?retryWrites=true&w=majority
```

## Data Models

### Product
```json
{
  "name": "string",
  "price": "number",
  "sizes": [
    {
      "size": "string",
      "quantity": "number"
    }
  ]
}
```

### Order
```json
{
  "userId": "string",
  "items": [
    {
      "productId": "string",
      "qty": "number"
    }
  ]
}
```

## Database Collections

- **products**: Stores product information
- **orders**: Stores order information with embedded product details





## Support

For issues related to deployment or MongoDB setup, refer to:
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Render Documentation](https://render.com/docs)
