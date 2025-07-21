import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple, Union

from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob import BlobSasPermissions, ContentSettings, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient as AsyncBlobServiceClient

from chainlit.data.storage_clients.base import BaseStorageClient, storage_expiry_time
from chainlit.logger import logger


class AzureBlobStorageClient(BaseStorageClient):
    def __init__(
        self,
        container_name: str,
        storage_account: str,
        storage_key: Optional[str] = None,
    ):
        self.container_name = container_name
        self.storage_account = storage_account
        self.storage_key = storage_key
        self.use_managed_identity = not bool(storage_key)

        if self.use_managed_identity:
            credential = DefaultAzureCredential()
            account_url = f"https://{storage_account}.blob.core.windows.net"
            self.service_client = AsyncBlobServiceClient(
                account_url, credential=credential
            )
            self._delegation_key_cache: Optional[Tuple[Any, datetime]] = None
            self._cache_lock = asyncio.Lock()
        else:
            connection_string = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={storage_account};"
                f"AccountKey={storage_key};"
                f"EndpointSuffix=core.windows.net"
            )
            self.service_client = AsyncBlobServiceClient.from_connection_string(
                connection_string
            )

        self.container_client = self.service_client.get_container_client(
            self.container_name
        )
        logger.info("AzureBlobStorageClient initialized")

    async def _get_user_delegation_key(self):
        async with self._cache_lock:
            now = datetime.now(tz=timezone.utc)

            if self._delegation_key_cache and self._delegation_key_cache[
                1
            ] > now + timedelta(minutes=5):
                return self._delegation_key_cache[0]

            start_time = now
            expiry_time = start_time + timedelta(hours=1)

            user_delegation_key = await self.service_client.get_user_delegation_key(
                key_start_time=start_time, key_expiry_time=expiry_time
            )

            self._delegation_key_cache = (user_delegation_key, expiry_time)
            return user_delegation_key

    async def get_read_url(self, object_key: str) -> str:
        sas_permissions = BlobSasPermissions(read=True)
        start_time = datetime.now(tz=timezone.utc)
        expiry_time = start_time + timedelta(seconds=storage_expiry_time)

        if self.use_managed_identity:
            user_delegation_key = await self._get_user_delegation_key()
            sas_token = generate_blob_sas(
                account_name=self.storage_account,
                container_name=self.container_name,
                blob_name=object_key,
                user_delegation_key=user_delegation_key,
                permission=sas_permissions,
                start=start_time,
                expiry=expiry_time,
            )
        else:
            sas_token = generate_blob_sas(
                account_name=self.storage_account,
                container_name=self.container_name,
                blob_name=object_key,
                account_key=self.storage_key,
                permission=sas_permissions,
                start=start_time,
                expiry=expiry_time,
            )

        return f"https://{self.storage_account}.blob.core.windows.net/{self.container_name}/{object_key}?{sas_token}"

    async def upload_file(
        self,
        object_key: str,
        data: Union[bytes, str],
        mime: str = "application/octet-stream",
        overwrite: bool = True,
    ) -> Dict[str, Any]:
        try:
            blob_client = self.container_client.get_blob_client(object_key)

            if isinstance(data, str):
                data = data.encode("utf-8")

            content_settings = ContentSettings(content_type=mime)

            await blob_client.upload_blob(
                data, overwrite=overwrite, content_settings=content_settings
            )

            properties = await blob_client.get_blob_properties()

            return {
                "path": object_key,
                "object_key": object_key,
                "url": await self.get_read_url(object_key),
                "size": properties.size,
                "last_modified": properties.last_modified,
                "etag": properties.etag,
                "content_type": properties.content_settings.content_type,
            }

        except Exception as e:
            raise Exception(f"Failed to upload file to Azure Blob Storage: {e!s}")

    async def delete_file(self, object_key: str) -> bool:
        try:
            blob_client = self.container_client.get_blob_client(blob=object_key)
            await blob_client.delete_blob()
            return True
        except Exception as e:
            logger.warning(f"AzureBlobStorageClient, delete_file error: {e}")
            return False
