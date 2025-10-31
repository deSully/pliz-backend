import os
import requests
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Enregistre les webhooks Djamo pour recevoir les notifications de transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--base-url',
            type=str,
            default='https://core.plizmoney.com',
            help='URL de base de votre API (ex: https://core.plizmoney.com)'
        )
        parser.add_argument(
            '--djamo-api-url',
            type=str,
            default='https://api.djamo.io',
            help='URL de base de l\'API Djamo'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Liste les webhooks existants'
        )
        parser.add_argument(
            '--delete-all',
            action='store_true',
            help='Supprime tous les webhooks existants'
        )

    def handle(self, *args, **options):
        access_token = os.getenv('DJAMO_ACCESS_TOKEN')
        
        if not access_token:
            raise CommandError(
                'DJAMO_ACCESS_TOKEN non défini. '
                'Ajoutez-le dans votre fichier .env'
            )

        djamo_api = options['djamo_api_url']
        
        # Lister les webhooks existants
        if options['list']:
            self.list_webhooks(djamo_api, access_token)
            return
        
        # Supprimer tous les webhooks
        if options['delete_all']:
            self.delete_all_webhooks(djamo_api, access_token)
            return
        
        # Enregistrer les webhooks
        base_url = options['base_url']
        webhook_url = f"{base_url}/api/transaction/webhooks/djamo/"
        
        self.stdout.write(self.style.WARNING(
            f"Enregistrement des webhooks Djamo vers : {webhook_url}"
        ))
        
        topics = [
            ('transactions/started', 'Transaction démarrée'),
            ('transactions/completed', 'Transaction complétée'),
            ('transactions/failed', 'Transaction échouée'),
        ]
        
        for topic, description in topics:
            success = self.register_webhook(
                djamo_api,
                access_token,
                topic,
                webhook_url
            )
            
            if success:
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Webhook '{topic}' enregistré : {description}"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"❌ Échec de l'enregistrement du webhook '{topic}'"
                ))
        
        self.stdout.write(self.style.SUCCESS(
            "\n🎉 Configuration des webhooks terminée !"
        ))
        self.stdout.write(
            "\nVous pouvez vérifier les webhooks avec : "
            "python manage.py setup_djamo_webhooks --list"
        )

    def register_webhook(self, api_url, access_token, topic, webhook_url):
        """Enregistre un webhook chez Djamo"""
        url = f"{api_url}/v1/webhooks"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'topic': topic,
            'url': webhook_url
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Erreur: {e}"))
            if hasattr(e.response, 'text'):
                self.stdout.write(self.style.ERROR(f"Réponse: {e.response.text}"))
            return False

    def list_webhooks(self, api_url, access_token):
        """Liste tous les webhooks enregistrés"""
        url = f"{api_url}/v1/webhooks"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            webhooks = response.json()
            
            if not webhooks:
                self.stdout.write(self.style.WARNING(
                    "Aucun webhook enregistré"
                ))
                return
            
            self.stdout.write(self.style.SUCCESS(
                f"\n📋 {len(webhooks)} webhook(s) enregistré(s) :\n"
            ))
            
            for webhook in webhooks:
                self.stdout.write(
                    f"  • ID: {webhook.get('id')}\n"
                    f"    Topic: {webhook.get('topic')}\n"
                    f"    URL: {webhook.get('url')}\n"
                )
                
        except requests.exceptions.RequestException as e:
            raise CommandError(f"Erreur lors de la récupération des webhooks: {e}")

    def delete_all_webhooks(self, api_url, access_token):
        """Supprime tous les webhooks enregistrés"""
        url = f"{api_url}/v1/webhooks"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        
        try:
            # Récupérer la liste des webhooks
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            webhooks = response.json()
            
            if not webhooks:
                self.stdout.write(self.style.WARNING(
                    "Aucun webhook à supprimer"
                ))
                return
            
            self.stdout.write(self.style.WARNING(
                f"\n🗑️  Suppression de {len(webhooks)} webhook(s)...\n"
            ))
            
            for webhook in webhooks:
                webhook_id = webhook.get('id')
                delete_url = f"{url}/{webhook_id}"
                
                delete_response = requests.delete(delete_url, headers=headers)
                delete_response.raise_for_status()
                
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Webhook supprimé : {webhook.get('topic')}"
                ))
            
            self.stdout.write(self.style.SUCCESS(
                "\n🎉 Tous les webhooks ont été supprimés !"
            ))
                
        except requests.exceptions.RequestException as e:
            raise CommandError(f"Erreur lors de la suppression des webhooks: {e}")
