import os
from typing import Dict, Any, Tuple, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config as BotoConfig

class S3Store:
    def __init__(self, settings: Any):
        self.settings = settings
        self.bucket = getattr(settings, "S3_BUCKET", "")
        self.endpoint = getattr(settings, "S3_ENDPOINT_URL", "")
        self.region = getattr(settings, "S3_REGION", "us-east-1")
        self.access_key = getattr(settings, "S3_ACCESS_KEY_ID", "")
        self.secret_key = getattr(settings, "S3_SECRET_ACCESS_KEY", "")
        self.force_path_style = getattr(settings, "S3_FORCE_PATH_STYLE", True)
        
        self.is_configured = bool(self.bucket)

    def _get_client(self):
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint if self.endpoint else None,
            aws_access_key_id=self.access_key if self.access_key else None,
            aws_secret_access_key=self.secret_key if self.secret_key else None,
            region_name=self.region if self.region else None,
            config=BotoConfig(s3={'addressing_style': 'path'}) if self.force_path_style else None
        )

    def upload_file(self, workspace_id: str, record_key: str, filename: str, file_bytes: bytes, content_type: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Uploads file to S3 and returns (success, metadata_dict).
        metadata_dict will contain status info like provider_not_configured.
        """
        if not self.is_configured:
            return False, {
                "providerStatus": "provider_not_configured",
                "storageMode": "s3_compatible",
                "warnings": ["S3 bucket is not configured. File will not be persisted in object storage."]
            }
            
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        object_key = f"workspaces/{workspace_id}/{record_key}.{ext}"
        
        s3 = self._get_client()
        try:
            s3.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=file_bytes,
                ContentType=content_type
            )
            # Safe URI creation (no secrets)
            if self.endpoint:
                uri = f"{self.endpoint}/{self.bucket}/{object_key}"
            else:
                uri = f"s3://{self.bucket}/{object_key}"
                
            return True, {
                "providerStatus": "ok",
                "storageMode": "s3_compatible",
                "objectKey": object_key,
                "objectUri": uri,
                "warnings": []
            }
        except (ClientError, NoCredentialsError) as e:
            return False, {
                "providerStatus": "error",
                "storageMode": "s3_compatible",
                "warnings": [f"S3 upload failed: {str(e)}"]
            }

    def delete_file(self, object_key: str) -> bool:
        if not self.is_configured or not object_key:
            return False
            
        s3 = self._get_client()
        try:
            s3.delete_object(Bucket=self.bucket, Key=object_key)
            return True
        except Exception:
            return False

    def get_file_bytes(self, object_key: str) -> Optional[bytes]:
        if not self.is_configured or not object_key:
            return None
            
        s3 = self._get_client()
        try:
            response = s3.get_object(Bucket=self.bucket, Key=object_key)
            return response['Body'].read()
        except Exception:
            return None
