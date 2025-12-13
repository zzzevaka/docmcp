import base64
import re

from nbconvert.preprocessors import Preprocessor
from nbformat import NotebookNode
from nbformat.v4 import new_output

_IMAGE_MIMES = ("image/png", "image/jpeg", "image/jpg", "image/svg+xml")


class EmbedImagesAsDataURI(Preprocessor):
    def _find_image_mime_and_data(self, data_map):
        for mime in ("image/png", "image/jpeg", "image/jpg", "image/svg+xml"):
            for k in list(data_map.keys()):
                if k.lower() == mime:
                    v = data_map.get(k)
                    return mime, v
        return None, None

    def _make_md_image(self, mime, data_value, alt_text=None):
        if mime == "image/svg+xml":
            if isinstance(data_value, str) and re.search(r"<\s*svg\b", data_value, flags=re.I):
                b64 = base64.b64encode(data_value.encode("utf-8")).decode("ascii")
            else:
                b64 = data_value
        else:
            b64 = data_value

        if isinstance(b64, str) and b64.startswith("data:"):
            uri = b64
        else:
            uri = f"data:{mime};base64,{b64}"

        alt = alt_text if alt_text is not None else ""

        uri = uri.replace("\n", "").replace("\r", "").strip()

        return f"![{alt}]({uri})"

    def preprocess_cell(self, cell: NotebookNode, resources, index):
        if cell.get("cell_type") != "code":
            return cell, resources


        new_outputs = []
        for out in cell.get("outputs", []):
            new_out = None

            if isinstance(out, dict) and "data" in out and isinstance(out["data"], dict):
                data = dict(out["data"])
                if any(k.lower().startswith("text/markdown") for k in data.keys()):
                    new_outputs.append(out)
                    continue

                mime, imgdata = self._find_image_mime_and_data(data)
                if mime and imgdata:
                    if isinstance(imgdata, list):
                        imgdata = "".join(imgdata)

                    meta = out.get("metadata", {}) or {}
                    alt = meta.get("alt", None)

                    md_image = self._make_md_image(mime, imgdata, alt_text=alt)

                    for k in list(data.keys()):
                        if k.lower().startswith("image/"):
                            data.pop(k, None)

                    data["text/markdown"] = md_image

                    new_out = new_output(
                        output_type="display_data",
                        data={"text/markdown": md_image},
                        metadata={}
                    )

            if new_out is None:
                new_out = out

            new_outputs.append(new_out)

        cell["outputs"] = new_outputs
        return cell, resources

    def preprocess(self, nb, resources):
        for i, cell in enumerate(nb.cells):
            nb.cells[i], resources = self.preprocess_cell(cell, resources, i)
        return nb, resources
