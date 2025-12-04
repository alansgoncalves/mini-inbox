import json
import os
from pathlib import Path
from datetime import datetime

# Importar o FastAPI, a base do modelo e a sessão do banco
from fastapi import FastAPI, Depends, HTTPException
from .models import Ticket, create_tables, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

# --- CONFIGURAÇÕES DE CAMINHO ---
# Pega o caminho para o diretório raiz do projeto (main.py)
# .parent.parent sobe dois níveis (de backend/ para a raiz do projeto)
BASE_DIR = Path(__file__).resolve().parent.parent

# Caminhos para os arquivos
SEEDS_FILE = BASE_DIR / "backend" / "seeds" / "initial_tickets.json"
METRICS_FILE = BASE_DIR / "data" / "processed" / "metrics.json"

# --- FUNÇÕES DE SEEDING E CONEXÃO ---
# Função geradora de dependência pra obter uma sessão de banco de dados
def get_db(): 
    db = SessionLocal() # Cria uma nova sessão
    try:
        yield db # Fornece a sessão para a rota que a requisitou
    finally:
        db.close() # Garante que a sessão seja fechada após o uso

# Função para popular o banco de dados com dados iniciais
def seed_database():
    db = SessionLocal() # Cria uma sessão dedicada para o seeding
    try:
        # Verifica se já existem tickets no banco
        if db.query(Ticket).count() == 0:
            print("Populando o banco de dados com 20 tickets iniciais...")
            # Verifica se o arquivo de seeds existe
            if not SEEDS_FILE.exists():
                print(f"ERRO: Arquivo de seeds não encontrado em {SEEDS_FILE}")
                return
            # Lê o arquivo JSON com os dados iniciais
            with open(SEEDS_FILE, 'r', encoding='utf-8') as f:
                seed_data = json.load(f)

            # Itera sobre cada ticket no arquivo JSON
            for item in seed_data:
                # Converte a string ISO de data para objeto datetime
                created_at_dt = datetime.fromisoformat(item["created_at"])
                # Cria uma nova instância do modelo Ticket
                ticket = Ticket(
                    created_at=created_at_dt,
                    customer_name=item["customer_name"],
                    channel=item["channel"],
                    subject=item["subject"],
                    status=item["status"],
                    priority=item["priority"]
                )
                db.add(ticket) # Adiciona o ticket à sessão
            # Salva todas as mudanças no banco de dados de uma vez
            db.commit()
            print("Seeds inseridos com sucesso!")
        else:
            print("O banco de dados já contém tickets. Pulando o seeding.")
            
    except Exception as e:
        # Se ocorrer algum erro, desfaz as mudanças
        print(f"Erro ao inserir seeds: {e}")
        db.rollback()
    finally:
        # Sempre fecha a sessão, independente de sucesso ou erro
        db.close()

# --- SCHEMAS (Modelos Pydantic para Validação) ---
# Define o schema (formato) dos dados de um ticket para a API
# BaseModel do Pydantic valida e serializa os dados automaticamente
class TicketBase(BaseModel):
    # Campos que serão retornados na API
    id: int  # ID único do ticket
    created_at: datetime  # Data e hora de criação
    customer_name: str  # Nome do cliente
    channel: str  # Canal de origem (email, chat, telefone, etc)
    subject: str  # Assunto/título do ticket
    status: str  # Status atual (open, closed, pending, etc)
    priority: str  # Prioridade (low, medium, high)

    class Config:
        # Permite que o Pydantic leia diretamente objetos ORM (SQLAlchemy)
        # Sem isso, seria necessário converter manualmente o objeto Ticket para dict
        from_attributes = True

# --- INICIALIZAÇÃO DO APP ---

# Cria a instância do FastAPI
app = FastAPI(title="Mini Inbox Backend")

# Decorator que executa a função quando o servidor inicia
@app.on_event("startup")
def startup_event():
    """Executado quando o servidor inicia."""
    # Cria as tabelas no banco se não existirem
    create_tables() 
    # Popula o banco se necessário
    seed_database()

# Endpoint GET para retornar métricas do dashboard geradas pelo script ETL
@app.get("/metrics", tags=["Dashboard"])
def get_metrics():
    """
    Retorna as métricas prontas geradas pelo script ETL com pandas.
    """
    # Verifica se o arquivo de métricas existe
    if not METRICS_FILE.exists():
        # Retorna erro 500 se o arquivo não for encontrado
        raise HTTPException(
            status_code=500, 
            detail="Arquivo de métricas não encontrado. Execute o 'python data/etl.py'."
        )
    
    try:
        # Abre e lê o arquivo JSON com as métricas
        with open(METRICS_FILE, 'r', encoding='utf-8') as f:
            metrics_data = json.load(f)
        # Retorna os dados como resposta JSON
        return metrics_data
    
    except json.JSONDecodeError:
        # Erro se o JSON estiver malformado
        raise HTTPException(
            status_code=500, 
            detail="Erro ao ler o arquivo de métricas. JSON inválido."
        )
    except Exception as e:
        # Captura qualquer outro erro inesperado
        raise HTTPException(status_code=500, detail=f"Erro desconhecido: {e}")

# Endpoint GET para listar todos os tickets
@app.get("/tickets", response_model=List[TicketBase], tags=["Tickets"])
def list_tickets(
    db: Session = Depends(get_db), # Injeta a sessão do banco via dependência
    search: Optional[str] = None  # Parâmetro opcional de query string (?search=termo)
):
    """
    Lista todos os tickets no banco de dados, com opção de filtrar por termos de busca.
    A busca é aplicada no assunto (subject) ou no nome do cliente (customer_name).
    
    Exemplos de uso:
    - GET /tickets → retorna todos os tickets
    - GET /tickets?search=problema → retorna tickets com "problema" no subject ou customer_name
    """

    # Cria query base para buscar todos os tickets
    query = db.query(Ticket) 
    
    # Lógica de Busca Simples
    if search:
        # Cria um filtro OR (OU): busca no subject OU customer_name (case-insensitive com .ilike)
        search_filter = Ticket.subject.ilike(f"%{search}%") | \
                        Ticket.customer_name.ilike(f"%{search}%")
        # Aplica o filtro à query
        query = query.filter(search_filter)
        
    # Ordena por data de criação de forma descendente (mais recentes primeiro)
    # .desc() = ordem descendente (mais recentes primeiro)
    # .all() = executa a query e retorna uma lista com todos os resultados
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    # Retorna a lista de tickets
    # O FastAPI e Pydantic convertem automaticamente os objetos ORM para JSON
    # usando o schema TicketBase definido no response_model
    return tickets