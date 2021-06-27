"""The token reader and DB writer part of the challenge.
This module also provides statistics on token dupes.

This file is part of the D4L 10M token challenge.

:author:  Christoph Koch
:date:  2021-06-23
"""
import csv

from collections import defaultdict
from io import BytesIO

import psycopg2 as psy


def init_db(pg_cur):
    """Setting up the DB."""
    pg_cur.execute(
        """
    DROP TABLE IF EXISTS tokens; 
    CREATE TABLE tokens (
        token VARCHAR(7) NOT NULL 
        );
    """
    )


def main():
    """The reader part of the d4l 10M token challenge."""
    # DB setup
    (pg_conn, pg_cur) = create_db_connection()
    init_db(pg_cur)

    try:  # making sure we really close the connection
        frequencies = pump_tokens_to_db(pg_cur)
    except:
        raise
    finally:
        pg_cur.close()
        pg_conn.close()

    write_frequency_table(frequencies)
    print("Please find the frequency table in frequency_table.csv of the working dir.")


def create_db_connection():
    """Connecting to a Postgres DB.

    Tested with the default container of https://hub.docker.com/_/postgres.
    The login credentials are the defaults of the container.
    """
    pg_conn = psy.connect(
        host="localhost",
        user="postgres",
        password="example",
    )
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()
    return (pg_conn, pg_cur)


def pump_tokens_to_db(pg_cur):
    """Reading in the token.csv file and writing its deduplicated contents to the db.

    This is accomplished by buffering a given amount of tokens, as a trade-off
    between memory usage and uploading speed. Also constructs the frequency table on the fly.
    """
    TOKEN_AMOUNT = 100_000
    CHUNK_SIZE = 8 * TOKEN_AMOUNT  # 7 chars + newline

    frequencies = defaultdict(int)
    token_buffer = []
    chunk_count = 1

    # We're working with bytestrings here, because they use less memory
    # compared to normal utf-8 strings. This little `b` shaves off around
    # 300 MiB.
    with open("tokens.csv", "rb") as f:
        data = f.read(chunk_count * CHUNK_SIZE)

        while data:
            amount = data.split(b"\n")

            for entry in amount:
                if entry == b"":  # filtering out empty strings
                    continue

                if entry not in frequencies:  # on-the-fly deduplication
                    token_buffer.append(entry)

                frequencies[entry] += 1

                if len(token_buffer) >= TOKEN_AMOUNT:
                    write_buffer_to_db(CHUNK_SIZE, pg_cur, token_buffer)
                    token_buffer = []

            # an additional write to db, in case
            # we have a buffer < TOKEN_AMOUNT left over
            write_buffer_to_db(CHUNK_SIZE, pg_cur, token_buffer)
            token_buffer = []

            data = f.read(chunk_count * CHUNK_SIZE)

    return frequencies


def write_buffer_to_db(CHUNK_SIZE, pg_cur, token_buffer):
    """Writing the token list to the DB by simulating a csv read in.

    A bit unintutive, but the most efficient variant I was able to
    find for this controlled environment. The csv is constructed in-memory
    to avoid disk latency. It is also created freshly on invocation to avoid
    accidentally writing garbage that was left from previous calls.

    (In this case the bytes buffer content list is logically equivalent to a single column csv)
    """
    fp_new = BytesIO(b"\n".join(token_buffer) + b"\n")

    # For the record: The upload size is not a power of two.
    # The source code of psycopg2 didn't give any notice that it could be an issue.
    pg_cur.copy_from(fp_new, "tokens", size=CHUNK_SIZE)


def write_frequency_table(frequencies):
    """Creates the requested frequency table as a headerless csv file on disk."""
    with open("frequency_table.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(
            ((k.decode("utf-8"), v) for k, v in frequencies.items() if v > 1)
        )


if __name__ == "__main__":
    # this will only get executed when the file is being used as
    # a standalone script
    import time
    import tokengen

    gen_start = time.time()
    tokengen.generate_tokens()
    gen_stop = time.time()

    read_start = time.time()
    main()
    read_stop = time.time()

    print(
        f"""
    generation: {gen_stop - gen_start} seconds
    reading: {read_stop - read_start} seconds
    total: {(gen_stop-gen_start) + (read_stop-read_start)}
    """
    )
