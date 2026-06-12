import os
import pytest
from unittest.mock import MagicMock, patch
from app.core.config import Settings
from app.storage.object_storage import ObjectStorageAdapter

def test_local_storage_fallback():
    """
    Verifies that ObjectStorageAdapter falls back to local storage when S3 settings are missing.
    """
    settings = Settings(
        S3_BUCKET_NAME=None,
        S3_ACCESS_KEY_ID=None,
        S3_SECRET_ACCESS_KEY=None
    )
    adapter = ObjectStorageAdapter(settings)
    assert adapter.use_s3 is False
    assert adapter.s3_client is None

    test_key = "test_ws/files/test.txt"
    test_data = b"hello world"
    
    # Save file
    storage_uri = adapter.put_object(test_key, test_data, "text/plain")
    assert os.path.isabs(storage_uri)
    assert os.path.exists(storage_uri)

    # Read file
    retrieved = adapter.get_object(storage_uri)
    assert retrieved == test_data

    # Delete file
    deleted = adapter.delete_object(storage_uri)
    assert deleted is True
    assert not os.path.exists(storage_uri)

@patch("boto3.client")
def test_s3_storage_active(mock_boto_client):
    """
    Verifies that ObjectStorageAdapter interacts with boto3 when S3 settings are configured.
    """
    settings = Settings(
        S3_BUCKET_NAME="my-bucket",
        S3_ACCESS_KEY_ID="access_key",
        S3_SECRET_ACCESS_KEY="secret_key",
        S3_ENDPOINT_URL="http://mock-minio:9000",
        S3_REGION_NAME="us-east-1"
    )
    
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3
    
    adapter = ObjectStorageAdapter(settings)
    assert adapter.use_s3 is True
    
    # Trigger client load
    client = adapter.s3_client
    assert client == mock_s3
    from unittest.mock import ANY
    mock_boto_client.assert_called_once_with(
        "s3",
        aws_access_key_id="access_key",
        aws_secret_access_key="secret_key",
        region_name="us-east-1",
        endpoint_url="http://mock-minio:9000",
        config=ANY
    )

    
    # Test put_object
    test_key = "workspaces/ws_123/files/data.csv"
    test_data = b"col1,col2\nval1,val2"
    uri = adapter.put_object(test_key, test_data, "text/csv")
    assert uri == "s3://my-bucket/workspaces/ws_123/files/data.csv"
    
    mock_s3.put_object.assert_called_once_with(
        Bucket="my-bucket",
        Key=test_key,
        Body=test_data,
        ContentType="text/csv"
    )

    # Test get_object
    mock_body = MagicMock()
    mock_body.read.return_value = test_data
    mock_s3.get_object.return_value = {"Body": mock_body}
    
    retrieved = adapter.get_object("s3://my-bucket/workspaces/ws_123/files/data.csv")
    assert retrieved == test_data
    mock_s3.get_object.assert_called_once_with(
        Bucket="my-bucket",
        Key="workspaces/ws_123/files/data.csv"
    )

    # Test delete_object
    success = adapter.delete_object("s3://my-bucket/workspaces/ws_123/files/data.csv")
    assert success is True
    mock_s3.delete_object.assert_called_once_with(
        Bucket="my-bucket",
        Key="workspaces/ws_123/files/data.csv"
    )
