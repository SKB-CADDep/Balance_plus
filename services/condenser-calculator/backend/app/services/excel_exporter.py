import io
from typing import Any
import openpyxl
from openpyxl.styles import Font, PatternFill


class ExcelExporter:
    """
    Сервис генерации Excel (PoC) для результатов расчёта конденсатора.
    Разбирает CalculationOutput и распределяет данные.
    """

    @classmethod
    def export_calculation(cls, calc_output: Any) -> io.BytesIO:
        data = calc_output.model_dump() if hasattr(calc_output, "model_dump") else dict(calc_output)

        wb = openpyxl.Workbook()
        ws_summary = wb.active
        ws_summary.title = "Сводная информация"
        ws_matrices = wb.create_sheet(title="Таблицы результатов")

        # Стили
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        bold_font = Font(bold=True)

        # Заголовки сводной страницы
        for col_num, text in enumerate(["Параметр", "Значение"], 1):
            cell = ws_summary.cell(row=1, column=col_num, value=text)
            cell.font = header_font
            cell.fill = header_fill

        row_sum = 2
        row_mat = 1

        for key, value in data.items():
            # Если данные - это список таблиц (как tables в CalculationOutput)
            if key == "tables" and isinstance(value, list):
                for table in value:
                    # Заголовок таблицы (например, режим)
                    mode_name = table.get("mode", f"Таблица {row_mat}")
                    ws_matrices.cell(row=row_mat, column=1, value=f"Режим: {mode_name}").font = bold_font
                    row_mat += 1

                    rows = table.get("rows",[])
                    if not rows:
                        continue
                    
                    # Заголовки колонок (ключи первого row)
                    headers = list(rows[0].keys())
                    for c_idx, h in enumerate(headers, 1):
                        h_cell = ws_matrices.cell(row=row_mat, column=c_idx, value=str(h))
                        h_cell.font = bold_font
                        h_cell.fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
                    
                    row_mat += 1
                    
                    # Данные строк
                    for row_data in rows:
                        for c_idx, h in enumerate(headers, 1):
                            cell_value = row_data.get(h)
                            if isinstance(cell_value, float):
                                cell_value = round(cell_value, 4)
                            ws_matrices.cell(row=row_mat, column=c_idx, value=cell_value)
                        row_mat += 1
                    
                    row_mat += 2 # Отступ между таблицами режимов
            
            # Скалярные метрики или простые списки
            elif not isinstance(value, (list, dict)):
                ws_summary.cell(row=row_sum, column=1, value=str(key))
                val_rounded = round(value, 4) if isinstance(value, float) else value
                ws_summary.cell(row=row_sum, column=2, value=val_rounded)
                row_sum += 1

        # Настройка ширины колонок
        for ws in [ws_summary, ws_matrices]:
            for col in ws.columns:
                max_length = 0
                column_letter = col[0].column_letter
                for cell in col:
                    try:
                        if cell.value and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except Exception:
                        pass
                ws.column_dimensions[column_letter].width = min(max_length + 2, 50)

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream