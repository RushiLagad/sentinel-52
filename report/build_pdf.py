#!/usr/bin/env python3
"""Build report/REPORT.pdf from report/REPORT.md with pandoc and xelatex.

    python report/build_pdf.py            # keeps the DRAFT STATUS banner
    python report/build_pdf.py --final    # drops the banner for submission

Needs pandoc and a TeX distribution with xelatex (TeX Live or MiKTeX). The
figures are referenced relative to report/, so the script runs pandoc from
there. Nothing here changes REPORT.md; the banner is stripped from a temporary
copy only.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "REPORT.md"
OUT = HERE / "REPORT.pdf"

HEADER = r"""
\usepackage{geometry}
\geometry{letterpaper, margin=1in}
\usepackage{pdflscape}
\usepackage{caption}
\captionsetup{font=small, labelfont=bf, width=0.92\textwidth}
\usepackage{float}
\floatplacement{figure}{H}
\usepackage{graphicx}
\makeatletter
\def\maxwidth{\ifdim\Gin@nat@width>\linewidth\linewidth\else\Gin@nat@width\fi}
\makeatother
\setkeys{Gin}{width=\maxwidth, keepaspectratio}
\usepackage{setspace}
\setstretch{1.08}
\setlength{\parskip}{6pt}
\setlength{\parindent}{0pt}
\usepackage{titlesec}
\titlespacing*{\section}{0pt}{18pt}{6pt}
\usepackage{xcolor}
\definecolor{linkblue}{HTML}{2a78d6}
\usepackage{hyperref}
\hypersetup{colorlinks=true, linkcolor=linkblue, urlcolor=linkblue, citecolor=linkblue}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small Sentinel-52, NAFSI Hub Student Data Challenge, Fall 2026}
\fancyhead[R]{\small\thepage}
\renewcommand{\headrulewidth}{0.2pt}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true", help="drop the DRAFT STATUS banner")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()

    for tool in ("pandoc", "xelatex"):
        if shutil.which(tool) is None:
            print(f"{tool} not found on PATH", file=sys.stderr)
            return 2

    md = SRC.read_text(encoding="utf-8")
    if a.final:
        md = re.sub(r"(?ms)^> \*\*DRAFT STATUS\..*?\*\*\n\n", "", md, count=1)
    # The two three-panel figures are 15 in wide and unreadable in portrait, so
    # each gets a landscape page of its own, written as raw LaTeX because pandoc
    # will not run markdown inside a raw environment.
    def landscape(m: re.Match) -> str:
        cap = m.group(1).replace("_", r"\_").replace("%", r"\%")
        return ("\\begin{landscape}\n\\begin{figure}[H]\\centering\n"
                f"\\includegraphics[width=\\linewidth]{{{m.group(2)}}}\n"
                f"\\caption{{{cap}}}\n\\end{{figure}}\n\\end{{landscape}}\n")
    md = re.sub(r"(?m)^!\[([^\]]*)\]\((figures/fig[12]_[^)]+)\)\n", landscape, md)

    with tempfile.TemporaryDirectory() as td:
        tmp_md = Path(td) / "REPORT.md"
        tmp_md.write_text(md, encoding="utf-8")
        header = Path(td) / "header.tex"
        header.write_text(HEADER, encoding="utf-8")
        cmd = [
            "pandoc", str(tmp_md), "-o", str(a.out),
            "--from", "markdown+smart", "--pdf-engine", "xelatex",
            "--resource-path", str(HERE),
            "-V", "fontsize=11pt", "-V", "documentclass=article",
            "-V", "mainfont=DejaVu Serif", "-V", "sansfont=DejaVu Sans",
            "-V", "monofont=DejaVu Sans Mono", "-V", "mainfontoptions=Scale=0.92",
            "-V", "monofontoptions=Scale=0.84",
            "-V", "colorlinks=true",
            "--include-in-header", str(header),
        ]
        # pandoc's template loads lmodern unconditionally even though fontspec
        # supplies the fonts under xelatex. Some TeX installs lack it; a stub
        # keeps the build from depending on an unused font package.
        env = dict(os.environ)
        if subprocess.run(["kpsewhich", "lmodern.sty"], capture_output=True).returncode != 0:
            (Path(td) / "lmodern.sty").write_text("% stub: fonts come from fontspec\n")
            env["TEXINPUTS"] = f"{td}:" + env.get("TEXINPUTS", "")
        print(" ".join(cmd))
        r = subprocess.run(cmd, cwd=HERE, env=env)
        if r.returncode != 0:
            return r.returncode
    print(f"wrote {a.out} ({a.out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
