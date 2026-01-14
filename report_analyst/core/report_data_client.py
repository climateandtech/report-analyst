"""
Sustainability Report Data Client

Unified client for accessing sustainability report data from multiple sources.
Uses URN-based resource identification (IETF RFC 8141 standard).
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ReportResource:
    """Sustainability report resource with URN-based identification"""

    name: str
    uri: str  # urn:report-analyst:backend:host:resource_id or file://path
    date: Optional[float] = None  # Timestamp
    size: Optional[int] = None  # File size in bytes
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata

    @property
    def is_backend_resource(self) -> bool:
        """Check if this is a backend resource (URN)"""
        return self.uri.startswith("urn:report-analyst:backend:")

    @property
    def is_local_resource(self) -> bool:
        """Check if this is a local resource"""
        return self.uri.startswith("file://") or Path(self.uri).exists()

    def parse_backend_urn(self) -> Optional[Dict[str, str]]:
        """Parse URN: urn:report-analyst:backend:host:resource_id

        Handles both with and without ports:
        - urn:report-analyst:backend:localhost:8000:abc-123 (host:port:resource_id)
        - urn:report-analyst:backend:api.example.com:abc-123 (host:resource_id)
        """
        if not self.is_backend_resource:
            return None
        # urn:report-analyst:backend:localhost:8000:abc-123
        # or urn:report-analyst:backend:api.example.com:abc-123
        parts = self.uri.replace("urn:report-analyst:backend:", "").split(":")
        if len(parts) >= 2:
            # Check if second part looks like a port (numeric)
            if len(parts) >= 3 and parts[1].isdigit():
                # Format: host:port:resource_id
                host = f"{parts[0]}:{parts[1]}"
                resource_id = ":".join(parts[2:])  # Handle resource IDs with colons
            else:
                # Format: host:resource_id (no port or port not numeric)
                host = parts[0]
                resource_id = ":".join(parts[1:])  # Handle resource IDs with colons
            return {"host": host, "resource_id": resource_id}
        return None

    def resolve_to_http_url(self) -> Optional[str]:
        """Resolve URN to HTTP URL for API access"""
        parsed = self.parse_backend_urn()
        if not parsed:
            return None
        # Determine protocol (http vs https) - could be config-based
        protocol = (
            "http"
            if "localhost" in parsed["host"] or "127.0.0.1" in parsed["host"]
            else "https"
        )
        return f"{protocol}://{parsed['host']}/resources/{parsed['resource_id']}"


class ReportDataClient:
    """Unified client for sustainability report data from multiple sources"""

    def __init__(self, temp_dir: Path = Path("temp")):
        self.temp_dir = temp_dir
        self._backend_clients: Dict[str, Any] = {}  # Cache backend clients by host

    def list_reports(
        self, backend_configs: Optional[List[Any]] = None
    ) -> List[ReportResource]:
        """
        List all available sustainability reports from all sources.

        Args:
            backend_configs: Optional list of backend configurations to query

        Returns:
            List of ReportResource objects with URN-based identification
        """
        resources = []

        # Local files
        resources.extend(self._list_local_reports())

        # Backend resources (if configured)
        if backend_configs:
            for config in backend_configs:
                if hasattr(config, "use_backend") and config.use_backend:
                    resources.extend(self._list_backend_reports(config))

        return sorted(resources, key=lambda x: x.date or 0, reverse=True)

    def _list_local_reports(self) -> List[ReportResource]:
        """List local PDF files from temp directory"""
        if not self.temp_dir.exists():
            return []

        files = []
        for file in self.temp_dir.glob("*.pdf"):
            # Verify file exists and has reasonable size
            if not file.exists():
                continue

            file_size = file.stat().st_size
            if file_size < 100:  # Minimum size for a valid PDF
                logger.warning(
                    f"Skipping {file.name}: file too small ({file_size} bytes), likely invalid"
                )
                continue

            # Try to validate it's a real PDF by attempting to open it
            try:
                import fitz  # PyMuPDF

                doc = fitz.open(str(file))
                page_count = doc.page_count
                doc.close()
                if page_count == 0:
                    logger.warning(
                        f"Skipping {file.name}: PDF has 0 pages, likely invalid"
                    )
                    continue
            except Exception as e:
                logger.warning(f"Skipping {file.name}: cannot open as PDF ({str(e)})")
                continue

            # Create file:// URI
            file_uri = f"file://{file.resolve()}"
            files.append(
                ReportResource(
                    name=file.name,
                    uri=file_uri,
                    date=file.stat().st_mtime,
                    size=file_size,
                    metadata={"path": str(file.resolve()), "pages": page_count},
                )
            )
            logger.info(
                f"Found valid PDF: {file.name}, size: {file_size} bytes, pages: {page_count}"
            )

        return files

    def _list_backend_reports(self, config: Any) -> List[ReportResource]:
        """List reports from a specific backend"""
        try:
            # Import here to avoid circular dependencies
            from report_analyst_search_backend.backend_service import BackendService

            backend_service = BackendService(config)
            return backend_service.list_reports()
        except Exception as e:
            logger.warning(f"Failed to list backend reports: {e}")
            return []


def get_backend_service_for_urn(urn: str, backend_configs: List[Any]) -> Optional[Any]:
    """Get BackendService instance for a given backend URN"""
    if not urn.startswith("urn:report-analyst:backend:"):
        return None

    resource = ReportResource(name="", uri=urn)
    parsed = resource.parse_backend_urn()
    if not parsed:
        return None

    # Find matching backend config
    for config in backend_configs:
        if not hasattr(config, "backend_url"):
            continue
        normalized = config.backend_url.replace("http://", "").replace("https://", "")
        if normalized == parsed["host"]:
            from report_analyst_search_backend.backend_service import BackendService

            return BackendService(config)

    return None


def get_chunks_for_backend_resource(
    urn: str, backend_configs: List[Any]
) -> Optional[List[Dict[str, Any]]]:
    """
    Get chunks for a backend resource identified by URN.

    Args:
        urn: URN identifying the backend resource
        backend_configs: List of backend configurations

    Returns:
        List of chunks or None if resource not found
    """
    backend_service = get_backend_service_for_urn(urn, backend_configs)
    if not backend_service:
        return None

    resource = ReportResource(name="", uri=urn)
    parsed = resource.parse_backend_urn()
    if not parsed:
        return None

    # Use BackendService to get chunks
    return backend_service.get_chunks(parsed["resource_id"])
