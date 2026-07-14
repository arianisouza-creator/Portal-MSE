# Portal-MSE

Portal administrativo em Streamlit com o modulo de `Controle de Internet`.

## Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## O que o portal faz hoje

- `Visao Geral` aberta para consulta.
- `Linhas Ativas e Acessos` protegida por usuario e senha.
- `Contratos` protegida por usuario e senha.
- Geracao automatica dos meses com base no cadastro mestre de contratos.
- Banco SQLite local em `portal_data.db`.

## Regras atuais

- Usuario do cadastro: `ADM`
- Senha do cadastro: `mse2026`
- Campos mensais pendentes aparecem em vermelho.
- Linhas ativas calculam o percentual automaticamente pela quantidade de centros de custo informados em cada linha.

## Estrutura principal

- `app.py`: app principal em Streamlit.
- `portal_data.db`: banco SQLite criado automaticamente na primeira execucao.
- `requirements.txt`: dependencias do projeto.

## Observacao importante sobre dados

O banco atual e local. Isso funciona bem no computador e durante o desenvolvimento, mas em hospedagens como Streamlit Community Cloud o arquivo SQLite pode ser recriado em uma nova publicacao ou reinicio do app. Para persistencia definitiva em producao, o proximo passo ideal e migrar para um banco externo, como Supabase, Neon ou PostgreSQL gerenciado.
