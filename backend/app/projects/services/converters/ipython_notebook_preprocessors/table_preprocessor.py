import re
from html import unescape
from html.parser import HTMLParser

from nbconvert.preprocessors import Preprocessor
from nbformat import NotebookNode


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset_state()

    def reset_state(self):
        self.in_table = False
        self.in_tr = False
        self.in_td = False
        self.current_cell_html = []
        self.current_row = []
        self.rows = []
        self.cell_attrs = {}

    def handle_starttag(self, tag, attrs):
        attrd = dict(attrs)
        if tag.lower() == "table":
            self.in_table = True
        if not self.in_table:
            return
        if tag.lower() == "tr":
            self.in_tr = True
            self.current_row = []
        if tag.lower() in ("td", "th") and self.in_tr:
            self.in_td = True
            self.current_cell_html = []
            self.cell_attrs = attrd

        if self.in_td:
            self.current_cell_html.append(f"<{tag}>")

    def handle_endtag(self, tag):
        if not self.in_table:
            return
        if tag.lower() in ("td", "th"):
            cell_html = "".join(self.current_cell_html)
            text = _strip_tags_and_unescape(cell_html)
            colspan = 1
            if self.cell_attrs:
                try:
                    colspan = int(self.cell_attrs.get("colspan", 1))
                except Exception:
                    colspan = 1
            for _ in range(max(1, colspan)):
                self.current_row.append(text)
            self.in_td = False
            self.current_cell_html = []
            self.cell_attrs = {}
        elif tag.lower() == "tr":
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = []
            self.in_tr = False
        elif tag.lower() == "table":
            self.in_table = False

        if self.in_td:
            self.current_cell_html.append(f"</{tag}>")

    def handle_data(self, data):
        if self.in_td:
            self.current_cell_html.append(data)

    def error(self, message):
        pass

def _strip_tags_and_unescape(html_text):
    s = re.sub(r"<[^>]+>", " ", html_text)
    s = unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def html_table_to_markdown(html):
    if not re.search(r"<\s*table\b", html, flags=re.I):
        return None
    parser = _TableParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    rows = parser.rows
    if not rows:
        return _simple_html_table_to_md(html)

    max_cols = max(len(r) for r in rows)
    norm_rows = []
    for r in rows:
        if len(r) < max_cols:
            r = r + [""] * (max_cols - len(r))
        elif len(r) > max_cols:
            r = r[:max_cols]
        norm_rows.append(r)

    header = norm_rows[0]
    body = norm_rows[1:] if len(norm_rows) > 1 else []

    md_lines = []
    md_lines.append("| " + " | ".join(header) + " |")
    md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in body:
        md_lines.append("| " + " | ".join(row) + " |")
    return "\n".join(md_lines)

def _simple_html_table_to_md(html):
    compact = re.sub(r">\s+<", "><", html)
    trs = re.findall(r"<tr.*?>(.*?)</tr>", compact, flags=re.I|re.S)
    rows = []
    for tr in trs:
        cells = re.findall(r"<t[dh].*?>(.*?)</t[dh]>", tr, flags=re.I|re.S)
        clean = [re.sub(r"<[^>]+>", "", unescape(c)).strip() for c in cells]
        if clean:
            rows.append(clean)
    if not rows:
        return None
    max_cols = max(len(r) for r in rows)
    norm = []
    for r in rows:
        if len(r) < max_cols:
            r = r + [""] * (max_cols - len(r))
        norm.append(r)
    header = norm[0]
    body = norm[1:] if len(norm) > 1 else []
    md = []
    md.append("| " + " | ".join(header) + " |")
    md.append("| " + " | ".join(["---"] * len(header)) + " |")
    for r in body:
        md.append("| " + " | ".join(r) + " |")
    return "\n".join(md)


class HtmlTableToMarkdownPreprocessor(Preprocessor):
    def _html_value_from_data(self, data):
        for k in list(data.keys()):
            if k.lower().startswith("text/html"):
                v = data.get(k)
                if isinstance(v, list):
                    return "".join(v)
                return v
        return None

    def preprocess_cell(self, cell: NotebookNode, resources, index):
        if cell.get("cell_type") != "code":
            return cell, resources

        outputs = cell.get("outputs", [])
        new_outputs = []
        for out in outputs:
            if isinstance(out, dict) and "data" in out and isinstance(out["data"], dict):
                data = out["data"]
                html = self._html_value_from_data(data)
                if html and re.search(r"<\s*table\b", html, flags=re.I):
                    md = html_table_to_markdown(html)
                    if md:
                        new_data = dict(data)
                        # убрать html-ключи
                        for k in list(new_data.keys()):
                            if k.lower().startswith("text/html"):
                                new_data.pop(k, None)
                        # добавить Markdown
                        new_data["text/markdown"] = md
                        out["data"] = new_data
            new_outputs.append(out)
        cell["outputs"] = new_outputs
        return cell, resources

    def preprocess(self, nb, resources):
        for i, cell in enumerate(nb.cells):
            nb.cells[i], resources = self.preprocess_cell(cell, resources, i)
        return nb, resources
