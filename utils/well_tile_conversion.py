"""Utility module for help converting between well and tile.

This conversion is relevant for 96-format plates only.

    - Well, e.g. 'A01', is the canonical way of referring to a position
      in a plate. This is what is used throughout the database.

    - Tile, e.g. 'Tile000001', is the prefix with which the microscope
      software Surveyor saves our images (as Tile000001.bmp). The same
      prefix has conventionally been used for the corresponding DevStaR
      output (Tile000001res.png and Tile000001cnt.txt), as well as lower
      resolution copies of the images.

While the legacy database was inconsistent in using 'well' in some
tables and 'tile' in other tables, the new database uses 'well'
consistently. However, translating to tiles is still needed, to
access the image and DevStaR filenames, and to sync the legacy
database to this database.

The helpers in this module refer to the "snake" order in which images
are generated by our scopes. Our snopes snake back and forth each row,
like this:

    A01, A02, ..., A12, B12, B11, ..., B01, C01, ...

"""

import re

from constants import ROWS_96, COLS_96
from wells import get_well_name

BACKWARDS_ROWS = 'BDFH'
NUM_COLS_96 = len(COLS_96)


def well_to_tile(well):
    """Convert a well (e.g. 'B05') to a tile (e.g. 'Tile000020')."""
    if not re.match('[A-H]\d\d?', well):
        raise ValueError('{} is an improper well string'.format(well))

    index = _well_to_index(well)
    return _index_to_tile(index)


def tile_to_well(tile):
    """Convert a tile (e.g. 'Tile000020') to a well (e.g. 'B05')."""
    if not re.match('Tile0000\d\d.*', tile):
        raise ValueError('{} is an improper tile string'.format(tile))

    index = _tile_to_index(tile)
    return _index_to_well(index)


def _well_to_index(well):
    """Convert well to 0-indexed snake order (see module docstring)."""
    row = well[0]
    column = int(well[1:])

    if column < 1 or column > NUM_COLS_96:
        raise ValueError('Well {} number outside acceptable range'
                         .format(well))

    position_from_left = column - 1

    min_row_index = (ord(row) - 65) * NUM_COLS_96

    if row in BACKWARDS_ROWS:
        index_in_row = NUM_COLS_96 - 1 - position_from_left
    else:
        index_in_row = position_from_left

    overall_index = min_row_index + index_in_row
    return overall_index


def _index_to_tile(index):
    """Convert 0-indexed snake order (see module docstring) to tile."""
    return 'Tile0000{}'.format(str(index + 1).zfill(2))


def _tile_to_index(tile):
    """Convert tile to 0-indexed snake order (see module docstring)."""
    tile_number = int(tile[8:10])

    if tile_number < 1 or tile_number > 96:
        raise ValueError('Tile {} number outside acceptable range'
                         .format(tile))

    index = tile_number - 1
    return index


def _index_to_well(index):
    """Convert 0-indexed snake order (see module docstring) to well."""
    row = ROWS_96[index / NUM_COLS_96]
    index_in_row = index % NUM_COLS_96

    if row in BACKWARDS_ROWS:
        position_from_left = NUM_COLS_96 - 1 - index_in_row
    else:
        position_from_left = index_in_row

    column = position_from_left + 1
    return get_well_name(row, column)
