from pathlib import Path
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qsl
from datetime import timedelta
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(key, default=False):
    val = os.getenv(key)
    if val is None:
        return default
    return val.lower() in ('true', '1', 'yes', 'on')


SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-only-mude-isso-em-prod")

DEBUG = env_bool("DEBUG", default=True)

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "api-data-sigma-lovat.vercel.app",
    "api-data-backend.onrender.com",
    "192.168.137.1",
    "https://sigepflo.vercel.app",

]

INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    'cloudinary_storage',
    'cloudinary',
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "api",
    "relatorios",
    "cobertura_vacinal",
    "canal_comunicacao",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = "api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "api.wsgi.application"

tmpPostgres = urlparse(os.getenv("DATABASE_URL"))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': tmpPostgres.path.replace('/', ''),
        'USER': tmpPostgres.username,
        'PASSWORD': tmpPostgres.password,
        'HOST': tmpPostgres.hostname,
        'PORT': 5432,
        'OPTIONS': dict(parse_qsl(tmpPostgres.query)),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"  # ✅ Fuso horário do Piauí
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ============================================================
# EMAIL (para dev; use SMTP em produção)
# ============================================================
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    "https://sigepflo.vercel.app",
]

if DEBUG:
    CORS_ALLOWED_ORIGINS += [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://0.0.0.0:8000",
    ]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/hour',  # Visitantes: 60 req/hora
        'user': '2000/hour',  # Usuários logados: 2000 req/hora
        'upload': '10/hour',  # Upload de arquivos: 10/hora
        'chat': '20/hour',  # Chat do assistente: 20/hora
        'export': '30/hour',  # Exportações: 30/hora
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'API SIGEP',
    'DESCRIPTION': 'Documentação dos endpoints do SIGEP',
    'VERSION': '1.0.1',
    'SERVE_INCLUDE_SCHEMA': False,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
}

# 🔥 A forma correta para Django 4.2+ (incluindo o 6.1)
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

UNFOLD = {
    "DASHBOARD_CALLBACK": "api.views.dashboard_callback",
    "SITE_TITLE": "SIGEP admin",
    "SITE_HEADER": "SIGEP",
    "SITE_SUBHEADER": "Vigilância Epidemiológica",
    "SITE_SYMBOL": "health_and_safety",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Painel"),
                "separator": True,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Cadastros"),
                "separator": True,
                "items": [
                    {
                        "title": _("Upload de Arquivos"),
                        "icon": "upload_file",
                        "link": reverse_lazy("admin:api_uploaddbf_changelist"),
                    },
                    {
                        "title": _("Perfis de Usuário"),
                        "icon": "manage_accounts",
                        "link": reverse_lazy("admin:api_perfilusuario_changelist"),
                    },
                ],
            },
            {
                "title": _("Doenças e Agravos"),
                "separator": True,
                "items": [
                    {"title": _("Dengue"), "icon": "coronavirus",
                     "link": reverse_lazy("admin:api_pacientedengue_changelist")},
                    {"title": _("Tuberculose"), "icon": "pulmonology",
                     "link": reverse_lazy("admin:api_pacientetuberculose_changelist")},
                    {"title": _("Sífilis"), "icon": "health_and_safety",
                     "link": reverse_lazy("admin:api_pacientesifilis_changelist")},
                    {"title": _("Doença de Chagas"), "icon": "bug_report",
                     "link": reverse_lazy("admin:api_pacientechagas_changelist")},
                    {"title": _("Violência Doméstica"), "icon": "report",
                     "link": reverse_lazy("admin:api_pacienteviolenciadomestica_changelist")},
                    {"title": _("Hanseníase"), "icon": "dermatology",
                     "link": reverse_lazy("admin:api_pacientehans_changelist")},
                    {"title": _("Hepatites Virais"), "icon": "vaccines",
                     "link": reverse_lazy("admin:api_pacientehepatite_changelist")},
                    {"title": _("Animais Peçonhentos"), "icon": "pest_control",
                     "link": reverse_lazy("admin:api_pacienteanimaispec_changelist")},
                    {"title": _("Intoxicação Exógena"), "icon": "science",
                     "link": reverse_lazy("admin:api_pacienteintoxicacao_changelist")},
                    {"title": _("Leishmaniose"), "icon": "coronavirus",
                     "link": reverse_lazy("admin:api_pacienteleish_changelist")},
                    {"title": _("AIDS Adulto"), "icon": "bloodtype",
                     "link": reverse_lazy("admin:api_pacienteaidsadulto_changelist")},
                ],
            },
            {
                "title": _("Imunização"),
                "separator": True,
                "items": [
                    {
                        "title": _("Cobertura Vacinal"),
                        "icon": "syringe",
                        "link": reverse_lazy("admin:cobertura_vacinal_coberturavacinal_changelist"),
                    },
                ],
            },
            {
                "title": _("Relatórios"),
                "separator": True,
                "items": [
                    {
                        "title": _("Relatórios Mensais"),
                        "icon": "description",
                        "link": reverse_lazy("admin:relatorios_relatoriomensal_changelist"),
                    },
                ],
            },
            {
                "title": _("Comunicação"),
                "separator": True,
                "items": [
                    {
                        "title": _("Canal de Comunicação"),
                        "icon": "forum",
                        "link": reverse_lazy("admin:canal_comunicacao_canalcomunicacao_changelist"),
                    },
                ],
            },
        ],
    },
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
WEASYPRINT_DLL_DIRECTORIES = r"C:\Program Files\GTK3-Runtime Win64\bin"
