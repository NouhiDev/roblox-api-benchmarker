import asyncio
import time
from tqdm import tqdm
import shutil
import os
import httpx
from datetime import datetime
import json

'''
Roblox API Endpoint Benchmarker v0.0.1
by nouhidev
'''

# ----- [ Benchmarking Parameters ] -----
BASE_URL = "https://games.roblox.com/v1/games?universeIds="

# UIDs/Url (Default: 100)
batch_size = 100

# Concurrent Requests (Default: 100)
concurrent_requests = 100

# Sample size (Default: 10)
sample_size = 100

# Amount of seconds that have to be passed before returning the data (Default: 3)
rate_limit_delay = 3

# Whether to generate a benchmark report or not (Default: True)
generate_benchmark_report = True

# ----- [ ----------------------- ] -----

'''
Only change settings below this point if
you know what you're doing.
'''

# -------- [ Benchmark Output ] ---------

BENCHMARK_REPORT_PREFIX = "benchmark_"

BENCHMARK_OUTPUT_PATH = "benchmark-results"

# -------- [ Benchmark Helpers ] --------

# Stores the UIDs/s --> used for calculating the average UIDs/s
uids_per_second_saved = []

# Stores the UIDs/s after gathering --> used for calculating the average UIDs/s after gathering
gathering_uids_per_second_saved = []

# Stores the average response time --> used for calculating the average response time
response_time_saved = []

# Stores the average gather time --> used for calculating the average gather time
gather_time_saved = []

# Stores how many UIDs were lost due to rate limiting
loss_count = 0 

# Stores how many UIDs were lost due to httpx request errors
httpx_lost_count = 0

# Stores how many times rate limiting was suspected due to high response times
suspected_rate_limit_count = 0

# Stores how many times rate limiting has been confirmed
confirmed_rate_limit_count = 0

# -------- [ Requests Managing ] --------

last_request_time = 0
response_time_threshold = 0
average_response_time = 0
response_time_count = 0
response_time_threshold_multiplier = 2
previous_uids_per_second = 0
MAX_HTTPX_TIMEOUT = 20

# ----- [ ----------------------- ] -----

# ------------- [ Other ] ---------------

progress_bar = None
terminal_width = shutil.get_terminal_size().columns
equals_line = "=" * terminal_width

# ----- [ ----------------------- ] -----

# -------- [ ANSI Escape Codes ] --------

GOLDEN = '\033[93m'
GRAY = '\033[90m'
CYAN = '\033[96m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
RESET = '\033[0m'

# ----- [ ----------------------- ] -----

async def fetch_uids(session, batch_start, batch_end):
    global last_request_time, rate_limit_delay, suspected_rate_limit_count, average_response_time, response_time_count, concurrent_requests, loss_count, response_time_saved, confirmed_rate_limit_count, httpx_lost_count, response_time_threshold, response_time_threshold_multiplier

    universe_ids = ",".join(str(i) for i in range(batch_start, batch_end))
    url = BASE_URL + universe_ids

    start_time = time.time()

    try:
        response = await session.get(url, timeout=MAX_HTTPX_TIMEOUT)
    except Exception as e:
        httpx_lost_count += batch_size

    response_time = time.time() - start_time
    response_time_saved.append(response_time)

    average_response_time = (average_response_time * response_time_count + response_time) / (response_time_count + 1)
    response_time_count += 1

    response_time_threshold = average_response_time * response_time_threshold_multiplier

    try:
        if response.status_code == 503:
            loss_count += batch_size
            confirmed_rate_limit_count += 1
    except:
        pass

    if response_time > response_time_threshold:
        suspected_rate_limit_count += 1

    progress_bar.update(1)

    if time.time() - last_request_time < rate_limit_delay:
        await asyncio.sleep(rate_limit_delay - (time.time() - last_request_time))

    last_request_time = time.time()

    try:
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        return []


async def main():
    global gather_time_saved, concurrent_requests, progress_bar, start_id, suspected_rate_limit_count, rate_limit_delay, average_response_time, response_time_threshold_multiplier, previous_uids_per_second, batch_size, rate_limit_delay, httpx_lost_count, confirmed_rate_limit_count

    print(f"{UNDERLINE}{GOLDEN}Benchmarking Roblox API Endpoint{RESET}:")
    print(f"{GRAY}- Targetting {BASE_URL}{RESET}")
    print(f"{GRAY}- {batch_size} UIDs/Url at {concurrent_requests} cReqs{RESET}")
    print(f"{GRAY}- Taking {sample_size} samples ({(batch_size*concurrent_requests*sample_size):,} total UIDs){RESET}")
    print(f"{GRAY}- Waiting at least {rate_limit_delay} seconds before returning data{RESET}")

    await asyncio.sleep(2)

    benchmark_time = time.time()

    async with httpx.AsyncClient(http2=True, limits=httpx.Limits(max_connections=None, max_keepalive_connections=0)) as session:
        for current_sample in range(sample_size):
            tasks = []

            start_time = time.time()

            start_id = 0

            progress_bar = tqdm(total=concurrent_requests, unit="req", desc=f"Running Sample #{(current_sample+1):02} with Batch Size of {(batch_size*concurrent_requests):,}")

            for _ in range(concurrent_requests):
                batch_end = start_id + batch_size
                tasks.append(fetch_uids(session, batch_start=start_id, batch_end=batch_end))
                start_id += batch_size

            await asyncio.gather(*tasks)

            progress_bar.close()

            elapsed_time = time.time() - start_time

            gather_time_saved.append(elapsed_time)

            uids_per_second = (batch_size*concurrent_requests)/elapsed_time

            gathering_uids_per_second_saved.append(uids_per_second)

            uids_per_second_saved.append((batch_size*concurrent_requests)/average_response_time)

        # Calculate average UID/s
        average_uids_per_second = round(sum(uids_per_second_saved) / len(uids_per_second_saved), 3)

        # Calculate average gather UID/s
        average_gathering_uids_per_second_saved = round(sum(gathering_uids_per_second_saved) / len(gathering_uids_per_second_saved), 3)

        # Calculate average response time
        average_response_time_calc = sum(response_time_saved) / len(response_time_saved)

        # Calculate average gather time
        average_gather_time = round(sum(gather_time_saved) / len(gather_time_saved), 3)

        print(f"{GRAY}{equals_line}{RESET}")
        print("Speed Results:")
        print(f"- Averaging {UNDERLINE}{average_gathering_uids_per_second_saved} UIDs/s{RESET} with an average gather time of {UNDERLINE}{round(average_gather_time, 2)} seconds{RESET}")
        print(f"- (Requests Only: Averaging {UNDERLINE}{average_uids_per_second} UIDs/s{RESET} with an average response time of {UNDERLINE}{round(average_response_time_calc, 2)} seconds{RESET})")
        print(f"- This speed is equal to {round(average_gathering_uids_per_second_saved*60, 3):,} UIDs/min, {round(average_gathering_uids_per_second_saved*60*60, 3):,} UIDs/h, {round(average_gathering_uids_per_second_saved*60*60*24, 3):,} UIDs/day,")
        print("Requests Results:")
        print(f"- Encountered an unusual response time {suspected_rate_limit_count} times")
        print(f"- Confirmed rate limiting {confirmed_rate_limit_count} times")
        print(f"- Lost {loss_count} UIDs ({round((loss_count/(batch_size*concurrent_requests*sample_size))*100, 2)}%) to rate limiting")
        print(f"- Lost {httpx_lost_count} UIDs to HTTPX errors")

        benchmark_time_elapsed = time.time() - benchmark_time

        print(f"This benchmark took {round(benchmark_time_elapsed, 2)} seconds")

        if generate_benchmark_report:
            # Create benchmark-results folder if it doen't exist
            if not os.path.exists(BENCHMARK_OUTPUT_PATH):
                os.makedirs(BENCHMARK_OUTPUT_PATH)
            
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            report_file_name = f"{BENCHMARK_REPORT_PREFIX}{current_time}.json"

            file_path = os.path.join(BENCHMARK_OUTPUT_PATH, report_file_name)

            data = {
                "target": BASE_URL,
                "batch_size": batch_size,
                "concurrent_requests": current_async_requests,
                "min_time_before_data_return": rate_limit_delay,
                "average_gather_speed": average_gathering_uids_per_second_saved,
                "average_gather_time": round(average_gather_time, 2),
                "average_requests_only_speed": average_uids_per_second,
                "average_requests_only_time": round(average_response_time_calc, 2),
                "unusual_response_time": suspected_rate_limit_count,
                "confirmed_rate_limit_count": confirmed_rate_limit_count,
                "uids_lost_to_rate_limiting": loss_count,
                "uids_lost_to_httpx_errors": loss_count,
            }

            with open(file_path, "w") as json_file:
                json.dump(data, json_file, indent=4)
            
            print(f"\n{CYAN}Saved detailed benchmark report to {file_path}.{RESET}")
       
if __name__ == "__main__":
    asyncio.run(main())