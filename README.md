# Arch Manager

Catálogo e mapa documental de arquitetura AWS para execução local. Permite cadastrar recursos arquiteturais (Lambdas, SQS, SNS, RDS, DynamoDB, Redis, API Gateway, APIs, etc.), relacioná-los entre si e manter documentação detalhada em Markdown.

## Stack

- **Python** 3.12
- **Django** 5
- **Wagtail** 6 (gerenciamento de documentação)
- **Bootstrap** 5
- **Tema escuro** (Bootstrap 5 dark mode)
- **SQLite**
- **Markdown** para documentação

## Estrutura do Projeto

```
arch-manager/
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── pytest.ini
├── manage.py
├── arch_manager/
│   ├── apps/
│   │   ├── core/          # Dashboard e navegação
│   │   ├── resources/     # Recursos arquiteturais
│   │   ├── relationships/ # Relacionamentos entre recursos
│   │   └── docs/          # Documentação Markdown
│   ├── templates/
│   ├── static/
│   └── media/
└── tests/
```

## Configuração Local

### 1. Ambiente virtual

```bash
python3.12 -m venv venv
source venv/bin/activate   # Linux/macOS
# ou: venv\Scripts\activate  # Windows
```

### 2. Dependências

```bash
pip install -r requirements.txt
```

### 3. Variáveis de ambiente

```bash
cp .env.example .env
# Edite .env se necessário (DEBUG, SECRET_KEY, ALLOWED_HOSTS)
```

### 4. Banco de dados

```bash
python manage.py migrate
python manage.py seed_resource_types
```

### 5. Executar o servidor

```bash
python manage.py runserver
```

Acesse: **http://127.0.0.1:8000/**

## Tema escuro

A interface usa **tema escuro (dark mode)** por padrão, via Bootstrap 5.3:

- `data-bs-theme="dark"` no elemento HTML
- highlight.js com estilo `github-dark` para código na documentação
- Cores e contraste otimizados para leitura prolongada

## Uso

- **Dashboard**: visão geral de recursos e tipos
- **Recursos**: listagem, criação, edição e detalhes
- **Tipos**: Lambda, SQS, SNS, RDS, DynamoDB, Redis, API Gateway, API Route, Internal API, External API, Other
- **Relacionamentos**: vincular recursos (ex.: fila SQS invoca Lambda)
- **Documentação**: editar conteúdo em Markdown na página de detalhes do recurso

## URLs Principais

| Rota | Descrição |
|------|-----------|
| `/` | Dashboard |
| `/resources/` | Lista de recursos |
| `/resources/new/` | Novo recurso |
| `/resources/type/<slug>/` | Recursos por tipo |
| `/resources/<slug>/` | Detalhe do recurso |
| `/resources/<slug>/edit/` | Editar recurso |
| `/relationships/new/` | Novo relacionamento |
| `/docs/resource/<slug>/edit/` | Editar documentação |

## Testes

```bash
pytest
```

## Modelagem

- **ResourceType**: tipo do recurso (Lambda, SQS, etc.)
- **Resource**: recurso individual com metadados
- **ResourceRelationship**: conexão origem → tipo → destino (ex.: invokes, publishes_to)
- **ResourceDocumentation**: documentação Markdown vinculada ao recurso (OneToOne)

## Integração Wagtail e Markdown

O Wagtail está configurado como base para o ecossistema de documentação. Cada recurso pode ter uma documentação em Markdown vinculada, editada via formulário próprio e renderizada na página de detalhes do recurso. A biblioteca `markdown` processa o conteúdo para HTML de forma segura.

## Requisitos

- Python 3.12
- Nenhuma autenticação (uso local)
- Sem configuração de Django Admin no fluxo principal
