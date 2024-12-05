from pydantic import BaseModel
from typing import List, Optional


class Product(BaseModel):
    id: str
    amount: int
    title: str
    price: float


class CustomerInfo(BaseModel):
    customerName: str
    customerEmail: str
    customerPhone: str


class Delivery(BaseModel):
    id: str
    street: Optional[str] = None
    flat: Optional[str] = None
    floor: Optional[str] = None
    type: str


class OrderMessage(BaseModel):
    id: str
    comment: Optional[str]
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
    orderNumber: int


class SendChatRequest(BaseModel):
    chat_id: int
    message: OrderMessage


class InputData(BaseModel):
    phone_number: str
    user_id: int
