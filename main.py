import argparse, asyncio, json, logging, os, signal, sys, time
from pathlib import Path

from yaml import safe_load as yaml_load
from kasa import Discover, Credentials

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("p110")

async def _connect(host, email, pwd):
    d = await Discover.discover_single(host, credentials=Credentials(email, pwd), port=80)
    await d.update()
    return d

async def _read(dev):
    await dev.update()
    u = dev.modules["Energy"].data["get_energy_usage"]
    return dict(today_m=u.get("today_runtime",0), month_m=u.get("month_runtime",0),
                today_wh=u.get("today_energy",0), month_wh=u.get("month_energy",0),
                w=round(u.get("current_power",0)/1000,1))

def _load_config(path_or_env):
    if os.getenv("DEVICES"):
        cfg = {}
        for p in os.getenv("DEVICES").split(","):
            if ":" in p:
                k, v = p.split(":", 1)
                cfg[k.strip()] = v.strip()
        return cfg
    path = Path(path_or_env)
    if path.suffix == ".json":
        return json.loads(path.read_text())
    return yaml_load(path.read_text())["devices"]

async def _main(args):
    cfg = _load_config(args.config)
    out = Path(args.out) if args.out else None
    shutdown = False

    def _stop(*_):
        nonlocal shutdown; shutdown = True
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    log.info("connecting %d device(s)", len(cfg))
    devs = {}
    for room, ip in cfg.items():
        try:
            devs[room] = (ip, await _connect(ip, args.email, args.password))
            log.info("  %s OK (%s)", room, devs[room][1].model)
        except Exception:
            log.exception("  %s FAIL", room)

    if not devs:
        log.error("no devices connected"); return

    log.info("polling every %ss", args.interval)
    while not shutdown:
        rooms, futures = list(devs.keys()), []
        for room in rooms:
            ip, dev = devs[room]
            futures.append(_read(dev))
        results = await asyncio.gather(*futures, return_exceptions=True)

        for room, result in zip(rooms, results):
            ip = devs[room][0]
            if isinstance(result, Exception):
                log.warning("%s failed, reconnecting", room)
                try:
                    devs[room] = (ip, await _connect(ip, args.email, args.password))
                    log.info("  %s reconnected", room)
                except Exception:
                    log.exception("  %s reconnect FAIL", room)
                continue
            d = result
            line = json.dumps({"ts": time.time(), "room": room, "ip": ip,
                               "today_m": d["today_m"], "month_m": d["month_m"],
                               "today_wh": d["today_wh"], "month_wh": d["month_wh"],
                               "w": d["w"]})
            if out is not None:
                out.write_text(line + "\n") if args.once else _append(out, line)
            log.info("%s: %sW %sWh", room, d["w"], d["today_wh"])

        if args.once:
            break
        await asyncio.sleep(args.interval)

    for _, (_, dev) in devs.items():
        try:
            await dev.disconnect()
        except Exception:
            pass
    log.info("stopped")

def _append(path, line):
    with open(path, "a") as f:
        f.write(line + "\n")

def main():
    p = argparse.ArgumentParser(description="TP-Link Tapo P110 energy logger")
    p.add_argument("--email", default=os.getenv("TAPO_EMAIL", os.getenv("TAPO_USER_EMAIL")))
    p.add_argument("--password", default=os.getenv("TAPO_PASSWORD", os.getenv("TAPO_USER_PASSWORD")))
    p.add_argument("--config", default="tapo.yaml")
    p.add_argument("--out", default=None, help="JSON output file")
    p.add_argument("--interval", default=60, type=int)
    p.add_argument("--once", action="store_true", help="query once and exit")
    args = p.parse_args()
    if not args.email or not args.password:
        p.error("--email and --password required (or set TAPO_EMAIL/TAPO_PASSWORD env vars)")
    try:
        asyncio.run(_main(args))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
