"""
ip26_excel_to_csv.py
====================
Step 6 (run last): converts every Excel workbook in the final output folder (output_final and its
scenario subfolders, made by ip26_final_network.py) to CSV files in output_final_csv/, one CSV per tab.
Formula cells are written as their calculated scalar value. The folders are set in config_excel_to_csv.yaml;
the converter works on any folder of workbooks. Excel lock files (~$...xlsx) are skipped.

The module also provides the formula evaluator (class Workbook) that ip26_final_network.py uses to read
the horizon workbooks of step 3.

Why a formula evaluator: workbooks written by openpyxl, which stores formulas but no
results. A plain read (pandas / openpyxl data_only=True) then gives empty cells for every formula
unless the file was opened and saved in Excel or LibreOffice first. This script therefore computes
the formulas itself (engine "evaluate"), and can fall back to the stored results or to a LibreOffice
recalculation (engine "auto"). The formulas used in the IP26 workbooks are arithmetic (+ - * / ^),
SQRT and cell references within the tab or to the Parameters tab; a few more common functions are
supported as well (ABS, MIN, MAX, SUM, AVERAGE, ROUND, IF, AND, OR, PI, POWER, EXP, LN).

Usage:
    python ip26_excel_to_csv.py                         # uses config_excel_to_csv.yaml
    python ip26_excel_to_csv.py my_config.yaml
"""
import csv
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import openpyxl
import yaml
from openpyxl.utils import column_index_from_string, get_column_letter

CONFIG_FILE = "config_excel_to_csv.yaml"


# --------------------------------------------------------------------------- formula evaluator
class Unsupported(Exception):
    """Formula syntax or function the evaluator does not handle."""


class ExcelError(str):
    """Excel error value such as #DIV/0! (written to the CSV as text)."""


TOKEN = re.compile(r"""
    (?P<ws>\s+)
  | (?P<num>\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)
  | (?P<str>"(?:[^"]|"")*")
  | (?P<ref>(?:(?:'(?:[^']|'')+'|[A-Za-z_][\w\.]*)!)?\$?[A-Za-z]{1,3}\$?\d+(?::\$?[A-Za-z]{1,3}\$?\d+)?)
  | (?P<func>[A-Za-z_][\w\.]*(?=\())
  | (?P<bool>TRUE|FALSE)
  | (?P<op><>|<=|>=|[-+*/^&=<>%(),])
""", re.X)


def tokenize(text):
    pos, out = 0, []
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m:
            raise Unsupported(f"cannot read formula at '{text[pos:]}'")
        pos = m.end()
        if m.lastgroup != "ws":
            out.append((m.lastgroup, m.group()))
    return out


def num(x):
    """Excel arithmetic value: empty -> 0, bool -> 0/1, numeric text -> number."""
    if isinstance(x, ExcelError):
        raise _Err(x)
    if x is None:
        return 0.0
    if isinstance(x, bool):
        return float(x)
    if isinstance(x, (int, float)):
        return x
    try:
        return float(x)
    except (TypeError, ValueError):
        raise _Err(ExcelError("#VALUE!"))


class _Err(Exception):
    def __init__(self, err):
        self.err = err


def flat(args):
    for a in args:
        if isinstance(a, list):
            yield from flat(a)
        else:
            yield a


def _round(x, d=0):
    x, d = num(x), int(num(d))
    q = 10 ** d
    return math.floor(abs(x) * q + 0.5) / q * (1 if x >= 0 else -1)  # Excel rounds half away from zero


FUNCS = {
    "SQRT": lambda x: math.sqrt(num(x)) if num(x) >= 0 else (_ for _ in ()).throw(_Err(ExcelError("#NUM!"))),
    "ABS": lambda x: abs(num(x)),
    "PI": lambda: math.pi,
    "POWER": lambda a, b: num(a) ** num(b),
    "EXP": lambda x: math.exp(num(x)),
    "LN": lambda x: math.log(num(x)),
    "ROUND": _round,
    "SUM": lambda *a: sum(num(v) for v in flat(a) if v is not None and not isinstance(v, str)),
    "MIN": lambda *a: min([num(v) for v in flat(a) if isinstance(v, (int, float))] or [0]),
    "MAX": lambda *a: max([num(v) for v in flat(a) if isinstance(v, (int, float))] or [0]),
    "AVERAGE": lambda *a: (lambda v: sum(v) / len(v) if v else (_ for _ in ()).throw(_Err(ExcelError("#DIV/0!"))))(
        [num(v) for v in flat(a) if isinstance(v, (int, float))]),
    "AND": lambda *a: all(bool(num(v)) for v in flat(a)),
    "OR": lambda *a: any(bool(num(v)) for v in flat(a)),
}


class Workbook:
    """Workbook with formulas, evaluated on demand (results cached, cycles detected)."""

    def __init__(self, path):
        self.wb = openpyxl.load_workbook(path)                     # formulas
        self.cached = openpyxl.load_workbook(path, data_only=True)  # results stored in the file (if any)
        self.memo, self.busy = {}, set()

    def value(self, sheet, col, row):
        key = (sheet, col, row)
        if key in self.memo:
            return self.memo[key]
        if sheet not in self.wb.sheetnames:
            raise _Err(ExcelError("#REF!"))
        v = self.wb[sheet].cell(row=row, column=col).value
        if isinstance(v, str) and v.startswith("="):
            if key in self.busy:
                raise Unsupported(f"circular reference at {sheet}!{get_column_letter(col)}{row}")
            self.busy.add(key)
            try:
                v = self.evaluate(v[1:], sheet)
            finally:
                self.busy.discard(key)
        elif not isinstance(v, (str, int, float, bool, type(None))):
            v = getattr(v, "text", v)  # rich text / dates are passed through
        self.memo[key] = v
        return v

    def cached_value(self, sheet, col, row):
        return self.cached[sheet].cell(row=row, column=col).value

    # --- parser (Excel precedence: comparison < & < + - < * / < ^ < unary minus < %)
    def evaluate(self, text, sheet):
        saved = getattr(self, "toks", None), getattr(self, "i", 0), getattr(self, "sheet", None)
        self.toks, self.i, self.sheet = tokenize(text), 0, sheet
        try:
            v = self._compare()
            if self.i != len(self.toks):
                raise Unsupported(f"unexpected '{self.toks[self.i][1]}'")
            return v[0] if isinstance(v, list) and len(v) == 1 else v
        except _Err as e:
            return e.err
        except ZeroDivisionError:
            return ExcelError("#DIV/0!")
        finally:
            self.toks, self.i, self.sheet = saved  # restore the caller's parser state (nested references)

    def _peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def _take(self, val=None):
        t = self._peek()
        if val is not None and t[1] != val:
            raise Unsupported(f"expected '{val}'")
        self.i += 1
        return t

    def _compare(self):
        a = self._concat()
        while self._peek()[1] in ("=", "<>", "<", ">", "<=", ">="):
            op = self._take()[1]
            b = self._concat()
            a, b = (num(a), num(b)) if not (isinstance(a, str) and isinstance(b, str)) else (a, b)
            a = {"=": a == b, "<>": a != b, "<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[op]
        return a

    def _concat(self):
        a = self._add()
        while self._peek()[1] == "&":
            self._take()
            b = self._add()
            a = ("" if a is None else _text(a)) + ("" if b is None else _text(b))
        return a

    def _add(self):
        a = self._mul()
        while self._peek()[1] in ("+", "-"):
            op = self._take()[1]
            b = self._mul()
            a = num(a) + num(b) if op == "+" else num(a) - num(b)
        return a

    def _mul(self):
        a = self._pow()
        while self._peek()[1] in ("*", "/"):
            op = self._take()[1]
            b = self._pow()
            a = num(a) * num(b) if op == "*" else num(a) / num(b)
        return a

    def _pow(self):
        a = self._unary()
        while self._peek()[1] == "^":
            self._take()
            a = num(a) ** num(self._unary())
        return a

    def _unary(self):
        if self._peek()[1] in ("-", "+"):
            op = self._take()[1]
            v = self._unary()
            return -num(v) if op == "-" else num(v)
        v = self._primary()
        while self._peek()[1] == "%":
            self._take()
            v = num(v) / 100
        return v

    def _primary(self):
        kind, val = self._take()
        if kind == "num":
            return float(val) if any(c in val for c in ".eE") else int(val)
        if kind == "str":
            return val[1:-1].replace('""', '"')
        if kind == "bool":
            return val == "TRUE"
        if kind == "ref":
            return self._ref(val)
        if kind == "func":
            name = val.upper()
            self._take("(")
            args = []
            if self._peek()[1] != ")":
                if name == "IF":
                    return self._if()
                args.append(self._compare())
                while self._peek()[1] == ",":
                    self._take()
                    args.append(self._compare())
            self._take(")")
            if name not in FUNCS:
                raise Unsupported(f"function {name} not supported")
            return FUNCS[name](*args)
        if val == "(":
            v = self._compare()
            self._take(")")
            return v
        raise Unsupported(f"unexpected '{val}'")

    def _if(self):
        cond = self._compare()
        a = b = False
        if self._peek()[1] == ",":
            self._take()
            a = self._compare()
            if self._peek()[1] == ",":
                self._take()
                b = self._compare()
        self._take(")")
        return a if bool(num(cond)) else b

    def _ref(self, text):
        sheet = self.sheet
        if "!" in text:
            s, text = text.rsplit("!", 1)
            sheet = s[1:-1].replace("''", "'") if s.startswith("'") else s
        parts = [re.match(r"\$?([A-Za-z]{1,3})\$?(\d+)", p).groups() for p in text.split(":")]
        (c1, r1) = parts[0]
        if len(parts) == 1:
            return self.value(sheet, column_index_from_string(c1.upper()), int(r1))
        (c2, r2) = parts[1]
        cs = sorted((column_index_from_string(c1.upper()), column_index_from_string(c2.upper())))
        rs = sorted((int(r1), int(r2)))
        return [self.value(sheet, c, r) for r in range(rs[0], rs[1] + 1) for c in range(cs[0], cs[1] + 1)]


def _text(v):
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


# --------------------------------------------------------------------------- LibreOffice fallback
def libreoffice_recalc(path, tmpdir):
    """Opens and re-saves the workbook with LibreOffice (headless), which stores the formula results."""
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        return None
    subprocess.run([exe, "--headless", "--calc", "--convert-to", "xlsx", "--outdir", str(tmpdir), str(path)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600, check=False)
    out = Path(tmpdir) / path.name
    return openpyxl.load_workbook(out, data_only=True) if out.exists() else None


# --------------------------------------------------------------------------- conversion
def close(a, b, tol):
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=tol, abs_tol=1e-12)
    return (a in (None, "") and b in (None, "")) or str(a) == str(b)


def fmt(v, float_format):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, float):
        if float_format:
            return float_format % v
        return str(int(v)) if v.is_integer() and abs(v) < 1e15 else repr(v)
    return v


def convert_workbook(path, out_base, cfg, report):
    csv_cfg = cfg.get("csv") or {}
    engine = cfg.get("engine", "auto")
    tol = float(cfg.get("tolerance", 1e-9))
    book = Workbook(path)
    sheets = book.wb.sheetnames if cfg.get("sheets", "all") == "all" else \
        [s for s in book.wb.sheetnames if s in cfg["sheets"]]
    lo_book, lo_tried = None, False
    stats = {"formulas": 0, "evaluated": 0, "cached": 0, "libreoffice": 0, "errors": 0, "mismatch": 0}
    tmp = tempfile.TemporaryDirectory()
    written = []
    for name in sheets:
        ws = book.wb[name]
        rows = []
        for r in range(1, ws.max_row + 1):
            row = []
            for c in range(1, ws.max_column + 1):
                raw = ws.cell(row=r, column=c).value
                if isinstance(raw, str) and raw.startswith("="):
                    stats["formulas"] += 1
                    cached = book.cached_value(name, c, r)
                    v, how = None, None
                    if engine in ("evaluate", "auto"):
                        try:
                            v, how = book.value(name, c, r), "evaluated"
                        except Unsupported as e:
                            if engine == "evaluate":
                                raise Unsupported(f"{path.name} {name}!{get_column_letter(c)}{r}: {e}")
                    if how is None and cached is not None:
                        v, how = cached, "cached"
                    if how is None and engine == "auto":
                        if not lo_tried:
                            lo_book, lo_tried = libreoffice_recalc(path, tmp.name), True
                        if lo_book is not None:
                            v, how = lo_book[name].cell(row=r, column=c).value, "libreoffice"
                    if how is None:
                        raise Unsupported(f"{path.name} {name}!{get_column_letter(c)}{r}: no result available for "
                                          f"'{raw}' (no stored result and LibreOffice not available)")
                    stats[how] += 1
                    if isinstance(v, ExcelError):
                        stats["errors"] += 1
                    if (how == "evaluated" and cfg.get("check_against_cached", True) and cached is not None
                            and not close(v, cached, tol)):
                        stats["mismatch"] += 1
                        report.append(f"  value differs from stored result: {path.name} {name}!"
                                      f"{get_column_letter(c)}{r} evaluated={v!r} stored={cached!r}")
                else:
                    v = book.value(name, c, r)
                row.append(v)
            rows.append(row)
        # trailing empty columns / rows
        width = max((max((i + 1 for i, v in enumerate(row) if v not in (None, "")), default=0) for row in rows),
                    default=0)
        rows = [row[:width] for row in rows]
        if csv_cfg.get("drop_empty_rows", True):
            rows = [row for row in rows if any(v not in (None, "") for v in row)]
        if rows and csv_cfg.get("header_newline") is not None:
            rows[0] = [v.replace("\r\n", "\n").replace("\n", csv_cfg["header_newline"]) if isinstance(v, str) else v
                       for v in rows[0]]
        safe = re.sub(r'[\\/:*?"<>|]', "_", name).strip() or "sheet"
        if cfg.get("layout", "folder_per_workbook") == "flat":
            target = out_base / f"{path.stem}__{safe}.csv"
        else:
            target = out_base / path.stem / f"{safe}.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", newline="", encoding=csv_cfg.get("encoding", "utf-8")) as f:
            w = csv.writer(f, delimiter=csv_cfg.get("delimiter", ","))
            for row in rows:
                w.writerow([fmt(v, csv_cfg.get("float_format")) for v in row])
        written.append(target)
    tmp.cleanup()
    return written, stats


def main(config_path=CONFIG_FILE):
    config_path = Path(config_path).resolve()
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    base = config_path.parent
    p = cfg["paths"]
    src = (base / p["input_folder"]).resolve()
    dst = (base / p["output_folder"]).resolve()
    skip = [(src / x).resolve() for x in p.get("exclude_folders") or []] + [dst]
    files = sorted(src.rglob("*.xlsx") if p.get("recursive", True) else src.glob("*.xlsx"))
    files = [f for f in files if not f.name.startswith("~$")
             and not any(s == f.parent or s in f.parents for s in skip)]
    if not files:
        print(f"No Excel files found in {src}")
        return
    report, total = [], {}
    for f in files:
        out_base = dst / f.parent.relative_to(src)
        written, stats = convert_workbook(f, out_base, cfg, report)
        for k, v in stats.items():
            total[k] = total.get(k, 0) + v
        print(f"{f.relative_to(src)}: {len(written)} CSV file(s); formulas {stats['formulas']} "
              f"(evaluated {stats['evaluated']}, stored {stats['cached']}, LibreOffice {stats['libreoffice']}); "
              f"Excel errors {stats['errors']}; differences from stored results {stats['mismatch']}")
    print(f"\n{len(files)} workbook(s) converted to {dst}")
    print(f"Total formulas {total['formulas']}: evaluated {total['evaluated']}, stored {total['cached']}, "
          f"LibreOffice {total['libreoffice']}; Excel errors {total['errors']}; "
          f"differences from stored results {total['mismatch']}")
    for line in report[:50]:
        print(line)
    if len(report) > 50:
        print(f"  ... {len(report) - 50} more")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent / CONFIG_FILE)
