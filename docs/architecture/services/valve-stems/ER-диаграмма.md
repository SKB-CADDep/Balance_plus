erDiagram
    %% Справочные данные (существуют)
    UNIQUE_TURBINE ||--o{ VALVE : contains
    UNIQUE_TURBINE {
        int id PK
        string name "Тип (напр. Т-100-130)"
    }
    VALVE {
        int id PK
        int turbine_id FK
        string name "Чертежный номер"
        string type "СК/РК"
        json geometry "Размеры"
    }

    %% Новая сущность: Проект (Инстанс турбины)
    PROJECT ||--|| UNIQUE_TURBINE : "based on type"
    PROJECT ||--o{ MULTI_CALC_RESULT : "has history"
    PROJECT {
        int id PK
        int turbine_id FK "Ссылка на тип"
        string station_name "Название станции"
        string station_no "Станционный №"
        string factory_no "Заводской № (Unique)"
        datetime created_at
    }

    %% История расчетов
    MULTI_CALC_RESULT {
        int id PK
        int project_id FK
        datetime created_at
        jsonb input_payload "Полный снапшот входа"
        jsonb output_payload "Результаты + Суммы"
    }