"""Pilot P2a: is the detector needed? (stage2/p2a/P2a_PROTOCOL.md, fixed before this run)

Simulates, with the frozen v1.0 simulator, FIR+fast+SR (frozen E6 logic, copied verbatim and
checked against fir_extensions.run_scenario in the same run) and the new rival Continuous+SR
(re-tune every window, no detector, same ski-rental rule). Records tuner invocations so that the
tuner term of total time can be charged at analysis with the C4 times measured in P3.

Usage (repository root): python stage2/p2a/p2a_run.py --data embeddings/flickr_28k_4col --seeds 0 1 ... 29
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def import_frozen(out):
    cwd = os.getcwd(); os.chdir(out)                      # fir_mint_v4 creates its OUT folder on import
    sys.path.insert(0, str(ROOT / "code_frozen"))
    import fir_mint_v4 as F, fir_baselines as B, fir_extensions as E
    os.chdir(cwd)
    return F, B, E


def run_scenario(F, E, est, bm, name, C, seed, si, qw_levels, k_fast):
    srng = np.random.default_rng([seed, si, 0])          # same streams as fir_baselines / E6
    dists, onset = F.scenario(name, C, srng)
    T = len(dists)
    wrng = np.random.default_rng([seed, si, 1])
    windows = [F.sample_window(p, wrng) for p in dists]
    init_win = F.sample_window(dists[0], np.random.default_rng([seed, si, 2]))
    init, *_ = F.full_retune(est, init_win)
    jcost = lambda cfg, t: est.score(dists[t], cfg)

    def summarize(pol, cfgs, builds_list, rts, calls, inv, qw=None):
        costs = [jcost(cfgs[t], t)[1] for t in range(T)]
        viols = [jcost(cfgs[t], t)[0] for t in range(T)]
        build_s = float(sum(bm(len(i)) for b in builds_list for i in b))
        return dict(scenario=name, seed=seed, policy=pol, qw=qw, onset=onset, post_cost=float(np.mean(costs[onset:])),
                    viol_mass=float(np.mean(viols)), switches=len(rts), false_switches=sum(t < onset for t in rts),
                    builds=int(sum(len(b) for b in builds_list)), build_s=build_s, whatif=int(calls),
                    tuner_invocations=int(inv), query_s={str(q): float(sum(costs) * q / 1000.0) for q in qw_levels},
                    total_s_no_tuner={str(q): float(sum(costs) * q / 1000.0 + build_s) for q in qw_levels})

    rows = [summarize("Static", [init] * T, [], [], 0, 0)]
    mk_frozen = lambda: F.Detector(init_win, np.random.default_rng([seed, si, 3]))
    mk_fast = lambda: E.FastDetector(init_win, np.random.default_rng([seed, si, 3]), F.WIN, 3.0, k_fast)

    def detector_loop(detector):
        cfg, cfgs, builds, rts, calls, inv = init, [], [], [], 0, 0
        for t in range(T):
            cfgs.append(cfg)
            p = detector.observe(windows[t])
            if p is None:
                continue
            new, _, k, _ = F.fir_retune(est, p, cfg); calls += k; inv += 1
            detector.reset(p)
            if new != cfg:
                builds.append(new - cfg); rts.append(t); cfg = new
        return cfgs, builds, rts, calls, inv
    rows.append(summarize("FIR+detector", *detector_loop(mk_frozen())))

    cfg, cfgs, builds, rts, calls = init, [], [], [], 0     # Continuous FIR, immediate switch
    for t in range(T):
        cfgs.append(cfg)
        new, _, kk, _ = F.fir_retune(est, windows[t], cfg); calls += kk
        if new != cfg:
            builds.append(new - cfg); rts.append(t); cfg = new
    rows.append(summarize("Continuous FIR", cfgs, builds, rts, calls, T))

    def rent_step(state, w, qw):
        """Frozen E6 ski-rental step (fir_extensions.run_scenario, ski_rental body)."""
        cfg, prop, rent, idle = state["cfg"], state["prop"], state["rent"], state["idle"]
        before = est.calls
        vc, cc = est.score(w, cfg); vn, cn = est.score(w, prop)
        state["calls"] += est.calls - before
        excess = qw * (cc - cn) / 1000.0
        if excess > 0:
            rent += excess; idle = 0
        else:
            idle += 1
        build = sum(bm(len(i)) for i in prop - cfg)
        if (vc > 0 and vn == 0) or rent >= build:
            return True, dict(state, prop=None, rent=0.0, idle=0)
        if idle >= 2:
            return False, dict(state, prop=None, rent=0.0, idle=0)
        return False, dict(state, rent=rent, idle=idle)

    def fir_fast_sr(qw):                                    # verbatim logic of E6 FIR+fast+SR
        det = mk_fast()
        st = dict(cfg=init, prop=None, rent=0.0, idle=0, calls=0)
        cfgs, builds, rts, inv = [], [], [], 0
        for t in range(T):
            cfgs.append(st["cfg"])
            w = windows[t]
            p = det.observe(w)
            if p is not None:
                new, _, kk, _ = F.fir_retune(est, p, st["cfg"]); st["calls"] += kk; inv += 1
                det.reset(p)
                st.update(prop=(new if new != st["cfg"] else None), rent=0.0, idle=0)
            if st["prop"] is None:
                continue
            prop = st["prop"]
            sw, st = rent_step(st, w, qw)
            if sw:
                builds.append(prop - st["cfg"]); rts.append(t); st["cfg"] = prop
        return cfgs, builds, rts, st["calls"], inv

    def continuous_sr(qw):                                  # new rival (protocol: rent kept per proposal)
        st = dict(cfg=init, prop=None, rent=0.0, idle=0, calls=0)
        cfgs, builds, rts = [], [], []
        for t in range(T):
            cfgs.append(st["cfg"])
            w = windows[t]
            new, _, kk, _ = F.fir_retune(est, w, st["cfg"]); st["calls"] += kk
            cand = new if new != st["cfg"] else None
            if cand != st["prop"]:
                st.update(prop=cand, rent=0.0, idle=0)
            if st["prop"] is None:
                continue
            prop = st["prop"]
            sw, st = rent_step(st, w, qw)
            if sw:
                builds.append(prop - st["cfg"]); rts.append(t); st["cfg"] = prop
        return cfgs, builds, rts, st["calls"], T

    for qw in qw_levels:
        rows.append(summarize("FIR+fast+SR", *fir_fast_sr(qw), qw=qw))
        rows.append(summarize("Continuous+SR", *continuous_sr(qw), qw=qw))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--out", default="results/p2a")
    ap.add_argument("--seeds", type=int, nargs="+", default=list(range(30)))
    ap.add_argument("--check_seeds", type=int, default=2, help="seeds on which rows are checked against frozen E6")
    a = ap.parse_args()
    folder = (ROOT / a.data).resolve(); out = (ROOT / a.out / folder.name).resolve(); out.mkdir(parents=True, exist_ok=True)
    F, B, E = import_frozen(out)
    B.check_api()
    C = F.load_real(str(folder))
    rows, checks, t0 = [], [], time.time()
    for seed in a.seeds:
        rng = np.random.default_rng(500 + seed)            # same as fir_baselines.py / E6
        store = F.get_store(F.gen_data(3, rng))
        est = F.Estimator(store, rng, n=80)
        bm = E.build_model(store)
        for si, sc in enumerate(E.SCENARIOS):
            r = run_scenario(F, E, est, bm, sc, C, seed, si, E.QW_LEVELS, E.K_FAST)
            rows += r
            if seed in a.seeds[:a.check_seeds]:             # verbatim check against the frozen E6 code
                ref = E.run_scenario(est, bm, sc, C, seed, si, E.QW_LEVELS, E.HORIZON, E.K_FAST)
                for qw in E.QW_LEVELS:
                    mine = next(x for x in r if x["policy"] == "FIR+fast+SR" and x["qw"] == qw)
                    theirs = next(x for x in ref if x["policy"] == "FIR+fast+SR" and x["qw"] == qw)
                    ok = all(abs(mine["total_s_no_tuner"][k] - theirs["total_s"][k]) < 1e-9 for k in theirs["total_s"])
                    checks.append(dict(seed=seed, scenario=sc, qw=qw, equal=bool(ok)))
                    assert ok, f"FIR+fast+SR differs from frozen E6: seed {seed} {sc} qw {qw}"
        print(f"[P2a seed {seed}] done ({time.time() - t0:.0f}s)", flush=True)
        json.dump(dict(rows=rows, frozen_checks=checks), open(out / "p2a_partial.json", "w"))
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    json.dump(dict(rows=rows, frozen_checks=checks, provenance=dict(commit=commit, pbs_job=os.environ.get("PBS_JOBID"),
              seeds=a.seeds, label="estimated (query time); measured (build model)", elapsed_s=time.time() - t0)),
              open(out / "p2a.json", "w"))
    print("done", len(rows), "rows;", sum(c["equal"] for c in checks), "of", len(checks), "frozen checks equal")


if __name__ == "__main__":
    main()
