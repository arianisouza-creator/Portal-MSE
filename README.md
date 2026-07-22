# Portal-MSE

Portal administrativo com interface HTML/CSS customizada e backend Flask,
persistindo os dados em um banco **MySQL**. Módulos:

- `Controle de Telefonia e Internet`
- `Controle da Diarista`
- `Controle de Passagens`

## Arquitetura

Antes o front-end conversava direto com o **Supabase** (PostgREST) a partir do
navegador. Como o navegador não fala diretamente com o MySQL, agora existe um
**servidor único em Flask** (`app.py`) que:

- serve o portal (`controle-internet.html`) com a configuração injetada;
- expõe uma **API REST** (subconjunto compatível com o formato antigo) que lê e
  grava no MySQL.

```
Navegador (controle-internet.html)
        │  fetch /rest/v1/<tabela>
        ▼
Flask (app.py)  ──►  MySQL (controle_internet_prod)
```

### Endpoints da API

| Método | Rota                    | Uso                                                        |
| ------ | ----------------------- | ---------------------------------------------------------- |
| GET    | `/`                     | Portal HTML com config injetada                            |
| GET    | `/health`               | Healthcheck + teste de conexão ao banco                    |
| GET    | `/rest/v1/<tabela>`     | `SELECT *` com `?select=*&order=coluna.asc,...`            |
| POST   | `/rest/v1/<tabela>`     | Upsert (`INSERT ... ON DUPLICATE KEY UPDATE`)              |
| DELETE | `/rest/v1/<tabela>`     | `DELETE` com filtro `?coluna=eq.valor`                     |

## Banco de dados

Aplique o schema no banco de produção:

```bash
mysql -h dbsubdominios.portalmse.com.br -u controle_internet_prod -p controle_internet < mysql-schema.sql
```

> O banco de dados é `controle_internet` e o usuário de acesso é
> `controle_internet_prod`. Ajuste `DB_NAME`/`DB_USER` no `.env` se mudar.

## Como rodar localmente

```bash
pip install -r requirements.txt
copy .env.example .env   # (Windows) e edite os valores
python app.py
```

Acesse http://localhost:8000

## Configuração

Todas as credenciais vêm de variáveis de ambiente (arquivo `.env`, veja
[.env.example](.env.example)):

- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `PASSAGENS_API_BASE_URL`, `PASSAGENS_API_TOKEN`
- `PORTAL_API_BASE_URL` (vazio = mesma origem)
- `PORT`, `FLASK_DEBUG`

## Deploy na AWS

Servidor único, então basta um processo WSGI atrás de um proxy:

```bash
gunicorn app:app --bind 0.0.0.0:8000 --workers 3
```

Sugestões:

- **EC2** (ou Elastic Beanstalk Python): `gunicorn app:app` + Nginx na frente.
- Banco em **Amazon RDS MySQL** — basta apontar `DB_HOST`/`DB_NAME`/credenciais.
- Configure as variáveis via ambiente/Secrets Manager (não versione o `.env`).

## Auto-deploy (webhook do GitHub)

Um push na branch `main` dispara o deploy automático no servidor:

```
GitHub push (main)
      │  POST https://controle-internet.portalmse.com.br/gh-deploy  (assinado HMAC)
      ▼
portal-mse-webhook.service (gunicorn :5061, webhook.py)
      │  valida assinatura -> dispara deploy.sh (destacado)
      ▼
deploy.sh: git reset --hard origin/main + pip install (se mudou) + restart do portal-mse.service
```

- `webhook.py`: listener isolado do app (serviço próprio), para não ser derrubado quando o portal reinicia.
- `deploy.sh`: script de atualização (log em `deploy.log`).
- Segurança: valida `X-Hub-Signature-256` (HMAC-SHA256) com `GITHUB_WEBHOOK_SECRET`; só faz deploy em push na branch `DEPLOY_BRANCH`.

## Comportamento

- O layout continua 100% no arquivo HTML.
- O portal lê e grava direto no MySQL via API do próprio servidor.
- Se o banco ficar indisponível, o portal usa cache local do navegador para não
  quebrar a interface.
- O módulo de `Passagens` também sincroniza linhas importadas da API externa,
  complementos manuais e créditos cadastrados.
- Abas protegidas continuam usando: usuário `ADM`, senha `mse2026`.

## Estrutura principal

- [app.py](app.py): servidor Flask (portal + API REST → MySQL).
- [controle-internet.html](controle-internet.html): layout e interações.
- [mysql-schema.sql](mysql-schema.sql): schema das tabelas no MySQL.

## Observação de segurança

O acesso `ADM / mse2026` protege a navegação, mas não substitui uma modelagem de
segurança mais forte. Para produção, considere autenticação real no backend e um
usuário MySQL com privilégios mínimos restrito a este banco.
