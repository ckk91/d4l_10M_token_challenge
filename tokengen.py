"""
Generating 10M tokens and writing them to disk, newline-delimited.
The tokens are of format /[a-z]{7}/.

This file is part of the D4L 10M token challenge.

:author:  Christoph Koch
:date:  2021-06-23
"""
import numpy as np


def generate_tokens():
    """Generates a tokens.csv file with 10M newline delimited tokens."""
    TOTAL_CHARS = 10_000_000 * 7
    CHUNK_SIZE = TOTAL_CHARS // 100

    ASCII_a = 97
    ASCII_z = 122
    ASCII_newline = 10

    # writing out as a binary file to not deal with encoding
    # in this case the resulting list is logically equivalent to a single column csv
    with open("tokens.csv", "wb") as f:
        count = 1

        while count * CHUNK_SIZE <= TOTAL_CHARS:  #  keep constant memory use
            d = np.random.randint(ASCII_a, ASCII_z + 1, size=CHUNK_SIZE)

            # add in a \n every 8 chars
            d = np.insert(d, range(7, len(d), 7), ASCII_newline)
            d = np.append(d, ASCII_newline)  # last newline

            # coerce integer to C Char, we have letters now.
            d.astype("ubyte").tofile(f)
            count += 1


if __name__ == "__main__":
    # this will only get executed when the file is being used as
    # a standalone script
    import time
    import reader

    gen_start = time.time()
    generate_tokens()
    gen_stop = time.time()

    read_start = time.time()
    reader.main()
    read_stop = time.time()

    print(
        f"""
    generation: {gen_stop - gen_start} seconds
    reading: {read_stop - read_start} seconds
    total: {(gen_stop-gen_start) + (read_stop-read_start)}
    """
    )
