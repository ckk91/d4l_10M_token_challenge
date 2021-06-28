# Data4Life 10M Tokens Challenge
Solution for the Data4Life coding challenge. This solution was created by Christoph Koch, on 2021-06-23. This document consists of an explanation on how to reproduce results and the underlying design decisions. Additional technical details are documented in-place in the source.

- [Data4Life 10M Tokens Challenge](#data4life-10m-tokens-challenge)
  - [Technical Requirements](#technical-requirements)
  - [How To Run](#how-to-run)
  - [How To Contribute](#how-to-contribute)
  - [Solution Stack](#solution-stack)
    - [Programming Language: Python](#programming-language-python)
    - [Database: PostgreSQL](#database-postgresql)
  - [Approach / Design Decisions](#approach--design-decisions)
    - [Token Generator](#token-generator)
    - [Token Reader](#token-reader)
    - [Frequency Table](#frequency-table)
    - [Database Layout](#database-layout)
    - [Database Schema](#database-schema)
  - [Conclusion](#conclusion)


## Technical Requirements
- Python >= 3.6
- 3rd-party libs: numpy, psycopg2-binary
- Tested under Ubuntu 20.04 LTS (WSL2, Win 10, Consumer grade laptop), results might vary on bare metal environments.
- Postgres Docker container from https://hub.docker.com/_/postgres with ports exposed to localhost

## How To Run
1. install dependencies via `pip install numpy, psycopg2-binary`
2. spin up the postgres container
3. run `python tokengen.py` or `python reader.py`, either will produce the same results. The modules themselves are import safe. The frequency table will be in the working directory.

## How To Contribute
- Memory profiler: `pip install memory-profiler`
- Code formatter: `pip install black`

## Solution Stack
### Programming Language: Python
Python was chosen because of personal preference also its default packages and large ecosystem serve as a fast prototyping environment. It is not the fastest language on the block by default, but the results are good-enough to provide tangible results. Also, implementation speed matters.

### Database: PostgreSQL
Force of habit at this point, to be honest.

## Approach / Design Decisions
Initial requirements gathering via email had shown that there should be a focus on execution speed, additionally to memory and network efficiency. Subsequent decisions were influenced by this, while weighing against clean code practices. Listed below are results of post-profiling and code optimization. The optimization itself was an iterative process, startign from a working minimum viable solution.

- Time: about 16-20s
- Memory: about 850 MiB
- Network: Good enough to not congest

(At this point I would like to stress that this result is not something that should ever see the light of a production environment, but this is besides the point of this exercise.)

### Token Generator
The initial naive approach of generating the tokens via on-board python tools were discarded after first profiling results. While working perfectly, the run time of about 25 seconds and general memory use of around 1GiB was deemed to be not sufficient.

To work around this, I exploited the fact that modern Unicode also uses legacy ASCII character codes. These can be generated as integers and coerced into the correct data type to be interpreted as a string. For this I chose the numpy library, because of its performant array and random implementations. The optimization after profiling showed a runtime of about 2 seconds and a maximum memory use of 80 MiB.

### Token Reader
The token reader uses a chunked stream-processing approach, to avoid having to read in the whole token file at once, and to avoid in-memory sorting, list deduplication and uneccessary copying around. The chunking ensures a constant memory utilization (except for the frequency table, see down below).

Ensuring uniqueness of the tokens is done by exploiting the frequency dictionary count: If the element exists in the table,
it's already been processed and can be skipped. That way we avoid the calculations of a deduplication step by. As such the time needed for deduplication is a combination of the constant access time of the table and the total length of the token list.

The insertion of the tokens is solved by faking a csv upload to the database over network. This upload is also size-limited, to not congest the network. This approach was directly chosen for performance reasons.

Originally, a 3rd-party ORM package was used, but I decided against it in favor of hand-rolling SQL because of performance reasons after profiling, despite potential security implications.

### Frequency Table
The approach I chose here is a simple Python `defaultdict`. It behaves the same in terms of memory use, access time and interfaces like the normal `dict` and also helps cutting down on error-prone boilerplate checking code. Post-profiling, it is the only component left growing linearly in terms of memory use. I chose to mitigate some of that memory growth by using bytearrays as token keys, since these are smaller than python strings. It is a micro-optimization, but it helped pushing memory utilization below the 1GiB range. 

The resulting frequency table is saved to the current working directory as a headless csv file `frequency_table.csv` for further processing.

The solution is good-enough for the current use case, but would need to be reengineered for larger files.

> Discarded approaches, for the record: As part of the target token table (wrong use case for statistics), In-memory sqlite-db (too slow, too large), builtin Counter(too slow, too large), hand-rolled trie (slow, large), external trie-package as a c module (slow, but log space complexity, could in theory work), pandas data tables(size issues, speed issues), offloading to shell uniq/sort(memory issues)

### Database Layout
The used table consists of a single VARCHAR column, restricted to the token length. I decided against using the token as a primary key or checking for uniqueness, because performance dropped quite a bit when using them. This on the other hand invites data inconsistencies, since we now need to trust that the code providing the data is doing the right things (i.e. deduplication).

### Database Schema
I decided against creating a DB schema, because a single table was enough for the solution. The SQL for creating the table is below.

```SQL
DROP TABLE IF EXISTS tokens; 
CREATE TABLE tokens (
    token VARCHAR(7) NOT NULL 
);
```

## Conclusion
The challenge was quite interesting because when I started profiling my inital solution in terms of memory use and execution time, I noticed that I moved further and further from good engineering practice and clean, maintainable code. The resulting code from this profiling was definitely unexpected in this form and I needed to get clever at some points. I would like to thank you for this challenge, it was fun!
