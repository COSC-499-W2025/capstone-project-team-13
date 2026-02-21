from fastapi import APIRouter

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

@router.get("/{id}")
def get_portfolio(id: int):
    return {"portfolio_id": id}

@router.post("/generate")
def generate_portfolio():
    return {"message": "Portfolio generated"}

@router.post("/{id}/edit")
def edit_portfolio(id: int):
    return {"message": f"Portfolio {id} updated"}
