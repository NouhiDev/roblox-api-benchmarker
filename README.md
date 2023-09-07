# Roblox API Benchmarker
Benchmarks Roblox API endpoints with adjustable parameters.

### Parameters:
- batch_size (How many Universe IDs should be requested in each url)
- concurrent_requests (How many concurrent requests should be performed each iteration)
- sample_size (How many iterations should be run to calculate the average)
- rate_limit_delay (Amount of seconds that have to pass before returning the data)
- generate_benchmark_report (Whether to generate and save a detailed benchmark report or not)

## Installation:
1. Clone the repository
2. Install all non-default modules (tqdm and httpx[http2])
3. Adjust the parameters at the top of the benchmark.py file
4. Run the script using a Python Interpreter
