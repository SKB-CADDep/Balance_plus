import io
from typing import Any
import openpyxl
from openpyxl.styles import Font, PatternFill


class ExcelExporter:
    """
    Сервис генерации Excel-отчета по результатам расчёта конденсатора.
    Строго ориентирован на модель CalculationOutput.
    Размещает все данные (матрицы участков и отсосы) на одном листе.
    """

    @staticmethod
    def _format_value(value: Any) -> Any:
        """
        Применяет бизнес-правила округления:
        - Округление до 4-х знаков.
        - Если округление даёт ровно 0.0000, но исходное значение не ноль —
          возвращается полное значение без округления (защита малых величин).
        """
        if isinstance(value, float):
            rounded = round(value, 4)
            if rounded == 0.0 and value != 0.0:
                return value
            return rounded
        return value

    @classmethod
    def export_calculation(cls, calc_output: Any) -> io.BytesIO:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Результаты расчёта"

        header_font = Font(bold=True)
        meta_font = Font(italic=True, color="404040")
        table_header_fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
        warning_font = Font(color="FF0000", italic=True)

        current_row = 1

        # =================================================================
        # 1. ТАБЛИЦЫ РЕЖИМОВ (МАТРИЦЫ УЧАСТКОВ)
        # =================================================================
        tables = getattr(calc_output, "tables",[])
        if tables:
            for idx, table in enumerate(tables, 1):
                ws.cell(row=current_row, column=1, value=f"Таблица {idx} (Участок)").font = header_font
                current_row += 1

                meta = getattr(table, "meta", {})
                if isinstance(meta, dict) and meta:
                    ws.cell(row=current_row, column=1, value="Режим:").font = meta_font
                    current_row += 1
                    for m_key, m_val in meta.items():
                        ws.cell(row=current_row, column=1, value=str(m_key)).font = meta_font
                        ws.cell(row=current_row, column=2, value=cls._format_value(m_val)).font = meta_font
                        current_row += 1

                cols = getattr(table, "columns", [])
                rows = getattr(table, "rows",[])
                values = getattr(table, "values",[])
                warnings = getattr(table, "warnings",[])

                ws.cell(row=current_row, column=1, value="t1 \\ G").font = header_font
                ws.cell(row=current_row, column=1).fill = table_header_fill
                
                for c_idx, col_val in enumerate(cols, 2):
                    cell = ws.cell(row=current_row, column=c_idx, value=cls._format_value(col_val))
                    cell.font = header_font
                    cell.fill = table_header_fill
                current_row += 1

                for r_idx, row_val in enumerate(rows):
                    cell = ws.cell(row=current_row, column=1, value=cls._format_value(row_val))
                    cell.font = header_font
                    cell.fill = table_header_fill
                    
                    if r_idx < len(values):
                        for c_idx, val in enumerate(values[r_idx], 2):
                            ws.cell(row=current_row, column=c_idx, value=cls._format_value(val))
                    current_row += 1
                
                if warnings:
                    ws.cell(row=current_row, column=1, value="Предупреждения:").font = warning_font
                    current_row += 1
                    for w in warnings:
                        ws.cell(row=current_row, column=1, value=str(w)).font = warning_font
                        current_row += 1

                current_row += 2

        # =================================================================
        # 2. ТАБЛИЦА ОТСОСОВ
        # =================================================================
        ejector_results = getattr(calc_output, "ejector_results",[])
        if ejector_results:
            ws.cell(row=current_row, column=1, value="Таблица по отсосам").font = header_font
            current_row += 1

            first_ejector = ejector_results[0]
            first_dict = (
                first_ejector.model_dump() if hasattr(first_ejector, "model_dump") 
                else (first_ejector if isinstance(first_ejector, dict) else vars(first_ejector))
            )
            
            headers = list(first_dict.keys())

            ws.cell(row=current_row, column=1, value="Отсос №").font = header_font
            ws.cell(row=current_row, column=1).fill = table_header_fill
            for c_idx, h in enumerate(headers, 2):
                cell = ws.cell(row=current_row, column=c_idx, value=str(h))
                cell.font = header_font
                cell.fill = table_header_fill
            current_row += 1

            for e_idx, ejector in enumerate(ejector_results, 1):
                e_dict = (
                    ejector.model_dump() if hasattr(ejector, "model_dump") 
                    else (ejector if isinstance(ejector, dict) else vars(ejector))
                )
                ws.cell(row=current_row, column=1, value=e_idx)
                for c_idx, h in enumerate(headers, 2):
                    ws.cell(row=current_row, column=c_idx, value=cls._format_value(e_dict.get(h)))
                current_row += 1

            current_row += 2

        # =================================================================
        # 3. АВТОМАТИЧЕСКАЯ ШИРИНА КОЛОНОК
        # =================================================================
        for col in ws.columns:
            max_length = 0
            column_letter = col[0].column_letter
            for cell in col:
                try:
                    if cell.value is not None:
                        max_length = max(max_length, len(str(cell.value)))
                except Exception:
                    pass
            ws.column_dimensions[column_letter].width = min(max(max_length + 2, 12), 40)

        # Сохранение в поток
        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream