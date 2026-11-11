"""
Lint the paper draft before anyone trusts it. Run after EVERY edit to main.tex:

  conda run -n robosketch --no-capture-output python docs/paper/check_paper.py

Exits non-zero on any ERROR. It catches the mistakes this project has actually seen or
that AI-written papers are known for:

  1. a \\cite key that is not in references.bib (an invented or mistyped reference)
  2. citing an entry flagged x_verify (metadata not yet checked by a human)
  3. a decimal number on a line with no `% src:` comment (a number nobody can trace)
  4. wording PAPER_PLAN.md forbids (overclaims, "no difference", "equivalent", ...)
  5. leftover \\TODO markers
  6. \\includegraphics pointing at a file that does not exist
  7. a LaTeX command eaten by a Python string escape: "\\ref" written from a non-raw
     string becomes a carriage return + "ef" (seen 2026-11-08); likewise \\t \\b \\f \\v \\a \\n
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TEX = os.path.join(HERE, "main.tex")
BIB = os.path.join(HERE, "references.bib")

# (regex, why) - checked case-insensitively, outside comments
FORBIDDEN = [
    (r"\bfirst (work|paper|method|approach|to)\b", "priority claim - prior art exists (PAPER_PLAN s5)"),
    (r"\bnovel\b", "say what is measured, not that it is novel (AGENTS.md s1)"),
    (r"\bno (significant )?difference\b", "write 'no detectable difference' (PAPER_PLAN s7)"),
    (r"\bequivalent\b(?!.*TOST)", "'equivalent' only for the H2 spaced TOST result, with 'TOST' on the same line (PAPER_PLAN s4.2-3)"),
    (r"\b(the same|identical) (performance|accuracy|results?)\b", "write 'no detectable difference'"),
    (r"\boutperform", "only if a pre-registered test says so - check PAPER_PLAN s2"),
    (r"\bprove[sd]?\b", "experiments support, they do not prove"),
    (r"\bstate[- ]of[- ]the[- ]art\b", "no SOTA comparison exists"),
    (r"\brecover(s|y)? better\b", "C4 is AT RISK - only with the H4 primary diff-in-diff (PAPER_PLAN s3)"),
    (r"\bsignificant(ly)?\b(?!.*\bt\s*=)", "'significant' needs a t value on the same line"),
]


def strip_comment(line):
    return re.split(r"(?<!\\)%", line, 1)[0]


def main():
    errors, warns = [], []
    if not os.path.exists(TEX):
        print("no main.tex"); return 1
    tex = open(TEX, encoding="utf-8").read().split("\n")
    bib = open(BIB, encoding="utf-8").read() if os.path.exists(BIB) else ""
    keys = set(re.findall(r"^@\w+\{(\w+),", bib, re.M))
    flagged = set(re.findall(r"^@\w+\{(\w+),(?:(?!^@).)*?x_verify", bib, re.M | re.S))

    # 7. escape accidents: control characters left in a line, or a line that starts with
    #    the tail of a command whose backslash+letter became a line break
    lines_raw = open(TEX, encoding="utf-8", newline="").read().replace("\r\n", "\n").split("\n")
    for n, raw in enumerate(lines_raw, 1):
        if re.search(r"[\x00-\x09\x0b-\x1f]", raw):
            errors.append(f"L{n}: control character (tab/CR/...) in the text - a Python escape ate a LaTeX command? -> {raw.strip()[:70]!r}")
        if re.match(r"(ef|ewcommand|oindent|ewline|ewpage)\b", raw):
            errors.append(f"L{n}: line starts with '{raw[:12]}' - a '\\r'/'\\n' escape ate a LaTeX command?")

    for n, raw in enumerate(tex, 1):
        body = strip_comment(raw)
        if raw.lstrip().startswith("%"):
            continue
        for grp in re.findall(r"\\cite[pt]?\{([^}]+)\}", body):
            for k in (x.strip() for x in grp.split(",")):
                if k not in keys:
                    errors.append(f"L{n}: \\cite{{{k}}} is not in references.bib - never invent references")
                elif k in flagged:
                    errors.append(f"L{n}: \\cite{{{k}}} is flagged VERIFY in references.bib - check it first")
        near = "\n".join(tex[n - 1:n + 2])        # this line or the next two (end of sentence)
        if re.search(r"(?<![\w.])\d*\.\d{2,}", body) and "% src:" not in near \
                and not re.search(r"\\(usepackage|documentclass|vspace|hspace|includegraphics|setlength)", body):
            errors.append(f"L{n}: number with no '% src:' comment -> {body.strip()[:70]}")
        for rx, why in FORBIDDEN:
            if re.search(rx, body, re.I):
                errors.append(f"L{n}: '{re.search(rx, body, re.I).group(0)}' - {why}")
        if "\\TODO" in body:
            warns.append(f"L{n}: TODO left")
        for g in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", body):
            if not os.path.exists(os.path.normpath(os.path.join(HERE, g))):
                errors.append(f"L{n}: figure not found: {g}")

    for e in errors:
        print("ERROR  " + e)
    for w in warns:
        print("todo   " + w)
    print(f"\n{len(errors)} errors, {len(warns)} TODOs left")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
