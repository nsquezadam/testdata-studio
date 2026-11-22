from __future__ import annotations

# ============================================================
# CREACIÓN 2026-11-21 - PRUEBAS AUTOMATIZADAS SELENIUM
# Configuración común para las pruebas E2E del frontend.
# Motivo: validar los flujos visibles más críticos del MVP sin
# acoplar credenciales reales al repositorio.
# ============================================================

import os
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


BASE_DIR = Path(__file__).resolve().parent
EVIDENCE_DIR = BASE_DIR / "evidencias"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("SELENIUM_BASE_URL", "http://localhost:5173").rstrip("/")


@pytest.fixture(scope="session")
def admin_credentials() -> tuple[str, str]:
    email = os.getenv("SELENIUM_ADMIN_EMAIL", "admin@testdata.local")
    password = os.getenv("SELENIUM_ADMIN_PASSWORD", "")
    if not password:
        pytest.fail(
            "Define SELENIUM_ADMIN_PASSWORD antes de ejecutar las pruebas Selenium."
        )
    return email, password


@pytest.fixture(scope="session")
def tester_credentials() -> tuple[str, str]:
    email = os.getenv("SELENIUM_TESTER_EMAIL", "tester@testdata.local")
    password = os.getenv("SELENIUM_TESTER_PASSWORD", "")
    if not password:
        pytest.fail(
            "Define SELENIUM_TESTER_PASSWORD antes de ejecutar las pruebas Selenium."
        )
    return email, password


@pytest.fixture()
def driver(request):
    options = Options()
    options.add_argument("--window-size=1600,1000")
    options.add_argument("--disable-notifications")

    # SELENIUM_HEADLESS=1 permite ejecución sin abrir ventana.
    if os.getenv("SELENIUM_HEADLESS", "0") == "1":
        options.add_argument("--headless=new")

    browser = webdriver.Chrome(options=options)
    browser.implicitly_wait(1)
    yield browser

    # Si una prueba falla, se conserva una captura adicional automática.
    if getattr(request.node, "rep_call", None) and request.node.rep_call.failed:
        browser.save_screenshot(
            str(EVIDENCE_DIR / f"FALLO_{request.node.name}.png")
        )

    browser.quit()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
