import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.routers.deps import get_current_user
from src.services import database

router = APIRouter(prefix="/api/export", tags=["export"])

_CSV_COLUMNS = ["id", "data", "estabelecimento", "descricao", "categoria", "valor", "cnpj", "tipo_entrada", "confianca", "created_at"]


@router.get("/csv")
async def export_csv(
    start: date,
    end: date,
    _user=Depends(get_current_user),
):
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start deve ser menor ou igual a end",
        )

    expenses = await database.get_expenses_by_period(start, end)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(_CSV_COLUMNS)
    for exp in expenses:
        writer.writerow([
            str(exp.id),
            exp.data.isoformat(),
            exp.estabelecimento or "",
            exp.descricao or "",
            exp.categoria,
            str(exp.valor),
            exp.cnpj or "",
            exp.tipo_entrada,
            exp.confianca if exp.confianca is not None else "",
            exp.created_at.isoformat(),
        ])

    output.seek(0)
    filename = f"expenses_{start}_{end}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
