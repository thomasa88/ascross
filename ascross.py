# This file is part of ascross, an ASCII to HTML crosswords renderer.
#
# Copyright (C) 2023  Thomas Axelsson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from dataclasses import dataclass
from enum import Enum
import tomllib
import argparse
import math

CellKind = Enum('CellKind', ['OUTSIDE', 'LETTER', 'BLOCKED'])
Direction = Enum('Direction', ['HORIZONTAL', 'VERTICAL'])

@dataclass
class Cell:
    kind: CellKind = CellKind.OUTSIDE
    solution: str = None
    is_starting_point: bool = False
    starting_point_num: int = -1
    wall_right: bool = False
    wall_bottom: bool = False
    arrow_down: bool = False
    arrow_right: bool = False

class Crossword:
    pass

def parse_crossword(input_file):
    cw = Crossword()
    
    cw.config = tomllib.load(input_file)
    cw.grid = parse_grid(cw.config['grid'])

    input_clues_horizontal = cw.config['clues_horizontal'].strip()
    input_clues_vertical = cw.config['clues_vertical'].strip()

    cw.clues_horizontal = map_clues(cw.grid, input_clues_horizontal, Direction.HORIZONTAL)
    cw.clues_vertical = map_clues(cw.grid, input_clues_vertical, Direction.VERTICAL)
    
    return cw

def parse_grid(input_grid):
    input_lines = input_grid.split('\n')
    max_line_len = 0
    for line in input_lines:
        max_line_len = max(max_line_len, len(line))
    
    # Convert the raw input lines to a grid so that
    # we can access it randomly.
    input_grid = []
    for line in input_lines:
        row = [c for c in line] + [' '] * (max_line_len - len(line))
        input_grid.append(row)

    next_starting_point_num = 1
    grid = []
    input_row_count = len(input_grid)
    input_col_count = len(input_grid[0])
    row_idx = 0
    while row_idx < input_row_count:
        row = []
        grid.append(row)
        col_idx = 0
        while col_idx < input_col_count:
            c = input_grid[row_idx][col_idx]
            cell = Cell()
            row.append(cell)
            match c:
                case ' ':
                    cell.kind = CellKind.OUTSIDE
                case '#':
                    cell.kind = CellKind.BLOCKED
                case _:
                    cell.kind = CellKind.LETTER
                    cell.solution = c.upper()
                    cell.is_starting_point = c.isupper()
                    if cell.is_starting_point:
                        cell.starting_point_num = next_starting_point_num
                        next_starting_point_num += 1
            
            # Is this an extended cell?
            # TODO: Handle full set of four characters for an extended cell:
            #  A.
            #  ..
            #
            if col_idx + 1 < input_col_count:
                c_right = input_grid[row_idx][col_idx + 1]
                if parse_extended(cell, c_right):
                    col_idx += 1
            
            col_idx += 1
        row_idx += 1
    return grid

def parse_extended(cell, c):
    extended = True
    match c:
        case '.':
            # Spacer/Null value
            pass
        case '|':
            cell.wall_right = True
        case '-':
            cell.wall_bottom = True
        case ')':
            cell.arrow_down = True
        case '(':
            cell.arrow_right = True
        case _:
            extended = False
    return extended

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
                    current_direction = direction
                    for i in range(1000):
                        if (letter_row_idx >= len(grid) or
                            letter_col_idx >= len(grid[letter_row_idx]) or
                            grid[letter_row_idx][letter_col_idx].kind != CellKind.LETTER):
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

                        if letter_cell.arrow_down:
                            current_direction = Direction.VERTICAL
                        elif letter_cell.arrow_right:
                            current_direction = Direction.HORIZONTAL
                        
                        if current_direction == Direction.HORIZONTAL:
                            if letter_cell.wall_right:
                                break
                            letter_col_idx += 1
                        else:
                            if letter_cell.wall_bottom:
                                break
                            letter_row_idx += 1
                    
                    if right_word:
                        if mapped_clue:
                            raise Exception(f'"{clue_text}" matches multiple prefixes.\nConsider using longer prefixes for both clues.')
                        if cell.starting_point_num in used_starting_points:
                            raise Exception(f'"{clue_text}" matches starting point {cell.starting_point_num}, which is already used:\n{[cl for cl in clues if cl[0] == cell.starting_point_num]}\nConsider using longer prefixes for both clues.')
                        used_starting_points.add(cell.starting_point_num)
                        clues.append((cell.starting_point_num, f'{clue_text} ({word_length})'))
                        mapped_clue = True
            #     if mapped_clue:
            #         break
            # if mapped_clue:
            #     break
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
                        print(f'{cell.starting_point_num: >2}{cell.solution}', end='')
                    else:
                        print(f'  {cell.solution}', end='')
        print()

def svg_grid(grid, with_solution=False, svg_file=False, cell_size_cm = 1.0, fixed_width=None):
    # Check svg: In venv, pip install svgcheck, svgcheck file.svg
    CELL_SIDE = 20
    svg = ''
    if svg_file:
        svg += '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    if fixed_width:
        width = fixed_width
    else:
        width = f'{len(grid[0]) * cell_size_cm}cm'
    # viewBox relates to the coordinates used when drawing. width and height can be set on the tag used in a web page to select the final size.
    svg += f'''<svg viewBox="0 0 {CELL_SIDE * len(grid[0])} {CELL_SIDE * len(grid)}" width="{width}" xmlns="http://www.w3.org/2000/svg" class="grid">
    <defs>
    <rect id="blocked" width="{CELL_SIDE}" height="{CELL_SIDE}" stroke-width="0.5" stroke="#000000" fill="#000000" />
    <rect id="letter" width="{CELL_SIDE}" height="{CELL_SIDE}" stroke-width="0.5" stroke="#000000" fill="#ffffff" />
    <line id="wall_right" x1="{CELL_SIDE}" y1="0" x2="{CELL_SIDE}" y2="{CELL_SIDE}" stroke-width="2" stroke="#000000" />
    <line id="wall_bottom" x1="0" y1="{CELL_SIDE}" x2="{CELL_SIDE}" y2="{CELL_SIDE}" stroke-width="2" stroke="#000000" />
    <marker 
      id="arrowhead" 
      orient="auto" 
      markerWidth="10" 
      markerHeight="10" 
      refX="5" 
      refY="5"
    >
      <path d="M3,3 L5,5 L3,7" fill="transparent" stroke-width="0.7" stroke="#000000" />
    </marker>
    <polyline id="arrow_down" stroke-width="0.5" stroke="#000000" fill="transparent" marker-end="url(#arrowhead)" points="{CELL_SIDE-5},2 {CELL_SIDE-2},2 {CELL_SIDE-2},5" />
    <polyline id="arrow_right" stroke-width="0.5" stroke="#000000" fill="transparent" marker-end="url(#arrowhead)" points="2,{CELL_SIDE-5} 2,{CELL_SIDE-2} 5,{CELL_SIDE-2}" />
    </defs>
    '''
    overlay_elements = ''
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
            if cell.wall_right:
                overlay_elements += f'<use href="#wall_right" x="{col_idx * CELL_SIDE}" y="{row_idx * CELL_SIDE}" />\n'
            if cell.wall_bottom:
                overlay_elements += f'<use href="#wall_bottom" x="{col_idx * CELL_SIDE}" y="{row_idx * CELL_SIDE}" />\n'
            if cell.arrow_down:
                overlay_elements += f'<use href="#arrow_down" x="{col_idx * CELL_SIDE}" y="{row_idx * CELL_SIDE}" />\n'
            if cell.arrow_right:
                overlay_elements += f'<use href="#arrow_right" x="{col_idx * CELL_SIDE}" y="{row_idx * CELL_SIDE}" />\n'
    svg += overlay_elements
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
    <!-- Generated using ascross. https://github.com/thomasa88/ascross -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/paper-css/0.3.0/paper.css">
    <style>
    @page { size: ''' + page_size + '''; }
    .grid { margin: 20px; }
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
    .multi-grid-container {
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
        width: 100%;
    }
    li { margin-bottom: 5px; }
    body {
        /* Firefox and Chromium selects different serif fonts. Be explicit to get the same size. */
        font-family: "Noto serif";
    }
    
    body.A4 { font-size: 12pt; }
    .A4 h1 { font-size: 18pt; }
    .A4 h2 { font-size: 16pt; }
    
    body.A5 { font-size: 10pt; }
    .A5 h1 { font-size: 16pt; }
    .A5 h2 { font-size: 12pt; }
    
    .footer {
        position: absolute;
        bottom: 1cm;
    }
    .footer.odd {
        right: 1.1cm;
    }
    .footer.even {
        left: 1.1cm;
    }
    /* Set up page margins (done using padding) */
    .A4 .sheet {
        padding: 20mm;
    }
    /* More padding towards the middle of the book */
    .A5 .sheet.odd {
        padding: 12mm;
        padding-left: 18mm;
    }
    .A5 .sheet.even {
        padding: 12mm;
        padding-right: 18mm;
    }
    .grid-container.vertical-center.odd {
       padding-left: 5mm; 
    }
    </style>
    ''')

def write_a5_two_page(f, cws, first_page_num, with_solution=False):
    page_num = first_page_num
    for cw in cws:
        input_title = cw.config['title']
        if page_num:
            page_num_even = page_num
            page_num_odd = page_num + 1
            page_num += 2
        else:
            page_num_even = ''
            page_num_odd = ''
        f.write(f'''
        <section class="sheet even">
            <h1>{input_title}</h1>
            {clues_div(cw.clues_horizontal, 'Vågrätt')}
            {clues_div(cw.clues_vertical, 'Lodrätt')}
            <div>{cw.config['extra_text']}</div>
            <div class="footer even">{page_num_even}</div>
        </section>
        <section class="sheet odd">
            <!-- Pad down to content height -->
            <h1>&nbsp;</h1>
            <div class="grid-container odd">
                {svg_grid(cw.grid, with_solution)}
            </div>
            <div class="footer odd">{page_num_odd}</div>
        </section>
        ''')

def write_a5_two_grid_page(f, cws, first_page_num, with_solution=False):
    if first_page_num:
        page_num = first_page_num
    else:
        page_num = ''
    solutions_title = 'Lösningar'
    grids_per_page = 6
    for p in range(math.ceil(len(cws) / grids_per_page)):
        odd_even = 'even' if p % 2 == 0 else 'odd'
        f.write(f'''
        <section class="sheet {odd_even}">
            <h1>{solutions_title}</h1>
                <div class="multi-grid-container">
                ''')
        for i in range(grids_per_page * p, min(grids_per_page * p + grids_per_page, len(cws))):
            input_title = cws[i].config['title']
            f.write(f'''<div style="width: 50%">
                    {input_title}
                    {svg_grid(cws[i].grid, with_solution, fixed_width='60%')}
                    </div>''')
        f.write(f'''
                </div>
            <div class="footer {odd_even}">{page_num}</div>
        </section>
        ''')
        if page_num:
            page_num += 1
        # Only show title on the first page
        # Put hard space to keep the header spacing
        solutions_title = '&nbsp;'

def write_a4_one_page(f, cws, first_page_num, with_solution=False):
    if first_page_num:
        page_num = first_page_num
    else:
        page_num = ''
    for cw in cws:
        input_title = cw.config['title']
        f.write(f'''
        <section class="sheet">
            <h1>{input_title}</h1>
            <div class="grid-container">{svg_grid(cw.grid, with_solution)}</div>
            {clues_div(cw.clues_horizontal, 'Vågrätt')}
            {clues_div(cw.clues_vertical, 'Lodrätt')}
            <div>{cw.config['extra_text']}</div>
            <div class="footer odd">{page_num}</div>
        </section>
        ''')
        if page_num:
            page_num += 1

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--debug', '-D', action='store_true', help="Print debug information")
    argparser.add_argument('--format', choices=['a4', 'a5two', 'a5two-grids', 'svg'], default='a4', help="Page format")
    argparser.add_argument('--page-num', type=int, help="Number the pages starting at the given number")
    argparser.add_argument('--solution', action='store_true', help="Output the solution (fill in the boxes)")
    argparser.add_argument('--output', help="Name of the output file")
    argparser.add_argument('CROSSWORD', nargs='+', type=argparse.FileType('rb'), help="Input files")
    args = argparser.parse_args()
    
    if args.output:
        output_filename = args.output
    elif args.format == 'svg':
        output_filename = 'out.svg'
    else:
        output_filename = 'out.html'
    cws = []
    for cw_file in args.CROSSWORD:
        print(f'Reading {cw_file.name}')
        cws.append(parse_crossword(cw_file))

    print(f'Writing {output_filename}')
    f = open(output_filename, 'w')
    if args.format != 'svg':
        format_to_class = { 'a4': 'A4', 'a5two': 'A5', 'a5two-grids': 'A5'}
        page_class = format_to_class[args.format]
        f.write('<meta charset="UTF-8">') 
        write_style(f, page_class)
        f.write(f'''
        <body class="{page_class}">
        ''')

    match args.format:
        case 'a4':
            write_a4_one_page(f, cws, args.page_num, args.solution)
        case 'a5two':
            write_a5_two_page(f, cws, args.page_num, args.solution)
        case 'a5two-grids':
            write_a5_two_grid_page(f, cws, args.page_num, args.solution)
        case 'svg':
            f.write(svg_grid(cws[0].grid, args.solution, svg_file=True))
    if format != 'svg':
        f.write('</body>')
    f.close()
    print('Done')

main()