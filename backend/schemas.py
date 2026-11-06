from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


RoomType = Literal["Single", "Double", "Deluxe", "Suite"]
RoomStatus = Literal["Available", "Occupied", "Maintenance"]
BookingStatus = Literal["Confirmed", "Checked-In", "Checked-Out", "Cancelled"]
PaymentMethod = Literal["Cash", "UPI", "Card", "Net Banking"]
PaymentStatus = Literal["Paid", "Pending", "Failed"]
ServiceStatus = Literal["Active", "Inactive"]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    user_id: int
    username: str
    authenticated: bool


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    age: int = Field(ge=1, le=120)
    gender: str = Field(min_length=1, max_length=30)
    phone: str = Field(min_length=3, max_length=30)
    email: EmailStr
    address: str = Field(min_length=1, max_length=250)


class Customer(CustomerCreate):
    customer_id: int

    class Config:
        from_attributes = True


class CustomerResponse(CustomerCreate):
    customer_id: int


class RoomCreate(BaseModel):
    room_number: str = Field(min_length=1, max_length=20)
    room_type: RoomType
    price_per_night: float = Field(gt=0)
    room_status: RoomStatus


class Room(RoomCreate):
    room_id: int


class RoomResponse(RoomCreate):
    room_id: int


class BookingCreate(BaseModel):
    customer_id: int = Field(gt=0)
    room_id: int = Field(gt=0)
    check_in_date: date
    check_out_date: date
    number_of_guests: int = Field(gt=0)
    booking_status: BookingStatus

    @model_validator(mode="after")
    def validate_dates(self):
        if self.check_out_date <= self.check_in_date:
            raise ValueError("check-out date must be after check-in date")
        return self


class BookingResponse(BookingCreate):
    booking_id: int
    customer_name: str
    room_number: str
    room_type: RoomType


class PaymentCreate(BaseModel):
    booking_id: int = Field(gt=0)
    customer_id: int = Field(gt=0)
    amount: float = Field(gt=0)
    payment_method: PaymentMethod
    payment_date: date
    payment_status: PaymentStatus


class PaymentResponse(PaymentCreate):
    payment_id: int
    customer_name: str


class ServiceCreate(BaseModel):
    service_name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)
    description: str | None = None
    service_status: ServiceStatus


class ServiceResponse(ServiceCreate):
    service_id: int


class BookingServiceCreate(BaseModel):
    service_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class BookingServiceResponse(BookingServiceCreate):
    booking_service_id: int
    booking_id: int
    service_name: str
    price: float
    total: float