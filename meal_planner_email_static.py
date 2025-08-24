#!/usr/bin/env python3
"""
Agente de cardápio semanal (ESTÁTICO, sem ingredientes) – envio por e-mail

• Lê um catálogo local `recipes_static.json` (nome + url).
• Sorteia 5 receitas para segunda–sexta.
• Monta um e-mail simples (apenas menu, sem lista de compras) e envia via SMTP.
• Sem dependências externas (apenas biblioteca padrão do Python).
• No GitHub Actions, o agendamento é feito pelo próprio workflow (cron), então
  este script roda uma única vez e termina rapidamente.

Variáveis de ambiente esperadas:
- MEAL_PLANNER_EMAIL  : e-mail remetente (ex.: Gmail)
- MEAL_PLANNER_PASS   : senha SMTP (Gmail = senha de app)
- RECIPIENT_EMAIL     : e-mail destinatário

Opcional:
- SMTP_SERVER (padrão: smtp.gmail.com)
- SMTP_PORT   (padrão: 465)
- RECIPES_FILE (padrão: recipes_static.json)
"""

import os
import json
import random
import ssl
import smtplib
from typing import List, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DIAS_UTEIS = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira"]

def load_static_recipes(path: str = None) -> List[dict]:
    path = path or os.environ.get("RECIPES_FILE", "recipes_static.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Arquivo '{path}' não encontrado. Crie um recipes_static.json na raiz do repositório."
        )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError("O arquivo de receitas deve ser uma lista JSON não vazia.")
    # garantir que cada item tenha 'name' e 'url'
    norm = []
    for it in data:
        name = (it.get("name") or "").strip()
        url = (it.get("url") or "").strip()
        if not name:
            continue
        norm.append({"name": name, "url": url})
    if len(norm) < 5:
        raise ValueError("É necessário ter pelo menos 5 receitas no catálogo estático.")
    return norm

def build_menu_static(recipes: List[dict]) -> List[Tuple[str, str]]:
    """Sorteia 5 receitas e retorna tuplas (name, url)."""
    selected = random.sample(recipes, 5)
    return [(it["name"], it.get("url", "")) for it in selected]

def compose_email_body(menu: List[Tuple[str, str]]) -> str:
    linhas = ["Olá! Aqui está o cardápio semanal (sem lista de ingredientes):", ""]
    for idx, (name, url) in enumerate(menu):
        dia = DIAS_UTEIS[idx]
        if url:
            linhas.append(f"{dia}: {name} — {url}")
        else:
            linhas.append(f"{dia}: {name}")
    return "\n".join(linhas)

def send_email(subject: str, body: str) -> None:
    user = os.environ.get("MEAL_PLANNER_EMAIL")
    password = os.environ.get("MEAL_PLANNER_PASS")
    recipient = os.environ.get("RECIPIENT_EMAIL")
    if not (user and password and recipient):
        raise RuntimeError(
            "Defina MEAL_PLANNER_EMAIL, MEAL_PLANNER_PASS e RECIPIENT_EMAIL nas variáveis de ambiente."
        )
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))

    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        server.login(user, password)
        server.sendmail(user, recipient, msg.as_string())

def main() -> None:
    recipes = load_static_recipes()
    menu = build_menu_static(recipes)
    body = compose_email_body(menu)
    send_email(subject="Cardápio semanal (segunda–sexta) – sem ingredientes", body=body)

if __name__ == "__main__":
    main()
