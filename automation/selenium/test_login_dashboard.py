from __future__ import annotations

# ============================================================
# CREACIÓN 2026-11-21 - PRUEBAS AUTOMATIZADAS SELENIUM
# Casos E2E sobre autenticación, separación por perfil y navegación.
# Motivo: cubrir los flujos visibles más críticos del MVP mediante
# interacción real con el navegador, complementando pytest backend.
# ============================================================

from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


EVIDENCE_DIR = Path(__file__).resolve().parent / "evidencias"
WAIT_SECONDS = 15


def login(driver, base_url: str, email: str, password: str) -> None:
    driver.get(base_url)
    wait = WebDriverWait(driver, WAIT_SECONDS)

    email_input = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[type="email"]'))
    )
    password_input = driver.find_element(
        By.CSS_SELECTOR, 'input[autocomplete="current-password"]'
    )

    email_input.clear()
    email_input.send_keys(email)
    password_input.clear()
    password_input.send_keys(password)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "profile-chip")))


def test_sel_01_login_admin_dashboard(
    driver, base_url, admin_credentials
):
    """SEL-01: Admin inicia sesión y visualiza el dashboard administrativo."""
    email, password = admin_credentials
    login(driver, base_url, email, password)

    wait = WebDriverWait(driver, WAIT_SECONDS)
    wait.until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, ".role-banner h2"), "Administrador"
        )
    )
    wait.until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, ".dashboard-summary-heading h2"),
            "Estado general de la plataforma",
        )
    )

    assert "Gestión de usuarios" in driver.page_source
    assert "Usuarios registrados" in driver.page_source
    assert "Proyectos" in driver.page_source
    assert "Modelos" in driver.page_source

    driver.save_screenshot(str(EVIDENCE_DIR / "EV_SEL_01_LOGIN_ADMIN_DASHBOARD.png"))


def test_sel_02_login_tester_dashboard(
    driver, base_url, tester_credentials
):
    """SEL-02: Analista/Tester accede a indicadores y módulos operativos."""
    email, password = tester_credentials
    login(driver, base_url, email, password)

    wait = WebDriverWait(driver, WAIT_SECONDS)
    wait.until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, ".role-banner h2"), "Analista/Tester"
        )
    )
    wait.until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, ".dashboard-summary-heading h2"),
            "Indicadores operativos",
        )
    )

    for label in (
        "Proyectos y modelos",
        "Campos y reglas",
        "Generación de datos",
        "Resultados y ejecución",
    ):
        assert label in driver.page_source

    # ============================================================
    # AJUSTE 2026-11-21 - SEL-02 / SINCRONIZACIÓN ASÍNCRONA
    # El encabezado del Dashboard se renderiza antes de finalizar la
    # consulta GET /api/dashboard/summary. Se espera explícitamente a
    # que las 5 métricas visibles de Analista/Tester dejen de mostrar
    # el placeholder "…" antes de validar sus valores.
    # Motivo: evitar falsos negativos por condición de carrera.
    # ============================================================
    def metricas_operativas_cargadas(current_driver):
        if current_driver.find_elements(By.CSS_SELECTOR, ".dashboard-metrics-error"):
            return False

        visibles = [
            value
            for value in current_driver.find_elements(
                By.CSS_SELECTOR, ".metric-card strong"
            )
            if value.is_displayed()
        ]

        textos = [value.text.strip() for value in visibles]

        return (
            len(textos) == 5
            and all(texto not in ("", "…") for texto in textos)
        )

    wait.until(metricas_operativas_cargadas)

    assert not driver.find_elements(
        By.CSS_SELECTOR, ".dashboard-metrics-error"
    ), "El Dashboard mostró un error al cargar los indicadores."

    metric_values = [
        value.text.strip()
        for value in driver.find_elements(By.CSS_SELECTOR, ".metric-card strong")
        if value.is_displayed()
    ]
    assert len(metric_values) == 5
    assert all(value not in ("", "…") for value in metric_values)

    driver.save_screenshot(str(EVIDENCE_DIR / "EV_SEL_02_LOGIN_TESTER_DASHBOARD.png"))


def test_sel_03_navegacion_operativa(
    driver, base_url, tester_credentials
):
    """SEL-03: El Analista/Tester navega a Generación y Resultados."""
    email, password = tester_credentials
    login(driver, base_url, email, password)
    wait = WebDriverWait(driver, WAIT_SECONDS)

    generation_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Generación de datos']")
        )
    )
    generation_button.click()
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(normalize-space(), 'Generación de datos de prueba')]")
        )
    )
    driver.save_screenshot(str(EVIDENCE_DIR / "EV_SEL_03_GENERACION.png"))

    results_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Resultados y ejecución']")
        )
    )
    results_button.click()
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(normalize-space(), 'Resultados y ejecución')]")
        )
    )
    driver.save_screenshot(str(EVIDENCE_DIR / "EV_SEL_03_RESULTADOS.png"))


def test_sel_04_logout(
    driver, base_url, tester_credentials
):
    """SEL-04: Cerrar sesión retorna al formulario de autenticación."""
    email, password = tester_credentials
    login(driver, base_url, email, password)

    driver.find_element(By.CLASS_NAME, "logout-button").click()

    wait = WebDriverWait(driver, WAIT_SECONDS)
    wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[type="email"]'))
    )
    assert "Iniciar sesión" in driver.page_source

    driver.save_screenshot(str(EVIDENCE_DIR / "EV_SEL_04_LOGOUT.png"))
