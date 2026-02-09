from unittest.mock import MagicMock, patch

from app.scripts.backend_pre_start import init, logger


def test_init_successful_connection() -> None:
    engine_mock = MagicMock()

    # Мок сессии
    session_exec_mock = MagicMock(return_value=True)

    # Мок объекта session, который возвращается из контекстного менеджера
    session_instance_mock = MagicMock()
    session_instance_mock.exec = session_exec_mock

    # Мок класса Session, который при вызове with возвращает session_instance_mock
    session_cls_mock = MagicMock()
    session_cls_mock.return_value.__enter__.return_value = session_instance_mock

    # Важно: патчим sqlmodel.Session ВНУТРИ МОДУЛЯ, где он используется
    # В файле app/scripts/backend_pre_start.py импорт выглядит как: from sqlmodel import Session
    # Значит патчить нужно "app.scripts.backend_pre_start.Session"
    with (
        patch("app.scripts.backend_pre_start.Session", new=session_cls_mock),
        patch.object(logger, "info"),
        patch.object(logger, "error"),
        patch.object(logger, "warn"),
    ):
        try:
            init(engine_mock)
            connection_successful = True
        except Exception:
            connection_successful = False

        assert connection_successful

        # Проверка
        session_instance_mock.exec.assert_called_once()
