"""Testes unitários para dashboard.models.qualidade."""
from __future__ import annotations

import pandas as pd
import pytest

from dashboard.models.qualidade import Aviso, RelatorioQualidade, mensagens


def test_relatorio_qualidade_vazio():
    rq = RelatorioQualidade()
    assert rq.vazio
    assert rq.avisos == []
    assert mensagens(rq) == []
    assert mensagens(None) == []

    df_vazio = rq.como_dataframe()
    assert isinstance(df_vazio, pd.DataFrame)
    assert list(df_vazio.columns) == ["tipo", "produto", "detalhe"]
    assert df_vazio.empty


def test_relatorio_qualidade_com_avisos():
    rq = RelatorioQualidade()
    a1 = Aviso(tipo="ATIVO_DESCONHECIDO", produto="XYZ3", detalhe="Não encontrado no catálogo")
    a2 = Aviso(tipo="CLASSE_DIVERGENTE", produto="ROXO34", detalhe="")
    rq.add(a1)
    rq.add(a2)

    assert not rq.vazio
    assert len(rq.avisos) == 2

    df = rq.como_dataframe()
    assert len(df) == 2
    assert df["produto"].tolist() == ["XYZ3", "ROXO34"]

    msgs = mensagens(rq)
    assert len(msgs) == 2
    assert msgs[0] == "[ATIVO_DESCONHECIDO] XYZ3: Não encontrado no catálogo"
    assert msgs[1] == "[CLASSE_DIVERGENTE] ROXO34"
