#!/usr/bin/env python3
"""Tier-2 aging: Mexico admin-1 65+ % from INEGI Census 2020 tabulado (population by entidad x 5-year age
group). Per entidad: sum 65+ groups / Total (2020 column) -> 65+ %. Maps entidad name -> ISO-3166-2:MX.
Writes public/data/aging/mx-admin1.json."""
import json
import os
import unicodedata
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'public', 'data'))
SRC = os.path.join(HERE, '_data_in', 'mx', 'Poblacion_01.xlsx')

OLD = {'65 a 69 años', '70 a 74 años', '75 a 79 años', '80 a 84 años',
       '85 a 89 años', '90 a 94 años', '95 a 99 años', '100 años y más'}
COL_2020_TOTAL = 8   # header: cols 2-4=2005, 5-7=2010, 8-10=2020 (Total/H/M)

def norm(s):
    s = unicodedata.normalize('NFD', str(s)).encode('ascii', 'ignore').decode().lower()
    return ''.join(c for c in s if c.isalnum())

ISO = {norm(k): v for k, v in {
    'Aguascalientes': 'MX-AGU', 'Baja California': 'MX-BCN', 'Baja California Sur': 'MX-BCS',
    'Campeche': 'MX-CAM', 'Coahuila de Zaragoza': 'MX-COA', 'Colima': 'MX-COL', 'Chiapas': 'MX-CHP',
    'Chihuahua': 'MX-CHH', 'Ciudad de México': 'MX-DIF', 'Durango': 'MX-DUR', 'Guanajuato': 'MX-GUA',
    'Guerrero': 'MX-GRO', 'Hidalgo': 'MX-HID', 'Jalisco': 'MX-JAL', 'México': 'MX-MEX',
    'Michoacán de Ocampo': 'MX-MIC', 'Morelos': 'MX-MOR', 'Nayarit': 'MX-NAY', 'Nuevo León': 'MX-NLE',
    'Oaxaca': 'MX-OAX', 'Puebla': 'MX-PUE', 'Querétaro': 'MX-QUE', 'Quintana Roo': 'MX-ROO',
    'San Luis Potosí': 'MX-SLP', 'Sinaloa': 'MX-SIN', 'Sonora': 'MX-SON', 'Tabasco': 'MX-TAB',
    'Tamaulipas': 'MX-TAM', 'Tlaxcala': 'MX-TLA', 'Veracruz de Ignacio de la Llave': 'MX-VER',
    'Yucatán': 'MX-YUC', 'Zacatecas': 'MX-ZAC',
}.items()}

ws = openpyxl.load_workbook(SRC, read_only=True, data_only=True)['Tabulado']
tot, o65 = {}, {}
for row in ws.iter_rows(values_only=True):
    ent, age = row[0], row[1]
    if not ent or not age or ent == 'Entidad federativa' or norm(ent) == 'estadosunidosmexicanos':
        continue
    val = row[COL_2020_TOTAL]
    if not isinstance(val, (int, float)):
        continue
    if age == 'Total':
        tot[ent] = val
    elif age in OLD:
        o65[ent] = o65.get(ent, 0) + val

by_unit, miss = {}, []
for ent, t in tot.items():
    iso = ISO.get(norm(ent))
    if not iso:
        miss.append(ent); continue
    if t:
        by_unit[iso] = round(100 * o65.get(ent, 0) / t, 1)

vals = list(by_unit.values())
nat = round(sum(vals) / len(vals), 1)
os.makedirs(os.path.join(OUT, 'aging'), exist_ok=True)
json.dump({'meta': {'metric': 'share of population aged 65+ (%)', 'age_group': '65+', 'year': 2020,
                    'source': 'INEGI Censo 2020 (población por entidad y edad)', 'resolution': 'admin-1',
                    'method': 'sum 65+ 5-year groups / total per entidad (2020); name -> ISO-3166-2:MX',
                    'national_pct_unweighted': nat},
           'byUnit': by_unit},
          open(os.path.join(OUT, 'aging', 'mx-admin1.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(f'mx: {len(by_unit)} entidades, range {min(vals)}-{max(vals)}%, nat {nat}' + (f' | MISS {miss}' if miss else ''))
