from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Portal Administrativo | Controle de Internet",
    page_icon=":globe_with_meridians:",
    layout="wide",
    initial_sidebar_state="expanded",
)


DB_FILE = Path(__file__).with_name("portal_data.db")
PROTECTED_USER = "ADM"
PROTECTED_PASS = "mse2026"
MONTH_NAMES = {
    1: "Jan",
    2: "Fev",
    3: "Mar",
    4: "Abr",
    5: "Mai",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Set",
    10: "Out",
    11: "Nov",
    12: "Dez",
}


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db_connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                project TEXT NOT NULL,
                due_day INTEGER NOT NULL,
                contract_number TEXT NOT NULL,
                status TEXT NOT NULL,
                start_month TEXT NOT NULL,
                inactive_month TEXT,
                contact TEXT,
                login_name TEXT,
                password_value TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS active_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month_ref TEXT NOT NULL,
                number_value TEXT NOT NULL,
                responsible TEXT NOT NULL,
                cost_centers TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS monthly_entries (
                contract_id INTEGER NOT NULL,
                month_ref TEXT NOT NULL,
                amount REAL,
                order_number TEXT,
                approved INTEGER,
                s1 INTEGER,
                notes TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (contract_id, month_ref),
                FOREIGN KEY (contract_id) REFERENCES contracts(id)
            );
            """
        )


def parse_month(value: str) -> date:
    year, month = value.split("-")
    return date(int(year), int(month), 1)


def month_key(value: date | datetime | None = None) -> str:
    base = value.date() if isinstance(value, datetime) else value or date.today()
    return base.strftime("%Y-%m")


def month_label(value: str) -> str:
    current = parse_month(value)
    return f"{MONTH_NAMES[current.month]}/{current.year}"


def month_to_int(value: str) -> int:
    current = parse_month(value)
    return current.year * 12 + current.month


def month_picker(label: str, key: str, value: str) -> str:
    default_date = parse_month(value)
    picked = st.date_input(
        label,
        value=default_date,
        format="DD/MM/YYYY",
        key=key,
    )
    return month_key(picked)


def format_currency(value: float | None) -> str:
    if value is None:
        return "Pendente"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def bool_label(value: int | None) -> str:
    if value is None:
        return "Pendente"
    return "Sim" if value == 1 else "Nao"


def auth_ok() -> bool:
    return st.session_state.get("cadastro_auth", False)


def logout() -> None:
    st.session_state["cadastro_auth"] = False


def render_auth_gate() -> bool:
    if auth_ok():
        return True

    st.markdown(
        """
        <div style="max-width:520px;padding:24px;border:1px solid #dbe3f0;border-radius:18px;background:#ffffff;box-shadow:0 12px 30px rgba(15,23,42,.08);margin:16px 0;">
          <div style="font-size:26px;font-weight:800;color:#17356c;margin-bottom:6px;">Area de cadastro protegida</div>
          <div style="color:#5f6c84;">Use este acesso apenas para contratos, linhas ativas e credenciais.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("protected_login"):
        cols = st.columns(2)
        username = cols[0].text_input("Usuario")
        password = cols[1].text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar", use_container_width=True)

    if submit:
        if username == PROTECTED_USER and password == PROTECTED_PASS:
            st.session_state["cadastro_auth"] = True
            st.rerun()
        st.error("Usuario ou senha invalidos.")

    st.caption("Acesso do cadastro: `ADM` / `mse2026`")
    return False


def list_contracts() -> list[dict[str, Any]]:
    with db_connect() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM contracts
            ORDER BY status DESC, company, project, contract_number
            """
        ).fetchall()
    return [dict(row) for row in rows]


def save_contract(data: dict[str, Any], contract_id: int | None = None) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    with db_connect() as conn:
        if contract_id:
            conn.execute(
                """
                UPDATE contracts
                SET company = ?, project = ?, due_day = ?, contract_number = ?, status = ?,
                    start_month = ?, inactive_month = ?, contact = ?, login_name = ?,
                    password_value = ?, notes = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    data["company"],
                    data["project"],
                    data["due_day"],
                    data["contract_number"],
                    data["status"],
                    data["start_month"],
                    data["inactive_month"] or None,
                    data["contact"],
                    data["login_name"],
                    data["password_value"],
                    data["notes"],
                    now,
                    contract_id,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO contracts (
                    company, project, due_day, contract_number, status,
                    start_month, inactive_month, contact, login_name,
                    password_value, notes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["company"],
                    data["project"],
                    data["due_day"],
                    data["contract_number"],
                    data["status"],
                    data["start_month"],
                    data["inactive_month"] or None,
                    data["contact"],
                    data["login_name"],
                    data["password_value"],
                    data["notes"],
                    now,
                    now,
                ),
            )


def get_contract(contract_id: int) -> dict[str, Any] | None:
    with db_connect() as conn:
        row = conn.execute(
            "SELECT * FROM contracts WHERE id = ?",
            (contract_id,),
        ).fetchone()
    return dict(row) if row else None


def contract_visible_for_month(contract: dict[str, Any], selected_month: str) -> bool:
    current = month_to_int(selected_month)
    start = month_to_int(contract["start_month"])
    inactive = contract.get("inactive_month")
    end = month_to_int(inactive) if inactive else None

    if current < start:
        return False
    if contract["status"] == "Inativo" and end is not None and current >= end:
        return False
    return True


def list_lines(month_ref: str) -> list[dict[str, Any]]:
    with db_connect() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM active_lines
            WHERE month_ref = ?
            ORDER BY id
            """,
            (month_ref,),
        ).fetchall()

    items: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        centers = [part.strip() for part in item["cost_centers"].split(",") if part.strip()]
        count = len(centers) if centers else 1
        item["centers_list"] = centers or [item["cost_centers"]]
        item["percentage_each"] = round(100 / count, 2)
        items.append(item)
    return items


def save_line(month_ref: str, number_value: str, responsible: str, cost_centers: str) -> None:
    with db_connect() as conn:
        conn.execute(
            """
            INSERT INTO active_lines (month_ref, number_value, responsible, cost_centers, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                month_ref,
                number_value,
                responsible,
                cost_centers,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def delete_line(line_id: int) -> None:
    with db_connect() as conn:
        conn.execute("DELETE FROM active_lines WHERE id = ?", (line_id,))


def load_monthly_entry(contract_id: int, month_ref: str) -> dict[str, Any] | None:
    with db_connect() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM monthly_entries
            WHERE contract_id = ? AND month_ref = ?
            """,
            (contract_id, month_ref),
        ).fetchone()
    return dict(row) if row else None


def save_monthly_entry(
    contract_id: int,
    month_ref: str,
    amount: float | None,
    order_number: str,
    approved: int | None,
    s1: int | None,
    notes: str,
) -> None:
    with db_connect() as conn:
        conn.execute(
            """
            INSERT INTO monthly_entries (contract_id, month_ref, amount, order_number, approved, s1, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(contract_id, month_ref)
            DO UPDATE SET
                amount = excluded.amount,
                order_number = excluded.order_number,
                approved = excluded.approved,
                s1 = excluded.s1,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            (
                contract_id,
                month_ref,
                amount,
                order_number or None,
                approved,
                s1,
                notes,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def month_rows(selected_month: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for contract in list_contracts():
        if not contract_visible_for_month(contract, selected_month):
            continue
        entry = load_monthly_entry(contract["id"], selected_month) or {}
        rows.append(
            {
                "id": contract["id"],
                "status": contract["status"],
                "project": contract["project"],
                "company": contract["company"],
                "due_day": contract["due_day"],
                "contract_number": contract["contract_number"],
                "contact": contract["contact"] or "-",
                "login_name": contract["login_name"] or "",
                "password_value": contract["password_value"] or "",
                "contract_notes": contract["notes"] or "",
                "month_notes": entry.get("notes") or "",
                "amount": entry.get("amount"),
                "order_number": entry.get("order_number") or "",
                "approved": entry.get("approved"),
                "s1": entry.get("s1"),
            }
        )
    return rows


def metric_card(label: str, value: str, help_text: str) -> None:
    st.markdown(
        f"""
        <div style="background:#ffffff;border:1px solid #dce6f4;border-radius:16px;padding:18px;box-shadow:0 4px 14px rgba(15,23,42,.04);min-height:110px;">
          <div style="font-size:12px;font-weight:700;color:#476183;text-transform:uppercase;">{label}</div>
          <div style="font-size:28px;font-weight:800;color:#183153;margin-top:8px;">{value}</div>
          <div style="font-size:12px;color:#74839b;margin-top:4px;">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pending_html(value: str, is_pending: bool) -> str:
    color = "#d92d20" if is_pending else "#1f2a37"
    return f"<span style='color:{color};font-weight:700;'>{value}</span>"


def render_sidebar(selected_month: str) -> str:
    st.sidebar.markdown(
        """
        <style>
          [data-testid="stSidebar"] { background: linear-gradient(180deg, #1f3968 0%, #243f74 100%); }
          [data-testid="stSidebar"] * { color: #ffffff !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("## Portal MSE")
    st.sidebar.caption(f"Mes ativo: {month_label(selected_month)}")

    with st.sidebar.expander("Administrativo", expanded=True):
        page = st.radio(
            "Menu",
            options=["Visao Geral", "Linhas Ativas e Acessos", "Contratos"],
            label_visibility="collapsed",
        )

    if auth_ok():
        st.sidebar.button("Sair do cadastro", on_click=logout, use_container_width=True)
    else:
        st.sidebar.caption("Cadastro protegido")

    return page


def render_overview(selected_month: str) -> None:
    rows = month_rows(selected_month)
    active_lines = list_lines(selected_month)
    contracts_count = len(rows)
    total_amount = sum(row["amount"] or 0 for row in rows)
    operators = len({row["company"] for row in rows})
    next_due = min((row["due_day"] for row in rows), default="-")
    orders = len([row for row in rows if row["order_number"]])

    st.markdown("## Dashboard Executivo")
    st.caption("Controle de Internet com geracao automatica por contrato.")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("Contratos ativos", str(contracts_count), "Visiveis neste mes")
    with c2:
        metric_card("Valor mensal", format_currency(total_amount if total_amount else 0), "Total preenchido")
    with c3:
        metric_card("Operadoras", str(operators), "Empresas distintas")
    with c4:
        metric_card("Proximo vencimento", str(next_due), "Dia mais proximo")
    with c5:
        metric_card("Linhas ativas", str(len(active_lines)), "Cadastro do mes")

    left, right = st.columns([1.5, 1])
    with left:
        st.markdown("### Valor por obra")
        if rows:
            chart_df = pd.DataFrame(
                {
                    "Obra": [row["project"] for row in rows],
                    "Valor": [row["amount"] or 0 for row in rows],
                }
            ).groupby("Obra", as_index=True).sum()
            st.bar_chart(chart_df)
        else:
            st.info("Nenhum contrato ativo no mes selecionado.")

    with right:
        st.markdown("### Pendencias do mes")
        pending = [
            row
            for row in rows
            if row["amount"] is None or not row["order_number"] or row["approved"] is None or row["s1"] is None
        ]
        if not pending:
            st.success("Nao ha pendencias neste mes.")
        else:
            for row in pending[:8]:
                fields = []
                if row["amount"] is None:
                    fields.append("Valor")
                if not row["order_number"]:
                    fields.append("Pedido")
                if row["approved"] is None:
                    fields.append("Aprovado")
                if row["s1"] is None:
                    fields.append("S1")
                st.markdown(f"**{row['company']}**  \n{row['project']}  \nPendente: {', '.join(fields)}")

    st.markdown("### Contratos do mes")
    header = st.columns([1.0, 1.2, 2.1, 0.8, 1.2, 1.4, 1.1, 1.0, 0.9, 0.8, 0.8])
    labels = [
        "Status",
        "Obra",
        "Empresa",
        "Venc.",
        "Contrato",
        "Contato",
        "Valor",
        "Pedido",
        "Aprov.",
        "S1",
        "Acoes",
    ]
    for col, label in zip(header, labels):
        col.markdown(
            f"<div style='font-size:11px;color:#7b8ba3;font-weight:700;text-transform:uppercase;padding-bottom:6px;'>{label}</div>",
            unsafe_allow_html=True,
        )

    if not rows:
        st.info("Nenhum contrato disponivel neste mes.")
        return

    for row in rows:
        cols = st.columns([1.0, 1.2, 2.1, 0.8, 1.2, 1.4, 1.1, 1.0, 0.9, 0.8, 0.8])
        cols[0].markdown(
            pending_html("ATIVO" if row["status"] == "Ativo" else "INATIVO", row["status"] != "Ativo"),
            unsafe_allow_html=True,
        )
        cols[1].write(row["project"])
        cols[2].write(row["company"])
        cols[3].write(str(row["due_day"]))
        cols[4].write(row["contract_number"])
        cols[5].write(row["contact"])
        cols[6].markdown(pending_html(format_currency(row["amount"]), row["amount"] is None), unsafe_allow_html=True)
        cols[7].markdown(pending_html(row["order_number"] or "Pendente", not row["order_number"]), unsafe_allow_html=True)
        cols[8].markdown(pending_html(bool_label(row["approved"]), row["approved"] is None), unsafe_allow_html=True)
        cols[9].markdown(pending_html(bool_label(row["s1"]), row["s1"] is None), unsafe_allow_html=True)
        if cols[10].button("Editar", key=f"edit_month_{row['id']}_{selected_month}"):
            st.session_state["edit_month_row"] = row["id"]
        st.divider()

    edit_id = st.session_state.get("edit_month_row")
    if not edit_id:
        return

    selected = next((item for item in rows if item["id"] == edit_id), None)
    if not selected:
        return

    st.markdown("### Atualizar pendencias do mes")
    with st.form("month_entry_form"):
        cols = st.columns(4)
        amount_raw = cols[0].text_input(
            "Valor",
            value="" if selected["amount"] is None else str(selected["amount"]).replace(".", ","),
            placeholder="Ex.: 1339,94",
        )
        order_number = cols[1].text_input("Pedido", value=selected["order_number"])
        approved = cols[2].selectbox(
            "Aprovado",
            options=["Pendente", "Sim", "Nao"],
            index=0 if selected["approved"] is None else 1 if selected["approved"] == 1 else 2,
        )
        s1 = cols[3].selectbox(
            "Aprovado no S1",
            options=["Pendente", "Sim", "Nao"],
            index=0 if selected["s1"] is None else 1 if selected["s1"] == 1 else 2,
        )
        notes = st.text_input("Observacao do mes", value=selected["month_notes"])
        save = st.form_submit_button("Salvar atualizacao", use_container_width=True)

    if save:
        amount = None
        if amount_raw.strip():
            amount = float(amount_raw.replace(".", "").replace(",", "."))
        save_monthly_entry(
            contract_id=selected["id"],
            month_ref=selected_month,
            amount=amount,
            order_number=order_number,
            approved=None if approved == "Pendente" else 1 if approved == "Sim" else 0,
            s1=None if s1 == "Pendente" else 1 if s1 == "Sim" else 0,
            notes=notes,
        )
        st.session_state["edit_month_row"] = None
        st.success("Registro mensal atualizado.")
        st.rerun()


def render_lines_page(selected_month: str) -> None:
    st.markdown("## Linhas Ativas")
    st.caption("Cadastre aqui as linhas do mes e o rateio automatico por centro de custo.")

    with st.form("line_form"):
        cols = st.columns(3)
        number_value = cols[0].text_input("Numero", placeholder="43 99999-0000")
        responsible = cols[1].text_input("Responsavel", placeholder="Nome do responsavel")
        cost_centers = cols[2].text_input("Centro de custo", placeholder="ADM, MKT, DTE")
        submit = st.form_submit_button("Adicionar linha", use_container_width=True)

    if submit:
        if number_value and responsible and cost_centers:
            save_line(selected_month, number_value, responsible, cost_centers)
            st.success("Linha cadastrada com sucesso.")
            st.rerun()
        st.error("Preencha numero, responsavel e centro de custo.")

    lines = list_lines(selected_month)
    st.markdown("### Linhas cadastradas no mes")
    if not lines:
        st.info("Nenhuma linha cadastrada para este mes.")
    else:
        head = st.columns([1.1, 1.2, 2.2, 1.0, 0.8])
        titles = ["Numero", "Responsavel", "Centros de custo", "Percentual", "Acoes"]
        for col, title in zip(head, titles):
            col.markdown(
                f"<div style='font-size:11px;color:#7b8ba3;font-weight:700;text-transform:uppercase;padding-bottom:6px;'>{title}</div>",
                unsafe_allow_html=True,
            )

        for line in lines:
            cols = st.columns([1.1, 1.2, 2.2, 1.0, 0.8])
            cols[0].write(line["number_value"])
            cols[1].write(line["responsible"])
            cols[2].write(", ".join(line["centers_list"]))
            cols[3].write(f"{line['percentage_each']:.2f}% por C.C")
            if cols[4].button("Remover", key=f"remove_line_{line['id']}"):
                delete_line(line["id"])
                st.rerun()
            st.divider()

    st.markdown("### Credenciais dos contratos ativos")
    contract_rows = month_rows(selected_month)
    if not contract_rows:
        st.info("Sem contratos ativos neste mes.")
    else:
        for row in contract_rows:
            with st.container(border=True):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"**{row['company']}**")
                    st.write(f"Obra: {row['project']}")
                    st.write(f"Contrato: {row['contract_number']}")
                    st.write(f"Contato: {row['contact']}")
                with c2:
                    st.write(f"Login: {row['login_name'] or '-'}")
                    st.write(f"Senha: {row['password_value'] or '-'}")
                if row["contract_notes"]:
                    st.caption(f"Observacao: {row['contract_notes']}")


def render_contracts_page(selected_month: str) -> None:
    st.markdown("## Cadastro de Contratos")
    st.caption("A base mestra gera automaticamente os registros de cada mes a partir do mes de inicio.")

    contract_rows = list_contracts()
    edit_id = st.session_state.get("edit_contract_id")
    editing = get_contract(edit_id) if edit_id else None

    with st.form("contract_form"):
        row1 = st.columns(4)
        company = row1[0].text_input("Empresa", value=editing["company"] if editing else "", placeholder="Ex.: VIVO")
        project = row1[1].text_input("Obra", value=editing["project"] if editing else "", placeholder="Ex.: Sede")
        due_day = row1[2].number_input(
            "Vencimento",
            min_value=1,
            max_value=31,
            value=int(editing["due_day"]) if editing else 1,
        )
        contract_number = row1[3].text_input(
            "Numero do contrato",
            value=editing["contract_number"] if editing else "",
            placeholder="Ex.: 285704686",
        )

        row2 = st.columns(4)
        status = row2[0].selectbox(
            "Status",
            options=["Ativo", "Inativo"],
            index=0 if not editing or editing["status"] == "Ativo" else 1,
        )
        with row2[1]:
            start_month = month_picker(
                "Mes de inicio",
                key="contract_start_month",
                value=editing["start_month"] if editing else selected_month,
            )
        with row2[2]:
            inactive_month = month_picker(
                "Mes/ano inativo",
                key="contract_inactive_month",
                value=editing["inactive_month"] if editing and editing["inactive_month"] else selected_month,
            )
        contact = row2[3].text_input("Contato", value=editing["contact"] if editing else "", placeholder="Telefone ou WhatsApp")

        row3 = st.columns(2)
        login_name = row3[0].text_input("Login", value=editing["login_name"] if editing else "")
        password_value = row3[1].text_input("Senha", value=editing["password_value"] if editing else "", type="password")
        notes = st.text_area("Observacao", value=editing["notes"] if editing else "", height=100)

        save = st.form_submit_button("Salvar contrato", use_container_width=True)

    if save:
        if not all([company.strip(), project.strip(), contract_number.strip()]):
            st.error("Preencha empresa, obra e numero do contrato.")
        else:
            save_contract(
                {
                    "company": company.strip(),
                    "project": project.strip(),
                    "due_day": int(due_day),
                    "contract_number": contract_number.strip(),
                    "status": status,
                    "start_month": start_month,
                    "inactive_month": inactive_month if status == "Inativo" else "",
                    "contact": contact.strip(),
                    "login_name": login_name.strip(),
                    "password_value": password_value,
                    "notes": notes.strip(),
                },
                contract_id=edit_id,
            )
            st.session_state["edit_contract_id"] = None
            st.success("Contrato salvo com sucesso.")
            st.rerun()

    st.markdown("### Contratos cadastrados")
    if not contract_rows:
        st.info("Nenhum contrato cadastrado ainda.")
        return

    head = st.columns([1.7, 1.2, 0.9, 1.0, 1.0, 0.9])
    labels = ["Empresa / Obra", "Contrato", "Status", "Inicio", "Inativo em", "Acoes"]
    for col, label in zip(head, labels):
        col.markdown(
            f"<div style='font-size:11px;color:#7b8ba3;font-weight:700;text-transform:uppercase;padding-bottom:6px;'>{label}</div>",
            unsafe_allow_html=True,
        )

    for contract in contract_rows:
        cols = st.columns([1.7, 1.2, 0.9, 1.0, 1.0, 0.9])
        cols[0].write(f"{contract['company']} | {contract['project']}")
        cols[1].write(contract["contract_number"])
        cols[2].write(contract["status"])
        cols[3].write(month_label(contract["start_month"]))
        cols[4].write(month_label(contract["inactive_month"]) if contract["inactive_month"] else "-")
        if cols[5].button("Editar", key=f"edit_contract_{contract['id']}"):
            st.session_state["edit_contract_id"] = contract["id"]
            st.rerun()
        st.divider()


def main() -> None:
    init_db()

    st.markdown(
        """
        <style>
          .stApp { background: #f4f7fb; }
          .block-container { padding-top: 1.1rem; padding-bottom: 3rem; }
          div[data-testid="stForm"] { background:#ffffff; border:1px solid #dde6f2; border-radius:18px; padding:18px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    top = st.columns([1.1, 3.8])
    with top[0]:
        selected_month = month_picker(
            "Mes de referencia",
            key="selected_month_picker",
            value=st.session_state.get("selected_month", month_key()),
        )
    st.session_state["selected_month"] = selected_month
    with top[1]:
        st.markdown("## Controle de Internet")
        st.caption("Portal administrativo com cadastro protegido e base persistida em SQLite.")

    page = render_sidebar(selected_month)

    if page == "Visao Geral":
        render_overview(selected_month)
        return

    if not render_auth_gate():
        return

    if page == "Linhas Ativas e Acessos":
        render_lines_page(selected_month)
    else:
        render_contracts_page(selected_month)


if __name__ == "__main__":
    main()
