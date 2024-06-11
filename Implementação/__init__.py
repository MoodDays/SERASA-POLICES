import logging
import os
import requests
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import PolicyClient
import azure.functions as func

# Configurações
GITHUB_REPO = os.getenv('GITHUB_REPO')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
AZURE_SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')

def get_policies_from_github():
    """
    Função para obter políticas do repositório GitHub.
    """
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(f'https://api.github.com/repos/{GITHUB_REPO}/contents/policies', headers=headers)
    
    if response.status_code != 200:
        logging.error(f"Erro ao acessar o GitHub: {response.status_code}")
        return {}

    files = response.json()
    policies = {}
    for file in files:
        if file['name'].endswith('.txt'):
            policy_name = file['name'].replace('.txt', '')
            file_content = requests.get(file['download_url'], headers=headers).text
            policies[policy_name] = file_content
    return policies

def apply_policy(client, policy_name, policy_rules):
    """
    Função para aplicar uma política no Azure.
    """
    try:
        client.policy_definitions.create_or_update(
            policy_name,
            {
                "policy_type": "Custom",
                "mode": "All",
                "display_name": policy_name,
                "description": f"Policy for {policy_name}",
                "policy_rule": policy_rules
            }
        )
        logging.info(f"Política {policy_name} aplicada com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao aplicar a política {policy_name}: {e}")

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Função principal que será executada pela Azure Function.
    """
    logging.info('Azure Function iniciada para aplicar políticas.')

    credential = DefaultAzureCredential()
    client = PolicyClient(credential, AZURE_SUBSCRIPTION_ID)
    
    policies = get_policies_from_github()
    if not policies:
        return func.HttpResponse("Nenhuma política encontrada ou erro ao acessar o GitHub.", status_code=500)
    
    for policy_name, policy_rules in policies.items():
        apply_policy(client, policy_name, policy_rules)

    return func.HttpResponse("Políticas aplicadas com sucesso.", status_code=200)
