import logging
from fastapi import APIRouter, status, HTTPException
from app.schemas.pydantic import OrderPayloadSchema, OrderResponseSchema
import sys
sys.path.insert(0, '..')
from models.order import Order
from models.user import User
from models.product import Product
from app.send import QueueService
import json
from tortoise.contrib.pydantic import pydantic_queryset_creator


router = APIRouter(prefix="/api/orders")
log = logging.getLogger("uvicorn")


''' 
Endpoint to create an order

Args:
    path: The API call URL path
    status_code: The expected HTTP status code for the response

Returns:
    A list of orders
'''
@router.post(
    path = "/", 
    response_model = OrderResponseSchema, 
    status_code = status.HTTP_201_CREATED
)
async def create_order(payload: OrderPayloadSchema) -> OrderResponseSchema:
    
    # log.info(f"Creating order with payload: {payload}")

    user = await User.get_or_none(id=payload.user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")
    
    product = await Product.get_or_none(id=payload.product_id)
   
    if not product:
        raise HTTPException(status_code=404, detail="Product not found!")

    order: OrderResponseSchema = await Order.create(
        product=product,
        product_quantity=payload.product_quantity,
        user=user)
    
    if not order:
        raise HTTPException(status_code=500, detail="Order could not be created!")
    
    orders_dict = json.dumps(dict(order), indent=4, sort_keys=False, default=str)

    log.info("ORDER placed: " + orders_dict)

    queue_service = QueueService()
    await queue_service.sendMessage(orders_dict)

    return order


''' 
List all orders

Args:
    path: The API call URL path
    status_code: The expected HTTP status code for the response

Returns:
    a list of orders
'''
@router.get(
    path = "/all", 
    response_model = list[OrderResponseSchema], 
    status_code = status.HTTP_200_OK
)
async def list_orders() -> list[OrderResponseSchema]:
    
    orders = await Order.all()

    if not orders:
        raise HTTPException(status_code=404, detail="Order not found!")
    
    return orders