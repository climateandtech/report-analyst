"""
Backend Integration Configuration

Centralized configuration management for all backend integration features.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

import streamlit as st


@dataclass
class BackendConfig:
    """Configuration for backend integration features"""

    use_backend: bool = False
    backend_url: str = "http://localhost:8000"
    use_centralized_llm: bool = False
    use_data_lake: bool = False
    use_full_backend_analysis: bool = False
    nats_url: str = "nats://localhost:4222"
    owner: str = "default_user"
    deployment_type: str = "experiment"
    experiment_name: str = "Streamlit Analysis"
    question_set: str = "tcfd"

    @property
    def has_advanced_features(self) -> bool:
        """Check if any advanced features are enabled"""
        return (
            self.use_centralized_llm
            or self.use_data_lake
            or self.use_full_backend_analysis
        )

    @property
    def flow_type(self) -> str:
        """Determine which flow is being used"""
        if not self.use_backend:
            return "local"
        elif self.use_full_backend_analysis:
            return "complete_backend"
        elif self.use_centralized_llm and self.use_data_lake:
            return "enhanced_integration"
        elif self.use_centralized_llm or self.use_data_lake:
            return "backend_with_features"
        else:
            return "basic_backend"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        return {
            "use_backend": self.use_backend,
            "backend_url": self.backend_url,
            "use_centralized_llm": self.use_centralized_llm,
            "use_data_lake": self.use_data_lake,
            "use_full_backend_analysis": self.use_full_backend_analysis,
            "nats_url": self.nats_url,
            "owner": self.owner,
            "deployment_type": self.deployment_type,
            "experiment_name": self.experiment_name,
            "question_set": self.question_set,
        }


def configure_backend_integration() -> BackendConfig:
    """
    Streamlit UI for configuring backend integration.

    Returns:
        BackendConfig: Configuration object with all settings
    """
    st.sidebar.subheader("🔧 Backend Integration")

    # Basic backend toggle
    use_backend = st.sidebar.checkbox(
        "Use Search Backend",
        value=False,
        help="Send PDFs to search backend for processing",
    )

    if not use_backend:
        return BackendConfig()

    # Backend URL
    backend_url = st.sidebar.text_input(
        "Backend URL", value="http://localhost:8000", help="Search backend API URL"
    )

    # Advanced features
    st.sidebar.subheader("🚀 Advanced Features")

    use_centralized_llm = st.sidebar.checkbox(
        "Use Centralized LLM (NATS)",
        value=False,
        help="Use search backend's LLM via NATS instead of local LLM calls",
    )

    use_data_lake = st.sidebar.checkbox(
        "Enable Data Lake",
        value=False,
        help="Store results in data lake with deployment tracking",
    )

    use_full_backend_analysis = st.sidebar.checkbox(
        "Complete Backend Analysis",
        value=False,
        help="Let search backend do all analysis and store results in its database",
    )

    nats_url = st.sidebar.text_input(
        "NATS URL", value="nats://localhost:4222", help="URL of your NATS server"
    )

    # Data lake configuration
    owner = "default_user"
    deployment_type = "experiment"
    experiment_name = "Streamlit Analysis"

    if use_data_lake:
        st.sidebar.subheader("📊 Data Lake Settings")

        owner = st.sidebar.text_input(
            "Owner/Client ID",
            value="default_user",
            help="Unique identifier for data ownership",
        )

        deployment_type = st.sidebar.selectbox(
            "Deployment Type",
            options=["experiment", "development", "staging", "production"],
            index=0,
            help="Type of deployment for data categorization",
        )

        experiment_name = st.sidebar.text_input(
            "Experiment Name",
            value="Streamlit Analysis",
            help="Name for this analysis session",
        )

    # Test connection
    if st.sidebar.button("Test Connections"):
        _test_connections(backend_url, use_centralized_llm, nats_url)

    return BackendConfig(
        use_backend=use_backend,
        backend_url=backend_url,
        use_centralized_llm=use_centralized_llm,
        use_data_lake=use_data_lake,
        use_full_backend_analysis=use_full_backend_analysis,
        nats_url=nats_url,
        owner=owner,
        deployment_type=deployment_type,
        experiment_name=experiment_name,
    )


def _test_connections(backend_url: str, use_centralized_llm: bool, nats_url: str):
    """Test backend and NATS connections"""
    import requests

    try:
        # Test backend
        response = requests.get(f"{backend_url}/resources/count", timeout=5)
        if response.status_code == 200:
            st.sidebar.success("✅ Backend connected!")
        else:
            st.sidebar.error(f"❌ Backend connection failed: {response.status_code}")

        # Test NATS if enabled
        if use_centralized_llm:
            st.sidebar.info("🔄 NATS connection test not implemented yet")

    except Exception as e:
        st.sidebar.error(f"❌ Connection error: {str(e)}")


def display_config_status(config: BackendConfig):
    """Display current configuration status in main area"""
    if config.use_backend:
        st.info(f"🔗 Using search backend at: {config.backend_url}")

        if config.use_centralized_llm:
            st.info(f"🤖 Using centralized LLM via NATS: {config.nats_url}")

        if config.use_data_lake:
            st.info(
                f"📊 Data lake enabled for owner: {config.owner} ({config.deployment_type})"
            )

        if config.use_full_backend_analysis:
            st.info("🏭 Complete backend analysis enabled - backend does all the work!")

    # Show flow type
    flow_descriptions = {
        "local": "📱 Local processing only",
        "basic_backend": "🔗 Basic backend processing",
        "backend_with_features": "🚀 Backend with enhanced features",
        "enhanced_integration": "✨ Full integration (Flow 3)",
        "complete_backend": "🏭 Complete backend analysis (Flow 4)",
    }

    flow_desc = flow_descriptions.get(config.flow_type, "❓ Unknown flow")
    st.info(f"**Current Flow:** {flow_desc}")
