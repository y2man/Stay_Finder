from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    ENVIRONMENT: str = 'development'
    DATABASE_URL: str = 'postgresql+psycopg://stayfinder:change-me@localhost:5432/stayfinder'
    SECRET_KEY: str = 'replace-this-with-a-long-random-secret-before-deployment'
    CORS_ORIGINS: str = 'http://localhost:5173'
    ACCESS_MINUTES: int = 30
    REFRESH_DAYS: int = 14
    SERVICE_FEE_RATE: float = 0.10
    TAX_RATE: float = 0.05
    FRONTEND_URL: str = 'http://localhost:5173'
    SMTP_HOST: str = ''
    SMTP_PORT: int = 587
    SMTP_USER: str = ''
    SMTP_PASSWORD: str = ''
    SMTP_FROM: str = ''
    SMTP_USE_SSL: bool = False
    SMTP_TIMEOUT: int = 15
    STRIPE_SECRET_KEY: str = ''
    STRIPE_WEBHOOK_SECRET: str = ''
    PAYMENT_CURRENCY: str = 'usd'
    GROQ_API_KEY: str = ''
    GROQ_MODEL: str = 'llama-3.3-70b-versatile'
    CLOUDINARY_CLOUD_NAME: str = ''
    CLOUDINARY_API_KEY: str = ''
    CLOUDINARY_API_SECRET: str = ''
    UPLOAD_PROVIDER: str = 'local'
    ADMIN_EMAILS: str = ''

settings = Settings()
