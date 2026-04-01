"""Localized EV campaign copy (tagline, highlights, pitch, tech)."""

from __future__ import annotations

from app.brand import BRAND_NAME
from app.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, get_locale

_CAMPAIGN: dict[str, dict] = {
    "en": {
        "tagline": "Open-source electric vehicle management for real hardware",
        "highlights": [
            "Battery management (BMS) with cell balancing, SOC/SOH, and thermal safety",
            "VESC motor control, charging (CCS/CHAdeMO/Tesla), and vehicle state orchestration",
            "CAN bus, telemetry, IMU/GPS, diagnostics (DTC, limp-home), and web dashboard",
            "Autopilot hooks with safe fallbacks and a modular, test-driven codebase",
        ],
        "pitch": f"""
We are raising funds to accelerate hardware bring-up, safety validation, and field
testing of the {BRAND_NAME} stack: a complete EV management platform spanning BMS, motor
control, charging, diagnostics, and telemetry. Backers help us ship reference
integrations, documentation, and hosted contributor sandboxes so the community can
build on a solid foundation.
""",
        "tech": """
The platform includes a real-time dashboard, CAN tooling, integration builders for
VESC/SimpBMS/Quectel, and extensive automated tests. Crowdfunding supports certification
readiness, hardware lab time, and open releases of firmware and tooling.
""",
    },
    "ru": {
        "tagline": "Открытая платформа управления электромобилем для реального железа",
        "highlights": [
            "BMS: балансировка ячеек, SOC/SOH, тепловая безопасность",
            "VESC, зарядка (CCS/CHAdeMO/Tesla), координация состояний автомобиля",
            "CAN, телеметрия, IMU/GPS, диагностика (DTC, limp-home), веб-дашборд",
            "Автопилот с безопасным запасным режимом, модульный код и тесты",
        ],
        "pitch": f"""
Мы собираем средства на доводку железа, проверку безопасности и полевые испытания
стека {BRAND_NAME}: полноценная платформа управления ЭТ — BMS, привод, зарядка,
диагностика и телеметрия. Поддержка помогает выпускать эталонные интеграции,
документацию и хостинг для контрибьюторов.
""",
        "tech": """
В составе — дашборд в реальном времени, инструменты CAN, сборщики VESC/SimpBMS/Quectel
и обширные автотесты. Краудфандинг идёт на сертификацию, лабораторию и открытые релизы.
""",
    },
    "de": {
        "tagline": "Open-Source-Elektrofahrzeug-Management für echte Hardware",
        "highlights": [
            "BMS mit Zellbalancing, SOC/SOH und thermischer Sicherheit",
            "VESC-Motorregelung, Laden (CCS/CHAdeMO/Tesla), Fahrzeugzustände",
            "CAN, Telemetrie, IMU/GPS, Diagnose (DTC, Limp-Home), Web-Dashboard",
            "Autopilot-Hooks mit sicherem Fallback, modularer, getesteter Code",
        ],
        "pitch": f"""
Wir sammeln Mittel für Hardware-Bring-up, Sicherheitsvalidierung und Feldtests des
{BRAND_NAME}-Stacks: eine komplette EV-Plattform mit BMS, Motor, Laden, Diagnose
und Telemetrie. Unterstützer helfen bei Referenzintegrationen, Doku und Sandboxes.
""",
        "tech": """
Die Plattform umfasst Echtzeit-Dashboard, CAN-Werkzeuge, Builder für VESC/SimpBMS/Quectel
und umfangreiche Tests. Crowdfunding unterstützt Zertifizierung und Lab-Zeit.
""",
    },
    "zh": {
        "tagline": "面向真实硬件的开源电动汽车管理软件",
        "highlights": [
            "电池管理（BMS）：均衡、SOC/SOH、热安全",
            "VESC 电机控制、充电（CCS/CHAdeMO/Tesla）、整车状态协调",
            "CAN、遥测、IMU/GPS、诊断（DTC、跛行回家）、Web 仪表盘",
            "自动驾驶接口与安全回退，模块化、测试驱动的代码库",
        ],
        "pitch": f"""
我们众筹以加速 {BRAND_NAME} 栈的硬件调试、安全验证与路试：涵盖 BMS、电机、充电、
诊断与遥测的完整电动汽车管理平台。支持者帮助交付参考集成、文档与托管沙箱。
""",
        "tech": """
平台包含实时仪表盘、CAN 工具、VESC/SimpBMS/Quectel 集成构建器及大量自动化测试。
众筹用于认证准备、实验室时间与固件/工具的开源发布。
""",
    },
}


def get_campaign_content() -> dict:
    loc = get_locale()
    if loc not in SUPPORTED_LOCALES:
        loc = DEFAULT_LOCALE
    return dict(_CAMPAIGN.get(loc) or _CAMPAIGN[DEFAULT_LOCALE])
