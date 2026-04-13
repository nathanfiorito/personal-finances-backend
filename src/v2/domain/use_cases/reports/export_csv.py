import csv
import io
from dataclasses import dataclass
from datetime import date
from typing import Literal

from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class ExportCsvQuery:
    start: date
    end: date
    transaction_type: Literal["income", "expense"] | None = None


class ExportCsv:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, query: ExportCsvQuery) -> bytes:
        expenses = await self._repo.list_by_period(
            query.start, query.end, query.transaction_type
        )
        output = io.StringIO()
        output.write("\ufeff")  # UTF-8 BOM for Excel compatibility
        writer = csv.writer(output)
        writer.writerow(
            ["date", "amount", "establishment", "category", "description",
             "tax_id", "entry_type", "transaction_type"]
        )
        for expense in expenses:
            writer.writerow([
                expense.date.isoformat(),
                str(expense.amount),
                expense.establishment or "",
                expense.category,
                expense.description or "",
                expense.tax_id or "",
                expense.entry_type,
                expense.transaction_type,
            ])
        return output.getvalue().encode("utf-8")
