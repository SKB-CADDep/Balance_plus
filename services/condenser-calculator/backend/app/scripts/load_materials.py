"""Загружает JSON-файлы материалов из db/materials/ в PostgreSQL."""
import json
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.material import Material 

def load_materials(db: Session, materials_dir: Path):
    for json_file in materials_dir.glob("*.json"):
        data = json.loads(json_file.read_text(encoding="utf-8"))
        
        # Извлекаем λ(t) из physical_properties
        lambda_data = data.get("physical_properties", {}).get(
            "coefficient_thermal_conductivity", {}
        )
        lambda_points = lambda_data.get("temperature_value_pairs", [])
        
        material = Material(
            material_uuid=data["material_id"],
            name=data["metadata"]["name_material_standard"],
            thermal_conductivity_points=lambda_points,
            full_properties=data,
        )
        db.merge(material)
    db.commit()