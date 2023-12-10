from dataclasses import dataclass
from enum import Enum
import tomllib
import argparse

CellKind = Enum('CellKind', ['OUTSIDE', 'LETTER', 'BLOCKED'])
Direction = Enum('Direction', ['HORIZONTAL', 'VERTICAL'])

next_starting_point_num = 1

@dataclass
class Cell:
    kind: CellKind
    solution: str = None
    is_starting_point: bool = False
    starting_point_num: int = -1
    
    def __init__(self, c):
        if c == ' ':
            self.kind = CellKind.OUTSIDE
        elif c == '.':
            self.kind = CellKind.BLOCKED
        else:
            self.kind = CellKind.LETTER
            self.solution = c.upper()
            self.is_starting_point = c.isupper()
            if self.is_starting_point:
                global next_starting_point_num
                self.starting_point_num = next_starting_point_num
                next_starting_point_num += 1

def load_config(filename):
    with open(filename, 'rb') as config_file:
        return tomllib.load(config_file)

def parse_grid(input_grid):
    input_lines = input_grid.split('\n')
    grid = []
    max_line_len = 0
    for line in input_lines:
        max_line_len = max(max_line_len, len(line))

    for line in input_lines:
        # Making a square grid, so that it can be assumed later
        row = [Cell(c) for c in line] + [Cell(' ')] * (max_line_len - len(line))
        grid.append(row)
    return grid

def map_clues(grid, input_clues, direction):
    clues = []
    used_starting_points = set()
    for input_clue in input_clues.split('\n'):
        mapped_clue = False
        prefix, clue_text = input_clue.split(':', 1)
        prefix = prefix.upper()
        for start_row_idx, row in enumerate(grid):
            for start_col_idx, cell in enumerate(row):
                if (cell.kind == CellKind.LETTER and
                    cell.is_starting_point and
                    cell.solution == prefix[0]):
                    right_word = True
                    word_length = 0
                    letter_row_idx = start_row_idx
                    letter_col_idx = start_col_idx
                    for i in range(1000):
                        if (letter_row_idx >= len(grid) or
                            letter_col_idx >= len(grid[letter_row_idx])):
                            # Out of letters in the current direction
                            if i == 1 or i < len(prefix) - 1:
                                # Only one letter (This is not a word) or
                                # prefix not fully matched.
                                right_word = False
                            break
                        
                        letter_cell = grid[letter_row_idx][letter_col_idx]
                        if len(prefix) > i and letter_cell.solution != prefix[i]:
                            right_word = False
                            break
                        
                        word_length += 1
                        
                        if direction == Direction.HORIZONTAL:
                            letter_col_idx += 1
                        else:
                            letter_row_idx += 1
                    
                    if right_word:
                        if cell.starting_point_num in used_starting_points:
                            raise Exception(f'"{clue_text}" matches starting point {cell.starting_point_num}, which is already used:\n{[cl for cl in clues if cl[0] == cell.starting_point_num]}\nConsider using longer prefixes for both clues.')
                        used_starting_points.add(cell.starting_point_num)
                        clues.append((cell.starting_point_num, f'{clue_text} ({word_length})'))
                        mapped_clue = True
                if mapped_clue:
                    break
            if mapped_clue:
                break
        if not mapped_clue:
            raise Exception(f"Clue was not mapped: {input_clue}")
    return sorted(clues)

def print_grid(grid):
    for row in grid:
        for cell in row:
            match cell.kind:
                case CellKind.OUTSIDE:
                    print('   ', end='')
                case CellKind.BLOCKED:
                    print('  #', end='')
                case CellKind.LETTER:
                    if cell.is_starting_point:
                        print(f'{cell.starting_point_num: 2}{cell.solution}', end='')
                    else:
                        print(f'  {cell.solution}', end='')
        print()

def svg_grid(grid, with_solution=False):
    # Check svg: In venv, pip install svgcheck, svgcheck file.svg
    svg = ''
    #svg += '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    # viewBox relates to the coordinates used when drawing. width and height can be set on the tag used in a web page to select the final size.
    CELL_SIDE = 20
    svg += f'<svg viewBox="0 0 {CELL_SIDE * len(grid[0])} {CELL_SIDE * len(grid)}" xmlns="http://www.w3.org/CELL_SIDE00/svg" class="grid">\n'
    svg += '<defs>'
    svg += f'<rect id="blocked" width="{CELL_SIDE}" height="{CELL_SIDE}" stroke-width="0.5" stroke="#000000" fill="#000000" />\n'
    svg += f'<rect id="letter" width="{CELL_SIDE}" height="{CELL_SIDE}" stroke-width="0.5" stroke="#000000" fill="#ffffff" />\n'
    svg += '</defs>'
    for row_idx, row in enumerate(grid):
        for col_idx, cell in enumerate(row):
            match cell.kind:
                case CellKind.OUTSIDE:
                    pass
                case CellKind.BLOCKED:
                    svg += f'<use href="#blocked" x="{col_idx * CELL_SIDE}" y="{row_idx * CELL_SIDE}" />\n'
                case CellKind.LETTER:
                    svg += f'<use href="#letter" x="{col_idx * CELL_SIDE}" y="{row_idx * CELL_SIDE}" />\n'
                    if with_solution:
                        svg += f'<text x="{(col_idx + 0.5) * CELL_SIDE}" y="{row_idx * CELL_SIDE + 16}" text-anchor="middle" font-size="16" font-family="sans-serif" color="#000000">{cell.solution}</text>\n'
                    if cell.is_starting_point:
                        svg += f'<text x="{col_idx * CELL_SIDE + 1.5}" y="{row_idx * CELL_SIDE + 5.5}" font-size="5" font-family="sans-serif" color="#000000">{cell.starting_point_num}</text>\n'
    svg += '</svg>'
    return svg

def clues_div(clues, title):
    src = ''
    src += f'<div><h2>{title}</h2><div><ol>'
    for starting_point_num, clue_text in clues:
        src += f'<li value="{starting_point_num}">{clue_text}</li>'
    src += '</ol></div></div>'
    return src

def write_style(f, page_size):
    f.write('''
    <!-- Generated using ascross -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/paper-css/0.3.0/paper.css">
    <style>
    @page { size: ''' + page_size + '''; }
    .grid { width: 400px; margin: 20px; }
    .grid-container {
        text-align: center;
    }
    .grid-container.vertical-center {
        display: flex;
        justify-content: center;
        flex-direction: row;
        position: absolute;
        top: 0; left: 0;
        right: 0; bottom: 0;
    }
    li { margin-bottom: 5px; }
    body {
        font-family: serif;
        font-size: 10pt;
    }
    h1 { font-size: 16pt; }
    h2 { font-size: 13pt; }
    .footer {
        position: absolute;
        bottom: 0.5cm;
    }
    .footer.odd {
        right: 0.8cm;
    }
    .footer.even {
        left: 0.8cm;
    }
    /* More padding towards the middle of the book */
    .sheet.odd {
        padding: 10mm;
        padding-left: 20mm;
    }
    .sheet.even {
        padding: 10mm;
        padding-right: 20mm;
    }
    .grid-container.even {
       padding-right: 10mm; 
    }
    </style>
    ''')

def write_a5_two_page(f, config, grid, clues_horizontal, clues_vertical):
    input_title = config['title']
    write_style(f, 'A5')
    f.write(f'''
    <title>{input_title}</title>
    <body class="A5">
    <section class="sheet even">
        <h1>{input_title}</h1>
        <div class="grid-container even vertical-center">
            {svg_grid(grid, with_solution=False)}
        </div>
        <div class="footer even">10</div>
    </section>
    <section class="sheet odd">
        <!-- The content should be below the header on the other page. Insert an empty
            header to get the correct spacing. -->
        <h1>&nbsp;</h1>
        {clues_div(clues_horizontal, 'Vågrätt')}
        {clues_div(clues_vertical, 'Lodrätt')}
        <div>{config['extra_text']}</div>
        <div class="footer odd">10</div>
    </section>
    </body>
    ''')

def write_a4_one_page(f, config, grid, clues_horizontal, clues_vertical):
    input_title = config['title']
    write_style(f, 'A4')
    f.write(f'''
    <title>{input_title}</title>
    <body class="A4">
    <section class="sheet padding-10mm">
        <h1>{input_title}</h1>
        <div class="grid-container">{svg_grid(grid, with_solution=False)}</div>
        {clues_div(clues_horizontal, 'Vågrätt')}
        {clues_div(clues_vertical, 'Lodrätt')}
        <div>{config['extra_text']}</div>
        <div class="footer even">10</div>
    </section>
    </body>
    ''')

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--debug', '-D', action='store_true')
    argparser.add_argument('--format', choices=['A4', 'A5two'], default='A4')
    argparser.add_argument('crossword')
    args = argparser.parse_args()
    
    config = load_config(args.crossword)
    
    grid = parse_grid(config['grid'])
    if args.debug:
        print_grid(grid)
        
    input_clues_horizontal = config['clues_horizontal'].strip()
    input_clues_vertical = config['clues_vertical'].strip()

    clues_horizontal = map_clues(grid, input_clues_horizontal, Direction.HORIZONTAL)
    clues_vertical = map_clues(grid, input_clues_vertical, Direction.VERTICAL)

    f = open('out.html', 'w')
    match args.format:
        case 'A4':
            write_a4_one_page(f, config, grid, clues_horizontal, clues_vertical)
        case 'A5two':
            write_a5_two_page(f, config, grid, clues_horizontal, clues_vertical)
    f.close()

main()