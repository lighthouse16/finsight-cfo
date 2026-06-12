import logging
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
import redis
import boto3
import httpx
from botocore.config import Config as BotoConfig

from app.core.config import settings
from app.core.auth import get_request_context, RequestContext
from app.db.session import get_engine

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/validate-production-env")
def validate_production_env(context: RequestContext = Depends(get_request_context)) -> Dict[str, Any]:
    """
    Runs production-readiness check & smoke test against Postgres/TimescaleDB, Redis, S3, and OIDC.
    If a service is unconfigured, returns 'provider_not_configured'.
    If validation fails, returns details about the failure.
    """
    # Enforce admin only
    if context.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to validate production environment."
        )

    results = {}
    overall_ok = True

    # 1. Postgres + TimescaleDB check
    results["postgres_timescale"] = check_postgres_timescale()

    # 2. Redis check
    results["redis"] = check_redis()

    # 3. Object Storage check
    results["object_storage"] = check_object_storage()

    # 4. OIDC check
    results["oidc"] = check_oidc()

    # Calculate overall status
    for service, res in results.items():
        if res["status"] == "failed":
            overall_ok = False
            break

    return {
        "status": "ok" if overall_ok else "failed",
        "checks": results
    }


def check_postgres_timescale() -> Dict[str, Any]:
    if settings.normalized_persistence_backend != "database":
        return {
            "status": "not_applicable",
            "details": "Persistence backend is not configured to use database."
        }

    db_url = settings.TIMESCALE_DATABASE_URL or settings.DATABASE_URL
    if not db_url or "sqlite" in db_url:
        return {
            "status": "provider_not_configured",
            "details": "A real PostgreSQL/TimescaleDB database URL is not configured."
        }

    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Check basic connection
            conn.execute(text("SELECT 1"))
            
            # Check TimescaleDB extension
            timescale_active = False
            try:
                res = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'timescaledb'")).fetchone()
                if res:
                    timescale_active = True
            except Exception:
                # pg_extension or some query failed, ignore
                pass

        return {
            "status": "ok",
            "details": "Successfully connected to Postgres database.",
            "timescaledb_active": timescale_active
        }
    except Exception as e:
        logger.error(f"Postgres/TimescaleDB health check failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


def check_redis() -> Dict[str, Any]:
    if settings.normalized_queue_backend != "redis":
        return {
            "status": "not_applicable",
            "details": "Queue backend is not configured to use Redis."
        }

    redis_url = settings.QUEUE_REDIS_URL or settings.REDIS_URL
    if not redis_url:
        return {
            "status": "provider_not_configured",
            "details": "Redis URL is not configured."
        }

    try:
        r = redis.Redis.from_url(redis_url, socket_connect_timeout=2.0)
        # Test connection
        r.ping()
        
        # Test read/write/delete cache cycle
        test_key = f"smoke_test:{int(time.time())}"
        r.setex(test_key, 10, "val")
        val = r.get(test_key)
        if val:
            val = val.decode("utf-8")
        r.delete(test_key)

        if val != "val":
            raise RuntimeError(f"Cache write/read cycle failed. Expected 'val', got '{val}'")

        return {
            "status": "ok",
            "details": "Redis connection ping and write-read cycle passed successfully."
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


def check_object_storage() -> Dict[str, Any]:
    if settings.normalized_object_storage_backend != "s3":
        return {
            "status": "not_applicable",
            "details": "Object storage backend is not configured to use S3."
        }

    bucket = settings.S3_BUCKET
    access_key = settings.S3_ACCESS_KEY_ID
    secret_key = settings.S3_SECRET_ACCESS_KEY

    if not bucket or not access_key or not secret_key:
        return {
            "status": "provider_not_configured",
            "details": "S3 object storage is missing bucket or credential config."
        }

    try:
        client_kwargs = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": settings.S3_REGION,
            "config": BotoConfig(signature_version="s3v4")
        }
        if settings.S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

        s3 = boto3.client("s3", **client_kwargs)
        
        # Run S3 upload/download/delete smoke test
        test_key = f"smoke_test_{int(time.time())}.txt"
        test_body = b"s3_smoke_test_content"
        
        # 1. Put
        s3.put_object(Bucket=bucket, Key=test_key, Body=test_body, ContentType="text/plain")
        
        # 2. Get
        resp = s3.get_object(Bucket=bucket, Key=test_key)
        downloaded = resp["Body"].read()
        
        # 3. Delete
        s3.delete_object(Bucket=bucket, Key=test_key)
        
        if downloaded != test_body:
            raise RuntimeError("Downloaded smoke test body did not match uploaded body.")
            
        return {
            "status": "ok",
            "details": f"Successfully performed S3 upload/download/delete smoke test in bucket '{bucket}'."
        }
    except Exception as e:
        logger.error(f"S3 object storage health check failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


def check_oidc() -> Dict[str, Any]:
    if settings.normalized_auth_mode != "oidc":
        return {
            "status": "not_applicable",
            "details": "Authentication mode is not configured to use OIDC."
        }

    issuer = settings.OIDC_ISSUER_URL
    jwks_url = settings.OIDC_JWKS_URL

    if not issuer and not jwks_url:
        return {
            "status": "provider_not_configured",
            "details": "OIDC issuer and JWKS URLs are not configured."
        }

    try:
        discovered_url = jwks_url
        # 1. If JWKS URL is missing, attempt discovery from issuer
        if not discovered_url and issuer:
            discovery_url = f"{issuer.rstrip('/')}/.well-known/openid-configuration"
            resp = httpx.get(discovery_url, timeout=3.0)
            resp.raise_for_status()
            discovered_url = resp.json().get("jwks_uri")
            
        if not discovered_url:
            raise RuntimeError("JWKS URL could not be resolved from OIDC config or settings.")
            
        # 2. Fetch JWKS keys to verify OIDC provider connectivity
        resp = httpx.get(discovered_url, timeout=3.0)
        resp.raise_for_status()
        jwks = resp.json()
        keys = jwks.get("keys", [])
        
        return {
            "status": "ok",
            "details": f"OIDC provider is reachable. Successfully retrieved {len(keys)} public keys from JWKS."
        }
    except Exception as e:
        logger.error(f"OIDC health check failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }
