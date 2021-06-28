# D4L 10M Token Code Challenge
Solution I produced for the D4L 10 Million token challenge. A bit of an unorthodox solution was needed to fulfill the requirements. For more details take a look at the [DOCUMENTATION.md](./DOCUMENTATION.md) file. Ideas from this solution should probably kept away from production use.

## Task
Create 10 million tokens of the form `/[a-z]{7}/`, save them as a list and pump them as fast as possible into a relational database. Also produce a frequency table of duplicate tokens. Also, the tokens in the db should be unique.

## Requirements and Constraints
- Should be fast and efficient in terms of resource usage (time, memory, network, cpu)

## Result
10 million tokens produced, saved, dumped and frequency-table'd in about 16.42 seconds @ 850 MiB of memory use on a 2019 Vivobook S15 (running Win10 (running Ubuntu@WSL2 (running Docker))). Profiled with `mprof`. See screenshot of profiling results (the large jumps are the Python memory manager kicking in):

![Profiling results of mprof](./mprof.png?raw=true "Profiling Results")

## Post-Submission
- Created [tokengen_but_even_faster.py](./tokengen_but_even_faster.py). Turns out that with the approach in there you can push the token generation into the sub-second range.

## TO DO
- [ ] click and run docker environment
- [ ] integration test
- [ ] Makefile w/ profiler
- [ ] How to run / execute. Refer to DOCUMENTATION.md for the time being
