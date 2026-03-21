"""
Data Lake Integration

This module implements the search backend as a central data lake with:
- Proper data provenance (where data comes from)
- Deployment management (production vs experiments)
- Ownership/tenant isolation
- Analysis results storage
- Configuration deployment from report-analyst

Architecture:
- All data stored in search backend with rich metadata
- Report-analyst "deploys" configurations creating deployment identifiers
- Can filter production vs experimental data
- Clear ownership and provenance tracking
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class DataSource(str, Enum):
    REPORT_ANALYST = "report_analyst"
    DIRECT_UPLOAD = "direct_upload"
    BULK_IMPORT = "bulk_import"
    API_UPLOAD = "api_upload"
    EXPERIMENT = "experiment"


class DeploymentType(str, Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    EXPERIMENT = "experiment"
    DEVELOPMENT = "development"


@dataclass
class DeploymentConfig:
    """Configuration deployed from report-analyst"""

    id: str
    name: str
    description: str
    deployment_type: DeploymentType
    owner: str  # Client/tenant identifier
    question_set: str
    model_config: Dict[str, Any]
    analysis_config: Dict[str, Any]
    created_at: datetime = None
    deployed_at: datetime = None
    version: str = "1.0"
    tags: List[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.tags is None:
            self.tags = []


@dataclass
class DataMetadata:
    """Enhanced metadata for all data in the lake"""

    source: DataSource
    owner: str  # Client/tenant identifier
    deployment_id: Optional[str] = None  # Links to deployment config
    experiment_id: Optional[str] = None  # For experimental data
    original_filename: Optional[str] = None
    upload_method: Optional[str] = None
    processing_config: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None
    tags: List[str] = None
    custom_metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.custom_metadata is None:
            self.custom_metadata = {}


@dataclass
class AnalysisResult:
    """Analysis results stored in the data lake"""

    id: str
    deployment_id: str
    resource_id: str
    question_set: str
    model_used: str
    results: Dict[str, Any]
    metadata: DataMetadata
    processing_time: Optional[float] = None
    confidence_scores: Optional[Dict[str, float]] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class DataLakeClient:
    """Client for interacting with the search backend data lake"""

    def __init__(self, backend_url: str = "http://localhost:8000", owner: str = "default"):
        self.backend_url = backend_url
        self.owner = owner

    async def deploy_configuration(self, config: DeploymentConfig) -> str:
        """Deploy a configuration to the data lake"""
        async with aiohttp.ClientSession() as session:
            # Store deployment configuration in search backend
            deployment_data = {
                **asdict(config),
                "deployed_at": datetime.utcnow().isoformat(),
            }

            async with session.post(f"{self.backend_url}/deployments/", json=deployment_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Deployed configuration {config.id} to data lake")
                    return result.get("deployment_id", config.id)
                else:
                    raise Exception(f"Failed to deploy configuration: {response.status}")

    async def upload_document_with_metadata(
        self,
        document_url: str,
        metadata: DataMetadata,
        deployment_id: Optional[str] = None,
    ) -> str:
        """Upload document with enhanced metadata"""
        async with aiohttp.ClientSession() as session:
            # Enhanced resource creation with metadata
            resource_data = {
                "url": document_url,
                "tags": metadata.tags,
                "resource_metadata": {
                    "data_lake_metadata": asdict(metadata),
                    "deployment_id": deployment_id,
                    "owner": self.owner,
                    "ingestion_time": datetime.utcnow().isoformat(),
                },
            }

            async with session.post(f"{self.backend_url}/resources/", json=resource_data) as response:
                if response.status == 200:
                    resource = await response.json()
                    logger.info(f"Uploaded document to data lake with metadata")
                    return resource["id"]
                else:
                    raise Exception(f"Failed to upload document: {response.status}")

    async def store_analysis_result(self, result: AnalysisResult) -> str:
        """Store analysis results in the data lake"""
        async with aiohttp.ClientSession() as session:
            # Store analysis results as a special resource type
            analysis_data = {
                "url": f"analysis://result/{result.id}",
                "tags": ["analysis_result"],
                "resource_metadata": {
                    "type": "analysis_result",
                    "analysis_data": asdict(result),
                    "owner": self.owner,
                    "created_at": datetime.utcnow().isoformat(),
                },
            }

            async with session.post(f"{self.backend_url}/resources/", json=analysis_data) as response:
                if response.status == 200:
                    resource = await response.json()
                    logger.info(f"Stored analysis result {result.id} in data lake")
                    return resource["id"]
                else:
                    raise Exception(f"Failed to store analysis result: {response.status}")

    async def get_deployment_data(self, deployment_id: str, data_types: List[str] = None) -> Dict[str, Any]:
        """Get all data for a specific deployment"""
        if data_types is None:
            data_types = ["documents", "chunks", "analysis_results"]

        deployment_data = {
            "deployment_id": deployment_id,
            "owner": self.owner,
            "data": {},
        }

        async with aiohttp.ClientSession() as session:
            # Get documents for this deployment
            if "documents" in data_types:
                documents = await self._get_documents_by_deployment(session, deployment_id)
                deployment_data["data"]["documents"] = documents

            # Get analysis results for this deployment
            if "analysis_results" in data_types:
                results = await self._get_analysis_results_by_deployment(session, deployment_id)
                deployment_data["data"]["analysis_results"] = results

            # Get chunks for documents in this deployment
            if "chunks" in data_types:
                chunks = await self._get_chunks_by_deployment(session, deployment_id)
                deployment_data["data"]["chunks"] = chunks

        return deployment_data

    async def list_deployments(self, deployment_type: Optional[DeploymentType] = None) -> List[Dict[str, Any]]:
        """List all deployments for this owner"""
        async with aiohttp.ClientSession() as session:
            # Filter resources by deployment metadata
            params = {"owner": self.owner}
            if deployment_type:
                params["deployment_type"] = deployment_type.value

            async with session.get(f"{self.backend_url}/deployments/", params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return []

    async def filter_production_data(self) -> Dict[str, Any]:
        """Get only production data (filter out experiments)"""
        return await self.get_data_by_type(DeploymentType.PRODUCTION)

    async def get_data_by_type(self, deployment_type: DeploymentType) -> Dict[str, Any]:
        """Get data filtered by deployment type"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.backend_url}/resources/",
                params={
                    "owner": self.owner,
                    "deployment_type": deployment_type.value,
                    "limit": 1000,
                },
            ) as response:
                if response.status == 200:
                    resources = await response.json()

                    # Group by data type
                    grouped_data = {
                        "documents": [],
                        "analysis_results": [],
                        "metadata": {
                            "deployment_type": deployment_type.value,
                            "owner": self.owner,
                            "total_resources": len(resources),
                        },
                    }

                    for resource in resources:
                        resource_type = resource.get("resource_metadata", {}).get("type", "document")
                        if resource_type == "analysis_result":
                            grouped_data["analysis_results"].append(resource)
                        else:
                            grouped_data["documents"].append(resource)

                    return grouped_data
                else:
                    return {"error": f"Failed to get data: {response.status}"}

    async def _get_documents_by_deployment(self, session: aiohttp.ClientSession, deployment_id: str) -> List[Dict[str, Any]]:
        """Get documents for a specific deployment"""
        async with session.get(
            f"{self.backend_url}/resources/",
            params={"deployment_id": deployment_id, "type": "document"},
        ) as response:
            if response.status == 200:
                return await response.json()
            return []

    async def _get_analysis_results_by_deployment(
        self, session: aiohttp.ClientSession, deployment_id: str
    ) -> List[Dict[str, Any]]:
        """Get analysis results for a specific deployment"""
        async with session.get(
            f"{self.backend_url}/resources/",
            params={"deployment_id": deployment_id, "type": "analysis_result"},
        ) as response:
            if response.status == 200:
                return await response.json()
            return []

    async def _get_chunks_by_deployment(self, session: aiohttp.ClientSession, deployment_id: str) -> List[Dict[str, Any]]:
        """Get chunks for documents in a specific deployment"""
        # This would use the search endpoint with deployment filtering
        async with session.post(
            f"{self.backend_url}/search/",
            json={
                "query": "document content",
                "top_k": 1000,
                "threshold": 0.0,
                "filters": {"deployment_id": deployment_id, "owner": self.owner},
            },
        ) as response:
            if response.status == 200:
                search_results = await response.json()
                chunks = []
                for result in search_results.get("results", []):
                    for chunk_data in result["chunks"]:
                        chunks.append(chunk_data["chunk"])
                return chunks
            return []


class ReportAnalystDataLakeIntegration:
    """Integration layer for report-analyst to use the data lake"""

    def __init__(self, owner: str, backend_url: str = "http://localhost:8000"):
        self.client = DataLakeClient(backend_url, owner)
        self.owner = owner

    async def create_experiment(self, name: str, description: str, question_set: str, config: Dict[str, Any]) -> str:
        """Create a new experiment deployment"""
        deployment = DeploymentConfig(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            deployment_type=DeploymentType.EXPERIMENT,
            owner=self.owner,
            question_set=question_set,
            model_config=config.get("model", {}),
            analysis_config=config.get("analysis", {}),
            tags=["experiment"],
        )

        return await self.client.deploy_configuration(deployment)

    async def promote_to_production(self, experiment_id: str, production_name: str) -> str:
        """Promote an experiment to production"""
        # Get experiment data
        experiment_data = await self.client.get_deployment_data(experiment_id)

        # Create production deployment
        production_deployment = DeploymentConfig(
            id=str(uuid.uuid4()),
            name=production_name,
            description=f"Production deployment promoted from experiment {experiment_id}",
            deployment_type=DeploymentType.PRODUCTION,
            owner=self.owner,
            question_set=experiment_data.get("question_set", "tcfd"),
            model_config=experiment_data.get("model_config", {}),
            analysis_config=experiment_data.get("analysis_config", {}),
            tags=["production", f"from_experiment_{experiment_id}"],
        )

        return await self.client.deploy_configuration(production_deployment)

    async def upload_experimental_document(self, document_url: str, experiment_id: str, filename: str = None) -> str:
        """Upload document for experimentation"""
        metadata = DataMetadata(
            source=DataSource.REPORT_ANALYST,
            owner=self.owner,
            deployment_id=experiment_id,
            experiment_id=experiment_id,
            original_filename=filename,
            upload_method="streamlit_experiment",
            tags=["experiment", "report_analyst"],
        )

        return await self.client.upload_document_with_metadata(document_url, metadata, experiment_id)

    async def store_experiment_results(self, experiment_id: str, resource_id: str, analysis_results: Dict[str, Any]) -> str:
        """Store analysis results for an experiment"""
        metadata = DataMetadata(
            source=DataSource.REPORT_ANALYST,
            owner=self.owner,
            deployment_id=experiment_id,
            experiment_id=experiment_id,
            tags=["analysis_result", "experiment"],
        )

        result = AnalysisResult(
            id=str(uuid.uuid4()),
            deployment_id=experiment_id,
            resource_id=resource_id,
            question_set=analysis_results.get("question_set", "tcfd"),
            model_used=analysis_results.get("model_used", "gpt-4o-mini"),
            results=analysis_results,
            metadata=metadata,
        )

        return await self.client.store_analysis_result(result)

    async def get_production_data(self) -> Dict[str, Any]:
        """Get only production data for this owner"""
        return await self.client.filter_production_data()


# Example usage
async def example_data_lake_usage():
    """Example of using the data lake integration"""

    # Initialize for a specific client/tenant
    integration = ReportAnalystDataLakeIntegration(owner="climate_corp")

    # Create an experiment
    experiment_id = await integration.create_experiment(
        name="TCFD Analysis V2",
        description="Testing new TCFD questions with GPT-4",
        question_set="tcfd_v2",
        config={
            "model": {"name": "gpt-4o-mini", "temperature": 0.1},
            "analysis": {"chunk_overlap": 50, "max_chunks": 20},
        },
    )

    print(f"Created experiment: {experiment_id}")

    # Upload document for experiment
    resource_id = await integration.upload_experimental_document(
        document_url="https://example.com/sustainability-report.pdf",
        experiment_id=experiment_id,
        filename="sustainability-report.pdf",
    )

    print(f"Uploaded document: {resource_id}")

    # Store analysis results
    analysis_results = {
        "question_set": "tcfd_v2",
        "model_used": "gpt-4o-mini",
        "results": [{"question": "Climate risks?", "answer": "Significant risks identified..."}],
    }

    result_id = await integration.store_experiment_results(experiment_id, resource_id, analysis_results)

    print(f"Stored results: {result_id}")

    # Get production data only
    production_data = await integration.get_production_data()
    print(f"Production documents: {len(production_data.get('documents', []))}")


if __name__ == "__main__":
    asyncio.run(example_data_lake_usage())
