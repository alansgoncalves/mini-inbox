# 🚀 Desafio Técnico - Mini Inbox Solution

Este projeto implementa uma solução completa de *Mini Inbox* para gestão de tickets, incluindo Backend com FastAPI, Frontend com Next.js (App Router), Persistência de Dados e uma automação de fluxo de trabalho (ETL/Webhook) com n8n, simulando um ecossistema de serviço ao cliente.

O projeto utiliza um dataset de transações de e-commerce no estilo da Amazon, encontrado no Kaggle:
🔗 **Dataset de Transações (Kaggle):** [https://www.kaggle.com/datasets/rohiteng/amazon-sales-dataset]

## 🎯 Requisitos e Funcionalidades

O projeto atende aos seguintes requisitos:

1.  **Backend (FastAPI):** API RESTful completa com endpoints para tickets (`GET`, `PATCH`) e métricas (`GET`).
2.  **Frontend (Next.js):** Interface de usuário com Dashboard, listagem com busca, e página de detalhes para atualização de tickets.
3.  **Persistência de Dados:** Uso de banco de dados SQLite para os tickets e arquivos JSON para métricas.
4.  **ETL e Analytics:** Geração de métricas de negócio a partir do dataset original.
5.  **Automação (n8n):** Configuração de um Webhook para notificação em casos de alta prioridade ou tickets fechados.

---

## ⚙️ Arquitetura do Projeto

A solução é composta por três camadas principais:

| Camada | Tecnologia | Função |
| :--- | :--- | :--- |
| **Backend** | FastAPI, SQLite, Pandas | API RESTful, lógica de negócio, e persistência dos tickets. |
| **Frontend** | Next.js 14+ (App Router), React | Interface web para visualização de métricas e gerenciamento de tickets. |
| **Automação** | n8n | Orquestração do Webhook para notificação em tempo real. |

---

## 🛠️ Como Executar o Projeto (Passo a Passo)

Para rodar o projeto localmente, siga estes passos. É necessário ter **Python (com Pip)**, **Node.js (com npm)** e **Docker (para o n8n)** instalados.

### 1. Inicialização do Backend (FastAPI)

1.  Crie e ative o ambiente virtual na raiz:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate   # Windows
    ```
2.  Instale as dependências:
    ```bash
    pip install -r backend/requirements.txt
    ```
3.  **Execute o script ETL** para popular o banco de dados e gerar as métricas:
    ```bash
    python data/etl.py
    ```
4.  Inicie o servidor Uvicorn:
    ```bash
    uvicorn backend.main:app --reload
    ```
    O Backend estará acessível em `http://127.0.0.1:8000`.

### 2. Configuração da Automação (n8n Webhook)

A n8n será usada para simular o envio de notificação (ex: Slack, Email) quando um ticket for atualizado.

1.  Inicie o n8n via Docker:
    ```bash
    docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
    ```
2.  Acesse o n8n em `http://localhost:5678` e crie um novo *workflow*.
3.  **Adicione um nó de Webhook** e configure-o para o método **`POST`**.
4.  **URL do Webhook:** Obtenha a URL de (`http://localhost:5678/webhook/xxxxxxx/`).
5.  **Nó de Teste:** Conecte o Webhook a um nó de **Log** ou **No-Op** para inspecionar os dados.
6.  **Ative o *Workflow***.

### 3. Configuração do Frontend (Next.js)

1.  Acesse a pasta `/frontend` no seu terminal.
2.  Instale as dependências:
    ```bash
    npm install
    ```
3.  Crie o arquivo de variáveis de ambiente **`.env`** na raiz da pasta `/frontend` e configure a rotas do Backend:
    ```
    # Variável para o Frontend acessar o Backend (FastAPI)
    NEXT_PUBLIC_API_URL=[http://127.0.0.1:8000]
    ```

4.  Inicie o servidor Next.js:
    ```bash
    npm run dev
    ```
    O Frontend estará acessível em `http://localhost:3000`.

---

## 🌐 Endpoints e Rotas Principais

### Backend (FastAPI)

| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| `GET` | `/tickets` | Retorna todos os tickets (com busca opcional via `?search=termo`). |
| `GET` | `/metrics` | Retorna métricas de negócio (total, por dia, top categorias). |
| `PATCH` | `/tickets/{id}` | Atualiza o `status` e/ou `priority` de um ticket. **Aciona o Webhook.** |

### Frontend (Next.js)

| Rota | Descrição |
| :--- | :--- |
| `/` | Redireciona para `/dashboard`. |
| `/dashboard` | Exibe métricas de negócio (total de tickets, tickets por ano). |
| `/tickets` | Tabela de tickets com busca (filtragem client-side). |
| `/tickets/{id}` | Página de detalhes, permitindo atualização de `status` e `priority`. |

---

## ✨ Demonstração da Funcionalidade Webhook (n8n)

O Webhook é acionado no Backend (via endpoint `PATCH /tickets/{id}`).

1.  Acesse um ticket em `http://localhost:3000/tickets/{id}`.
2.  Altere o `Status` para **`closed`** ou a `Prioridade` para **`high`**.
3.  Clique em **"Salvar Alterações"**.
4.  O Backend envia um `POST` para a `N8N_WEBHOOK_URL`.

**Payload Enviado ao Webhook:**

O payload é um objeto JSON que contém as informações do ticket atualizado (por exemplo, `id`, `subject`, `status`, `priority`).

```json
{
  "id": 12,
  "subject": "Duplicate charge",
  "status": "closed",
  "priority": "high",
  "customer_name": "Elijah Scott",
  "channel": "Email",
  "created_at": "2024-01-01T10:00:00"
}
```

## 📸 Demonstração e Evidências do MVP

Esta seção apresenta capturas de tela que comprovam o funcionamento da interface do usuário e o fluxo de automação via n8n.

### 1. Interface (Dashboard ou Listagem de Tickets)

**Evidência da Solução Frontend:**

/dashboard
<img width="1432" height="964" alt="dashboard" src="https://github.com/user-attachments/assets/aba65728-575f-4d2d-9b8f-bb898c534c6c" />

/tickets
<img width="1425" height="979" alt="tickets" src="https://github.com/user-attachments/assets/8e0d10f5-f7a2-4e00-a50f-95fa30bd739d" />


### 2. Automação (Fluxo do n8n)

**Evidência do Workflow n8n:**

workflow
<img width="1681" height="1007" alt="fluxo_n8n" src="https://github.com/user-attachments/assets/0d623d4e-b0e8-4011-b642-62ab5a63604b" />

webhook
<img width="1130" height="904" alt="webhook" src="https://github.com/user-attachments/assets/6cdef384-9770-4cec-8a05-8bc7384cf9a5" />

