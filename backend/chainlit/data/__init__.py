import os
import warnings
from typing import Optional

from .base import BaseDataLayer
from .utils import (
    queue_until_user_message as queue_until_user_message,  # TODO: Consider deprecating re-export.; Redundant alias tells type checkers to STFU.
)

_data_layer: Optional[BaseDataLayer] = None
_data_layer_initialized = False


def get_data_layer():
    global _data_layer, _data_layer_initialized

    if not _data_layer_initialized:
        if _data_layer:
            # Data layer manually set, warn user that this is deprecated.

            warnings.warn(
                "Setting data layer manually is deprecated. Use @data_layer instead.",
                DeprecationWarning,
            )

        else:
            from chainlit.config import config
            from chainlit.telemetry import trace_event

            if config.code.data_layer:
                # When @data_layer is configured, call it to get data layer.
                _data_layer = config.code.data_layer()
            elif database_url := os.environ.get("DATABASE_URL"):
                from .chainlit_data_layer import ChainlitDataLayer

                trace_event("Init Chainlit official data layer")

                bucket_name = os.environ.get("BUCKET_NAME")

                # Azure Storage
                azure_storage_account = os.getenv("APP_AZURE_STORAGE_ACCOUNT")
                azure_storage_key = os.getenv("APP_AZURE_STORAGE_ACCESS_KEY")
                is_using_azure = bool(azure_storage_account and azure_storage_key)

                storage_client = None

                if is_using_azure:
                    from chainlit.data.storage_clients.azure_blob import (
                        AzureBlobStorageClient,
                    )

                    storage_client = AzureBlobStorageClient(
                        container_name=bucket_name,
                        storage_account=azure_storage_account,
                        storage_key=azure_storage_key,
                    )

                _data_layer = ChainlitDataLayer(
                    database_url=database_url, storage_client=storage_client
                )

        _data_layer_initialized = True

    return _data_layer
