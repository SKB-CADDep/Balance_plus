# 🌳 Дерево проекта: Balance_plus-1

> Автоматически сгенерировано: `2026-04-06 15:18:28`  
> Директорий: **117** | Файлов: **383**

```
Balance_plus-1/
├── 📁 .github/
│   ├── 📁 prompts/
│   │   ├── 📝 system_prompt.md
│   │   └── 📝 test_generator_prompt.md
│   ├── 📁 scripts/
│   │   ├── 🐍 ai_reviewer.py
│   │   └── 🐍 ai_test_generator.py
│   └── 📁 workflows/
│       ├── ⚙️ ai-generate-tests.yml
│       └── ⚙️ ai-review.yml
├── 📁 _archive/
│   ├── 🐍 conftest.py
│   └── 📖 README.md
├── 📁 docs/
│   ├── 📁 architecture/
│   │   ├── 📁 platform/
│   │   │   ├── 📝 container-orchestration.md
│   │   │   ├── 📝 data-schema-management.md
│   │   │   ├── 📝 gitlab.md
│   │   │   ├── 📝 message-broker.md
│   │   │   ├── 📝 observability.md
│   │   │   └── 📝 postgresql-database.md
│   │   ├── 📁 services/
│   │   │   ├── 📁 valve-stems/
│   │   │   │   ├── 📝 ER-диаграмма.md
│   │   │   │   ├── 📋 Request_calculations_multi.json
│   │   │   │   └── 📋 Response_calculations_multi.json
│   │   │   ├── 📝 api-gateway.md
│   │   │   ├── 📝 condenser_worker.md
│   │   │   ├── 📝 frontend-ide.md
│   │   │   └── 📝 orchestrator.md
│   │   └── 📝 C2_Containers.md
│   ├── 📁 materials/
│   │   ├── 📄 1.txt
│   │   ├── 📄 25.04.21_Балансы.pdf
│   │   ├── 📄 25.04.25_Пользовательское ТЗ.docx
│   │   ├── 📄 Общая схема.pdf
│   │   ├── 📄 ред2_Преза_для_завода_триквел.pptx
│   │   ├── 📄 ред4_Для презентации.docx
│   │   └── 📊 ред_План разработки БАЛАНС+ (для руководства).xlsx
│   ├── 📁 methods/
│   │   ├── 📁 balance/
│   │   │   ├── 📝 CALC-COND-BERMAN.md
│   │   │   ├── 📝 CALC-COND-METRO_VIKKERS.md
│   │   │   ├── 📝 CALC-STEM-RTM.md
│   │   │   └── 📝 flow_path.md
│   │   ├── 📁 common/
│   │   │   └── 📝 CALC-AIR-PROPERTIES.md
│   │   ├── 📁 database_structure/
│   │   │   ├── 📝 DB-EQUIP-CONDENSER.md
│   │   │   └── 📝 DB-MATERIALS.md
│   │   └── 📁 templates/
│   │       ├── 📝 database.md
│   │       ├── 📝 LaTeX_docs.md
│   │       └── 📝 methods.md
│   ├── 📁 specifications/
│   │   ├── 📝 condensercalculator.md
│   │   ├── 📝 taskmanager.md
│   │   ├── 📝 uniconv.md
│   │   └── 📝 valvecalculator.md
│   └── 📖 README.md
├── 📁 GitLAB_pipeline/
│   └── 📁 report_MR/
│       ├── ⚙️ .gitlab-ci.yml
│       ├── 🐍 custom_diff.py
│       └── ⚙️ view_template.yaml
├── 📁 Parameter Registry Manager/
│   ├── 🐍 app.py
│   └── 🗃️ registry.db
├── 📁 services/
│   ├── 📁 balance-orchestrator/
│   │   ├── 📁 backend/
│   │   │   ├── 📁 app/
│   │   │   │   ├── 📁 api/
│   │   │   │   │   ├── 📁 routes/
│   │   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   │   ├── 🐍 calculations.py
│   │   │   │   │   │   ├── 🐍 config.py
│   │   │   │   │   │   ├── 🐍 geometries.py
│   │   │   │   │   │   ├── 🐍 health.py
│   │   │   │   │   │   ├── 🐍 projects.py
│   │   │   │   │   │   ├── 🐍 tasks.py
│   │   │   │   │   │   └── 🐍 user.py
│   │   │   │   │   └── 🐍 __init__.py
│   │   │   │   ├── 📁 core/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   └── 🐍 gitlab_adapter.py
│   │   │   │   ├── 📁 schemas/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 calculation.py
│   │   │   │   │   ├── 🐍 geometry.py
│   │   │   │   │   └── 🐍 task.py
│   │   │   │   └── 🐍 main.py
│   │   │   ├── 📁 tests/
│   │   │   │   ├── 📁 api/
│   │   │   │   │   └── 📁 routes/
│   │   │   │   │       ├── ⚙️ __group__.yml
│   │   │   │   │       ├── 🐍 test_berman_demo_calc.py
│   │   │   │   │       ├── 🐍 test_calculations.py
│   │   │   │   │       ├── ⚙️ test_calculations.tavern.yaml
│   │   │   │   │       ├── 🐍 test_projects.py
│   │   │   │   │       ├── 🐍 test_tasks.py
│   │   │   │   │       └── ⚙️ test_turbines.db.yaml
│   │   │   │   ├── 📁 unit/
│   │   │   │   │   └── ⚙️ __group__.yml
│   │   │   │   ├── 🐍 conftest.py
│   │   │   │   └── 📖 README.md
│   │   │   ├── 📄 .env.example
│   │   │   ├── 🐳 Dockerfile
│   │   │   ├── 🔒 poetry.lock
│   │   │   ├── 📦 pyproject.toml
│   │   │   └── ⚙️ pytest.ini
│   │   ├── 📁 frontend/
│   │   │   ├── 📁 .vscode/
│   │   │   │   └── 📋 extensions.json
│   │   │   ├── 📁 public/
│   │   │   │   └── 🖼️ vite.svg
│   │   │   ├── 📁 src/
│   │   │   │   ├── 📁 assets/
│   │   │   │   │   └── 🖼️ vue.svg
│   │   │   │   ├── 📁 components/
│   │   │   │   │   ├── 📁 apps/
│   │   │   │   │   │   └── 📄 WsaWrapper.vue
│   │   │   │   │   ├── 📁 layout/
│   │   │   │   │   │   └── 📄 Header.vue
│   │   │   │   │   ├── 📁 task-board/
│   │   │   │   │   │   ├── 📄 CreateTaskModal.vue
│   │   │   │   │   │   ├── 📄 NewTaskCard.vue
│   │   │   │   │   │   └── 📄 TaskCard.vue
│   │   │   │   │   ├── 📁 ui/
│   │   │   │   │   │   └── 📄 Badge.vue
│   │   │   │   │   └── 📄 HelloWorld.vue
│   │   │   │   ├── 📄 App.vue
│   │   │   │   ├── 📜 main.ts
│   │   │   │   └── 🎨 style.css
│   │   │   ├── 🙈 .gitignore
│   │   │   ├── 🐳 Dockerfile
│   │   │   ├── 🌐 index.html
│   │   │   ├── 📄 nginx.conf
│   │   │   ├── 📋 package-lock.json
│   │   │   ├── 📋 package.json
│   │   │   ├── 📖 README.md
│   │   │   ├── 📋 tsconfig.app.json
│   │   │   ├── 📋 tsconfig.json
│   │   │   ├── 📋 tsconfig.node.json
│   │   │   └── 📜 vite.config.ts
│   │   └── ⚙️ docker-compose.yaml
│   ├── 📁 condenser-calculator/
│   │   ├── 📁 backend/
│   │   │   ├── 📁 alembic/
│   │   │   ├── 📁 app/
│   │   │   │   ├── 📁 adapters/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   └── 🐍 calculation_adapter.py
│   │   │   │   ├── 📁 api/
│   │   │   │   │   ├── 📁 routes/
│   │   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   │   ├── 🐍 calculations.py
│   │   │   │   │   │   ├── 🐍 condensers.py
│   │   │   │   │   │   ├── 🐍 health.py
│   │   │   │   │   │   └── 🐍 materials.py
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   └── 🐍 main.py
│   │   │   │   ├── 📁 core/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 config.py
│   │   │   │   │   ├── 🐍 database.py
│   │   │   │   │   ├── 🐍 exceptions.py
│   │   │   │   │   └── 🐍 range_parser.py
│   │   │   │   ├── 📁 crud/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 calculations.py
│   │   │   │   │   ├── 🐍 condensers.py
│   │   │   │   │   └── 🐍 materials.py
│   │   │   │   ├── 📁 models/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 calculation_result.py
│   │   │   │   │   ├── 🐍 condenser.py
│   │   │   │   │   └── 🐍 material.py
│   │   │   │   ├── 📁 schemas/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 calculation.py
│   │   │   │   │   ├── 🐍 condenser.py
│   │   │   │   │   ├── 🐍 errors.py
│   │   │   │   │   └── 🐍 material.py
│   │   │   │   ├── 📁 scripts/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 load_condensers.py
│   │   │   │   │   └── 🐍 load_materials.py
│   │   │   │   ├── 📁 utils/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 base_for_selection.py
│   │   │   │   │   ├── 🐍 berman_strategy.py
│   │   │   │   │   ├── 🐍 calculation_engine.py
│   │   │   │   │   ├── 🐍 Constants.py
│   │   │   │   │   ├── 🐍 division_range.py
│   │   │   │   │   ├── 🐍 exceptions_method.py
│   │   │   │   │   ├── 🐍 metrovickers_strategy.py
│   │   │   │   │   ├── 🐍 selection_methods.py
│   │   │   │   │   ├── 🐍 table_models.py
│   │   │   │   │   ├── 🐍 TPS_module.py
│   │   │   │   │   ├── 🐍 uniconv.py
│   │   │   │   │   └── 🐍 VKU_strategy.py
│   │   │   │   ├── 🐍 __init__.py
│   │   │   │   ├── 🐍 dependencies.py
│   │   │   │   └── 🐍 main.py
│   │   │   ├── 📁 scripts/
│   │   │   │   ├── 🐍 _common.py
│   │   │   │   ├── 🐍 compare_selection_methods.py
│   │   │   │   ├── 🐍 generate_report_on_selecting_values.py
│   │   │   │   ├── 🐍 report_calculation_engine.py
│   │   │   │   ├── 🐍 report_metrovickers_strategy.py
│   │   │   │   ├── 🐍 report_module_berman.py
│   │   │   │   ├── 🐍 report_TPS_module.py
│   │   │   │   ├── 🐍 validate_exceptions_method.py
│   │   │   │   ├── 🐍 validate_TPS_module.py
│   │   │   │   └── 🐍 validate_vku.py
│   │   │   ├── 📁 tests/
│   │   │   │   ├── 📁 api/
│   │   │   │   │   └── 🐍 __init__.py
│   │   │   │   ├── 📁 unit/
│   │   │   │   │   ├── ⚙️ __group__.yml
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 test_division_range.py
│   │   │   │   │   ├── 🐍 test_metrovickers_strategy.py
│   │   │   │   │   ├── 🐍 test_module_berman.py
│   │   │   │   │   ├── 🐍 test_selecting_values.py
│   │   │   │   │   ├── 🐍 test_table_models.py
│   │   │   │   │   ├── 🐍 test_uniconv.py
│   │   │   │   │   └── 🐍 test_VKU_strategy.py
│   │   │   │   ├── 📁 validation/
│   │   │   │   │   ├── 📁 berman/
│   │   │   │   │   │   ├── ⚙️ __group__.yml
│   │   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   │   ├── 🐍 conftest.py
│   │   │   │   │   │   ├── 🐍 test_mode_1.py
│   │   │   │   │   │   ├── 🐍 test_mode_2.py
│   │   │   │   │   │   ├── 🐍 test_mode_3.py
│   │   │   │   │   │   ├── 🐍 test_mode_4.py
│   │   │   │   │   │   └── 🐍 test_verification.py
│   │   │   │   │   └── 🐍 __init__.py
│   │   │   │   ├── 🐍 __init__.py
│   │   │   │   ├── 🐍 conftest.py
│   │   │   │   └── 📖 README.md
│   │   │   ├── 📄 .env
│   │   │   ├── 🐳 Dockerfile
│   │   │   ├── ⚡ entrypoint.sh
│   │   │   ├── 🔒 poetry.lock
│   │   │   ├── 📦 pyproject.toml
│   │   │   └── 📖 README.md
│   │   ├── 📁 db/
│   │   │   ├── 📁 materials/
│   │   │   │   └── 📋 12MHL.json
│   │   │   ├── 📊 condensers_data.xlsx
│   │   │   └── 📄 init.dump
│   │   └── ⚙️ docker-compose.yml
│   └── 📁 valve-stems/
│       ├── 📁 backend/
│       │   ├── 📁 _archive/
│       │   │   └── 📁 database/
│       │   │       ├── 📁 sql/
│       │   │       │   ├── 📁 archive/
│       │   │       │   │   ├── 🗃️ database.sql
│       │   │       │   │   ├── 🗃️ Table_Base.sql
│       │   │       │   │   ├── 🗃️ Table_Capacitors.sql
│       │   │       │   │   ├── 🗃️ Table_MP.sql
│       │   │       │   │   ├── 🗃️ Table_PadsOUP.sql
│       │   │       │   │   └── 🗃️ Table_Stock.sql
│       │   │       │   ├── 🗃️ actual_scheme.sql
│       │   │       │   ├── 🗃️ backup_v3.sql
│       │   │       │   ├── 🗃️ backup_v4.sql
│       │   │       │   ├── 🗃️ backup_v5.sql
│       │   │       │   ├── 🗃️ backup_v6.sql
│       │   │       │   ├── 🗃️ backup_v7.sql
│       │   │       │   ├── 🗃️ bacup_v3.sql
│       │   │       │   ├── 📄 postgres_server_fullbackup.dump
│       │   │       │   ├── 🗃️ resultcalcs.sql
│       │   │       │   ├── 🗃️ SQL-script.sql
│       │   │       │   ├── 🗃️ stocks.sql
│       │   │       │   └── 🗃️ turbines.sql
│       │   │       ├── 📁 xlsx/
│       │   │       │   ├── 📊 BD.xlsx
│       │   │       │   ├── 📊 Subject1_3parts.xlsx
│       │   │       │   ├── 📊 Subject2_4parts.xlsx
│       │   │       │   ├── 📊 Subject3_4parts.xlsx
│       │   │       │   ├── 📊 Subject4_3parts.xlsx
│       │   │       │   └── 📊 Схема хранения данных в БД.xlsx
│       │   │       └── 📄 Функциональная схема (Калькулятор штоков).graphml
│       │   ├── 📁 app/
│       │   │   ├── 📁 adapters/
│       │   │   │   └── 🐍 calculation_adapter.py
│       │   │   ├── 📁 alembic/
│       │   │   │   ├── 🐍 env.py
│       │   │   │   └── 📄 script.py.mako
│       │   │   ├── 📁 api/
│       │   │   │   ├── 📁 routes/
│       │   │   │   │   ├── 🐍 calculations.py
│       │   │   │   │   ├── 🐍 drawio.py
│       │   │   │   │   ├── 🐍 health.py
│       │   │   │   │   ├── 🐍 turbines.py
│       │   │   │   │   ├── 🐍 utils.py
│       │   │   │   │   └── 🐍 valves.py
│       │   │   │   └── 🐍 main.py
│       │   │   ├── 📁 core/
│       │   │   │   ├── 🐍 __init__.py
│       │   │   │   ├── 🐍 config.py
│       │   │   │   ├── 🐍 converter.py
│       │   │   │   ├── 🐍 database.py
│       │   │   │   ├── 🐍 error_handlers.py
│       │   │   │   ├── 🐍 exceptions.py
│       │   │   │   └── 🐍 logging_config.py
│       │   │   ├── 📁 crud/
│       │   │   │   ├── 🐍 __init__.py
│       │   │   │   ├── 🐍 calculations.py
│       │   │   │   ├── 🐍 turbines.py
│       │   │   │   └── 🐍 valves.py
│       │   │   ├── 📁 domain/
│       │   │   │   ├── 🐍 models.py
│       │   │   │   └── 🐍 valve_physics_engine.py
│       │   │   ├── 📁 generated_diagrams/
│       │   │   ├── 📁 middleware/
│       │   │   │   ├── 🐍 __init__.py
│       │   │   │   └── 🐍 logging_middleware.py
│       │   │   ├── 📁 models/
│       │   │   │   ├── 🐍 __init__.py
│       │   │   │   ├── 🐍 calculation_result.py
│       │   │   │   ├── 🐍 turbine.py
│       │   │   │   └── 🐍 valve.py
│       │   │   ├── 📁 schemas/
│       │   │   │   ├── 🐍 __init__.py
│       │   │   │   ├── 🐍 calculation.py
│       │   │   │   ├── 🐍 errors.py
│       │   │   │   ├── 🐍 turbine.py
│       │   │   │   └── 🐍 valve.py
│       │   │   ├── 📁 scripts/
│       │   │   │   ├── 🐍 backend_pre_start.py
│       │   │   │   ├── 🐍 check_drawio.py
│       │   │   │   ├── 🐍 initial_data.py
│       │   │   │   ├── 🐍 load_from_excel.py
│       │   │   │   └── 🐍 tests_pre_start.py
│       │   │   ├── 📁 services/
│       │   │   ├── 📁 templates/
│       │   │   │   └── 📄 template_2_parts.xml
│       │   │   ├── 📁 tests/
│       │   │   │   ├── 📁 api/
│       │   │   │   │   ├── ⚙️ __group__.yml
│       │   │   │   │   ├── 🐍 __init__.py
│       │   │   │   │   └── ⚙️ test_full_cycle.tavern.yaml
│       │   │   │   ├── 📁 crud/
│       │   │   │   │   ├── ⚙️ __group__.yml
│       │   │   │   │   ├── 🐍 __init__.py
│       │   │   │   │   ├── 🐍 conftest.py
│       │   │   │   │   └── 🐍 test_crud.py
│       │   │   │   ├── 📁 scripts/
│       │   │   │   │   ├── ⚙️ __group__.yml
│       │   │   │   │   ├── 🐍 __init__.py
│       │   │   │   │   └── 🐍 test_backend_pre_start.py
│       │   │   │   ├── 📁 utils/
│       │   │   │   │   ├── ⚙️ __group__.yml
│       │   │   │   │   ├── 🐍 __init__.py
│       │   │   │   │   ├── 🐍 test_calculations.py
│       │   │   │   │   └── 🐍 test_valve_stems_calc.py
│       │   │   │   ├── 🐍 __init__.py
│       │   │   │   └── 🐍 conftest.py
│       │   │   ├── 🐍 __init__.py
│       │   │   ├── 🐍 dependencies.py
│       │   │   └── 🐍 main.py
│       │   ├── 📄 .dockerignore
│       │   ├── 🙈 .gitignore
│       │   ├── ⚙️ alembic.ini
│       │   ├── 🐳 Dockerfile
│       │   ├── ⚡ entrypoint.sh
│       │   ├── 📋 package-lock.json
│       │   ├── 🔒 poetry.lock
│       │   ├── 📦 pyproject.toml
│       │   ├── 📖 README.md
│       │   └── 📄 valve-stems-v2.tar.gz
│       ├── 📁 db/
│       │   ├── 📊 Data.xlsx
│       │   ├── 📊 Data_1.xlsx
│       │   ├── 📄 init.dump
│       │   └── ⚡ restore.sh
│       ├── 📁 frontend/
│       │   ├── 📁 public/
│       │   │   ├── 📁 assets/
│       │   │   │   └── 📁 images/
│       │   │   │       └── 🖼️ favicon.ico
│       │   │   ├── 🌐 index.html
│       │   │   └── 🖼️ logo.png
│       │   ├── 📁 src/
│       │   │   ├── 📁 client/
│       │   │   │   ├── 📁 core/
│       │   │   │   │   ├── 📜 ApiError.ts
│       │   │   │   │   ├── 📜 ApiRequestOptions.ts
│       │   │   │   │   ├── 📜 ApiResult.ts
│       │   │   │   │   ├── 📜 CancelablePromise.ts
│       │   │   │   │   ├── 📜 OpenAPI.ts
│       │   │   │   │   ├── 📜 request.ts
│       │   │   │   │   └── 📜 types.ts
│       │   │   │   ├── 📜 index.ts
│       │   │   │   ├── 📜 models.ts
│       │   │   │   ├── 📜 schemas.ts
│       │   │   │   └── 📜 services.ts
│       │   │   ├── 📁 components/
│       │   │   │   ├── 📁 Calculator/
│       │   │   │   │   ├── 📄 EarlyCalculationPage.tsx
│       │   │   │   │   ├── 📄 ResultsPage.tsx
│       │   │   │   │   ├── 📄 StockInputPage.tsx
│       │   │   │   │   ├── 📄 StockSelection.tsx
│       │   │   │   │   └── 📄 TurbineSearch.tsx
│       │   │   │   ├── 📁 Common/
│       │   │   │   │   ├── 📄 InputWithUnit.tsx
│       │   │   │   │   ├── 📄 MainLayout.tsx
│       │   │   │   │   ├── 📄 NotFound.tsx
│       │   │   │   │   ├── 📄 Sidebar.tsx
│       │   │   │   │   └── 📄 ThemeToggleButton.tsx
│       │   │   │   └── 📁 OtherPages/
│       │   │   │       ├── 📄 AboutPage.tsx
│       │   │   │       └── 📄 HelpPage.tsx
│       │   │   ├── 📁 routes/
│       │   │   │   ├── 📄 __root.tsx
│       │   │   │   ├── 📄 about.tsx
│       │   │   │   ├── 📄 calculator.tsx
│       │   │   │   ├── 📄 help.tsx
│       │   │   │   └── 📄 index.tsx
│       │   │   ├── 📄 main.tsx
│       │   │   ├── 📜 routeTree.gen.ts
│       │   │   ├── 📄 theme.tsx
│       │   │   └── 📜 vite-env.d.ts
│       │   ├── 📄 .dockerignore
│       │   ├── 📄 .env.production
│       │   ├── 🙈 .gitignore
│       │   ├── 📄 .nvmrc
│       │   ├── 📋 biome.json
│       │   ├── 🐳 Dockerfile
│       │   ├── 🌐 index.html
│       │   ├── 📜 modify-openapi-operationids.js
│       │   ├── 📄 nginx-backend-not-found.conf
│       │   ├── 📄 nginx.conf
│       │   ├── 📋 package-lock.json
│       │   ├── 📋 package.json
│       │   ├── 📜 playwright.config.ts
│       │   ├── 📖 README.md
│       │   ├── 📋 tsconfig.json
│       │   ├── 📋 tsconfig.node.json
│       │   └── 📜 vite.config.ts
│       ├── 📄 .env
│       ├── ⚙️ docker-compose.yml
│       ├── 📋 package-lock.json
│       └── 📖 README.md
├── 📁 tests/
│   └── 📁 e2e/
│       └── 📖 README.md
├── 📁 validation_data/
│   ├── 📁 balance/
│   │   └── 📁 source_data/
│   │       └── 📋 test_1.json
│   ├── 📁 condenser-calculator/
│   │   └── 📁 strategies/
│   │       ├── 📁 berman/
│   │       │   ├── 📁 geometrys/
│   │       │   │   ├── 📋 geometry.json
│   │       │   │   └── 📋 geometry_4.json
│   │       │   ├── 📁 modes/
│   │       │   │   ├── 📋 mode_1.json
│   │       │   │   ├── 📋 mode_2.json
│   │       │   │   ├── 📋 mode_3.json
│   │       │   │   └── 📋 mode_4.json
│   │       │   └── 📁 results/
│   │       │       ├── 📋 results_1.json
│   │       │       ├── 📋 results_2.json
│   │       │       ├── 📋 results_3.json
│   │       │       └── 📋 results_4.json
│   │       └── 📁 metro_vikers/
│   │           ├── 📋 geometry_mv.json
│   │           └── 📋 mode_mv.json
│   ├── 📁 scripts/
│   │   ├── 🐍 excel_to_json_berman.py
│   │   ├── 🐍 excel_to_json_metro_vikkers.py
│   │   ├── 🐍 read_dbf_for_zone_json.py
│   │   └── 🐍 treu_to_json.py
│   ├── 📁 valve-stems/
│   │   ├── 📋 1_st_stock_data.json
│   │   ├── 📋 1_st_stock_result.json
│   │   ├── 📋 2_nd_stock_data.json
│   │   ├── 📋 2_nd_stock_result.json
│   │   ├── 📋 3_rd_stock_data.json
│   │   ├── 📋 3_rd_stock_result.json
│   │   ├── 📋 group_of_stocks_data.json
│   │   └── 📋 group_of_stocks_results.json
│   └── 📖 README.md
├── 🙈 .gitignore
├── 📄 balance-orchestrator.tar.gz
├── 📝 CONTRIBUTING.md
├── 🐍 generate_tree.py
├── 📋 package-lock.json
├── 📖 README.md
├── 📖 README_TESTING.md
├── ⚙️ ruff.toml
└── 🐍 test_runner.py
```

---

<details>
<summary>🚫 Игнорируемые директории</summary>

`*.egg-info`, `.eggs`, `.env`, `.git`, `.idea`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.tox`, `.venv`, `__pycache__`, `build`, `dist`, `env`, `migrations`, `node_modules`, `venv`

</details>
