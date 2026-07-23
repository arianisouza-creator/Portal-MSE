# Portal Internet

Projeto dedicado ao modulo de `Controle de Telefonia e Internet`.

## Escopo

Este projeto publica somente o modulo de internet, com:

- contratos de internet
- lancamentos mensais
- linhas ativas e acessos
- visao geral do fechamento mensal

## Arquitetura

- `app.py`: backend Flask que serve o HTML e expõe a API REST para o banco
- `controle-internet.html`: interface do portal
- `project-config.json`: define que este projeto abre somente o modulo `internet`
- `mysql-schema.sql`: schema atual do banco

## Como rodar

```bash
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Depois acesse `http://localhost:8000`.
