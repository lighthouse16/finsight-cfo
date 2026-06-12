import os
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class ObjectStorageAdapter:
    """
    Storage adapter that handles writing/reading files to/from either the local filesystem 
    or an S3-compatible service (like MinIO or AWS S3), based on environment configuration.
    """
    def __init__(self, app_settings=settings):
        self.settings = app_settings
        self.use_s3 = bool(
            getattr(self.settings, "S3_BUCKET_NAME", None) and 
            getattr(self.settings, "S3_ACCESS_KEY_ID", None) and 
            getattr(self.settings, "S3_SECRET_ACCESS_KEY", None)
        )
        self._s3_client = None

    @property
    def s3_client(self):
        if not self.use_s3:
            return None
        if self._s3_client is None:
            import boto3
            from botocore.client import Config
            
            endpoint_url = getattr(self.settings, "S3_ENDPOINT_URL", None)
            region_name = getattr(self.settings, "S3_REGION_NAME", "us-east-1")
            
            client_kwargs = {
                "aws_access_key_id": getattr(self.settings, "S3_ACCESS_KEY_ID", None),
                "aws_secret_access_key": getattr(self.settings, "S3_SECRET_ACCESS_KEY", None),
                "region_name": region_name,
                "config": Config(signature_version="s3v4")
            }
            if endpoint_url:
                client_kwargs["endpoint_url"] = endpoint_url
                
            self._s3_client = boto3.client("s3", **client_kwargs)
        return self._s3_client


    def put_object(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """
        Stores file bytes.
        Returns: A storage URI (e.g., s3://bucket/key or absolute path to local file).
        """
        if self.use_s3:
            try:
                bucket = self.settings.S3_BUCKET_NAME
                self.s3_client.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=data,
                    ContentType=content_type
                )
                return f"s3://{bucket}/{key}"
            except Exception as e:
                logger.error(f"S3 upload failed for key {key}: {str(e)}")
                raise RuntimeError(f"Object storage upload failed: {str(e)}")
        else:
            # Fall back to local file storage
            from app.storage.workspace_store import STORAGE_DIR
            upload_root = os.path.join(STORAGE_DIR, "uploads")
            file_path = os.path.join(upload_root, key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(data)
            return os.path.abspath(file_path)

    def get_object(self, storage_uri: str) -> Optional[bytes]:
        """
        Retrieves file bytes from storage URI.
        """
        if not storage_uri:
            return None
            
        if storage_uri.startswith("s3://"):
            if not self.use_s3:
                raise RuntimeError("S3 storage URI provided but S3 is not configured.")
            try:
                # Parse s3://bucket/key
                path_parts = storage_uri[5:].split("/", 1)
                if len(path_parts) != 2:
                    return None
                bucket, key = path_parts
                response = self.s3_client.get_object(Bucket=bucket, Key=key)
                return response["Body"].read()
            except Exception as e:
                logger.error(f"S3 download failed for URI {storage_uri}: {str(e)}")
                return None
        else:
            # Local file path
            if os.path.exists(storage_uri):
                try:
                    with open(storage_uri, "rb") as f:
                        return f.read()
                except Exception:
                    pass
            return None

    def delete_object(self, storage_uri: str) -> bool:
        """
        Deletes object from storage.
        """
        if not storage_uri:
            return False
            
        if storage_uri.startswith("s3://"):
            if not self.use_s3:
                return False
            try:
                path_parts = storage_uri[5:].split("/", 1)
                if len(path_parts) != 2:
                    return False
                bucket, key = path_parts
                self.s3_client.delete_object(Bucket=bucket, Key=key)
                return True
            except Exception as e:
                logger.error(f"S3 delete failed for URI {storage_uri}: {str(e)}")
                return False
        else:
            # Local file path
            if os.path.exists(storage_uri):
                try:
                    os.remove(storage_uri)
                    return True
                except Exception:
                    pass
            return False
