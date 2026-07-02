# POST-Rec methodology article (Elsevier elsarticle)

Formal methodology paper for **POST-Rec**, written using the bundled `elsarticle` document class.

## Files

| File | Purpose |
|------|---------|
| `post-rec-ideation.tex` | Main article source |
| `post-rec-references.bib` | BibTeX references (14 entries) |
| `post-rec-ideation.pdf` | Compiled PDF (generated) |
| `Makefile` | Build automation |

## Build

From this directory:

```bash
# First time only (if elsarticle.cls is missing):
latex elsarticle.ins

# Build PDF:
make
# Or manually:
pdflatex post-rec-ideation
bibtex post-rec-ideation
pdflatex post-rec-ideation
pdflatex post-rec-ideation
```

On Windows with MiKTeX, the same `pdflatex` / `bibtex` sequence applies.

## Contents

The article (~14 pages) includes:

- Abstract, highlights, keywords (Elsevier frontmatter)
- Introduction with contributions and section roadmap
- Related work comparison table
- **The proposal:** overview, data features, notation, metrics, equations, motivation scenario, algorithms
- Online experimental evaluation (primary) and supplementary offline checks
- Discussion, conclusion, numbered references

## Related docs

- Web UI: `/how-it-works`
- Markdown draft: `../POST-Rec_Literature-Grounded_Research_Ideation.md`
- System docs: `../../docs/how-it-works.md`, `../../docs/fggv-evaluation.md`
