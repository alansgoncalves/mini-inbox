import pytest
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Importações do projeto
from backend.main import app, get_db
from backend.models import Base, Ticket
from datetime import datetime, timezone

# 1. Configurar o banco de dados de teste (em memória)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Mock da dependência get_db
def override_get_db():
    """Cria uma sessão de banco de dados de teste isolada."""
    Base.metadata.create_all(bind=engine) # Cria as tabelas
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Aplica o mock no app do FastAPI
app.dependency_overrides[get_db] = override_get_db

# 3. Cria o cliente de teste
client = TestClient(app)

# 4. Fixture de dados iniciais para os testes
@pytest.fixture(scope="module")
def setup_db_with_tickets():
    """Insere dados de teste antes de rodar os testes."""
    # Garante que as tabelas existem antes de inserir
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Insere 2 tickets de teste
    test_tickets = [
        Ticket(
            created_at=datetime.now(timezone.utc),
            customer_name="Test Alan",
            channel="Chat",
            subject="Bug Report",
            status="open",
            priority="high"
        ),
        Ticket(
            created_at=datetime.now(timezone.utc),
            customer_name="Test Emily",
            channel="Email",
            subject="Inquiry about pricing",
            status="closed",
            priority="low"
        )
    ]
    db.add_all(test_tickets)
    db.commit()
    db.refresh(test_tickets[0])
    db.refresh(test_tickets[1])
    db.close()
    # O teardown (limpeza) é feito automaticamente pelo override_get_db

    # Continuação do /backend/tests/test_api.py

def test_get_metrics_success(monkeypatch):
    """Testa se o GET /metrics retorna 200 e os dados esperados."""
    # Como o endpoint lê um arquivo, simulamos a leitura do arquivo e a existência do arquivo.
    monkeypatch.setattr(json, 'load', lambda f: {"total_tickets": 100, "tickets_by_day": []})
    monkeypatch.setattr(Path, 'exists', lambda self: True)
    
    response = client.get("/metrics")
    
    assert response.status_code == 200
    assert response.json()["total_tickets"] == 100


def test_list_tickets_all(setup_db_with_tickets):
    """Testa se o GET /tickets retorna todos os 2 tickets de teste."""
    response = client.get("/tickets")
    
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["customer_name"] == "Test Emily" # Deve estar ordenado por data descendente


def test_list_tickets_search(setup_db_with_tickets):
    """Testa a funcionalidade de busca."""
    response = client.get("/tickets?search=Alan")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["customer_name"] == "Test Alan"


def test_patch_ticket_status_update(setup_db_with_tickets, monkeypatch):
    """Testa o PATCH /tickets/{id} para mudar o status."""
    # ID conhecido (neste setup, o ID 1 e 2 são criados)
    ticket_id = 1
    new_status = "pending"
    
    # Mock do envio do n8n para não falhar
    monkeypatch.setattr('backend.main.send_to_n8n', lambda ticket_data: None, raising=False)
    
    response = client.patch(f"/tickets/{ticket_id}", json={"status": new_status})
    
    assert response.status_code == 200
    assert response.json()["status"] == new_status
    assert response.json()["priority"] == "high" # Prioridade não mudou


def test_patch_ticket_not_found():
    """Testa o PATCH /tickets/{id} quando o ticket não existe."""
    response = client.patch("/tickets/999", json={"status": "closed"})
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Ticket com ID 999 não encontrado."
