from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_required as get_current_user
from app.schemas.transaction import (
    BalanceResponse,
    TonPaymentCreateRequest,
    TonPaymentCreateResponse,
    TonPaymentStatusResponse,
    PackageListResponse,
    PackageResponse
)
from app.services.payment_service import PaymentService
from app.models.user import User

router = APIRouter()


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    user: User = Depends(get_current_user)
):
    """Получение баланса пользователя"""
    return BalanceResponse(balance=user.balance)


@router.post("/ton/create", response_model=TonPaymentCreateResponse)
async def create_ton_payment(
    data: TonPaymentCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание TON платежа"""
    try:
        result = PaymentService.create_ton_payment(
            db=db,
            user=user,
            package_id=data.package_id
        )
        return TonPaymentCreateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating payment: {str(e)}")


@router.get("/ton/check/{transaction_id}", response_model=TonPaymentStatusResponse)
async def check_ton_payment(
    transaction_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Проверка статуса TON платежа"""
    try:
        print(f"[Payment Check] Request received: transaction_id={transaction_id}, user_id={user.tg_id}")
        result = await PaymentService.check_ton_payment_status(db, transaction_id, user)
        print(f"[Payment Check] Result: {result}")
        return TonPaymentStatusResponse(**result)
    except Exception as e:
        print(f"[Payment Check] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


@router.get("/packages", response_model=PackageListResponse)
async def get_packages():
    """Получение списка пакетов искр"""
    packages = PaymentService.get_packages()
    return PackageListResponse(
        packages=[
            PackageResponse(
                id=pkg["id"],
                amount=pkg["amount"],
                price=pkg["price"],
                min_ton_amount=str(pkg.get("min_ton_amount_nanotons", 0)),
                original_price=pkg.get("original_price"),
                discount=pkg.get("discount"),
                title=pkg.get("title"),
                description=pkg.get("description")
            )
            for pkg in packages
        ]
    )
