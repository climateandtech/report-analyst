# pgvector

--8<-- "snippets/enterprise.md"

This page is `report_analyst_enterprise`. These helpers check and install the Postgres `vector` extension used by the enterprise image. The core image uses its own local store and does not call them.

::: report_analyst_enterprise.database.pgvector_support.check_pgvector_available

::: report_analyst_enterprise.database.pgvector_support.setup_pgvector_extension

::: report_analyst_enterprise.database.pgvector_support.get_vector_distance_func
