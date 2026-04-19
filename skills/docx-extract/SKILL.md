---
name: docx-extract
type: deterministic
---

# docx-extract

Converts Word whitepapers to Markdown skeletons with equation placeholders, extracts embedded images, and produces a per-document manifest that captures the context around each equation for downstream OCR.

## When to use

Use this skill when the user wants to:
- "Extract the pilot doc" / "run docx-extract on raw/Model_A.docx"
- "Process all whitepapers in raw/" into skeletons
- Refresh extraction for a doc that was updated

Do NOT use this skill when:
- The user wants final cleaned Markdown — that's `md-normalize`, which runs after this.
- The user wants formula OCR — that's `formula-ocr`, which runs after this.
- The source is a PDF — this skill only handles .docx. Reject PDFs with a clear message.

## Inputs

- **Required:** one or more `.docx` paths, usually under `raw/`. Accept either a single file or a directory.
- **Config:** `doc_id` convention — if not provided, derive from filename (lowercase, replace spaces with `_`, strip version suffix into a separate field).

## Outputs

Per input document:
- `artifacts/extracted/{doc_id}.md` — Markdown skeleton with `{{EQUATION_<id>}}` tokens where formulas were.
- `artifacts/extracted/{doc_id}/images/{image_id}.{ext}` — every embedded image, named by a stable `image_id`.
- `artifacts/manifests/{doc_id}.json` — equation manifest with context. Schema below.

### Manifest schema

```json
{
  "doc_id": "model_a_lgd_v3",
  "source_file": "Model_A_LGD_v3.2.docx",
  "title": "Model A — Loss Given Default Methodology",
  "equations": [
    {
      "equation_id": "eq_001",
      "type": "image",
      "image_path": "artifacts/extracted/model_a_lgd_v3/images/eq_001.png",
      "paragraph_index": 42,
      "section_heading": "3.2 Loss Given Default",
      "section_anchor": "loss-given-default",
      "surrounding_context": "The LGD is estimated using the following logistic specification where collateral coverage is the primary driver:",
      "display_mode": "display"
    },
    {
      "equation_id": "eq_002",
      "type": "omml",
      "omml_xml": "<m:oMath>...</m:oMath>",
      "latex_converted": "PD = \\frac{1}{1+e^{-x}}",
      "paragraph_index": 87,
      "section_heading": "4.1 PD Calibration",
      "section_anchor": "pd-calibration",
      "display_mode": "display"
    }
  ],
  "non_equation_images": [
    { "image_id": "img_003", "image_path": "...", "paragraph_index": 120, "caption": "Figure 2: Calibration plot" }
  ]
}
```

## Procedure

Claude Code should follow these steps when the skill is triggered:

1. **Validate inputs.** Check that each path exists and ends in `.docx`. If a directory, glob `*.docx` one level deep.
2. **For each doc, call `helper.py`.** Pass the docx path and output directories. The helper:
   - Unzips the docx.
   - Parses `word/document.xml` with lxml.
   - Finds `<m:oMath>` elements (OMML equations) and converts to LaTeX via `pandoc` if available, falling back to leaving the OMML XML in the manifest with `latex_converted: null`.
   - Finds `<w:drawing>` and `<w:pict>` elements, extracts the embedded image from `word/media/`, and assigns a stable `image_id`.
   - Captures `paragraph_index`, walks up to find the containing heading, and captures the previous 2-3 sentences as `surrounding_context`.
   - Runs `mammoth` to convert the body to HTML, then to Markdown, replacing equation elements with `{{EQUATION_<id>}}` tokens.
   - Writes skeleton, images, and manifest.
3. **Report summary** to the user: doc_id, number of OMML equations, number of image equations, number of non-equation images, path to manifest. Recommend that the user open the manifest and spot-check before running `formula-ocr`.
4. **On error:** write a partial manifest if possible, log the error, and surface it clearly. Do not silently skip failed docs.

## Example invocations

- "Run docx-extract on `raw/Model_A_LGD_v3.2.docx`."
- "Extract all whitepapers in `raw/`."
- "Re-extract Model A — I updated the source."

## Common gotchas

- **Mammoth flattens heading levels** if the source uses custom styles. If the extracted Markdown has fewer heading levels than the source, build a mammoth style map in `helper.py`.
- **Images may be referenced multiple times** (same `word/media/image1.png` embedded in two places). Use position-based `image_id`, not the media filename.
- **OMML inside nested tables** — the XML walker must handle nested tables; a flat `iterfind` misses them.
- **Section anchors must match `md-normalize`'s slug logic.** Both skills compute slugs from heading text; if they disagree, formula locators will break downstream.
