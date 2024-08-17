import hashlib
import json
import random


def get_random_videocard() -> str:
    videocards = [
        "GeForce GTX 1660 Super",
        "GeForce GTX 1660 Ti",
        "GeForce GTX 1650",
        "GeForce GTX 1660",
        "GeForce GTX 1650 Super",
        "GeForce GTX 1080 Ti",
        "GeForce GTX 1060",
        "GeForce GTX 1050 Ti",
        "GeForce GTX 1050",
        "GeForce GTX 980",
    ]

    return random.choice(videocards)


def get_random_resolution() -> tuple[int, int]:
    resolutions = [
        (2560, 1440),
        (1920, 1080),
        (1366, 768),
        (1280, 720),
    ]

    return random.choice(resolutions)


def get_random_hash(fingerprint: dict) -> str:
    fingerprint_str = json.dumps(fingerprint, sort_keys=True)
    fingerprint_hash = hashlib.sha256(fingerprint_str.encode()).hexdigest()
    return fingerprint_hash[:32]


def generate_fingerprint() -> dict:
    fingerprint = {
        "version": "4.2.1",
        "components": {
            "fonts": {
                "value": [
                    "Calibri",
                    "Century",
                    "Century Gothic",
                    "Franklin Gothic",
                    "Leelawadee",
                    "MS Reference Specialty",
                    "MS UI Gothic",
                    "MT Extra",
                    "Marlett",
                    "Microsoft Uighur",
                    "Segoe UI Light",
                ],
                "duration": 122,
            },
            "domBlockers": {"duration": 25},
            "fontPreferences": {
                "value": {
                    "default": 149.3125,
                    "apple": 149.3125,
                    "serif": 149.3125,
                    "sans": 144.015625,
                    "mono": 121.515625,
                    "min": 9.34375,
                    "system": 147.859375,
                },
                "duration": 36,
            },
            "audio": {
                "value": random.uniform(0.0000800000, 0.00008997532),
                "duration": random.randint(100, 114),
            },
            "screenFrame": {"value": [0, 0, 50, 0], "duration": 0},
            "canvas": None,
            "osCpu": {"duration": 0},
            "languages": {"value": [["ru"]], "duration": 0},
            "colorDepth": {"value": random.randint(22, 26), "duration": 0},
            "deviceMemory": {"value": random.randint(7, 8), "duration": 0},
            "screenResolution": {
                "value": None,
                "duration": 0,
            },
            "hardwareConcurrency": {"value": random.randint(10, 12), "duration": 0},
            "timezone": {"value": "Europe/Moscow", "duration": random.randint(2, 5)},
            "sessionStorage": {"value": True, "duration": 0},
            "localStorage": {"value": True, "duration": 0},
            "indexedDB": {"value": True, "duration": 0},
            "openDatabase": {"value": False, "duration": 0},
            "cpuClass": {"duration": 0},
            "platform": {"value": "Win32", "duration": 0},
            "plugins": {
                "value": [
                    {
                        "name": "PDF Viewer",
                        "description": "Portable Document Format",
                        "mimeTypes": [
                            {"type": "application/pdf", "suffixes": "pdf"},
                            {"type": "text/pdf", "suffixes": "pdf"},
                        ],
                    },
                    {
                        "name": "Chrome PDF Viewer",
                        "description": "Portable Document Format",
                        "mimeTypes": [
                            {"type": "application/pdf", "suffixes": "pdf"},
                            {"type": "text/pdf", "suffixes": "pdf"},
                        ],
                    },
                    {
                        "name": "Chromium PDF Viewer",
                        "description": "Portable Document Format",
                        "mimeTypes": [
                            {"type": "application/pdf", "suffixes": "pdf"},
                            {"type": "text/pdf", "suffixes": "pdf"},
                        ],
                    },
                    {
                        "name": "Microsoft Edge PDF Viewer",
                        "description": "Portable Document Format",
                        "mimeTypes": [
                            {"type": "application/pdf", "suffixes": "pdf"},
                            {"type": "text/pdf", "suffixes": "pdf"},
                        ],
                    },
                    {
                        "name": "WebKit built-in PDF",
                        "description": "Portable Document Format",
                        "mimeTypes": [
                            {"type": "application/pdf", "suffixes": "pdf"},
                            {"type": "text/pdf", "suffixes": "pdf"},
                        ],
                    },
                ],
                "duration": 1,
            },
            "touchSupport": {
                "value": {
                    "maxTouchPoints": 0,
                    "touchEvent": False,
                    "touchStart": False,
                },
                "duration": 0,
            },
            "vendor": {"value": "Google Inc.", "duration": 0},
            "vendorFlavors": {"value": ["chrome"], "duration": 0},
            "cookiesEnabled": {"value": True, "duration": 0},
            "colorGamut": {"value": "srgb", "duration": 0},
            "invertedColors": {"duration": 0},
            "forcedColors": {"value": False, "duration": 0},
            "monochrome": {"value": 0, "duration": 0},
            "contrast": {"value": 0, "duration": 0},
            "reducedMotion": {"value": False, "duration": 0},
            "reducedTransparency": {"value": True, "duration": 0},
            "hdr": {"value": False, "duration": 0},
            "math": {
                "value": {
                    "acos": random.uniform(1.4473588658278522, 1.4478588658278522),
                    "acosh": random.uniform(709.889355822726, 709.889455822726),
                    "acoshPf": random.uniform(355.291251501643, 355.291351501643),
                    "asin": random.uniform(0.12343746096704435, 0.12353746096704435),
                    "asinh": random.uniform(0.881373587019543, 0.881473587019543),
                    "asinhPf": random.uniform(0.8813735870195429, 0.8814735870195429),
                    "atanh": random.uniform(0.5493061443340548, 0.5494061443340548),
                    "atanhPf": random.uniform(0.5493061443340548, 0.5494061443340548),
                    "atan": random.uniform(0.4636476090008061, 0.4637476090008061),
                    "sin": random.uniform(0.8178819121159085, 0.8179819121159085),
                    "sinh": random.uniform(1.1752011936438014, 1.1753011936438014),
                    "sinhPf": random.uniform(2.534342107873324, 2.534442107873324),
                    "cos": random.uniform(-0.8390715290095377, -0.8391715290095377),
                    "cosh": random.uniform(1.5430806348152437, 1.5431806348152437),
                    "coshPf": random.uniform(1.5430806348152437, 1.5431806348152437),
                    "tan": random.uniform(-1.4214488238747245, -1.4213488238747245),
                    "tanh": random.uniform(0.7615941559557649, 0.7616941559557649),
                    "tanhPf": random.uniform(0.7615941559557649, 0.7616941559557649),
                    "exp": random.uniform(2.718281828459045, 2.718291828459045),
                    "expm1": random.uniform(1.718281828459045, 1.718381828459045),
                    "expm1Pf": random.uniform(1.718281828459045, 1.718381828459045),
                    "log1p": random.uniform(2.3978952727983707, 2.3979952727983707),
                    "log1pPf": random.uniform(2.3978952727983707, 2.3979952727983707),
                    "powPI": random.uniform(
                        1.9275814160560204e-50, 1.9275815160560204e-50
                    ),
                },
                "duration": 1,
            },
            "pdfViewerEnabled": {"value": True, "duration": 0},
            "architecture": {"value": 255, "duration": 0},
            "applePay": {"value": -1, "duration": 0},
            "privateClickMeasurement": {"duration": 0},
            "webGlBasics": {
                "value": {
                    "version": "WebGL 1.0 (OpenGL ES 2.0 Chromium)",
                    "vendor": "WebKit",
                    "vendorUnmasked": "Google Inc. (NVIDIA)",
                    "renderer": "WebKit WebGL",
                    "rendererUnmasked": f"ANGLE (NVIDIA, NVIDIA {get_random_videocard()} (0x0000{random.randint(2172, 2192)}) Direct3D11 vs_5_0 ps_5_0, D3D11)",
                    "shadingLanguageVersion": "WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
                },
                "duration": 9,
            },
            "webGlExtensions": None,
        },
    }

    random_resolution: tuple[int, int] = get_random_resolution()
    random_hash = get_random_hash(fingerprint=fingerprint)
    fingerprint["visitorId"] = random_hash
    fingerprint["components"]["screenResolution"]["value"] = [
        random_resolution[0],
        random_resolution[1],
    ]
    return fingerprint
