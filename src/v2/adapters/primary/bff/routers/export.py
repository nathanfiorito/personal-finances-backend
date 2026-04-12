from datetime import date as _date

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from src.v2.adapters.primary.bff.deps import get_current_user, get_export_csv
from src.v2.domain.use_cases.reports.export_csv import ExportCsvQuery

router = APIRouter(prefix="/api/v2/export", tags=["v2-export"])


@router.get("/csv")
async def export_csv(
    start: _date,
    end: _date,
    _user=Depends(get_current_user),
    use_case=Depends(get_export_csv),
):
    content = await use_case.execute(ExportCsvQuery(start=start, end=end))
    filename = f"expenses_{start}_{end}.csv"
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
