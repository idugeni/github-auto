"""Anti-detection stealth injection (ported from autoregister-account)."""

from __future__ import annotations

import json
import random
from typing import Optional  # noqa: F401

from playwright.sync_api import Page

SCREEN_RESOLUTIONS = [
    {"width": 1920, "height": 1080, "colorDepth": 24, "pixelRatio": 1},
    {"width": 1366, "height": 768, "colorDepth": 24, "pixelRatio": 1},
    {"width": 1536, "height": 864, "colorDepth": 24, "pixelRatio": 1},
    {"width": 1440, "height": 900, "colorDepth": 24, "pixelRatio": 1},
    {"width": 1280, "height": 720, "colorDepth": 24, "pixelRatio": 1},
    {"width": 1600, "height": 900, "colorDepth": 24, "pixelRatio": 1},
    {"width": 2560, "height": 1440, "colorDepth": 30, "pixelRatio": 1},
    {"width": 3840, "height": 2160, "colorDepth": 30, "pixelRatio": 1},
]

WEBGL_VENDORS = [
    "Google Inc. (NVIDIA)",
    "Google Inc. (AMD)",
    "Google Inc. (Intel)",
    "Google Inc. (Intel Inc.)",
]

WEBGL_RENDERERS = [
    "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (AMD, AMD Radeon RX 5700 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (AMD, AMD Radeon Vega 8 Graphics Direct3D11 vs_5_0 ps_5_0)",
]

LANGUAGES_BY_COUNTRY = {
    "US": ["en-US", "en"],
    "GB": ["en-GB", "en"],
    "ID": ["id-ID", "id", "en-US", "en"],
    "DE": ["de-DE", "de", "en-US", "en"],
    "FR": ["fr-FR", "fr", "en-US", "en"],
    "JP": ["ja-JP", "ja", "en-US", "en"],
}


def _pick_random(arr: list) -> str:
    return random.choice(arr)


def _generate_canvas_noise() -> str:
    noise = [random.randint(0, 255) for _ in range(16)]
    return json.dumps(noise)


def get_stealth_script(country_code: str = "US", user_agent: str = "") -> str:
    """Generate JavaScript stealth injection script."""
    resolution = json.loads(_pick_random(SCREEN_RESOLUTIONS).replace("'", '"'))
    languages = LANGUAGES_BY_COUNTRY.get(country_code, ["en-US", "en"])
    vendor = _pick_random(WEBGL_VENDORS)
    renderer = _pick_random(WEBGL_RENDERERS)
    canvas_noise = _generate_canvas_noise()
    hw_concurrency = random.choice([4, 6, 8, 12, 16])
    device_memory = random.choice([4, 8, 16])

    return f"""
    // webdriver
    Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});

    // languages
    Object.defineProperty(navigator, 'languages', {{ get: () => {json.dumps(languages)} }});
    Object.defineProperty(navigator, 'language', {{ get: () => '{languages[0]}' }});

    // plugins
    Object.defineProperty(navigator, 'plugins', {{
        get: () => [
            {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
            {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' }},
            {{ name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }}
        ]
    }});

    // hardware
    Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {hw_concurrency} }});
    Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {device_memory} }});
    Object.defineProperty(navigator, 'maxTouchPoints', {{ get: () => 0 }});

    // screen
    Object.defineProperty(screen, 'width', {{ get: () => {resolution['width']} }});
    Object.defineProperty(screen, 'height', {{ get: () => {resolution['height']} }});
    Object.defineProperty(screen, 'availWidth', {{ get: () => {resolution['width']} }});
    Object.defineProperty(screen, 'availHeight', {{ get: () => {resolution['height'] - 40} }});
    Object.defineProperty(screen, 'colorDepth', {{ get: () => {resolution['colorDepth']} }});
    Object.defineProperty(screen, 'pixelDepth', {{ get: () => {resolution['colorDepth']} }});
    window.devicePixelRatio = {resolution['pixelRatio']};

    // WebGL
    const getParameterOrig = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {{
        if (param === 37445) return '{vendor}';
        if (param === 37446) return '{renderer}';
        return getParameterOrig.call(this, param);
    }};

    // Canvas fingerprint noise
    const toDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function() {{
        try {{
            const ctx = this.getContext('2d');
            if (ctx) {{
                const noise = {canvas_noise};
                const imgData = ctx.getImageData(0, 0, Math.min(this.width, 16), 1);
                for (let i = 0; i < noise.length && i < imgData.data.length; i += 4) {{
                    imgData.data[i] = (imgData.data[i] + noise[i/4]) % 256;
                }}
                ctx.putImageData(imgData, 0, 0);
            }}
        }} catch(e) {{}}
        return toDataURL.apply(this, arguments);
    }};

    // Chrome runtime
    if (!window.chrome) window.chrome = {{}};
    if (!window.chrome.runtime) window.chrome.runtime = {{ connect: function() {{}}, sendMessage: function() {{}} }};

    // Performance timing jitter
    const origNow = performance.now.bind(performance);
    performance.now = function() {{ return origNow() + Math.random() * 0.01; }};

    // Date.now jitter
    const origDateNow = Date.now;
    Date.now = function() {{ return origDateNow() + Math.floor(Math.random()); }};

    // Delete automation markers
    ['cdc_adoQpoasnfa76pfcZLmcfl_Array', 'cdc_adoQpoasnfa76pfcZLmcfl_Promise',
     'cdc_adoQpoasnfa76pfcZLmcfl_Symbol', '__selenium_unwrapped', '__webdriver_evaluate',
     '__driver_evaluate', '__webdriver_unwrapped', '__driver_unwrapped',
     '__fxdriver_evaluate', '__fxdriver_unwrapped'].forEach(prop => {{
        try {{ delete navigator[prop]; }} catch(e) {{}}
    }});

    // userAgentData
    Object.defineProperty(navigator, 'userAgentData', {{
        get: () => ({{
            brands: [
                {{ brand: 'Chromium', version: '{random.randint(120, 128)}' }},
                {{ brand: 'Google Chrome', version: '{random.randint(120, 128)}' }},
                {{ brand: 'Not_A Brand', version: '24' }}
            ],
            mobile: false,
            platform: 'Windows'
        }})
    }});

    // outerWidth/outerHeight
    window.outerWidth = {resolution['width']};
    window.outerHeight = {resolution['height'] - 80};

    // Notification permission
    Object.defineProperty(Notification, 'permission', {{ get: () => 'default' }});
    """


def apply_stealth(page: Page, country_code: str = "US", user_agent: str = "") -> None:
    """Apply stealth script to a Playwright page."""
    script = get_stealth_script(country_code, user_agent)
    page.add_init_script(script)


CHROME_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-webrtc",
    "--disable-extensions",
    "--disable-infobars",
    "--window-size=1920,1080",
    "--start-maximized",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-breakpad",
    "--disable-client-side-phishing-detection",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-domain-reliability",
    "--disable-hang-monitor",
    "--disable-ipc-flooding-protection",
    "--disable-popup-blocking",
    "--disable-prompt-on-repost",
    "--disable-renderer-backgrounding",
    "--disable-sync",
    "--metrics-recording-only",
    "--no-first-run",
    "--password-store=basic",
    "--use-mock-keychain",
]
