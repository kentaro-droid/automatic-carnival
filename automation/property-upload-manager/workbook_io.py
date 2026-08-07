from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET

from openpyxl import load_workbook
from openpyxl.utils.datetime import to_excel

MASTER_SHEET = '01_物件マスター'
HEADER_ROW = 4
DATA_START_ROW = 5


def load_master(path: str):
    # Read-only use of openpyxl. Direct openpyxl saving can remove the x14 list validations used by this workbook.
    wb = load_workbook(path, data_only=False, read_only=False)
    ws = wb[MASTER_SHEET]
    headers = {ws.cell(HEADER_ROW, c).value: c for c in range(1, ws.max_column + 1)}
    rows=[]
    for r in range(DATA_START_ROW, ws.max_row + 1):
        if ws.cell(r, headers['物件ID']).value in (None, ''):
            continue
        values={h: ws.cell(r,c).value for h,c in headers.items() if h}
        rows.append({'excel_row': r, **values})
    wb.close()
    return rows, headers


def _sheet_xml_path(xlsx_path: str, sheet_name: str) -> str:
    NS_MAIN='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    NS_REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    NS_PKG='http://schemas.openxmlformats.org/package/2006/relationships'
    with ZipFile(xlsx_path) as z:
        root=ET.fromstring(z.read('xl/workbook.xml'))
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        relmap={el.attrib['Id']:el.attrib['Target'] for el in rels.findall(f'{{{NS_PKG}}}Relationship')}
        for s in root.findall(f'.//{{{NS_MAIN}}}sheet'):
            if s.attrib.get('name') == sheet_name:
                rid=s.attrib[f'{{{NS_REL}}}id']; target=relmap[rid]
                return target.lstrip('/') if target.startswith('/') else 'xl/' + target
    raise KeyError(sheet_name)


def _cell_ref(row: int, col: int) -> str:
    from openpyxl.utils import get_column_letter
    return f'{get_column_letter(col)}{row}'


def _set_cell_value(root: ET.Element, ref: str, value):
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    sheet_data=root.find(f'{{{ns}}}sheetData')
    row_num=int(''.join(ch for ch in ref if ch.isdigit()))
    row_el=next((r for r in sheet_data.findall(f'{{{ns}}}row') if int(r.attrib['r']) == row_num), None)
    if row_el is None:
        row_el=ET.SubElement(sheet_data, f'{{{ns}}}row', {'r':str(row_num)})
    cell=next((c for c in row_el.findall(f'{{{ns}}}c') if c.attrib.get('r') == ref), None)
    if cell is None:
        cell=ET.SubElement(row_el, f'{{{ns}}}c', {'r':ref})
    for child in list(cell):
        if child.tag in {f'{{{ns}}}f',f'{{{ns}}}v',f'{{{ns}}}is'}:
            cell.remove(child)
    if value is None or value == '':
        cell.attrib.pop('t', None); return
    from datetime import date, datetime
    if isinstance(value, (datetime, date)):
        cell.attrib.pop('t', None); ET.SubElement(cell,f'{{{ns}}}v').text=str(to_excel(value))
    elif isinstance(value, (int,float)) and not isinstance(value,bool):
        cell.attrib.pop('t', None); ET.SubElement(cell,f'{{{ns}}}v').text=str(value)
    else:
        cell.attrib['t']='inlineStr'; isel=ET.SubElement(cell,f'{{{ns}}}is'); t=ET.SubElement(isel,f'{{{ns}}}t'); t.text=str(value)


def save_updates_preserving_validations(source_path: str, dest_path: str, updates: list[tuple[int,int,object]]):
    # Patch only cell values in sheet XML, preserving the workbook's x14 data-validation extensions.
    sheet_path=_sheet_xml_path(source_path, MASTER_SHEET)
    with ZipFile(source_path,'r') as zin:
        sheet_xml=ET.fromstring(zin.read(sheet_path))
        for row,col,value in updates:
            _set_cell_value(sheet_xml, _cell_ref(row,col), value)
        new_sheet=ET.tostring(sheet_xml, encoding='utf-8', xml_declaration=True)
        Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(dest_path,'w',ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                zout.writestr(item, new_sheet if item.filename == sheet_path else zin.read(item.filename))
