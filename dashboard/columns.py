try:
    from dashboard.aliases.common import build_lookup, normalize_alias
    from dashboard.aliases.movimentacao import ALIASES_MOV
except ImportError:  # pragma: no cover
    from aliases.common import build_lookup, normalize_alias
    from aliases.movimentacao import ALIASES_MOV


def normaliza_colunas(df, aliases=None):
    aliases = aliases or ALIASES_MOV
    lookup = build_lookup(aliases)
    renamed = {}
    for col in df.columns:
        key = normalize_alias(col)
        renamed[col] = lookup.get(key, key)
    return df.rename(columns=renamed)
