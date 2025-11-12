# Script PowerShell para simular make en Windows
param(
    [string]$Target = ""
)

# Verificar que existe el archivo .env
if (-not (Test-Path ".env")) {
    Write-Error ".env file is missing. Please create one based on .env.example"
    exit 1
}

$CHECK_DIRS = "."

switch ($Target) {
    "format-fix" {
        Write-Host "Ejecutando format-fix..." -ForegroundColor Green
        uv run ruff format $CHECK_DIRS
        uv run ruff check --select I --fix
    }
    
    "lint-fix" {
        Write-Host "Ejecutando lint-fix..." -ForegroundColor Green
        uv run ruff check --fix
    }
    
    "format-check" {
        Write-Host "Ejecutando format-check..." -ForegroundColor Green
        uv run ruff format --check $CHECK_DIRS
        uv run ruff check -e
        uv run ruff check --select I -e
    }
    
    "lint-check" {
        Write-Host "Ejecutando lint-check..." -ForegroundColor Green
        uv run ruff check $CHECK_DIRS
    }
    
    "index-qdrant" {
        Write-Host "Indexing documents to Qdrant..." -ForegroundColor Green
        uv run python -c "from telegram_agent_aws.application.rag_indexing_service.index_documents import index_documents; index_documents()"
        Write-Host "Documents indexed successfully." -ForegroundColor Green
    }
    
    default {
        Write-Host "Targets disponibles:" -ForegroundColor Yellow
        Write-Host "  format-fix     - Formatear código y arreglar imports"
        Write-Host "  lint-fix       - Corregir problemas de linting"
        Write-Host "  format-check   - Verificar formato del código"
        Write-Host "  lint-check     - Verificar problemas de linting"
        Write-Host "  index-qdrant   - Indexar documentos en Qdrant"
        Write-Host ""
        Write-Host "Uso: .\make.ps1 <target>"
        Write-Host "Ejemplo: .\make.ps1 index-qdrant"
    }
}