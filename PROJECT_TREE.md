# 🌳 Дерево проекта: Balance_plus-1

> Автоматически сгенерировано: `2026-05-13 11:47:18`  
> Директорий: **134** | Файлов: **512**

```
Balance_plus-1/
├── 📁 .cursor/
├── 📁 .github/
│   ├── 📁 prompts/
│   │   ├── 📝 system_prompt.md
│   │   └── 📝 test_generator_prompt.md
│   ├── 📁 scripts/
│   │   ├── 🐍 ai_reviewer.py
│   │   └── 🐍 ai_test_generator.py
│   └── 📁 workflows/
│       ├── ⚙️ ai-generate-tests.yml
│       ├── ⚙️ ai-review.yml
│       └── ⚙️ ci.yml
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
│   │   │   │   │       └── 🐍 test_tasks.py
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
│   │   │   │   ├── 📁 versions/
│   │   │   │   │   └── 🐍 c24375df89dc_initial_full_schema.py
│   │   │   │   ├── 🐍 env.py
│   │   │   │   ├── 📖 README
│   │   │   │   └── 📄 script.py.mako
│   │   │   ├── 📁 app/
│   │   │   │   ├── 📁 adapters/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   └── 🐍 calculation_adapter.py
│   │   │   │   ├── 📁 api/
│   │   │   │   │   └── 📁 routes/
│   │   │   │   │       ├── 🐍 __init__.py
│   │   │   │   │       ├── 🐍 async_calculations.py
│   │   │   │   │       ├── 🐍 calculations.py
│   │   │   │   │       ├── 🐍 condensers.py
│   │   │   │   │       ├── 🐍 health.py
│   │   │   │   │       └── 🐍 materials.py
│   │   │   │   ├── 📁 core/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 celery_app.py
│   │   │   │   │   ├── 🐍 condenser_validators.py
│   │   │   │   │   ├── 🐍 config.py
│   │   │   │   │   ├── 🐍 converter.py
│   │   │   │   │   ├── 🐍 database.py
│   │   │   │   │   ├── 🐍 exceptions.py
│   │   │   │   │   ├── 🐍 logging.py
│   │   │   │   │   ├── 🐍 material_lambda.py
│   │   │   │   │   ├── 🐍 middleware.py
│   │   │   │   │   └── 🐍 range_parser.py
│   │   │   │   ├── 📁 crud/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 calculations.py
│   │   │   │   │   ├── 🐍 condensers.py
│   │   │   │   │   └── 🐍 materials.py
│   │   │   │   ├── 📁 models/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 base.py
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
│   │   │   │   ├── 📁 services/
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   └── 🐍 excel_exporter.py
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
│   │   │   │   ├── 🐍 main.py
│   │   │   │   └── 🐍 worker.py
│   │   │   ├── 📁 scripts/
│   │   │   │   ├── 🐍 _common.py
│   │   │   │   ├── 🐍 compare_selection_methods.py
│   │   │   │   ├── 🐍 generate_report_on_selecting_values.py
│   │   │   │   ├── 🐍 report_calculation_engine.py
│   │   │   │   ├── 🐍 report_metrovickers_strategy.py
│   │   │   │   ├── 🐍 report_module_berman.py
│   │   │   │   ├── 🐍 report_TPS_module.py
│   │   │   │   ├── 🐍 seed_db.py
│   │   │   │   ├── 🐍 validate_exceptions_method.py
│   │   │   │   ├── 🐍 validate_TPS_module.py
│   │   │   │   └── 🐍 validate_vku.py
│   │   │   ├── 📁 tests/
│   │   │   │   ├── 📁 api/
│   │   │   │   │   ├── ⚙️ __group__.yml
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 test_calculations.py
│   │   │   │   │   └── 🐍 test_health.py
│   │   │   │   ├── 📁 unit/
│   │   │   │   │   ├── ⚙️ __group__.yml
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 test_calculation_adapter.py
│   │   │   │   │   ├── 🐍 test_division_range.py
│   │   │   │   │   ├── 🐍 test_excel_exporter.py
│   │   │   │   │   ├── 🐍 test_metrovickers_strategy.py
│   │   │   │   │   ├── 🐍 test_module_berman.py
│   │   │   │   │   ├── 🐍 test_range_parser.py
│   │   │   │   │   ├── 🐍 test_selecting_values.py
│   │   │   │   │   ├── 🐍 test_table_models.py
│   │   │   │   │   ├── 🐍 test_uniconv.py
│   │   │   │   │   ├── 🐍 test_validations.py
│   │   │   │   │   └── 🐍 test_VKU_strategy.py
│   │   │   │   ├── 📁 utils/
│   │   │   │   │   ├── ⚙️ __group__.yml
│   │   │   │   │   └── 🐍 test_material_lambda.py
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
│   │   │   │   │   ├── ⚙️ __group__.yml
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   └── 🐍 test_berman_verification_calc.py
│   │   │   │   ├── 🐍 __init__.py
│   │   │   │   ├── 🐍 conftest.py
│   │   │   │   └── 📖 README.md
│   │   │   ├── 📄 .dockerignore
│   │   │   ├── 📄 .env
│   │   │   ├── ⚙️ alembic.ini
│   │   │   ├── ⚙️ docker-compose.dev.yml
│   │   │   ├── 🐳 Dockerfile
│   │   │   ├── ⚡ entrypoint.sh
│   │   │   ├── 🔒 poetry.lock
│   │   │   ├── 📦 pyproject.toml
│   │   │   ├── 📖 README.md
│   │   │   └── 🐍 seed.py
│   │   ├── 📁 db/
│   │   │   └── 📁 materials/
│   │   │       ├── 📋 08Х13.json
│   │   │       ├── 📋 08Х16Н13М2Б.json
│   │   │       ├── 📋 08Х18Н10Т.json
│   │   │       ├── 📋 09Г2С.json
│   │   │       ├── 📋 12МХЛ.json
│   │   │       ├── 📋 12Х13.json
│   │   │       ├── 📋 12Х18Н10Т.json
│   │   │       ├── 📋 12Х18Н9Т.json
│   │   │       ├── 📋 12Х1МФ.json
│   │   │       ├── 📋 12ХМ.json
│   │   │       ├── 📋 15Х11МФ.json
│   │   │       ├── 📋 15Х12ВНМФ.json
│   │   │       ├── 📋 15Х1М1Ф.json
│   │   │       ├── 📋 15Х1М1ФЛ.json
│   │   │       ├── 📋 15ХМ.json
│   │   │       ├── 📋 18X11МНФБ-Ш.json
│   │   │       ├── 📋 18Х12ВМБФР.json
│   │   │       ├── 📋 20ГСЛ.json
│   │   │       ├── 📋 20К.json
│   │   │       ├── 📋 20Л.json
│   │   │       ├── 📋 20Х12ВНМФ.json
│   │   │       ├── 📋 20Х13.json
│   │   │       ├── 📋 20Х1М1Ф1ТР.json
│   │   │       ├── 📋 20Х3МВФА.json
│   │   │       ├── 📋 20ХМЛ.json
│   │   │       ├── 📋 20ХМФЛ.json
│   │   │       ├── 📋 22К.json
│   │   │       ├── 📋 25Л.json
│   │   │       ├── 📋 25Х1М1ФА.json
│   │   │       ├── 📋 25Х1МФ.json
│   │   │       ├── 📋 25Х2М1Ф.json
│   │   │       ├── 📋 25Х2Н4МФА.json
│   │   │       ├── 📋 26ХН3М2ФА.json
│   │   │       ├── 📋 27ХН3МФА.json
│   │   │       ├── 📋 30ХМА.json
│   │   │       ├── 📋 30ХН2МФА.json
│   │   │       ├── 📋 30ХН3М2ФА.json
│   │   │       ├── 📋 34ХМА.json
│   │   │       ├── 📋 34ХН1МА.json
│   │   │       ├── 📋 34ХН3МА.json
│   │   │       ├── 📋 35Х.json
│   │   │       ├── 📋 35ХМ.json
│   │   │       ├── 📋 35ХН1М2ФА.json
│   │   │       ├── 📋 36ХН3МФА.json
│   │   │       ├── 📋 38ХН3МФА.json
│   │   │       ├── 📋 40Х.json
│   │   │       ├── 📋 40ХА.json
│   │   │       ├── 📋 X10CrMoNb9-1.json
│   │   │       ├── 📋 ВТ1-0.json
│   │   │       ├── 📋 ВТ5.json
│   │   │       ├── 📋 Л68.json
│   │   │       ├── 📋 ЛО70-1.json
│   │   │       ├── 📋 МНЖ5-1.json
│   │   │       ├── 📋 Ст3сп.json
│   │   │       ├── 📋 Сталь 20.json
│   │   │       ├── 📋 Сталь 25.json
│   │   │       ├── 📋 Сталь 30.json
│   │   │       ├── 📋 Сталь 35.json
│   │   │       ├── 📋 Сталь 40.json
│   │   │       ├── 📋 Сталь 45.json
│   │   │       └── 📋 ХН35ВТ.json
│   │   ├── 📁 frontend/
│   │   │   ├── 📁 public/
│   │   │   │   ├── 📁 assets/
│   │   │   │   │   └── 📁 images/
│   │   │   │   │       └── 🖼️ favicon.ico
│   │   │   │   ├── 🌐 index.html
│   │   │   │   └── 🖼️ logo.png
│   │   │   ├── 📁 src/
│   │   │   │   ├── 📁 client/
│   │   │   │   │   ├── 📁 core/
│   │   │   │   │   │   ├── 📜 ApiError.ts
│   │   │   │   │   │   ├── 📜 ApiRequestOptions.ts
│   │   │   │   │   │   ├── 📜 ApiResult.ts
│   │   │   │   │   │   ├── 📜 CancelablePromise.ts
│   │   │   │   │   │   ├── 📜 OpenAPI.ts
│   │   │   │   │   │   ├── 📜 request.ts
│   │   │   │   │   │   └── 📜 types.ts
│   │   │   │   │   ├── 📜 index.ts
│   │   │   │   │   ├── 📜 models.ts
│   │   │   │   │   ├── 📜 schemas.ts
│   │   │   │   │   └── 📜 services.ts
│   │   │   │   ├── 📁 components/
│   │   │   │   │   ├── 📁 Calculator/
│   │   │   │   │   │   ├── 📄 EarlyCalculationPage.tsx
│   │   │   │   │   │   ├── 📄 ResultsPage.tsx
│   │   │   │   │   │   ├── 📄 StockInputPage.tsx
│   │   │   │   │   │   ├── 📄 StockSelection.tsx
│   │   │   │   │   │   └── 📄 TurbineSearch.tsx
│   │   │   │   │   ├── 📁 Common/
│   │   │   │   │   │   ├── 📄 InputWithUnit.tsx
│   │   │   │   │   │   ├── 📄 MainLayout.tsx
│   │   │   │   │   │   ├── 📄 NotFound.tsx
│   │   │   │   │   │   ├── 📄 Sidebar.tsx
│   │   │   │   │   │   └── 📄 ThemeToggleButton.tsx
│   │   │   │   │   └── 📁 OtherPages/
│   │   │   │   │       ├── 📄 AboutPage.tsx
│   │   │   │   │       └── 📄 HelpPage.tsx
│   │   │   │   ├── 📁 routes/
│   │   │   │   │   ├── 📄 __root.tsx
│   │   │   │   │   ├── 📄 calculator.tsx
│   │   │   │   │   └── 📄 index.tsx
│   │   │   │   ├── 📁 utils/
│   │   │   │   │   └── 📜 parser.ts
│   │   │   │   ├── 📄 main.tsx
│   │   │   │   ├── 📜 routeTree.gen.ts
│   │   │   │   ├── 📄 theme.tsx
│   │   │   │   └── 📜 vite-env.d.ts
│   │   │   ├── 📄 .env.production
│   │   │   ├── 🙈 .gitignore
│   │   │   ├── 📋 biome.json
│   │   │   ├── 🌐 index.html
│   │   │   ├── 📋 openapi.json
│   │   │   ├── 📋 package-lock.json
│   │   │   ├── 📋 package.json
│   │   │   ├── 📋 tsconfig.json
│   │   │   ├── 📋 tsconfig.node.json
│   │   │   └── 📜 vite.config.ts
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
│       │   └── 📖 README.md
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
