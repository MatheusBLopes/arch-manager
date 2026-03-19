# Especificação Completa do Projeto Django Local

## 1. Visão Geral do Projeto

### 1.1 Nome do projeto

`arch-manager`

### 1.2 Objetivo

Construir uma aplicação web local em **Django 5**, utilizando **Django Templates**, **Bootstrap 5**, **Python 3.12.0** e **SQLite**, com foco em **cadastro, visualização, relacionamento e documentação arquitetural de recursos AWS**.

O sistema deverá funcionar como um **catálogo e mapa documental de arquitetura**, permitindo registrar recursos de infraestrutura e integração, relacioná-los entre si e manter uma documentação rica em **Markdown**, armazenada e organizada com **Wagtail**.

### 1.3 Resumo funcional

A aplicação deverá permitir que um único usuário local:

* cadastre recursos da AWS e recursos relacionados à arquitetura
* categorize esses recursos por tipo
* relacione recursos entre si
* visualize dependências e integrações
* mantenha documentação detalhada por recurso
* edite a documentação sempre em Markdown
* navegue por listagens separadas por tipo de recurso
* abra uma página de detalhes de cada recurso contendo seus metadados e documentação

### 1.4 Público-alvo

* Usuário principal: desenvolvedor, arquiteto de software, engenheiro de plataforma ou estudante que queira mapear arquiteturas AWS localmente
* Uso esperado: individual e local

### 1.5 Escopo inicial

O sistema deverá incluir:

* aplicação Django 5 rodando localmente
* banco SQLite
* interface com Django Templates + Bootstrap 5
* cadastro de recursos arquiteturais
* cadastro de relacionamentos entre recursos
* documentação detalhada por recurso com Wagtail
* edição da documentação em Markdown
* listagens por tipo de recurso
* tela de detalhes do recurso com documentação e relacionamentos
* criação e edição de recursos
* criação e edição de relacionamentos
* documentação do projeto via README
* estrutura de projeto organizada com pasta `apps`

### 1.6 Fora do escopo inicial

Não deverá incluir nesta primeira versão:

* autenticação
* login/logout
* permissões
* Django Admin configurado para uso manual
* uploads de imagem
* integração real com APIs da AWS
* sincronização automática de infraestrutura
* multiusuário
* deploy em nuvem
* versionamento avançado de documentação

---

## 2. Objetivo para a IA implementadora

A IA implementadora deverá gerar um projeto Django completo, funcional e pronto para rodar localmente, seguindo exatamente esta especificação.

Ela deverá entregar:

* estrutura completa de diretórios
* projeto Django configurado com Django 5
* configuração compatível com Python 3.12.0
* banco SQLite pronto para uso local
* apps organizadas dentro de `arch_manager/apps`
* models, views, forms, urls e templates necessários
* integração com Wagtail para páginas de documentação
* suporte a edição em Markdown para documentação textual
* testes automatizados para os fluxos principais
* README detalhado
* `.env.example` mesmo que simples
* `.gitignore`
* `requirements.txt`

---

## 3. Stack técnica obrigatória

### 3.1 Linguagem e framework

* Python **3.12.0**
* Django **5.x**

### 3.2 Banco de dados

* SQLite obrigatório
* arquivo padrão local: `db.sqlite3`

### 3.3 Front-end

* Django Templates
* HTML5
* CSS3
* Bootstrap 5
* **tema escuro** (Bootstrap 5 dark mode via `data-bs-theme="dark"`)
* JavaScript vanilla apenas para pequenas interações de interface, se necessário

### 3.4 Documentação de conteúdo

* Wagtail para gerenciamento de páginas de documentação
* Markdown como formato obrigatório de edição e armazenamento textual da documentação

### 3.5 Testes

* pytest + pytest-django preferencialmente
* uso de factories é opcional

### 3.6 Ambiente

* execução local com `venv`
* uso de `.env` simples
* `django-environ` ou `python-dotenv` para leitura das variáveis

### 3.7 Qualidade de código

* Ruff ou Flake8
* Black opcional
* isort opcional

---

## 4. Restrições técnicas obrigatórias

As seguintes decisões são mandatórias e não devem ser alteradas pela IA implementadora:

* o projeto deve usar **Django 5**
* o projeto deve usar **Python 3.12.0**
* o projeto deve usar **Django Templates**, não React/Vue
* o layout deve usar **Bootstrap 5**
* o projeto deve rodar **localmente**
* o banco deve ser **SQLite**
* **não deve haver autenticação**
* **não deve haver tela de login**
* **não deve haver configuração de uso do Django Admin como parte da solução principal**
* a documentação de cada recurso deve ser **editada em Markdown**
* deve existir integração com **Wagtail** para estruturar a documentação dos recursos
* o projeto deve usar a pasta mãe `arch-manager/` e dentro dela a pasta Django `arch_manager/`
* as apps devem ficar dentro de `arch_manager/apps/`

---

## 5. Estrutura de diretórios obrigatória

A IA implementadora deverá seguir esta estrutura base:

```text
arch-manager/
├─ README.md
├─ .gitignore
├─ .env.example
├─ requirements.txt
├─ pytest.ini
├─ manage.py
├─ arch_manager/
│  ├─ __init__.py
│  ├─ asgi.py
│  ├─ wsgi.py
│  ├─ urls.py
│  ├─ settings.py                     # pode ser único ou dividido, mas simples é aceitável
│  ├─ apps/
│  │  ├─ __init__.py
│  │  ├─ core/
│  │  ├─ resources/
│  │  ├─ relationships/
│  │  └─ docs/
│  ├─ templates/
│  │  ├─ base.html
│  │  ├─ includes/
│  │  ├─ core/
│  │  ├─ resources/
│  │  ├─ relationships/
│  │  └─ docs/
│  ├─ static/
│  │  ├─ css/
│  │  ├─ js/
│  │  └─ img/
│  └─ media/
└─ tests/                             # opcional; pode haver testes nas apps
```

### 5.1 Observações de estrutura

* `arch-manager/` é a raiz do repositório
* `arch_manager/` é o núcleo do projeto Django
* todas as apps criadas para o projeto devem estar dentro de `arch_manager/apps/`
* os templates devem ficar centralizados em `arch_manager/templates/`
* os arquivos estáticos devem ficar em `arch_manager/static/`
* a pasta `media/` deve existir, mesmo que inicialmente não haja upload de imagens

---

## 6. Conceito do sistema

O sistema será um **gerenciador local de arquitetura AWS**, permitindo cadastrar e documentar componentes arquiteturais.

Cada recurso será uma entidade navegável no sistema. Exemplos:

* Lambda
* SQS
* SNS
* RDS
* DynamoDB
* Redis
* API Gateway
* rota de API
* API externa/interna
* outros tipos arquiteturais futuros

O sistema deverá representar não apenas os recursos isoladamente, mas também **como eles se conectam**.

Exemplo de relacionamento que o sistema deve suportar:

* a fila SQS `payments-events-queue` invoca a Lambda `process_payment`
* a Lambda `process_payment` publica no tópico SNS `payment-approved-topic`
* a rota `POST /checkout` chama a API `payments-service`
* a API `payments-service` persiste dados no RDS `payments-db`

---

## 7. Modelagem funcional principal

## 7.1 App `core`

Responsável por:

* dashboard inicial
* navegação principal
* páginas institucionais simples se necessário
* componentes visuais compartilhados

## 7.2 App `resources`

Responsável por:

* cadastro de recursos arquiteturais
* edição de recursos
* listagem geral
* listagens por tipo
* visualização detalhada do recurso
* filtros e busca

## 7.3 App `relationships`

Responsável por:

* cadastro de relacionamentos entre recursos
* edição de relacionamentos
* remoção de relacionamentos
* exibição de dependências de entrada e saída

## 7.4 App `docs`

Responsável por:

* integração com Wagtail
* estruturação da documentação por recurso
* renderização do Markdown armazenado
* vínculo entre recurso e página documental

---

## 8. Entidades do sistema

## 8.1 Entidade principal: `ResourceType`

### Objetivo

Representar o tipo do recurso arquitetural.

### Exemplos de tipos

* Lambda
* SQS Queue
* SNS Topic
* RDS Database
* DynamoDB Table
* Redis Cache
* API Gateway
* API Route
* Internal API
* External API
* Other

### Campos sugeridos

* `id`
* `name`: string, obrigatório, único
* `slug`: string, obrigatório, único
* `description`: texto, opcional
* `is_active`: boolean, padrão true
* `created_at`
* `updated_at`

### Regras

* deve permitir cadastrar tipos adicionais no futuro
* o slug deve ser usado nas URLs de listagem por tipo

---

## 8.2 Entidade principal: `Resource`

### Objetivo

Representar um recurso arquitetural individual cadastrado no sistema.

### Exemplos

* Lambda `process-user-created`
* SQS `user-created-events`
* SNS `user-notifications`
* RDS `auth-db`
* rota `POST /users`
* API `users-service`

### Campos obrigatórios

* `id`
* `name`: string, obrigatório, máximo 200 caracteres
* `slug`: string, obrigatório, único
* `resource_type`: FK para `ResourceType`, obrigatório
* `short_description`: texto curto, obrigatório
* `detailed_description`: texto, opcional
* `service_name`: string, opcional
* `environment`: string, opcional
* `region`: string, opcional
* `identifier`: string, opcional
* `endpoint_or_path`: string, opcional
* `status`: string, opcional
* `notes`: texto, opcional
* `is_active`: boolean, padrão true
* `created_at`
* `updated_at`

### Observação sobre campos genéricos

Como o sistema suportará diferentes tipos de recurso, os campos devem ser suficientemente genéricos para acomodar vários cenários. A IA implementadora pode incluir campos extras úteis, desde que mantenha simplicidade.

### Regras de negócio

* todo recurso deve pertencer a um tipo
* todo recurso deve possuir nome e slug únicos
* todo recurso pode ou não possuir documentação detalhada vinculada
* um recurso pode se relacionar com vários outros recursos
* um recurso pode receber relacionamentos de vários outros recursos

---

## 8.3 Entidade principal: `ResourceRelationship`

### Objetivo

Representar uma conexão explícita entre dois recursos.

### Exemplo conceitual

* origem: `payments-queue`
* relação: `invokes`
* destino: `process-payment-lambda`

### Campos obrigatórios

* `id`
* `source_resource`: FK para `Resource`, obrigatório
* `target_resource`: FK para `Resource`, obrigatório
* `relationship_type`: string, obrigatório
* `description`: texto, opcional
* `is_active`: boolean, padrão true
* `created_at`
* `updated_at`

### Exemplos de `relationship_type`

* invokes
* publishes_to
* subscribes_to
* reads_from
* writes_to
* persists_in
* consumes_from
* exposes
* routes_to
* depends_on
* calls
* triggers
* sends_to
* receives_from

### Regras de negócio

* um recurso não deve poder se relacionar consigo mesmo
* a combinação entre origem, tipo de relação e destino não deve se repetir desnecessariamente
* deve ser possível visualizar relações de saída e de entrada
* a descrição do relacionamento deve permitir explicar o contexto da integração

---

## 8.4 Entidade documental: `ResourceDocumentationPage`

### Objetivo

Representar a documentação rica em texto de um recurso usando Wagtail.

### Observação importante

A documentação deve ser sempre editada em Markdown e exibida renderizada no detalhe do recurso.

### Estrutura esperada

A IA implementadora deverá usar Wagtail para criar um tipo de página ou estrutura equivalente vinculada ao recurso.

### Campos esperados

* vínculo único com `Resource`
* `title`
* `markdown_content`
* `rendered_content` pode ser calculado em runtime ou gerado automaticamente
* `last_updated_at`

### Regras de negócio

* cada recurso deve ter no máximo uma página documental principal
* a documentação deve aceitar texto extenso
* a edição deve ser em Markdown puro
* a renderização final deve ser segura e legível
* não haverá imagens nesta primeira versão

---

## 9. Requisitos funcionais detalhados

## 9.1 Cadastro de tipos de recursos

* RF-001: O sistema deve permitir cadastrar tipos de recursos arquiteturais.
* RF-002: O sistema deve permitir listar tipos de recursos.
* RF-003: O sistema deve permitir editar tipos de recursos.
* RF-004: O sistema deve permitir desativar tipos de recursos, se necessário.

## 9.2 Cadastro de recursos

* RF-005: O sistema deve permitir cadastrar recursos como Lambda, SQS, SNS, RDS, DynamoDB, Redis, API Gateway, rota de API, outras APIs e tipos futuros.
* RF-006: O sistema deve permitir editar um recurso já cadastrado.
* RF-007: O sistema deve permitir visualizar os detalhes de um recurso.
* RF-008: O sistema deve permitir listar todos os recursos.
* RF-009: O sistema deve permitir listar recursos separados por tipo.
* RF-010: O sistema deve permitir busca textual por nome, descrição e tipo.
* RF-011: O sistema deve permitir desativar ou excluir logicamente um recurso, se a IA optar por soft delete.

## 9.3 Documentação do recurso

* RF-012: O sistema deve permitir que cada recurso possua uma documentação detalhada.
* RF-013: A documentação deve ser armazenada e gerenciada com Wagtail.
* RF-014: A edição da documentação deve ser feita sempre em Markdown.
* RF-015: A tela de detalhes do recurso deve exibir a documentação renderizada.
* RF-016: Deve ser possível criar a documentação de um recurso ainda não documentado.
* RF-017: Deve ser possível editar a documentação existente de um recurso.

## 9.4 Relacionamentos entre recursos

* RF-018: O sistema deve permitir relacionar recursos entre si.
* RF-019: O sistema deve permitir informar tipo de relação entre origem e destino.
* RF-020: O sistema deve permitir descrever textualmente a relação.
* RF-021: O sistema deve exibir, na página de detalhes do recurso, as relações em que ele é origem.
* RF-022: O sistema deve exibir, na página de detalhes do recurso, as relações em que ele é destino.
* RF-023: O sistema deve permitir editar e remover relacionamentos.

## 9.5 Navegação e telas

* RF-024: O sistema deve possuir dashboard inicial.
* RF-025: O sistema deve possuir menu de navegação global.
* RF-026: O sistema deve possuir tela de listagem geral de recursos.
* RF-027: O sistema deve possuir telas de listagem por tipo de recurso.
* RF-028: O sistema deve possuir tela de criação e edição de recurso.
* RF-029: O sistema deve possuir tela de detalhe de recurso.
* RF-030: O sistema deve possuir tela de criação e edição de relacionamento.
* RF-031: O sistema deve possuir tela de criação e edição da documentação Markdown do recurso.

---

## 10. Requisitos não funcionais

* RNF-001: O sistema deve rodar localmente com poucos comandos.
* RNF-002: O sistema deve utilizar SQLite sem necessidade de serviços externos.
* RNF-003: O sistema não deve depender de autenticação.
* RNF-004: O sistema deve ter interface clara e responsiva com Bootstrap 5.
* RNF-005: O código deve ser organizado em apps dentro de `arch_manager/apps`.
* RNF-006: A documentação do recurso deve ser legível e renderizada a partir de Markdown.
* RNF-007: O sistema deve ser fácil de evoluir para novos tipos de recurso.
* RNF-008: O sistema deve ser manutenível e modular.
* RNF-009: O projeto deve possuir README claro e completo.
* RNF-010: O sistema deve possuir testes para os principais fluxos.

---

## 11. Fluxos principais do usuário

## 11.1 Fluxo de cadastro de recurso

1. usuário acessa “Novo recurso”
2. escolhe o tipo do recurso
3. preenche os metadados principais
4. salva o recurso
5. sistema redireciona para a página de detalhe do recurso
6. usuário pode então criar ou editar a documentação Markdown
7. usuário pode cadastrar relacionamentos com outros recursos

## 11.2 Fluxo de documentação do recurso

1. usuário acessa a página de detalhe de um recurso
2. clica em “Editar documentação” ou “Criar documentação”
3. abre a tela de edição em Markdown
4. salva o conteúdo
5. sistema renderiza esse Markdown na página de detalhe do recurso

## 11.3 Fluxo de relacionamento

1. usuário acessa a tela de um recurso
2. clica em “Adicionar relacionamento”
3. escolhe recurso de origem, tipo da relação e recurso de destino
4. opcionalmente descreve a integração
5. salva o relacionamento
6. sistema exibe o relacionamento na seção de dependências

## 11.4 Fluxo de navegação por tipo

1. usuário acessa a listagem de tipos
2. clica em um tipo específico, como Lambda
3. sistema exibe apenas os recursos daquele tipo
4. usuário pode abrir qualquer recurso dessa listagem

---

## 12. Telas obrigatórias

## 12.1 Dashboard

Deve conter:

* resumo da quantidade total de recursos
* resumo por tipo
* atalhos para criar novo recurso
* atalhos para navegar por tipos
* lista de recursos recentes opcional

## 12.2 Listagem geral de recursos

Deve conter:

* tabela ou cards com recursos
* nome
* tipo
* descrição curta
* ambiente ou região se existir
* link para detalhes
* busca textual
* filtros por tipo opcionalmente

## 12.3 Listagem por tipo

Deve conter:

* título do tipo
* total de recursos daquele tipo
* lista paginada dos recursos
* botão para criar novo recurso daquele tipo

## 12.4 Formulário de recurso

Deve conter campos para:

* nome
* slug
* tipo
* descrição curta
* descrição detalhada
* service name
* environment
* region
* identifier
* endpoint/path
* status
* notes
* ativo/inativo

## 12.5 Tela de detalhes do recurso

Deve conter:

* nome do recurso
* tipo
* metadados do recurso
* documentação renderizada em Markdown
* botão para editar recurso
* botão para editar documentação
* lista de relacionamentos de saída
* lista de relacionamentos de entrada
* botão para adicionar relacionamento

## 12.6 Formulário de relacionamento

Deve conter:

* recurso de origem
* tipo de relação
* recurso de destino
* descrição opcional

## 12.7 Formulário de documentação Markdown

Deve conter:

* título da documentação
* campo grande para Markdown
* botão salvar
* pré-visualização opcional é desejável, mas não obrigatória

---

## 13. Padrões visuais e UX

### 13.1 Layout base

A aplicação deve ter:

* navbar superior com nome do projeto
* menu com links para dashboard, recursos, tipos e criação
* container central com espaçamento adequado
* mensagens de sucesso/erro com Bootstrap alerts

### 13.2 Estilo

* usar Bootstrap 5 de forma limpa
* priorizar legibilidade
* usar cards para resumos
* usar tabelas para listagens quando fizer sentido
* usar badges para tipo de recurso e status

### 13.3 Página de detalhe

A página de detalhe é central no sistema e deve priorizar:

* leitura rápida dos metadados
* leitura confortável da documentação
* visualização clara dos relacionamentos

### 13.4 Tema escuro

A aplicação utiliza **tema escuro (dark mode)** por padrão:

* Bootstrap 5.3+ com `data-bs-theme="dark"` no elemento raiz
* highlight.js com estilo `github-dark` para blocos de código na documentação Markdown
* variáveis CSS do Bootstrap (`--bs-tertiary-bg`, `--bs-border-color`) para consistência visual em blocos de código e tabelas
* navbar em tons escuros para harmonia com o tema

---

## 14. Regras específicas de documentação com Wagtail

A IA implementadora deve adotar a seguinte abordagem conceitual:

* Wagtail será usado como camada de modelagem/organização da documentação textual
* cada `Resource` deverá poder ter uma página documental específica
* essa página deverá armazenar conteúdo em Markdown
* a interface do projeto principal deve exibir essa documentação renderizada

### 14.1 Regras obrigatórias

* a documentação é textual, sem necessidade de imagens
* o campo principal da documentação deve ser Markdown puro
* deve haver integração entre o recurso cadastrado e a página documental do Wagtail
* a documentação deve poder ser criada e editada a partir do fluxo principal do sistema

### 14.2 Decisão de implementação permitida

A IA pode escolher a melhor forma técnica de integrar Django + Wagtail + Markdown, desde que:

* exista uma entidade documental por recurso
* a edição seja em Markdown
* a exibição seja renderizada na página de detalhe do recurso

---

## 15. Regras de validação

### 15.1 Recurso

* nome é obrigatório
* slug é obrigatório e único
* tipo é obrigatório
* descrição curta é obrigatória

### 15.2 Relacionamento

* origem é obrigatória
* destino é obrigatório
* tipo de relação é obrigatório
* origem e destino não podem ser iguais
* não deve haver duplicidade exata do mesmo relacionamento

### 15.3 Documentação

* recurso vinculado é obrigatório
* markdown_content pode ser vazio apenas se a IA optar por permitir rascunho
* título da documentação é obrigatório

---

## 16. Estratégia de implementação sugerida

### 16.1 Ordem ideal

1. criar estrutura base do projeto
2. configurar Django 5 e SQLite
3. configurar Bootstrap base e templates globais
4. criar app `core`
5. criar app `resources`
6. criar app `relationships`
7. criar app `docs`
8. integrar Wagtail
9. implementar modelos
10. implementar forms
11. implementar views e urls
12. implementar templates
13. implementar renderização Markdown
14. implementar testes
15. escrever README

### 16.2 Tipo de views

* CBVs são preferenciais para CRUDs
* FBVs podem ser usadas em páginas específicas quando simplificarem a solução

### 16.3 Forms

* usar `ModelForm` para `Resource`, `ResourceType` e `ResourceRelationship`
* usar form específico para documentação Markdown

---

## 17. URLs esperadas

A IA implementadora deverá seguir um padrão claro de rotas, como por exemplo:

```text
/
/resources/
/resources/new/
/resources/<slug>/
/resources/<slug>/edit/
/resources/type/<type_slug>/
/relationships/new/
/relationships/<id>/edit/
/docs/resource/<resource_slug>/edit/
/docs/resource/<resource_slug>/
```

Os nomes exatos podem variar, mas a organização precisa permanecer clara.

---

## 18. Templates obrigatórios

A IA implementadora deverá criar no mínimo:

* `base.html`
* `core/dashboard.html`
* `resources/resource_list.html`
* `resources/resource_by_type.html`
* `resources/resource_detail.html`
* `resources/resource_form.html`
* `relationships/relationship_form.html`
* `docs/documentation_form.html`
* `docs/documentation_detail.html` se a IA quiser separar, embora o ideal seja embutir no detalhe do recurso
* includes reutilizáveis para mensagens, navbar e cards

---

## 19. Testes obrigatórios

A IA implementadora deve gerar testes para:

### 19.1 Models

* criação de `ResourceType`
* criação de `Resource`
* criação válida e inválida de `ResourceRelationship`
* vínculo entre `Resource` e documentação
* `__str__` das entidades principais

### 19.2 Views

* dashboard responde com 200
* listagem geral responde com 200
* listagem por tipo responde com 200
* criação de recurso funciona
* edição de recurso funciona
* detalhe de recurso funciona
* criação de relacionamento funciona
* edição de documentação funciona

### 19.3 Forms

* form de recurso válido
* form de relacionamento inválido quando origem = destino
* form de documentação aceita Markdown

### 19.4 Integração

* fluxo completo de criar recurso -> documentar -> relacionar -> visualizar detalhe

---

## 20. Dados iniciais desejáveis

A IA pode incluir seed inicial com alguns tipos de recurso padrão:

* Lambda
* SQS Queue
* SNS Topic
* RDS Database
* DynamoDB Table
* Redis Cache
* API Gateway
* API Route
* Internal API
* External API
* Other

Opcionalmente pode incluir alguns recursos de exemplo para demonstração.

---

## 21. README obrigatório

O README deverá conter:

* visão geral do sistema
* stack usada
* estrutura de pastas
* instruções para criar venv
* instruções para instalar dependências
* instruções para configurar `.env`
* instruções para rodar migrações
* instruções para subir o servidor local
* instruções para acessar o sistema
* instruções para rodar testes
* explicação breve da modelagem
* explicação da integração com Wagtail e Markdown

---

## 22. Dependências esperadas

A IA implementadora deverá incluir as dependências necessárias para:

* Django 5
* Wagtail
* renderização Markdown
* leitura de `.env`
* pytest e pytest-django
* Bootstrap via CDN ou arquivos estáticos

A versão exata pode ser escolhida pela IA, desde que compatível com Python 3.12.0 e Django 5.

---

## 23. Critérios de aceitação

A implementação será considerada correta se:

* o projeto rodar localmente com SQLite
* não houver autenticação nem tela de login
* o projeto utilizar Django Templates com Bootstrap 5
* for possível cadastrar recursos arquiteturais
* for possível listar recursos por tipo
* for possível visualizar detalhes de um recurso
* for possível documentar um recurso usando Wagtail e Markdown
* a documentação aparecer renderizada na tela de detalhes
* for possível relacionar recursos entre si
* a estrutura de pastas respeitar `arch-manager/` e `arch_manager/apps/`
* os testes principais passarem
* o README permitir que outra pessoa rode o projeto sem contexto prévio

---

## 24. Instrução final

Esta especificação substitui a versão genérica anterior. A IA implementadora não deve simplificar a arquitetura pedida, nem introduzir autenticação, nem trocar SQLite, nem substituir Django Templates por frontend SPA. O foco é um sistema local, limpo, modular, extensível e totalmente alinhado ao gerenciamento e documentação de arquitetura AWS.
