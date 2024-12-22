from pydantic import BaseModel
from typing import List, Optional


class AdditionProduct(BaseModel):
    id: str
    amount: int
    title: str
    price: float


class Product(BaseModel):
    id: str
    amount: int
    title: str
    price: float
    additions: Optional[List[AdditionProduct]] = []


class CustomerInfo(BaseModel):
    customerName: str
    customerEmail: str
    customerPhone: str


class Delivery(BaseModel):
    id: str
    address: Optional[str] = None
    flat: Optional[str] = None
    floor: Optional[str] = None
    porch: Optional[str] = None
    price: Optional[int] = None
    doorCode: Optional[str] = None
    type: str
    pickupCode: Optional[str] = None


class Place(BaseModel):
    id: str = None
    title: str


class OrderMessage(BaseModel):
    id: str
    comment: Optional[str] = None
    personsCount: int
    totalCost: float
    readyTime: str
    createdAt: str
    customerInfo: CustomerInfo
    delivery: Delivery
    products: List[Product]
    order_link: str
    order_cancel: str
    order_approve: str
    order_completed: str
    places: Place
    orderNumber: int
    status: str


class SendChatRequest(BaseModel):
    chat_id: int
    message: OrderMessage


class EditChatRequest(BaseModel):
    chat_id: int
    message_id: int
    new_text: OrderMessage


class InputData(BaseModel):
    phone_number: str
    user_id: int
