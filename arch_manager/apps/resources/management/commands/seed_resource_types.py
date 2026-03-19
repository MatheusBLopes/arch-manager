from django.core.management.base import BaseCommand

from arch_manager.apps.resources.models import ResourceType


DEFAULT_TYPES = [
    ("Lambda", "lambda", "Funções serverless AWS Lambda"),
    ("SQS Queue", "sqs-queue", "Filas Amazon SQS"),
    ("SNS Topic", "sns-topic", "Tópicos Amazon SNS"),
    ("RDS Database", "rds-database", "Bancos de dados Amazon RDS"),
    ("DynamoDB Table", "dynamodb-table", "Tabelas Amazon DynamoDB"),
    ("Redis Cache", "redis-cache", "Caches Redis/ElastiCache"),
    ("API Gateway", "api-gateway", "Amazon API Gateway"),
    ("API Route", "api-route", "Rotas de API"),
    ("Internal API", "internal-api", "APIs internas"),
    ("External API", "external-api", "APIs externas"),
    ("Other", "other", "Outros tipos de recurso"),
]


class Command(BaseCommand):
    help = "Cria tipos de recurso iniciais"

    def handle(self, *args, **options):
        created = 0
        for name, slug, description in DEFAULT_TYPES:
            _, was_created = ResourceType.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "description": description, "is_active": True},
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Criado tipo: {name}"))

        if created == 0:
            self.stdout.write("Todos os tipos já existem.")
        else:
            self.stdout.write(self.style.SUCCESS(f"Total: {created} tipo(s) criado(s)."))
