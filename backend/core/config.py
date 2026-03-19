from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_PATH), extra="ignore")

    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:1003@localhost:5432/workplace_intel"
    JWT_PRIVATE_KEY: str = "-----BEGIN RSA PRIVATE KEY-----\nMIIEoQIBAAKCAQEA2lfnfZ/oS8UPkJk/x0DrQLd1lupKdDYL1CnYg7h/sV5VbpJ7\nc3R0Dpgv0Da78JtYFEhE10eA16Tmo8/MAm1/H5GlAF4KWHSEtSlH4/chQo2JxtdY\nwUr/KeW06akn0sAjv47qxuQ9g/DJ0ClnwkKdZTv2ZOq7TeqUvztzaPSUARfj5QtB\nHpVLjVysAuo0oVW9QspSsQekdDIMvyfxX7Uk+02ZlkhuPgHjIvLQAdEXDLDhJwKJ\nBQnSx1ib6lWlk8MnpXkDxiMEH6Xq20I0o34dsWr3C98h+II5Sy+Fl1m2xg4eHybZ\n8ytUDQrTjKVXQkYt/NFYwfQKJKqEokCs4TXPqQIDAQABAoH/bhuzIcCb5M0u8qMi\noD9pluyHRq153odi1ht3YVwpb2Jv5gYsCCbLk11fJbra2Pt974lPLg4t0cUKJCuM\nz6ybiJzQf0VTvxSdCyVGNWNRfCTkb67DLR1YKeJgcw7BUznFM7te3YeisTOi+Na1\nYvTOniUfAsVdFgeDLuzlxof26C7oRJE1uOJs/vSgAmkAQvJkA4SQkcba9oOGrrio\nzIXBNx3JMVWfMFVH8/wtb3AvjdSBBllNt023ohXWbXGJfoz37j7vsAjQ5pXIYqSw\neBi+p6v4hMfm1FrE8AqNaUmnv0KEP/oyIQKeE8Ss5jrZwI87PIDtga6+VlU8CyIk\nDV/ZAoGBAPySD/yEjHovLpTOn9ewT13NHLtJhOaAIZ5on6kL1dGFv0VaCqhby/tB\nd9UuhmNlC+UxT9rVPdmKLPjmf+nhriJ26yzkIK0JCAhksLSKJpNJKsuQ6Il4gRRj\n7boAiWy1y+a8OHtQvZZTMw4nhM/yr+Cn+czKaZdd+KjrAN21dDyFAoGBAN1O3imn\nh6HQ1QOkdMcWAuX7gs1dtj/06yxQF8QGLSZfAe7jXUXvyLRZ6cRA6xTV0OQOLo8f\nuHl2q8s+XqCnAHigi7lFNxRkJfLINu3uJCeNsiORRK8Vzfx3ZbThGFZJ7s5FMuOt\nuDVSwdqtS9s5wSqjTDdGPmbWzaz290OZYjHVAoGBAJvOyzfe2P4jDxxTXv3i0QMv\nnlLXJro/Pv4G0r+pAm1vkbAJvNthTbOhDnifa93zHuRziCyaMb56ZAXjw/MW+qJe\nM/QMgy/bi24KF4w4UVW45EKSETGE+jQG9UcyP5SljbS4ViuUgnAywSMxM9hIgUEY\nvpwcHgl3ugcSegVLg/o1AoGAWq2nIAAx9d6geWaYJr7hHyTH+qfMNjZ/ad/DbSFu\nvIsvOpfUrwRKA4PX4f8Lk7Tsa5VYBHLl3nb+ez+p/D+RVNvLhHVU1TkXx3u77g+m\npsJLXIF4WBkiFrFBbjTRCQIwJDp8WIfks4yeO6DINSJcAMF6SCezB+Y5zgY/WGZv\nsqUCgYA4wk62qc/7s3A47AtiEA8PMuZ1aKX71/AXU9tCPyqmdqn4TU1hw6Am+yYt\nV+aq2nSd1QKzQnnW3IFVFYDmqyPojuTE8ANjpfRggrRZEFeTrMIODSDjGIdhYf45\nmr86GIdeW1MtpmTgm9ypZDa9bRhoro0RrX4xk3TUsoP2fKsNSw==\n-----END RSA PRIVATE KEY-----"
    JWT_PUBLIC_KEY: str = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2lfnfZ/oS8UPkJk/x0Dr\nQLd1lupKdDYL1CnYg7h/sV5VbpJ7c3R0Dpgv0Da78JtYFEhE10eA16Tmo8/MAm1/\nH5GlAF4KWHSEtSlH4/chQo2JxtdYwUr/KeW06akn0sAjv47qxuQ9g/DJ0ClnwkKd\nZTv2ZOq7TeqUvztzaPSUARfj5QtBHpVLjVysAuo0oVW9QspSsQekdDIMvyfxX7Uk\n+02ZlkhuPgHjIvLQAdEXDLDhJwKJBQnSx1ib6lWlk8MnpXkDxiMEH6Xq20I0o34d\nsWr3C98h+II5Sy+Fl1m2xg4eHybZ8ytUDQrTjKVXQkYt/NFYwfQKJKqEokCs4TXP\nqQIDAQAB\n-----END PUBLIC KEY-----"
    ACCESS_TOKEN_TTL_MINUTES: int = 15
    REFRESH_TOKEN_TTL_DAYS: int = 7
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "workplace-intel"
    DYNAMODB_TABLE: str = "workplace-events"
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    RATE_LIMIT_AUTHENTICATED: str = "100/minute"
    RATE_LIMIT_ANONYMOUS: str = "20/minute"


@lru_cache
def get_settings() -> Settings:
    return Settings()