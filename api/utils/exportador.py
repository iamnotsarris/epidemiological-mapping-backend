"""
Exportadores de dados dos modelos epidemiológicos.
Suporta: CSV, XLSX (Excel) e DBF (compatível com SINAN/legado).
"""
import csv
import io
import os
import tempfile
from datetime import date, datetime

FORMATOS_SUPORTADOS = ("csv", "xlsx", "dbf")

MIMETYPES = {
    "csv":  "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "dbf":  "application/x-dbf",
}


def _campos_concretos(modelo):
    """Lista (nome, field) apenas de campos concretos (colunas reais do banco)."""
    campos = []
    for f in modelo._meta.get_fields():
        if not getattr(f, "concrete", False):
            continue
        if not hasattr(f, "column"):
            continue
        campos.append((f.name, f))
    return campos


def _to_str(v):
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):
        return v.strftime("%Y-%m-%d")
    return str(v)


def exportar_csv(queryset, modelo):
    campos = [n for n, _ in _campos_concretos(modelo)]
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(campos)
    for obj in queryset.iterator():
        writer.writerow([_to_str(getattr(obj, c, "")) for c in campos])
    # BOM (\ufeff) → Excel abre com acentuação correta em pt-BR
    return buf.getvalue().encode("utf-8-sig")


def exportar_xlsx(queryset, modelo):
    try:
        from openpyxl import Workbook
    except ImportError as e:
        raise ImportError("Instale openpyxl: pip install openpyxl") from e

    campos = [n for n, _ in _campos_concretos(modelo)]
    wb = Workbook()
    ws = wb.active
    ws.title = modelo.__name__[:31]  # limite de 31 chars do Excel
    ws.append(campos)
    for obj in queryset.iterator():
        ws.append([_to_str(getattr(obj, c, "")) for c in campos])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _nome_dbf(nome, usados):
    """DBF clássico: máx 10 chars, ASCII, sem duplicatas."""
    base = "".join(c for c in nome.upper() if c.isalnum() or c == "_")[:10] or "COL"
    nome_final = base
    i = 1
    while nome_final in usados:
        sufixo = str(i)
        nome_final = base[: 10 - len(sufixo)] + sufixo
        i += 1
    usados.add(nome_final)
    return nome_final


def exportar_dbf(queryset, modelo):
    try:
        import dbf
    except ImportError as e:
        raise ImportError("Instale a lib dbf: pip install dbf") from e

    campos = _campos_concretos(modelo)
    usados = set()
    partes = []
    meta = []

    for nome, field in campos:
        nome_dbf = _nome_dbf(nome, usados)
        tipo = field.__class__.__name__

        if "DateTime" in tipo or "Date" in tipo:
            spec, cast = "D", "date"
        elif "Integer" in tipo or "AutoField" in tipo:
            spec, cast = "N(18,0)", "int"
        elif "Float" in tipo or "Decimal" in tipo:
            spec, cast = "N(18,6)", "float"
        elif "Boolean" in tipo:
            spec, cast = "L", "bool"
        else:
            spec, cast = "C(254)", "str"

        partes.append(f"{nome_dbf} {spec}")
        meta.append((nome, cast))

    schema = "; ".join(partes)

    tmp_dir = tempfile.mkdtemp()
    caminho = os.path.join(tmp_dir, "export.dbf")

    try:
        tabela = dbf.Table(caminho, schema, codepage="cp1252")
        tabela.open(dbf.READ_WRITE)

        for obj in queryset.iterator():
            linha = []
            for nome, cast in meta:
                v = getattr(obj, nome, None)

                if v is None:
                    if cast == "date":
                        linha.append(None)
                    elif cast == "int":
                        linha.append(0)
                    elif cast == "float":
                        linha.append(0.0)
                    elif cast == "bool":
                        linha.append(False)
                    else:
                        linha.append("")
                    continue

                if cast == "date":
                    if isinstance(v, datetime):
                        v = v.date()
                    linha.append(v)
                elif cast == "int":
                    linha.append(int(v))
                elif cast == "float":
                    linha.append(float(v))
                elif cast == "bool":
                    linha.append(bool(v))
                else:
                    linha.append(_to_str(v)[:254])

            tabela.append(tuple(linha))

        tabela.close()

        with open(caminho, "rb") as f:
            return f.read()
    finally:
        # Sempre limpa o temp
        try:
            for arq in os.listdir(tmp_dir):
                os.remove(os.path.join(tmp_dir, arq))
            os.rmdir(tmp_dir)
        except OSError:
            pass


def exportar(queryset, modelo, formato):
    """Retorna (bytes, mimetype, extensão). Levanta ValueError se formato inválido."""
    formato = (formato or "csv").lower()
    if formato not in FORMATOS_SUPORTADOS:
        raise ValueError(
            f"Formato '{formato}' não suportado. "
            f"Use um destes: {', '.join(FORMATOS_SUPORTADOS)}"
        )

    if formato == "csv":
        conteudo = exportar_csv(queryset, modelo)
    elif formato == "xlsx":
        conteudo = exportar_xlsx(queryset, modelo)
    else:
        conteudo = exportar_dbf(queryset, modelo)

    return conteudo, MIMETYPES[formato], formato