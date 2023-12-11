# ASCROSS Crossword Renderer

## Input
```
title = "Thomas Mikrokrypto"

grid = """
SoL
ö.å
Mus
"""

clues_horizontal = """
S:Stjärna
M:Gnagare
"""

clues_vertical = """
S:Kan var sicksack
L:Håller ute ute och inne inne
"""

extra_text = """"""
```

## Output
```
python3 ascross.py crosswords.samples/*.toml --format a4 --page-num 1 --output crosswords.samples/a4.html
```
![](screenshot_a4.png)

```
python3 ascross.py crosswords.samples/*.toml --format a5two --page-num 2 --output crosswords.samples/a5two.html
```
![](screenshot_a5two.png)
