"""
Popula o banco com massa de dados de exemplo para demonstrar todas as funcionalidades.
Execute: python manage.py seed_sample_data
Use --flush para limpar dados existentes antes (CUIDADO: apaga tudo).
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from arch_manager.apps.docs.models import ResourceDocumentation
from arch_manager.apps.projects.models import Project, ProjectDocumentation
from arch_manager.apps.relationships.models import ResourceRelationship
from arch_manager.apps.resources.models import (
    ApiGatewayEndpoint,
    ApiGatewayEndpointMethod,
    ApiGatewayExampleCurl,
    ApiGatewayInvocation,
    ApiGatewayParameter,
    ApiGatewayPayload,
    DatabaseQuery,
    DatabaseTable,
    LambdaDetails,
    Resource,
    ResourceType,
    TableField,
    TableRelationship,
)


def _slug(name):
    return slugify(name) or "untitled"


class Command(BaseCommand):
    help = "Popula o banco com massa de dados de exemplo completa"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Limpa dados existentes antes (apaga recursos, projetos, tipos customizados)",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()
        self._ensure_types()
        with transaction.atomic():
            self._create_projects()
            self._create_resources()
            self._create_lambda_details()
            self._create_documentations()
            self._create_relationships()
            self._create_database_schema()
            self._create_api_gateway_data()
        self.stdout.write(self.style.SUCCESS("Massa de dados criada com sucesso!"))

    def _flush(self):
        """Remove dados de exemplo (preserva tipos do seed padrão)."""
        ResourceRelationship.objects.all().delete()
        ResourceDocumentation.objects.all().delete()
        DatabaseQuery.objects.all().delete()
        TableRelationship.objects.all().delete()
        TableField.objects.all().delete()
        DatabaseTable.objects.all().delete()
        ApiGatewayExampleCurl.objects.all().delete()
        ApiGatewayInvocation.objects.all().delete()
        ApiGatewayPayload.objects.all().delete()
        ApiGatewayParameter.objects.all().delete()
        ApiGatewayEndpointMethod.objects.all().delete()
        ApiGatewayEndpoint.objects.all().delete()
        ProjectDocumentation.objects.all().delete()
        Project.objects.all().delete()
        Resource.objects.all().delete()
        self.stdout.write("Dados existentes removidos.")

    def _ensure_types(self):
        """Garante que os tipos de recurso existam."""
        types_data = [
            ("Lambda", "lambda", "Funções serverless AWS Lambda"),
            ("SQS Queue", "sqs-queue", "Filas Amazon SQS"),
            ("SNS Topic", "sns-topic", "Tópicos Amazon SNS"),
            ("RDS Database", "rds-database", "Bancos de dados Amazon RDS"),
            ("DynamoDB Table", "dynamodb-table", "Tabelas Amazon DynamoDB"),
            ("API Gateway", "api-gateway", "Amazon API Gateway"),
        ]
        for name, slug, desc in types_data:
            ResourceType.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "description": desc, "is_active": True},
            )

    def _create_projects(self):
        """Cria projetos com documentação."""
        projects_data = [
            (
                "Checkout e Pagamentos",
                "Sistema de processamento de pagamentos e fluxo de checkout.",
                """# Visão Geral do Projeto Checkout

## Objetivos
- Processar pagamentos de forma segura
- Integrar com gateways de pagamento
- Auditoria e conformidade PCI-DSS

## Componentes principais
- API de checkout
- Worker de processamento
- Banco de transações
""",
            ),
            (
                "Notificações",
                "Serviços de envio de e-mail, SMS e push.",
                """# Sistema de Notificações

## Arquitetura
- SNS como barramento de eventos
- Lambda consumers por canal (email, SMS, push)
- DynamoDB para histórico de envios

## Fluxos
1. Evento dispara publicação no tópico
2. Lambdas consomem e enviam por canal
""",
            ),
        ]
        self.projects = []
        for name, short, md in projects_data:
            proj, _ = Project.objects.get_or_create(
                slug=_slug(name),
                defaults={
                    "name": name,
                    "short_description": short,
                },
            )
            self.projects.append(proj)
            doc, created = ProjectDocumentation.objects.get_or_create(
                project=proj,
                defaults={
                    "title": f"Documentação: {name}",
                    "markdown_content": md,
                },
            )
            if not created:
                doc.markdown_content = md
                doc.save()

    def _create_resources(self):
        """Cria recursos de diversos tipos."""
        rt_lambda = ResourceType.objects.get(slug="lambda")
        rt_sqs = ResourceType.objects.get(slug="sqs-queue")
        rt_sns = ResourceType.objects.get(slug="sns-topic")
        rt_rds = ResourceType.objects.get(slug="rds-database")
        rt_api = ResourceType.objects.get(slug="api-gateway")

        proj_checkout = self.projects[0]
        proj_notif = self.projects[1]

        resources_data = [
            # Lambda
            ("process-payment-lambda", rt_lambda, proj_checkout,
             "Lambda que processa pagamentos", "Integra com Stripe, valida cartão e registra transação.",
             "python3.12", "https://github.com/empresa/checkout-lambdas", True),
            ("send-email-lambda", rt_lambda, proj_notif,
             "Envia e-mails transacionais", "Usa SES para envio de e-mails.",
             "python3.12", "https://github.com/empresa/notifications", False),
            ("order-validator", rt_lambda, proj_checkout,
             "Valida pedidos antes do checkout", "Verifica estoque e regras de negócio.",
             "nodejs20.x", "", False),
            # SQS
            ("payments-queue", rt_sqs, proj_checkout,
             "Fila de eventos de pagamento", "Mensagens assíncronas entre API e processador.",
             "", "", False),
            ("notification-events", rt_sqs, proj_notif,
             "Fila de eventos para notificações", "Eventos que disparam e-mail/SMS.",
             "", "", False),
            # SNS
            ("payment-events-topic", rt_sns, proj_checkout,
             "Tópico de eventos de pagamento", "Publica confirmações e falhas.",
             "", "", False),
            # RDS
            ("checkout-database", rt_rds, proj_checkout,
             "PostgreSQL do checkout", "Transações, pedidos, clientes.",
             "", "", True),
            # API Gateway
            ("checkout-api", rt_api, proj_checkout,
             "API REST de checkout", "Endpoints de carrinho, pedido e pagamento.",
             "", "https://github.com/empresa/checkout-api", True),
        ]

        self.resources = {}
        self._lambda_runtimes = {}
        for slug, rt, proj, short, detailed, runtime, repo, pentest in resources_data:
            r, _ = Resource.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": slug.replace("-", " ").title(),
                    "resource_type": rt,
                    "project": proj,
                    "short_description": short,
                    "detailed_description": detailed,
                    "repository_url": repo,
                    "has_pentest": pentest,
                    "notes": "Recurso de exemplo para demonstração.",
                },
            )
            self.resources[slug] = r
            if rt.slug == "lambda":
                self._lambda_runtimes[slug] = runtime

    def _create_lambda_details(self):
        """Detalhes específicos para recursos Lambda."""
        lambda_data = {
            "process-payment-lambda": {
                "runtime_version": self._lambda_runtimes.get("process-payment-lambda", "python3.12"),
                "example_invocation_payload": '{\n  "payment_id": "pay_123",\n  "amount": 99.90,\n  "currency": "BRL",\n  "customer_id": "cus_456"\n}',
                "mermaid_diagram": "flowchart TD\n  A[Recebe evento] --> B{Valida Stripe}\n  B -->|OK| C[Registra transação]\n  B -->|Erro| D[Publica falha]\n  C --> E[Publica confirmação]",
            },
            "send-email-lambda": {
                "runtime_version": self._lambda_runtimes.get("send-email-lambda", "python3.12"),
                "example_invocation_payload": '{\n  "to": "user@example.com",\n  "template": "payment_confirmation",\n  "data": {"order_id": "ord_789"}\n}',
                "mermaid_diagram": "flowchart LR\n  A[SNS Event] --> B[Parse payload]\n  B --> C[SES Send]",
            },
            "order-validator": {
                "runtime_version": self._lambda_runtimes.get("order-validator", "nodejs20.x"),
                "example_invocation_payload": "",
                "mermaid_diagram": "",
            },
        }
        for slug, data in lambda_data.items():
            r = self.resources.get(slug)
            if r and r.is_lambda():
                LambdaDetails.objects.update_or_create(
                    resource=r,
                    defaults=data,
                )

    def _create_documentations(self):
        """Documentação Markdown para recursos."""
        docs = [
            ("process-payment-lambda", "Processamento de Pagamentos", """# Lambda de Pagamento

## Fluxo
1. Recebe evento da fila
2. Valida dados com Stripe
3. Registra em `transactions`
4. Publica no tópico de confirmação

## Variáveis de ambiente
- `STRIPE_SECRET_KEY`
- `DB_HOST`
"""),
            ("checkout-api", "API de Checkout", """# API REST Checkout

## Autenticação
Bearer token via header `Authorization`.

## Rate limit
100 req/min por cliente.
"""),
            ("checkout-database", "Schema do Banco", """# PostgreSQL Checkout

## Conexão
- Host: checkout-db.xxx.rds.amazonaws.com
- Porta: 5432
- SSL obrigatório
"""),
        ]
        for slug, title, md in docs:
            r = self.resources.get(slug)
            if r:
                ResourceDocumentation.objects.update_or_create(
                    resource=r,
                    defaults={"title": title, "markdown_content": md},
                )

    def _create_relationships(self):
        """Relacionamentos entre recursos."""
        rels = [
            ("checkout-api", "invokes", "process-payment-lambda", "API chama Lambda via integração"),
            ("checkout-api", "consumes_from", "payments-queue", "Worker consome da fila"),
            ("process-payment-lambda", "publishes_to", "payment-events-topic", "Publica confirmação"),
            ("process-payment-lambda", "writes_to", "checkout-database", "Registra transação"),
            ("order-validator", "consumes_from", "payments-queue", "Valida antes do processamento"),
            ("send-email-lambda", "subscribes_to", "payment-events-topic", "Envia e-mail de confirmação"),
        ]
        for src, typ, tgt, desc in rels:
            if src in self.resources and tgt in self.resources:
                ResourceRelationship.objects.get_or_create(
                    source_resource=self.resources[src],
                    relationship_type=typ,
                    target_resource=self.resources[tgt],
                    defaults={"description": desc, "is_active": True},
                )

    def _create_database_schema(self):
        """Tabelas, campos, relacionamentos e queries para RDS."""
        db = self.resources.get("checkout-database")
        if not db:
            return

        # Tabelas
        tables_data = [
            ("users", "Usuários do sistema", [
                ("id", "UUID", True, False, "PK"),
                ("email", "VARCHAR(255)", False, False, "E-mail único"),
                ("created_at", "TIMESTAMP", False, False, ""),
            ]),
            ("orders", "Pedidos", [
                ("id", "UUID", True, False, "PK"),
                ("user_id", "UUID", False, False, "FK users"),
                ("total", "DECIMAL(10,2)", False, False, ""),
                ("status", "VARCHAR(50)", False, False, ""),
            ]),
            ("transactions", "Transações de pagamento", [
                ("id", "UUID", True, False, "PK"),
                ("order_id", "UUID", False, False, "FK orders"),
                ("amount", "DECIMAL(10,2)", False, False, ""),
                ("payment_method", "VARCHAR(50)", False, False, ""),
            ]),
        ]
        created_tables = {}
        for order, (tname, tdesc, fields) in enumerate(tables_data):
            t, _ = DatabaseTable.objects.get_or_create(
                resource=db,
                name=tname,
                defaults={"description": tdesc, "order": order},
            )
            created_tables[tname] = t
            for i, (fname, ftype, pk, null, fdesc) in enumerate(fields):
                TableField.objects.get_or_create(
                    table=t,
                    name=fname,
                    defaults={
                        "data_type": ftype,
                        "is_primary_key": pk,
                        "is_nullable": null,
                        "description": fdesc,
                        "order": i,
                    },
                )

        # Relacionamento entre tabelas
        users = created_tables["users"]
        orders = created_tables["orders"]
        transactions = created_tables["transactions"]
        user_id = users.fields.get(name="id")
        order_user_id = orders.fields.get(name="user_id")
        order_id = orders.fields.get(name="id")
        txn_order_id = transactions.fields.get(name="order_id")

        TableRelationship.objects.get_or_create(
            source_table=users,
            target_table=orders,
            defaults={
                "relationship_type": "one_to_many",
                "source_field": user_id,
                "target_field": order_user_id,
                "description": "Um usuário tem muitos pedidos",
            },
        )
        TableRelationship.objects.get_or_create(
            source_table=orders,
            target_table=transactions,
            defaults={
                "relationship_type": "one_to_many",
                "source_field": order_id,
                "target_field": txn_order_id,
                "description": "Um pedido pode ter várias transações",
            },
        )

        # Queries úteis
        queries = [
            ("Pedidos por usuário", "Lista pedidos de um usuário com totais",
             "SELECT o.*, SUM(t.amount) as paid FROM orders o LEFT JOIN transactions t ON t.order_id = o.id WHERE o.user_id = :user_id GROUP BY o.id;"),
            ("Transações do dia", "Transações concluídas hoje",
             "SELECT * FROM transactions WHERE created_at >= CURRENT_DATE ORDER BY created_at DESC;"),
        ]
        for i, (qname, qdesc, qtext) in enumerate(queries):
            DatabaseQuery.objects.get_or_create(
                resource=db,
                name=qname,
                defaults={"description": qdesc, "query_text": qtext, "order": i},
            )

    def _create_api_gateway_data(self):
        """Endpoints, métodos, parâmetros, payloads, invocações e curls para API Gateway."""
        api = self.resources.get("checkout-api")
        if not api:
            return

        lambda_payment = self.resources.get("process-payment-lambda")
        queue = self.resources.get("payments-queue")

        # Endpoint /orders
        ep_orders, _ = ApiGatewayEndpoint.objects.get_or_create(
            resource=api,
            path="/orders",
            defaults={"description": "CRUD de pedidos", "order": 0},
        )
        m_get, _ = ApiGatewayEndpointMethod.objects.get_or_create(
            endpoint=ep_orders,
            http_method="GET",
            defaults={"description": "Lista pedidos do usuário", "order": 0},
        )
        ApiGatewayParameter.objects.get_or_create(
            method=m_get,
            name="user_id",
            param_in="query",
            defaults={"param_type": "string", "required": True, "description": "ID do usuário", "order": 0},
        )
        ApiGatewayPayload.objects.get_or_create(
            method=m_get,
            direction="response",
            defaults={
                "content_type": "application/json",
                "body": '{"orders": [{"id": "uuid", "total": 99.90, "status": "completed"}]}',
                "order": 0,
            },
        )
        if lambda_payment:
            ApiGatewayInvocation.objects.get_or_create(
                method=m_get,
                target_resource=lambda_payment,
                defaults={"description": "Busca via Lambda", "order": 0},
            )
        ApiGatewayExampleCurl.objects.get_or_create(
            method=m_get,
            label="Listar pedidos",
            defaults={
                "curl_command": 'curl -X GET "https://api.example.com/orders?user_id=usr_123" -H "Authorization: Bearer TOKEN"',
                "order": 0,
            },
        )

        m_post, _ = ApiGatewayEndpointMethod.objects.get_or_create(
            endpoint=ep_orders,
            http_method="POST",
            defaults={"description": "Cria novo pedido", "order": 1},
        )
        ApiGatewayPayload.objects.get_or_create(
            method=m_post,
            direction="request",
            defaults={
                "content_type": "application/json",
                "body": '{"items": [{"product_id": "prod_1", "quantity": 2}], "payment_method": "card"}',
                "order": 0,
            },
        )
        ApiGatewayPayload.objects.get_or_create(
            method=m_post,
            direction="response",
            defaults={
                "content_type": "application/json",
                "body": '{"order_id": "ord_xyz", "status": "pending", "total": 199.80}',
                "order": 1,
            },
        )
        if lambda_payment:
            ApiGatewayInvocation.objects.get_or_create(
                method=m_post,
                target_resource=lambda_payment,
                defaults={"description": "Processa pedido via Lambda", "order": 0},
            )
        ApiGatewayExampleCurl.objects.get_or_create(
            method=m_post,
            label="Criar pedido",
            defaults={
                "curl_command": 'curl -X POST https://api.example.com/orders -H "Content-Type: application/json" -H "Authorization: Bearer TOKEN" -d \'{"items":[{"product_id":"prod_1","quantity":2}]}\'',
                "order": 0,
            },
        )

        # Endpoint /orders/{id}
        ep_order_id, _ = ApiGatewayEndpoint.objects.get_or_create(
            resource=api,
            path="/orders/{id}",
            defaults={"description": "Detalhe e atualização de pedido", "order": 1},
        )
        m_get_id, _ = ApiGatewayEndpointMethod.objects.get_or_create(
            endpoint=ep_order_id,
            http_method="GET",
            defaults={"description": "Retorna pedido por ID", "order": 0},
        )
        ApiGatewayParameter.objects.get_or_create(
            method=m_get_id,
            name="id",
            param_in="path",
            defaults={"param_type": "string", "required": True, "description": "UUID do pedido", "order": 0},
        )
        ApiGatewayExampleCurl.objects.get_or_create(
            method=m_get_id,
            label="Buscar pedido",
            defaults={
                "curl_command": 'curl -X GET "https://api.example.com/orders/ord_123" -H "Authorization: Bearer TOKEN"',
                "order": 0,
            },
        )
