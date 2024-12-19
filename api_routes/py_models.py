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
    additions: list[AdditionProduct]


class CustomerInfo(BaseModel):
    customerName: str
    customerEmail: str
    customerPhone: str


class Place(BaseModel):
    id: str
    logoUrl: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    isDeliveryAvailable: Optional[bool] = None
    isInPlaceAvailable: Optional[bool] = None
    isOnPlaceAvailable: Optional[bool] = None
    isActive: Optional[bool] = None
    geolocation: Optional[str] = None
    city: Optional[str] = None
    schedule: Optional[str] = None
    organization: Optional[str] = None
    organizationId: Optional[str] = None
    info: Optional[str] = None


class Courier(BaseModel):
    name: Optional[str] = None
    car: Optional[str] = None
    carNumber: Optional[str] = None


class Delivery(BaseModel):
    id: str
    address: Optional[str] = None
    flat: Optional[str] = None
    floor: Optional[str] = None
    porch: Optional[str] = None
    price: Optional[int] = 0
    doorCode: Optional[str] = None
    type: str
    pickupCode: Optional[int] = None
    courier: Optional[Courier] = None
    status: Optional[str] = None


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
    paymentUrl: Optional[str] = None
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
