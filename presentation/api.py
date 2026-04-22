import os
from fastapi import  APIRouter, HTTPException
from application.dto import CreateOrderDTO, PaymentCallbackDTO
from infrastructure.clients import CatalogClient, PaymentsClient, NotificationServiceClient
from infrastructure.exceptions import OrderNotFoundError, ItemNotFoundError, NotEnoughStockError, CatalogServiceError
from domain.exceptions import InvalidQuantityError, PaymentCreationError
from presentation.schemas.request import CreateOrderRequest, PaymentCallbackRequest
from presentation.schemas.response import OrderResponse
from application.use_cases import GetOrderUseCase, CreateOrderUseCase, CallBackPaymentsUseCase
from infrastructure.db.session import SessionLocal
from infrastructure.unit_of_work import UnitOfWork

router = APIRouter()

@router.get("/api/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
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
            updated_at=res.updated_at
        )
        return response
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    finally:
        session.close()



@router.post("/api/orders", response_model=OrderResponse, status_code=201)
async def create_order(order: CreateOrderRequest):
    order_dto = CreateOrderDTO(user_id=order.user_id,
                               quantity=order.quantity,
                               item_id=order.item_id,
                               idempotency_key=order.idempotency_key)
    catalog = CatalogClient(base_url=os.environ["BASE_URL"],
                            api_key=os.environ["API_KEY"],)
    payments_client = PaymentsClient(base_url=os.environ["BASE_URL"],
                                     api_key=os.environ["API_KEY"],)
    notification_client = NotificationServiceClient(base_url=os.environ["BASE_URL"],
                                                    api_key=os.environ["API_KEY"],)
    session = SessionLocal()
    try:
        uow = UnitOfWork(session)
        use_case = CreateOrderUseCase(catalog=catalog, 
                                      uow=uow, 
                                      payments_client=payments_client, 
                                      notification_client=notification_client
        )
        res = use_case(order_dto)
        response = OrderResponse(
            id=res.id,
            user_id=res.user_id,
            quantity=res.quantity,
            item_id=res.item_id,
            status=res.status.value,
            created_at=res.created_at,
            updated_at=res.updated_at
        )
        return response
    except  ItemNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotEnoughStockError as e:
         raise HTTPException(status_code=400, detail=str(e))
    except CatalogServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except  InvalidQuantityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PaymentCreationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        session.close()


@router.post("/api/orders/payment-callback", status_code=200)
async def payment_callback(callback: PaymentCallbackRequest):
    payment_callback_dto = PaymentCallbackDTO(order_id=callback.order_id,
                                              status=callback.status)
    notification_client = NotificationServiceClient(base_url=os.environ["BASE_URL"],
                                                    api_key=os.environ["API_KEY"],)
    session = SessionLocal()
    try:
        uow = UnitOfWork(session)
        use_case = CallBackPaymentsUseCase(uow=uow, notification_client=notification_client)
        use_case(payment_callback_dto)
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        session.close()

    return {"status": "ok"}



@router.get("/ping")
async def ping():
    return {"status": "ok"}

