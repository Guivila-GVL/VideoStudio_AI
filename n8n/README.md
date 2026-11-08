# Automatizaciones n8n y Base de Datos

Este directorio agrupa los flujos de trabajo originales y utilidades de automatización con n8n:

- **`workflows/`**: Contiene los 11 flujos de trabajo de n8n exportados en formato JSON (Fases de agente, LangChain, OpenAI, bots de Telegram y pipelines de producción).
- **`scripts_db/`**: Scripts en Python y sentencias SQL utilizadas para insertar y configurar flujos directamente en la base de datos de n8n (TimescaleDB / PostgreSQL), además de respaldos de credenciales (`credenciales_backup/`).
