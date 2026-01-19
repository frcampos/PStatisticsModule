#!/usr/bin/env python3
"""
utils.py - Utilitários Gerais
Sistema de Análise Estatística DL 54/2018 v2.0

Funções auxiliares e utilitários reutilizáveis em todo o sistema.

Autor: Sistema de Qualidade de Dados Educacionais
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger('DL54.utils')


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Formata valor como percentagem.

    Args:
        value: Valor numérico (0-100)
        decimals: Número de casas decimais

    Returns:
        String formatada com %
    """
    return f"{value:.{decimals}f}%"


def format_number(value: int) -> str:
    """
    Formata número com separador de milhares.

    Args:
        value: Valor inteiro

    Returns:
        String formatada
    """
    return f"{value:,}".replace(',', '.')


def safe_divide(numerator: float, denominator: float,
                default: float = 0.0) -> float:
    """
    Divisão segura com tratamento de divisão por zero.

    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor padrão se denominador for zero

    Returns:
        Resultado da divisão ou valor padrão
    """
    if denominator == 0:
        return default
    return numerator / denominator


def calculate_percentage(part: int, total: int, decimals: int = 2) -> float:
    """
    Calcula percentagem com tratamento de divisão por zero.

    Args:
        part: Parte
        total: Total
        decimals: Casas decimais

    Returns:
        Percentagem (0-100)
    """
    if total == 0:
        return 0.0
    return round((part / total) * 100, decimals)


def create_timestamp(format: str = "%Y%m%d_%H%M%S") -> str:
    """
    Cria timestamp formatado.

    Args:
        format: Formato do timestamp

    Returns:
        String com timestamp
    """
    return datetime.now().strftime(format)


def ensure_directory(path: Path) -> Path:
    """
    Garante que diretório existe, criando se necessário.

    Args:
        path: Caminho do diretório

    Returns:
        Path do diretório
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_filename(filename: str) -> str:
    """
    Limpa nome de ficheiro removendo caracteres inválidos.

    Args:
        filename: Nome original

    Returns:
        Nome limpo
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def truncate_string(text: str, max_length: int = 50,
                    suffix: str = '...') -> str:
    """
    Trunca string se exceder tamanho máximo.

    Args:
        text: Texto original
        max_length: Tamanho máximo
        suffix: Sufixo para texto truncado

    Returns:
        Texto truncado se necessário
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Gera resumo estatístico de um DataFrame.

    Args:
        df: DataFrame

    Returns:
        Dicionário com estatísticas
    """
    return {
        'rows': len(df),
        'columns': len(df.columns),
        'memory_mb': df.memory_usage(deep=True).sum() / (1024 ** 2),
        'missing_values': df.isnull().sum().sum(),
        'dtypes': df.dtypes.value_counts().to_dict()
    }


def validate_columns(df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Valida se DataFrame contém colunas necessárias.

    Args:
        df: DataFrame a validar
        required_columns: Lista de colunas obrigatórias

    Returns:
        Tupla (válido, colunas_em_falta)
    """
    missing = [col for col in required_columns if col not in df.columns]
    return (len(missing) == 0, missing)


def filter_numeric_columns(df: pd.DataFrame) -> List[str]:
    """
    Filtra colunas numéricas de um DataFrame.

    Args:
        df: DataFrame

    Returns:
        Lista de nomes de colunas numéricas
    """
    return df.select_dtypes(include=[np.number]).columns.tolist()


def filter_categorical_columns(df: pd.DataFrame) -> List[str]:
    """
    Filtra colunas categóricas de um DataFrame.

    Args:
        df: DataFrame

    Returns:
        Lista de nomes de colunas categóricas
    """
    return df.select_dtypes(include=['object', 'category']).columns.tolist()


def get_value_counts_dict(series: pd.Series) -> Dict[Any, int]:
    """
    Converte value_counts para dicionário ordenado.

    Args:
        series: Série pandas

    Returns:
        Dicionário {valor: contagem}
    """
    return series.value_counts().to_dict()


def calculate_mode(series: pd.Series) -> Any:
    """
    Calcula moda com tratamento de multimodal.

    Args:
        series: Série pandas

    Returns:
        Moda ou primeira moda se multimodal
    """
    mode_series = series.mode()
    return mode_series[0] if len(mode_series) > 0 else None


def calculate_quartiles(series: pd.Series) -> Dict[str, float]:
    """
    Calcula quartis de uma série.

    Args:
        series: Série numérica

    Returns:
        Dicionário com quartis
    """
    return {
        'Q1': series.quantile(0.25),
        'Q2': series.quantile(0.50),  # Mediana
        'Q3': series.quantile(0.75),
        'IQR': series.quantile(0.75) - series.quantile(0.25)
    }


def detect_outliers_iqr(series: pd.Series, multiplier: float = 1.5) -> pd.Series:
    """
    Detecta outliers usando método IQR.

    Args:
        series: Série numérica
        multiplier: Multiplicador do IQR (1.5 padrão, 3 extremo)

    Returns:
        Série booleana indicando outliers
    """
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - (multiplier * IQR)
    upper_bound = Q3 + (multiplier * IQR)

    return (series < lower_bound) | (series > upper_bound)


def normalize_series(series: pd.Series, method: str = 'minmax') -> pd.Series:
    """
    Normaliza série numérica.

    Args:
        series: Série numérica
        method: Método ('minmax' ou 'zscore')

    Returns:
        Série normalizada
    """
    if method == 'minmax':
        return (series - series.min()) / (series.max() - series.min())
    elif method == 'zscore':
        return (series - series.mean()) / series.std()
    else:
        raise ValueError(f"Método desconhecido: {method}")


def group_by_bins(series: pd.Series, bins: List[float],
                  labels: Optional[List[str]] = None) -> pd.Series:
    """
    Agrupa valores contínuos em bins.

    Args:
        series: Série numérica
        bins: Lista de limites dos bins
        labels: Labels para os bins

    Returns:
        Série categórica
    """
    return pd.cut(series, bins=bins, labels=labels, include_lowest=True)


def calculate_concentration_index(series: pd.Series) -> float:
    """
    Calcula índice de concentração (similar ao Gini).

    Args:
        series: Série numérica não-negativa

    Returns:
        Índice de concentração (0-1)
    """
    # Ordenar valores
    sorted_values = np.sort(series.dropna().values)
    n = len(sorted_values)

    if n == 0:
        return 0.0

    # Calcular índice
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * sorted_values)) / (n * np.sum(sorted_values)) - (n + 1) / n


def create_crosstab_percentage(df: pd.DataFrame, index_col: str,
                               columns_col: str, normalize: str = 'index') -> pd.DataFrame:
    """
    Cria crosstab com percentagens.

    Args:
        df: DataFrame
        index_col: Coluna para índice
        columns_col: Coluna para colunas
        normalize: Como normalizar ('index', 'columns', 'all')

    Returns:
        DataFrame com crosstab percentual
    """
    ct = pd.crosstab(df[index_col], df[columns_col], normalize=normalize)
    return ct * 100  # Converter para percentagem


def rank_values(series: pd.Series, ascending: bool = False) -> pd.Series:
    """
    Cria ranking de valores.

    Args:
        series: Série a rankear
        ascending: Se True, menor valor tem rank 1

    Returns:
        Série com rankings
    """
    return series.rank(ascending=ascending, method='dense').astype(int)


def format_table_data(data: Dict[str, Any], decimals: int = 2) -> Dict[str, str]:
    """
    Formata dados para exibição em tabela.

    Args:
        data: Dicionário com dados
        decimals: Casas decimais para números

    Returns:
        Dicionário com valores formatados
    """
    formatted = {}

    for key, value in data.items():
        if isinstance(value, float):
            formatted[key] = f"{value:.{decimals}f}"
        elif isinstance(value, int):
            formatted[key] = format_number(value)
        else:
            formatted[key] = str(value)

    return formatted


def create_comparison_table(data1: Dict[str, Any], data2: Dict[str, Any],
                            labels: Tuple[str, str] = ('Grupo 1', 'Grupo 2')) -> pd.DataFrame:
    """
    Cria tabela de comparação entre dois conjuntos de dados.

    Args:
        data1: Dados do primeiro grupo
        data2: Dados do segundo grupo
        labels: Labels para os grupos

    Returns:
        DataFrame com comparação
    """
    df = pd.DataFrame({
        labels[0]: pd.Series(data1),
        labels[1]: pd.Series(data2)
    })

    # Adicionar coluna de diferença
    if df[labels[0]].dtype in [np.int64, np.float64] and \
            df[labels[1]].dtype in [np.int64, np.float64]:
        df['Diferença'] = df[labels[1]] - df[labels[0]]
        df['Diferença %'] = calculate_percentage(
            df[labels[1]], df[labels[0]]
        ) - 100

    return df


def log_dataframe_info(df: pd.DataFrame, name: str = "DataFrame"):
    """
    Loga informações sobre DataFrame.

    Args:
        df: DataFrame
        name: Nome do DataFrame
    """
    logger.info(f"{name}: {len(df)} linhas, {len(df.columns)} colunas")
    logger.debug(f"{name} - Colunas: {', '.join(df.columns.tolist())}")
    logger.debug(f"{name} - Memória: {df.memory_usage(deep=True).sum() / (1024 ** 2):.2f} MB")


def get_missing_value_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Gera relatório de valores em falta.

    Args:
        df: DataFrame

    Returns:
        DataFrame com estatísticas de valores em falta
    """
    missing = df.isnull().sum()
    missing = missing[missing > 0]

    if len(missing) == 0:
        return pd.DataFrame()

    missing_df = pd.DataFrame({
        'Coluna': missing.index,
        'Valores em Falta': missing.values,
        'Percentagem': (missing.values / len(df) * 100).round(2)
    })

    return missing_df.sort_values('Valores em Falta', ascending=False)


def aggregate_by_group(df: pd.DataFrame, group_col: str,
                       agg_cols: List[str], agg_func: str = 'sum') -> pd.DataFrame:
    """
    Agrega dados por grupo.

    Args:
        df: DataFrame
        group_col: Coluna para agrupar
        agg_cols: Colunas a agregar
        agg_func: Função de agregação

    Returns:
        DataFrame agregado
    """
    return df.groupby(group_col)[agg_cols].agg(agg_func).reset_index()


def calculate_growth_rate(old_value: float, new_value: float) -> float:
    """
    Calcula taxa de crescimento.

    Args:
        old_value: Valor anterior
        new_value: Valor novo

    Returns:
        Taxa de crescimento em percentagem
    """
    if old_value == 0:
        return 0.0 if new_value == 0 else 100.0
    return ((new_value - old_value) / old_value) * 100


def export_to_json(data: Dict[str, Any], filepath: Path):
    """
    Exporta dados para JSON.

    Args:
        data: Dados a exportar
        filepath: Caminho do ficheiro
    """
    import json

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Dados exportados para JSON: {filepath}")


def export_to_csv(df: pd.DataFrame, filepath: Path, **kwargs):
    """
    Exporta DataFrame para CSV.

    Args:
        df: DataFrame
        filepath: Caminho do ficheiro
        **kwargs: Argumentos para to_csv
    """
    default_kwargs = {
        'index': False,
        'encoding': 'utf-8-sig',
        'sep': ';'
    }
    default_kwargs.update(kwargs)

    df.to_csv(filepath, **default_kwargs)
    logger.info(f"Dados exportados para CSV: {filepath}")


class ProgressTracker:
    """Rastreador de progresso para operações longas"""

    def __init__(self, total: int, description: str = "Progresso"):
        self.total = total
        self.current = 0
        self.description = description
        self.logger = logging.getLogger('DL54.progress')

    def update(self, increment: int = 1):
        """Atualiza progresso"""
        self.current += increment
        percentage = (self.current / self.total) * 100

        if self.current % max(1, self.total // 10) == 0 or self.current == self.total:
            self.logger.info(
                f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%)"
            )

    def reset(self):
        """Reset do progresso"""
        self.current = 0


def create_summary_dict(series: pd.Series, include_outliers: bool = False) -> Dict[str, Any]:
    """
    Cria dicionário com resumo estatístico completo.

    Args:
        series: Série numérica
        include_outliers: Incluir detecção de outliers

    Returns:
        Dicionário com estatísticas
    """
    summary = {
        'count': int(series.count()),
        'mean': float(series.mean()),
        'std': float(series.std()),
        'min': float(series.min()),
        'max': float(series.max()),
        'median': float(series.median()),
        'mode': calculate_mode(series)
    }

    # Adicionar quartis
    summary.update(calculate_quartiles(series))

    # Adicionar outliers se solicitado
    if include_outliers:
        outliers = detect_outliers_iqr(series)
        summary['outliers_count'] = int(outliers.sum())
        summary['outliers_pct'] = calculate_percentage(outliers.sum(), len(series))

    return summary