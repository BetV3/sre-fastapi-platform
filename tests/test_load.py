import argparse
import asyncio
import json as jsonlib
import time
from collections import Counter
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

import aiohttp


def percentile(sorted_vals: List[float], p: float) -> float:
    """Linear interpolation percentile (p in [0, 100]). Expects sorted list."""
    if not sorted_vals:
        return float("nan")
    if p <= 0:
        return sorted_vals[0]
    if p >= 100:
        return sorted_vals[-1]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if c == f:
        return sorted_vals[f]
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return d0 + d1


@dataclass
class WorkerResult:
    latencies_ms: List[float]
    statuses: Counter
    errors: Counter
    requests: int


async def worker_duration(
    wid: int,
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    headers: Dict[str, str],
    data: Optional[bytes],
    json_body: Optional[Any],
    timeout_s: float,
    deadline: float,
) -> WorkerResult:
    latencies: List[float] = []
    statuses = Counter()
    errors = Counter()
    reqs = 0

    while time.perf_counter() < deadline:
        start = time.perf_counter()
        try:
            async with session.request(
                method,
                url,
                headers=headers,
                data=data,
                json=json_body,
                timeout=aiohttp.ClientTimeout(total=timeout_s),
            ) as resp:
                # Read the body so the connection can be cleanly reused
                await resp.read()
                statuses[resp.status] += 1
        except asyncio.TimeoutError:
            errors["timeout"] += 1
        except aiohttp.ClientError as e:
            errors[type(e).__name__] += 1
        except Exception as e:
            errors[type(e).__name__] += 1
        else:
            reqs += 1
            latencies.append((time.perf_counter() - start) * 1000.0)

    return WorkerResult(latencies, statuses, errors, reqs)


async def worker_total(
    wid: int,
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    headers: Dict[str, str],
    data: Optional[bytes],
    json_body: Optional[Any],
    timeout_s: float,
    queue: asyncio.Queue,
) -> WorkerResult:
    latencies: List[float] = []
    statuses = Counter()
    errors = Counter()
    reqs = 0

    while True:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        start = time.perf_counter()
        try:
            async with session.request(
                method,
                url,
                headers=headers,
                data=data,
                json=json_body,
                timeout=aiohttp.ClientTimeout(total=timeout_s),
            ) as resp:
                await resp.read()
                statuses[resp.status] += 1
        except asyncio.TimeoutError:
            errors["timeout"] += 1
        except aiohttp.ClientError as e:
            errors[type(e).__name__] += 1
        except Exception as e:
            errors[type(e).__name__] += 1
        else:
            reqs += 1
            latencies.append((time.perf_counter() - start) * 1000.0)
        finally:
            queue.task_done()

    return WorkerResult(latencies, statuses, errors, reqs)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="Target URL (e.g. http://127.0.0.1:8000/api/ping)")
    ap.add_argument("--method", default="GET", help="HTTP method (GET/POST/PUT/...)")
    ap.add_argument("--concurrency", type=int, default=50, help="Number of concurrent workers")
    ap.add_argument("--duration", type=float, default=0.0, help="Test duration in seconds (use this OR --requests)")
    ap.add_argument("--requests", type=int, default=0, help="Total requests (use this OR --duration)")
    ap.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout seconds")
    ap.add_argument("--header", action="append", default=[], help='Extra header, e.g. --header "Authorization: Bearer X"')
    ap.add_argument("--json", default=None, help='JSON body string for POST/PUT, e.g. \'{"x":1}\'')
    ap.add_argument("--data", default=None, help="Raw body string (sent as-is)")
    ap.add_argument("--no-keepalive", action="store_true", help="Disable keep-alive (usually slower)")
    args = ap.parse_args()

    if (args.duration <= 0) == (args.requests <= 0):
        raise SystemExit("Provide exactly one of --duration (seconds) OR --requests (total).")

    method = args.method.upper()

    headers: Dict[str, str] = {}
    for h in args.header:
        if ":" not in h:
            raise SystemExit(f"Bad header format: {h!r}. Use 'Key: Value'")
        k, v = h.split(":", 1)
        headers[k.strip()] = v.strip()

    json_body = None
    data_bytes: Optional[bytes] = None
    if args.json is not None:
        json_body = jsonlib.loads(args.json)
        headers.setdefault("Content-Type", "application/json")
    elif args.data is not None:
        data_bytes = args.data.encode("utf-8")

    # Connector settings: keep these aligned with your intended concurrency.
    connector = aiohttp.TCPConnector(
        limit=args.concurrency,
        limit_per_host=args.concurrency,
        ttl_dns_cache=300,
        force_close=args.no_keepalive,
        enable_cleanup_closed=True,
    )

    started = time.perf_counter()
    async with aiohttp.ClientSession(connector=connector) as session:
        if args.duration > 0:
            deadline = time.perf_counter() + args.duration
            tasks = [
                asyncio.create_task(
                    worker_duration(
                        wid=i,
                        session=session,
                        method=method,
                        url=args.url,
                        headers=headers,
                        data=data_bytes,
                        json_body=json_body,
                        timeout_s=args.timeout,
                        deadline=deadline,
                    )
                )
                for i in range(args.concurrency)
            ]
            results = await asyncio.gather(*tasks)
        else:
            q: asyncio.Queue = asyncio.Queue()
            for _ in range(args.requests):
                q.put_nowait(1)

            tasks = [
                asyncio.create_task(
                    worker_total(
                        wid=i,
                        session=session,
                        method=method,
                        url=args.url,
                        headers=headers,
                        data=data_bytes,
                        json_body=json_body,
                        timeout_s=args.timeout,
                        queue=q,
                    )
                )
                for i in range(args.concurrency)
            ]
            results = await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - started

    all_lat = []
    status_counts = Counter()
    error_counts = Counter()
    total_sent = 0

    for r in results:
        all_lat.extend(r.latencies_ms)
        status_counts.update(r.statuses)
        error_counts.update(r.errors)
        total_sent += r.requests + sum(r.errors.values())

    all_lat.sort()
    ok = sum(c for s, c in status_counts.items() if 200 <= s < 400)
    total_ok = sum(status_counts.values())
    total_err = sum(error_counts.values())
    total_done = total_ok + total_err
    rps = total_done / elapsed if elapsed > 0 else float("inf")

    print("\n=== aiohttp load test results ===")
    print(f"URL:         {args.url}")
    print(f"Method:      {method}")
    print(f"Concurrency: {args.concurrency}")
    if args.duration > 0:
        print(f"Duration:    {args.duration:.2f}s")
    else:
        print(f"Requests:    {args.requests}")
    print(f"Elapsed:     {elapsed:.3f}s")
    print(f"Completed:   {total_done} (ok={total_ok}, errors={total_err})")
    print(f"RPS:         {rps:.1f}")
    print(f"Statuses:    {dict(status_counts)}")
    if error_counts:
        print(f"Errors:      {dict(error_counts)}")

    if all_lat:
        print("\nLatency (ms):")
        print(f"  p50  {percentile(all_lat, 50):.2f}")
        print(f"  p90  {percentile(all_lat, 90):.2f}")
        print(f"  p95  {percentile(all_lat, 95):.2f}")
        print(f"  p99  {percentile(all_lat, 99):.2f}")
        print(f"  min  {all_lat[0]:.2f}")
        print(f"  max  {all_lat[-1]:.2f}")
        avg = sum(all_lat) / len(all_lat)
        print(f"  avg  {avg:.2f}")
    else:
        print("\nNo successful responses recorded (all timed out/errored).")


if __name__ == "__main__":
    asyncio.run(main())
