import os
from fastapi import  APIRouter, HTTPException
from application.dto import CreateOrderDTO
from infrastructure.clients import CatalogClient
from infrastructure.exceptions import OrderNotFoundError, ItemNotFoundError, NotEnoughStockError, CatalogServiceError
from domain.exceptions import InvalidQuantityError
from schemas.request import CreateOrderRequest
from schemas.response import OrderResponse
from application.use_cases import GetOrderUseCase, CreateOrderUseCase
from infrastructure.db.session import SessionLocal
from infrastructure.repository import OrderRepository

router = APIRouter()

@router.get("/api/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    session = SessionLocal()

    try:
        repository = OrderRepository(session=session)
        use_case = GetOrderUseCase(repository=repository)
        res = use_case(order_id)
        response = OrderResponse(
            id=res.id,
            user_id=res.user_id,
            quantity=res.quantity,
            item_id=res.item_id,
            status=res.status,
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
    catalog = CatalogClient(catalog_url=os.environ["CATALOG_URL"],
                            api_key=os.environ["API_KEY"],)
    session = SessionLocal()
    try:
        repository = OrderRepository(session=session)
        use_case = CreateOrderUseCase(catalog=catalog, repository=repository)
        res = use_case(order_dto)
        response = OrderResponse(
        id=res.id,
        user_id=res.user_id,
        quantity=res.quantity,
        item_id=res.item_id,
        status=res.status,
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
    
    finally:
        session.close()


@router.get("/ping")
async def ping():
    return {"status": "ok"}

