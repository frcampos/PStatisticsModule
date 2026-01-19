#!/usr/bin/env python3
"""
data_loader.py - Carregamento e Validação de Dados
Sistema de Análise Estatística DL 54/2018 v2.0

Responsável por:
- Carregar dados de Excel/CSV
- Validar estrutura e tipos
- Pré-processamento
- Limpeza de dados

Autor: Sistema de Qualidade de Dados Educacionais
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from config import ConfigManager
from utils import (
    validate_columns, log_dataframe_info,
    get_missing_value_report, get_data_summary
)

logger = logging.getLogger('DL54.data_loader')


class DataLoadError(Exception):
    """Exceção para erros no carregamento de dados"""
    pass


class DataLoader:
    """
    Carregador e validador de dados educacionais.

    Responsabilidades:
    - Carregar dados de múltiplos formatos
    - Validar estrutura e tipos
    - Limpeza e pré-processamento
    - Geração de relatórios de qualidade
    """

    def __init__(self, config: ConfigManager, logger_instance: logging.Logger):
        """
        Inicializa o carregador de dados.

        Args:
            config: Gestor de configuração
            logger_instance: Logger para registos
        """
        self.config = config
        self.logger = logger_instance
        self.df: Optional[pd.DataFrame] = None
        self.validation_report: Dict = {}

    def load_data(self) -> pd.DataFrame:
        """
        Carrega dados do ficheiro especificado na configuração.

        Returns:
            DataFrame com os dados carregados

        Raises:
            DataLoadError: Se houver erro no carregamento
        """
        input_file = self.config.get('IO', 'INPUT_FILE')
        file_path = Path(input_file)

        if not file_path.exists():
            raise DataLoadError(f"Ficheiro não encontrado: {input_file}")

        self.logger.info(f"Carregando dados de: {input_file}")

        try:
            # Determinar formato pelo sufixo
            suffix = file_path.suffix.lower()

            if suffix == '.csv':
                df = self._load_csv(file_path)
            elif suffix in ['.xlsx', '.xls']:
                df = self._load_excel(file_path)
            else:
                raise DataLoadError(f"Formato não suportado: {suffix}")

            self.logger.info(
                f"✓ Dados carregados: {len(df)} registos, {len(df.columns)} colunas"
            )

            self.df = df
            return df

        except Exception as e:
            raise DataLoadError(f"Erro ao carregar dados: {e}")

    def _load_csv(self, file_path: Path) -> pd.DataFrame:
        """Carrega dados de ficheiro CSV"""
        encoding = self.config.get('IO', 'INPUT_ENCODING', 'utf-8')
        delimiter = self.config.get('IO', 'CSV_DELIMITER', ',')

        try:
            df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
        except UnicodeDecodeError:
            self.logger.warning("Falha UTF-8, tentando UTF-16...")
            df = pd.read_csv(file_path, encoding='utf-16', delimiter=delimiter)

        return df

    def _load_excel(self, file_path: Path) -> pd.DataFrame:
        """Carrega dados de ficheiro Excel"""
        df = pd.read_excel(file_path)
        return df

    def validate_structure(self, df: Optional[pd.DataFrame] = None) -> bool:
        """
        Valida estrutura básica do DataFrame.

        Args:
            df: DataFrame a validar (usa self.df se None)

        Returns:
            True se válido

        Raises:
            DataLoadError: Se validação falhar
        """
        if df is None:
            df = self.df

        if df is None:
            raise DataLoadError("Nenhum dado carregado")

        self.logger.info("Validando estrutura dos dados...")

        # Verificar se não está vazio
        if len(df) == 0:
            raise DataLoadError("Dataset vazio")

        # Obter colunas requeridas
        required_cols = self._get_required_columns()

        # Validar colunas
        is_valid, missing = validate_columns(df, required_cols)

        if not is_valid:
            if self.config.getboolean('VALIDACAO', 'STRICT_VALIDATION', False):
                raise DataLoadError(
                    f"Colunas obrigatórias em falta: {', '.join(missing)}"
                )
            else:
                self.logger.warning(
                    f"Colunas em falta (continuando): {', '.join(missing)}"
                )
                self.validation_report['missing_columns'] = missing

        self.logger.info("✓ Estrutura validada")
        return True

    def _get_required_columns(self) -> List[str]:
        """Retorna lista de colunas obrigatórias"""
        cfg = self.config.config['COLUNAS_DL54']

        required = [
            cfg['COLUNA_ESCOLA'],
            cfg['MEDIDAS_UNIVERSAIS'],
            cfg['MEDIDAS_SELETIVAS'],
            cfg['MEDIDAS_ADICIONAIS']
        ]

        return [col for col in required if col]

    def validate_types(self, df: Optional[pd.DataFrame] = None) -> bool:
        """
        Valida tipos de dados das colunas.

        Args:
            df: DataFrame a validar

        Returns:
            True se válido
        """
        if df is None:
            df = self.df

        if not self.config.getboolean('VALIDACAO', 'VALIDATE_DATA_TYPES', True):
            return True

        self.logger.info("Validando tipos de dados...")

        cfg = self.config.config['COLUNAS_DL54']
        type_issues = []

        # Validar colunas binárias (0/1)
        binary_cols = [
            cfg['MEDIDAS_UNIVERSAIS'],
            cfg['MEDIDAS_SELETIVAS'],
            cfg['MEDIDAS_ADICIONAIS']
        ]

        for col in binary_cols:
            if col in df.columns:
                unique_vals = df[col].dropna().unique()
                if not all(v in [0, 1, 0.0, 1.0] for v in unique_vals):
                    type_issues.append(f"{col}: esperado binário (0/1)")

        if type_issues:
            self.logger.warning(f"Problemas de tipos: {', '.join(type_issues)}")
            self.validation_report['type_issues'] = type_issues
        else:
            self.logger.info("✓ Tipos de dados validados")

        return True

    def clean_data(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Limpa e prepara dados para análise.

        Args:
            df: DataFrame a limpar

        Returns:
            DataFrame limpo
        """
        if df is None:
            df = self.df.copy()
        else:
            df = df.copy()

        self.logger.info("Limpando dados...")

        # Remover duplicados
        initial_count = len(df)
        df = df.drop_duplicates()
        duplicates_removed = initial_count - len(df)

        if duplicates_removed > 0:
            self.logger.info(f"Removidos {duplicates_removed} registos duplicados")
            self.validation_report['duplicates_removed'] = duplicates_removed

        # Tratamento de valores em falta
        if self.config.getboolean('VALIDACAO', 'HANDLE_MISSING_VALUES', True):
            df = self._handle_missing_values(df)

        # Converter tipos
        df = self._convert_types(df)

        self.logger.info("✓ Dados limpos")
        self.df = df
        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Trata valores em falta"""
        strategy = self.config.get('VALIDACAO', 'MISSING_VALUE_STRATEGY', 'skip')

        missing_report = get_missing_value_report(df)

        if len(missing_report) > 0:
            self.logger.info(
                f"Valores em falta encontrados em {len(missing_report)} colunas"
            )
            self.validation_report['missing_values'] = missing_report.to_dict('records')

            if strategy == 'fill_zero':
                # Preencher colunas numéricas com 0
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                df[numeric_cols] = df[numeric_cols].fillna(0)
                self.logger.info("Valores em falta preenchidos com 0")
            elif strategy == 'skip':
                self.logger.info("Valores em falta mantidos (skip)")

        return df

    def _convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converte tipos de dados apropriadamente"""
        cfg = self.config.config['COLUNAS_DL54']

        # Converter colunas binárias para int
        binary_cols = [
            cfg['MEDIDAS_UNIVERSAIS'],
            cfg['MEDIDAS_SELETIVAS'],
            cfg['MEDIDAS_ADICIONAIS']
        ]

        # Adicionar medidas específicas
        for prefix in ['MU_', 'MS_', 'MA_', 'ART28_']:
            binary_cols.extend([
                v for k, v in cfg.items()
                if k.startswith(prefix) and v in df.columns
            ])

        for col in binary_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # Converter coluna de escola para int
        escola_col = cfg['COLUNA_ESCOLA']
        if escola_col in df.columns:
            df[escola_col] = pd.to_numeric(df[escola_col], errors='coerce').astype('Int64')

        # Converter coluna de ano para int
        ano_col = cfg['COLUNA_ANO']
        if ano_col in df.columns:
            df[ano_col] = pd.to_numeric(df[ano_col], errors='coerce').astype('Int64')

        return df

    def generate_quality_report(self, df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Gera relatório de qualidade dos dados.

        Args:
            df: DataFrame para análise

        Returns:
            Dicionário com relatório de qualidade
        """
        if df is None:
            df = self.df

        self.logger.info("Gerando relatório de qualidade...")

        report = {
            'timestamp': datetime.now().isoformat(),
            'file_info': {
                'rows': len(df),
                'columns': len(df.columns),
                'memory_mb': round(df.memory_usage(deep=True).sum() / (1024 ** 2), 2)
            },
            'data_summary': get_data_summary(df),
            'validation_issues': self.validation_report,
            'column_info': {}
        }

        # Informação por coluna
        for col in df.columns:
            report['column_info'][col] = {
                'dtype': str(df[col].dtype),
                'null_count': int(df[col].isnull().sum()),
                'null_pct': round(df[col].isnull().sum() / len(df) * 100, 2),
                'unique_values': int(df[col].nunique())
            }

        self.logger.info("✓ Relatório de qualidade gerado")
        return report

    def get_column_info(self, column_name: str, df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Obtém informação detalhada sobre uma coluna.

        Args:
            column_name: Nome da coluna
            df: DataFrame

        Returns:
            Dicionário com informação
        """
        if df is None:
            df = self.df

        if column_name not in df.columns:
            return {'error': f'Coluna {column_name} não encontrada'}

        col_data = df[column_name]

        info = {
            'name': column_name,
            'dtype': str(col_data.dtype),
            'count': int(col_data.count()),
            'null_count': int(col_data.isnull().sum()),
            'null_pct': round(col_data.isnull().sum() / len(df) * 100, 2),
            'unique_values': int(col_data.nunique())
        }

        # Estatísticas para colunas numéricas
        if pd.api.types.is_numeric_dtype(col_data):
            info.update({
                'mean': float(col_data.mean()),
                'std': float(col_data.std()),
                'min': float(col_data.min()),
                'max': float(col_data.max()),
                'median': float(col_data.median())
            })

        # Top valores para colunas categóricas
        if col_data.nunique() < 20:
            info['value_counts'] = col_data.value_counts().to_dict()

        return info

    def filter_by_escola(self, codigo_escola: int,
                         df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Filtra dados por escola.

        Args:
            codigo_escola: Código da escola
            df: DataFrame

        Returns:
            DataFrame filtrado
        """
        if df is None:
            df = self.df

        escola_col = self.config.get('COLUNAS_DL54', 'COLUNA_ESCOLA')

        if escola_col not in df.columns:
            self.logger.warning(f"Coluna {escola_col} não encontrada")
            return df

        filtered = df[df[escola_col] == codigo_escola].copy()

        self.logger.debug(
            f"Filtrado por escola {codigo_escola}: {len(filtered)} registos"
        )

        return filtered

    def filter_by_ano(self, ano: int,
                      df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Filtra dados por ano de escolaridade.

        Args:
            ano: Ano de escolaridade
            df: DataFrame

        Returns:
            DataFrame filtrado
        """
        if df is None:
            df = self.df

        ano_col = self.config.get('COLUNAS_DL54', 'COLUNA_ANO')

        if ano_col not in df.columns:
            self.logger.warning(f"Coluna {ano_col} não encontrada")
            return df

        filtered = df[df[ano_col] == ano].copy()

        self.logger.debug(
            f"Filtrado por ano {ano}: {len(filtered)} registos"
        )

        return filtered

    def get_unique_values(self, column_name: str,
                          df: Optional[pd.DataFrame] = None) -> List:
        """
        Obtém valores únicos de uma coluna.

        Args:
            column_name: Nome da coluna
            df: DataFrame

        Returns:
            Lista de valores únicos ordenados
        """
        if df is None:
            df = self.df

        if column_name not in df.columns:
            return []

        unique_vals = sorted(df[column_name].dropna().unique())
        return unique_vals

    def load_and_validate(self) -> pd.DataFrame:
        """
        Pipeline completo: carrega, valida e limpa dados.

        Returns:
            DataFrame pronto para análise

        Raises:
            DataLoadError: Se houver erro no processo
        """
        self.logger.info("=" * 80)
        self.logger.info("CARREGAMENTO E VALIDAÇÃO DE DADOS")
        self.logger.info("=" * 80)

        # 1. Carregar
        df = self.load_data()
        log_dataframe_info(df, "Dataset Original")

        # 2. Validar estrutura
        self.validate_structure(df)

        # 3. Validar tipos
        self.validate_types(df)

        # 4. Limpar
        df = self.clean_data(df)
        log_dataframe_info(df, "Dataset Limpo")

        # 5. Relatório de qualidade
        quality_report = self.generate_quality_report(df)

        self.logger.info("=" * 80)
        self.logger.info("✓ DADOS PRONTOS PARA ANÁLISE")
        self.logger.info(f"  Total: {len(df)} registos, {len(df.columns)} colunas")
        self.logger.info("=" * 80)

        return df

    def export_quality_report(self, output_path: Path):
        """
        Exporta relatório de qualidade para JSON.

        Args:
            output_path: Caminho do ficheiro de saída
        """
        import json

        report = self.generate_quality_report()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        self.logger.info(f"Relatório de qualidade exportado: {output_path}")

    def __repr__(self) -> str:
        """Representação string"""
        if self.df is not None:
            return f"DataLoader(loaded={len(self.df)} registos)"
        return "DataLoader(no data loaded)"