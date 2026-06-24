from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.services.payment_service import PaymentService
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories import PaymentRepository
from app.schemas.payment_schema import PaymentResponse, ProcessPaymentRequest
from libs.common.exceptions import NotFoundError
from libs.common.response import ApiResponse


router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post("/process", response_model=ApiResponse[PaymentResponse])
def process_payment(payload: ProcessPaymentRequest, db: Session = Depends(get_db)):
    payment = PaymentService(db).process_payment(payload)
    return ApiResponse[PaymentResponse].ok(data=PaymentResponse.model_validate(payment, from_attributes=True))


@router.get("/{payment_id}", response_model=ApiResponse[PaymentResponse])
def get_payment(payment_id: UUID, db: Session = Depends(get_db)):
    payment = PaymentRepository(db).get(str(payment_id))
    if not payment:
        raise NotFoundError("Payment not found", code="PAYMENT_NOT_FOUND")
    return ApiResponse[PaymentResponse].ok(data=PaymentResponse.model_validate(payment, from_attributes=True))
