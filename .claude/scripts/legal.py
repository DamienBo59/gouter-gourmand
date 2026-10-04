#!/usr/bin/env python3
"""Lance l'outil de generation des pages legales sur ce blog.

L'outil n'est pas versionne dans ce repo. Son emplacement et son nom de module
sont lus dans l'environnement :
  LEGAL_TOOL_DIR     dossier qui contient le module
  LEGAL_TOOL_MODULE  nom du module Python a importer (il expose ROOT et main())
  LEGAL_TOOL_MARKER  prefixe des marqueurs que l'outil attend dans le theme
                     (facultatif)

L'outil ecrit dans <ROOT>/<nom du repo> : ROOT est donc force sur le dossier
parent de ce repo, et le nom de repo passe par defaut est celui de ce dossier.
D'autres repos voisins peuvent etre passes en arguments.

Les blocs inseres dans le theme sont reperes par des marqueurs, `legal-links`
et `legal-noindex` dans ce repo. Si l'outil attend un autre prefixe, ils sont
traduits le temps de l'appel puis remis en place, pour que l'outil retrouve ses
blocs au lieu de les dupliquer.
"""
import importlib
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
LOCAL_MARKER = "legal-links"
LOCAL_NOINDEX = "legal-noindex"


def theme_files(repos):
    for repo in repos:
        yield from _theme_files(repo)


def _theme_files(repo):
    for pattern in ("themes/*/layouts/partials/footer.html",
                    "themes/*/layouts/_default/baseof.html",
                    "themes/*/assets/css/main.css"):
        yield from repo.glob(pattern)


def translate(repos, pairs):
    for f in theme_files(repos):
        text = f.read_text(encoding="utf-8")
        new = text
        for old, rep in pairs:
            new = new.replace(old, rep)
        if new != text:
            f.write_text(new, encoding="utf-8")


def main():
    tool_dir = os.environ.get("LEGAL_TOOL_DIR")
    module = os.environ.get("LEGAL_TOOL_MODULE")
    if not tool_dir or not module:
        sys.exit("LEGAL_TOOL_DIR et LEGAL_TOOL_MODULE doivent etre definis.")
    sys.path.insert(0, os.path.expanduser(tool_dir))
    tool = importlib.import_module(module)
    tool.ROOT = str(REPO.parent)

    names = sys.argv[1:] or [REPO.name]
    repos = [REPO.parent / n for n in names if not n.startswith("-")]
    marker = os.environ.get("LEGAL_TOOL_MARKER")
    if marker:
        translate(repos, [(LOCAL_NOINDEX, marker + "-noindex"), (LOCAL_MARKER, marker)])
    try:
        sys.argv = [module + ".py"] + names
        tool.main()
    finally:
        if marker:
            translate(repos, [(marker + "-noindex", LOCAL_NOINDEX), (marker, LOCAL_MARKER)])


if __name__ == "__main__":
    main()
