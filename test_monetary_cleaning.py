#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para validar la función clean_monetary_value
"""

import re
import pandas as pd
import numpy as np
from typing import Union

def clean_monetary_value(value: Union[str, float, int]) -> int:
    """Limpia valores monetarios removiendo caracteres no numéricos y preservando todos los dígitos"""
    if pd.isna(value) or value == '':
        return 0
    
    if isinstance(value, (int, float)):
        # Si ya es numérico, convertir a entero
        return int(value) if not pd.isna(value) and not np.isinf(value) else 0
    
    if isinstance(value, str):
        # Limpiar string: remover espacios, guiones y caracteres especiales excepto dígitos
        cleaned = str(value).strip()
        
        # Si es solo guiones o espacios, retornar 0
        if cleaned in ['-', ' ', '', '   ']:
            return 0
        
        # Remover todos los caracteres no numéricos excepto comas y puntos
        cleaned = re.sub(r'[^\d.,]', '', cleaned)
        
        # Si está vacío después de limpiar, retornar 0
        if not cleaned:
            return 0
        
        # Detectar si usa punto como separador de miles (formato: 123.456.789)
        # vs punto como decimal (formato: 123.45)
        if '.' in cleaned:
            parts = cleaned.split('.')
            # Si hay múltiples puntos O el último segmento tiene más de 2 dígitos,
            # entonces es separador de miles
            if len(parts) > 2 or (len(parts) == 2 and len(parts[-1]) > 2):
                # Es separador de miles, remover todos los puntos
                cleaned = cleaned.replace('.', '')
            else:
                # Es decimal, tomar solo la parte entera
                cleaned = parts[0]
        
        # Remover comas (separadores de miles)
        cleaned = cleaned.replace(',', '')
        
        try:
            return int(cleaned) if cleaned else 0
        except ValueError:
            return 0
    
    return 0

# Casos de prueba basados en los datos reales del CSV
test_cases = [
    " 224.436.000 ",
    " 290.296.000 ",
    " 185.268.000 ",
    " 140.000.000 ",
    " 25.000.000 ",
    " -   ",
    "-",
    " ",
    "",
    "123.45",  # decimal real
    "1.234.567.890",  # número grande con separadores de miles
    "500000",  # número sin separadores
]

print("Pruebas de la función clean_monetary_value:")
print("=" * 50)

for test in test_cases:
    result = clean_monetary_value(test)
    print(f"Entrada: '{test}' -> Salida: {result}")
