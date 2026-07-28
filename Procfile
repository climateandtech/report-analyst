# Heroku Procfile
# Release phase runs migrations before the web dyno starts
release: python -m alembic upgrade head || echo "Migrations skipped (USE_ALEMBIC_MIGRATIONS not enabled or not PostgreSQL)"
web: streamlit run report_analyst/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0


