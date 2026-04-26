from fastapi import APIRouter, Depends, HTTPException

from application.dto import CreateOrderDTO, PaymentCallbackDTO
from application.use_cases import (
    CallBackPaymentsUseCase,
    CreateOrderUseCase,
    GetOrderUseCase,
)
from domain.exceptions import InvalidQuantityError, PaymentCreationError
from infrastructure.config import settings
from infrastructure.db.session import SessionLocal
from infrastructure.exceptions import (
    CatalogServiceError,
    ItemNotFoundError,
    NotEnoughStockError,
    OrderNotFoundError,
)
from infrastructure.unit_of_work import UnitOfWork
from presentation.dependencies import (
    get_catalog_client,
    get_notification_client,
    get_payments_client,
)
from presentation.schemas.request import CreateOrderRequest, PaymentCallbackRequest
from presentation.schemas.response import OrderResponse

router = APIRouter()


@router.get("/api/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str):
    session = SessionLocal()

    try:
        uow = UnitOfWork(session)
        use_case = GetOrderUseCase(uow=uow)
        res = use_case(order_id)
        response = OrderResponse(
            id=res.id,
            user_id=res.user_id,
            quantity=res.quantity,
            item_id=res.item_id,
            status=res.status.value,
            created_at=res.created_at,
            updated_at=res.updated_at,
        )
        return response
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    finally:
        session.close()


@router.post("/api/orders", response_model=OrderResponse, status_code=201)
def create_order(
    order: CreateOrderRequest,
    catalog=Depends(get_catalog_client),
    payments_client=Depends(get_payments_client),
    notification_client=Depends(get_notification_client),
):
    order_dto = CreateOrderDTO(
        user_id=order.user_id,
        quantity=order.quantity,
        item_id=order.item_id,
        idempotency_key=order.idempotency_key,
    )
    callback_url = settings.CALLBACK_URL
    session = SessionLocal()
    try:
        uow = UnitOfWork(session)
        use_case = CreateOrderUseCase(
            catalog=catalog,
            uow=uow,
            payments_client=payments_client,
            notification_client=notification_client,
            callback_url=callback_url,
        )
        res = use_case(order_dto)
        response = OrderResponse(
            id=res.id,
            user_id=res.user_id,
            quantity=res.quantity,
            item_id=res.item_id,
            status=res.status.value,
            created_at=res.created_at,
            updated_at=res.updated_at,
        )
        return response
    except ItemNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotEnoughStockError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CatalogServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except InvalidQuantityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PaymentCreationError as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        session.close()


@router.post("/api/orders/payment-callback", status_code=200)
def payment_callback(
    callback: PaymentCallbackRequest,
    notification_client=Depends(get_notification_client),
):
    payment_callback_dto = PaymentCallbackDTO(
        order_id=callback.order_id, status=callback.status
    )
    session = SessionLocal()
    try:
        uow = UnitOfWork(session)
        use_case = CallBackPaymentsUseCase(
            uow=uow, notification_client=notification_client
        )
        use_case(payment_callback_dto)
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        session.close()

    return {"status": "ok"}


@router.get("/ping")
def ping():
    return {"status": "ok"}
