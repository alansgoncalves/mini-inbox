import json
import os
import requests
from pathlib import Path
from datetime import datetime

# Importar o FastAPI, a base do modelo e a sessão do banco
from fastapi import FastAPI, Depends, HTTPException
from .models import Ticket, create_tables, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Mini Inbox Backend")

# --- CONFIGURAÇÃO CORS ---
origins = [
    # Permite acesso do seu frontend Next.js na porta 3000
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    # Adicione a porta do backend se você a acessa diretamente, embora não seja necessário para o Next.js
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,              # Lista de origens permitidas
    allow_credentials=True,             # Permite cookies (se necessário)
    allow_methods=["*"],                # Permite todos os métodos (GET, POST, PATCH, OPTIONS, etc.)
    allow_headers=["*"],                # Permite todos os headers
)

# --- EVENTOS DE INICIALIZAÇÃO ---

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

# Schema para definir quais campos podem ser atualizados
class TicketUpdate(BaseModel):
    """Define quais campos podem ser alterados no PATCH."""
    # Usamos Optional, pois o usuário pode querer alterar apenas o status OU a priority
    status: Optional[str] = None
    priority: Optional[str] = None

# Schema para a resposta da API após atualização
class TicketResponse(TicketBase):
    """
    Schema para a resposta, herdando de TicketBase para incluir todos os campos.
    É usado para garantir que o ticket retornado esteja no formato correto.
    """
    pass # Não adiciona campos novos, apenas reutiliza os de TicketBase

@app.on_event("startup")
def startup_event():
    """Executa quando o servidor inicia."""
    print("Iniciando o servidor...")
    create_tables()
    seed_database()

# --- CONFIGURAÇÃO DO N8N ---
N8N_WEBHOOK_URL = os.environ.get(
    "N8N_WEBHOOK_URL",
    "http://localhost:5678/webhook/f3edc7d6-6ff1-44ee-a2be-475a3e839cc5" # <-- SUBSTITUA PELA SUA URL REAL
)


def send_to_n8n(ticket_data: dict):
    """
    Envia o payload de ticket atualizado para o webhook do n8n.
    Esta função não bloqueia o endpoint principal (aqui é simplificado para não bloquear o response).
    """
    try:
        # Envia uma requisição POST com JSON convertido para o webhook do n8n
        response = requests.post(N8N_WEBHOOK_URL, json=ticket_data, timeout=5)
        response.raise_for_status() # Lança erro para status HTTP 4xx/5xx
        print(f"Sucesso: Ticket {ticket_data['id']} enviado para n8n. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        # Captura erros de conexão, timeout, etc.
        print(f"ERRO: Falha ao enviar ticket para n8n: {e}")

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
    - GET /tickets?search=Alan retorna tickets com "Alan" no subject ou customer_name
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

# Endpoint PATCH para atualizar um ticket
@app.patch("/tickets/{ticket_id}", response_model=TicketResponse, tags=["Tickets"])
def update_ticket(
    ticket_id: int, 
    update_data: TicketUpdate,
    db: Session = Depends(get_db) # Sessão do banco injetada via dependência
):
    """
    Atualiza o status ou a prioridade de um ticket e dispara o webhook do n8n.
    """
    # Buscar o ticket no banco de dados
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    # Se o ticket não existir, retorna erro 404
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket com ID {ticket_id} não encontrado.")
    
    # Aplicar as alterações
    # Rastrea se algum campo foi realmente modificado
    changes_made = False

    # Atualiza o status se foi fornecido na requisição
    # if update_data.status not in ["open", "pending", "closed"]: raise HTTPException(400, "Status inválido")
    if update_data.status is not None:
        # AQUI VOCÊ PODE ADICIONAR VALIDAÇÃO (ex: status in ["open", "pending", "closed"])
        ticket.status = update_data.status
        changes_made = True
    
    # Atualiza a prioridade se foi fornecida na requisição
    # if update_data.priority not in ["low", "medium", "high"]: raise HTTPException(400, "Prioridade inválida")
    if update_data.priority is not None:
        # AQUI VOCÊ PODE ADICIONAR VALIDAÇÃO (ex: priority in ["low", "medium", "high"])
        ticket.priority = update_data.priority
        changes_made = True

    # Se nenhum campo foi enviado para atualização (body vazio: {})    
    if not changes_made:
        # Retorna o ticket sem alterações
        return ticket

    
    db.commit() # Salva as alterações no banco
    db.refresh(ticket)
    
    # Converte o objeto ORM (ticket) para o formato JSON/dict
    ticket_dict = TicketResponse.model_validate(ticket).model_dump()

    # Serializa a data de criação para string ISO 8601
    if 'created_at' in ticket_dict and isinstance(ticket_dict['created_at'], datetime):
        # Converte o objeto datetime para uma string ISO 8601 (o formato ideal para JSON)
        ticket_dict['created_at'] = ticket_dict['created_at'].isoformat()
    
    # Envia o payload para o n8n
    send_to_n8n(ticket_dict)

    # Retorna o ticket atualizado
    return ticket
