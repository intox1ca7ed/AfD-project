# Presentation Setup Notes

This folder contains a Quarto + Reveal.js presentation project that renders to:

- `docs/presentation/`

## Local Preview

From the repository root:

```powershell
cd presentation
quarto preview
```

## Render

From the repository root:

```powershell
cd presentation
quarto render
```

## GitHub Pages Configuration

Use repository settings:

- Branch: `main` (or your default branch)
- Folder: `/docs`

The presentation will be published from `docs/presentation/index.html`.
A single `.nojekyll` is kept at `docs/.nojekyll` (the publish root).

## Timeline File

Current timeline source used by the deck:

- `presentation/afd_research_design_timeline.html`

If you export an updated timeline later, overwrite this same file and rerender.
