import re
from pathlib import Path
import pandas as pd
import pytest

from dashboard.loaders.movimentacao import read_movimentacao_file
from dashboard.loaders.posicao import read_posicao_file
from dashboard.models.ativos import (
    AtivoDesconhecido,
    AtivoId,
    Classe,
    anotar_ativos,
    normalizar_nome,
    resolver_ativo,
    resolver_ativo_seguro,
)
from dashboard.models.qualidade import Aviso, RelatorioQualidade


FIXTURES_MOV_DIR = Path(__file__).resolve().parents[1] / "xlsx" / "movimentacao"


def obter_produtos_extrato() -> list[str]:
    arquivos = list(FIXTURES_MOV_DIR.glob("*.xlsx"))
    if not arquivos:
        pytest.skip("Nenhum arquivo de movimentação encontrado")
    dfs = [read_movimentacao_file(p) for p in arquivos]
    df = pd.concat(dfs, ignore_index=True)
    return sorted(df["produto"].dropna().unique().tolist())


def test_31_produtos_do_extrato_resolvem_para_ativo_id():
    """(a) Os 31 valores distintos de produto do extrato resolvem para um AtivoId."""
    produtos = obter_produtos_extrato()
    assert len(produtos) == 31, f"Esperado 31 produtos distintos no extrato, obtido {len(produtos)}"

    ids_resolvidos = []
    for prod in produtos:
        ativo_id = resolver_ativo(prod)
        assert isinstance(ativo_id, AtivoId)
        assert ativo_id.classe != "PENDENTE"
        assert ativo_id.codigo != "PENDENTE"
        assert len(ativo_id.codigo.strip()) > 0
        ids_resolvidos.append(ativo_id)

    # Garante que nenhum id tem campos vazios ou inventados
    assert all(a.classe in {"AÇÕES", "BDR", "ETF", "TESOURO"} for a in ids_resolvidos)


@pytest.mark.parametrize(
    "variacao_1, variacao_2, codigo_esperado",
    [
        ("CPFE3 - CPFL ENERGIA S.A.", "CPFE3 - CPFL ENERGIA S/A", "CPFE3"),
        ("ITSA4 - ITAUSA S.A.", "ITSA4 - ITAUSA S/A", "ITSA4"),
        ("ITSA2 - ITAUSA S.A.", "ITSA2 - ITAUSA S/A", "ITSA2"),
        ("VALE3 - VALE S.A.", "VALE3 - VALE S/A", "VALE3"),
        (
            "PETR4 - PETROLEO BRASILEIRO S/A - PETROBRAS",
            "PETR4 - PETROLEO BRASILEIRO S/A PETROBRAS",
            "PETR4",
        ),
        (
            "PETR4 - PETROLEO BRASILEIRO S/A PETROBRAS",
            "PETR4 - PETROLEO BRASILEIRO S.A. PETROBRAS",
            "PETR4",
        ),
        (
            "B3SA3 - B3",
            "B3SA3 - B3 S.A. - BRASIL, BOLSA, BALCÃO",
            "B3SA3",
        ),
        (
            "ROXO34 - NU HOLDINGS",
            "ROXO34 - NU HOLDINGS LTD.",
            "ROXO34",
        ),
    ],
)
def test_variacoes_de_razao_social_dao_o_mesmo_id(variacao_1, variacao_2, codigo_esperado):
    """(a) Variações de razão social ('S/A' e 'S.A.', 'PETROBRAS' com e sem hífen) dão o mesmo id."""
    id_1 = resolver_ativo(variacao_1)
    id_2 = resolver_ativo(variacao_2)

    assert id_1 == id_2
    assert id_1.codigo == codigo_esperado


def test_9_titulos_do_tesouro_viram_ids_distintos():
    """(b) Os 9 títulos do Tesouro viram ids distintos e 'Tesouro Prefixado 2024' nunca vira '2024'."""
    titulos_tesouro = [
        "Tesouro Educa+ 2026",
        "Tesouro Educa+ 2028",
        "Tesouro IPCA+ 2026",
        "Tesouro IPCA+ 2032",
        "Tesouro Prefixado 2024",
        "Tesouro Prefixado com Juros Semestrais 2035",
        "Tesouro Prefixado com Juros Semestrais 2037",
        "Tesouro Selic 2028",
        "Tesouro Selic 2031",
    ]

    ids = [resolver_ativo(t) for t in titulos_tesouro]

    # Todos devem ser instâncias de AtivoId com classe TESOURO
    for ativo_id in ids:
        assert isinstance(ativo_id, AtivoId)
        assert ativo_id.classe == "TESOURO"

    # Devem ser 9 ids únicos e distintos
    assert len(set(ids)) == 9
    assert len(set(a.codigo for a in ids)) == 9

    # Distinções específicas exigidas
    assert resolver_ativo("Tesouro IPCA+ 2026") != resolver_ativo("Tesouro IPCA+ 2032")
    assert resolver_ativo("Tesouro Educa+ 2026") != resolver_ativo("Tesouro Educa+ 2028")
    assert resolver_ativo("Tesouro Selic 2028") != resolver_ativo("Tesouro Selic 2031")
    assert resolver_ativo("Tesouro Prefixado com Juros Semestrais 2035") != resolver_ativo(
        "Tesouro Prefixado com Juros Semestrais 2037"
    )

    # 'Tesouro Prefixado 2024' nunca vira '2024'
    prefixado_2024 = resolver_ativo("Tesouro Prefixado 2024")
    assert prefixado_2024.codigo != "2024"
    assert "Tesouro" in prefixado_2024.codigo
    assert prefixado_2024 == AtivoId(classe="TESOURO", codigo="Tesouro Prefixado 2024")


def test_nubr33_nubr35_e_roxo34_resolvem_para_o_mesmo_id():
    """(c) NUBR33, NUBR35 e ROXO34 resolvem para o mesmo id."""
    id_nubr33 = resolver_ativo("NUBR33 - NU HOLDINGS LTD.")
    id_nubr35 = resolver_ativo("NUBR35 - NU HOLDINGS LTD.")
    id_roxo34 = resolver_ativo("ROXO34 - NU HOLDINGS")

    # Também com tickers simples
    id_tick_33 = resolver_ativo("NUBR33")
    id_tick_35 = resolver_ativo("NUBR35")
    id_tick_34 = resolver_ativo("ROXO34")

    assert id_nubr33 == id_roxo34
    assert id_nubr35 == id_roxo34
    assert id_tick_33 == id_roxo34
    assert id_tick_35 == id_roxo34
    assert id_tick_34 == id_roxo34

    assert id_roxo34.codigo == "ROXO34"
    assert id_roxo34.classe == "BDR"


@pytest.mark.parametrize(
    "produto_invalido",
    [
        "PRODUTO_TOTALMENTE_DESCONHECIDO_XYZ",
        "Criptomoeda Fictícia 123",
        "INVENTADO4",
        "",
        None,
    ],
)
def test_produto_desconhecido_gera_erro_ou_aviso_nunca_chave_inventada(produto_invalido):
    """(d) Produto desconhecido gera erro ou aviso explícito, nunca uma chave inventada."""
    with pytest.raises((ValueError, KeyError)):
        resolver_ativo(produto_invalido)


def test_ativo_id_nao_e_igual_a_string():
    aid = AtivoId(Classe.BDR, "ROXO34")
    assert aid != "ROXO34"


def test_resolver_ativo_desconhecido_levanta():
    with pytest.raises(AtivoDesconhecido) as exc_info:
        resolver_ativo("Tesouro IPCA+ 2040")
    assert exc_info.value.produto == "Tesouro IPCA+ 2040"


def test_resolver_ativo_seguro_registra_aviso():
    qualidade = RelatorioQualidade()
    aid = resolver_ativo_seguro("Tesouro IPCA+ 2040", qualidade)
    assert aid == AtivoId(Classe.DESCONHECIDO, normalizar_nome("Tesouro IPCA+ 2040"))
    assert len(qualidade.avisos) == 1
    assert qualidade.avisos[0].produto == "Tesouro IPCA+ 2040"

    id_2026 = resolver_ativo("Tesouro IPCA+ 2026")
    id_2032 = resolver_ativo("Tesouro IPCA+ 2032")
    assert aid != id_2026
    assert aid != id_2032


def test_loaders_anotam_ativo_id():
    mov_fixture = Path(__file__).resolve().parent / "fixtures" / "movimentacao_7_ativos.xlsx"
    pos_fixture = Path(__file__).resolve().parent / "fixtures" / "posicao_7_ativos.xlsx"

    df_mov = read_movimentacao_file(mov_fixture)
    df_pos = read_posicao_file(pos_fixture)

    assert "ativo_id" in df_mov.columns
    assert "ativo" in df_mov.columns
    assert "ativo_id" in df_pos.columns
    assert "ativo" in df_pos.columns

    assert all(isinstance(a, AtivoId) for a in df_mov["ativo_id"])
    assert all(isinstance(a, AtivoId) for a in df_pos["ativo_id"])
    assert all(isinstance(c, str) and len(c) > 0 for c in df_mov["ativo"])
    assert all(isinstance(c, str) and len(c) > 0 for c in df_pos["ativo"])


def test_classe_do_catalogo_coincide_com_aba_da_posicao():
    pos_dir = Path(__file__).resolve().parents[1] / "xlsx" / "posicao"
    snapshots = sorted(pos_dir.glob("*.xlsx"))
    assert len(snapshots) >= 4, f"Esperado pelo menos 4 snapshots de posição, encontrado {len(snapshots)}"

    for snap in snapshots:
        qualidade = RelatorioQualidade()
        df = read_posicao_file(snap, qualidade=qualidade)
        assert "ativo_id" in df.columns
        for _, row in df.iterrows():
            aid = row["ativo_id"]
            cat = row.get("categoria")
            assert aid.classe == cat, f"Divergência no arquivo {snap.name}: {row['produto']} tem classe {aid.classe} != aba {cat}"
        divergencias = [a for a in qualidade.avisos if a.tipo == "CLASSE_DIVERGENTE"]
        assert len(divergencias) == 0


def test_normalizar_nome_unifica_razao_social():
    assert normalizar_nome("CPFE3 - CPFL ENERGIA S/A") == normalizar_nome("CPFE3 - CPFL ENERGIA S.A.")
    assert normalizar_nome("PETR4 - PETROLEO BRASILEIRO S/A - PETROBRAS") == normalizar_nome(
        "PETR4 - PETROLEO BRASILEIRO S.A. PETROBRAS"
    )


def test_anotar_ativos_preenche_ativo_id_e_codigo():
    df = pd.DataFrame({"produto": ["PETR4", "ROXO34", "Tesouro Selic 2028"]})
    out = anotar_ativos(df)
    assert list(out["ativo"]) == ["PETR4", "ROXO34", "Tesouro Selic 2028"]
    assert all(isinstance(aid, AtivoId) for aid in out["ativo_id"])
    assert out.loc[0, "ativo_id"].classe == Classe.ACOES
    assert out.loc[1, "ativo_id"].classe == Classe.BDR
    assert out.loc[2, "ativo_id"].classe == Classe.TESOURO


def test_anotar_ativos_dataframe_vazio_ganha_colunas():
    vazio = pd.DataFrame(columns=["produto"])
    out = anotar_ativos(vazio)
    assert "ativo_id" in out.columns
    assert "ativo" in out.columns
    assert out.empty


def test_sem_ticker_nem_renomear_em_producao():
    root = Path(__file__).resolve().parents[1]
    padrao = re.compile(r"\b(ticker\(|renomear_ativo\()")
    arquivos = list((root / "dashboard").rglob("*.py")) + list((root / "scripts").glob("*.py"))
    ocorrencias = []
    for arq in arquivos:
        conteudo = arq.read_text(encoding="utf-8")
        for num, linha in enumerate(conteudo.splitlines(), start=1):
            if padrao.search(linha):
                ocorrencias.append(f"{arq.relative_to(root)}:{num}: {linha.strip()}")
    assert not ocorrencias, "Ocorrências proibidas de ticker( ou renomear_ativo( encontradas:\n" + "\n".join(ocorrencias)

