"""Build the acquisition work view without changing the authoritative ledger."""
import csv
import hashlib
import io
import json
import lzma
from collections import Counter
from pathlib import Path


def build():
    out = Path(__file__).resolve().parent
    root = out.parent
    current = json.loads((root / "CURRENT.json").read_text())
    source = root / current["remaining_fields"]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != current["remaining_fields_sha256"]:
        raise ValueError("Remaining-list hash mismatch")
    with lzma.open(source, "rt", newline="") as handle:
        rows = list(csv.DictReader(handle))
    allowed = {"missing_data", "external_conflict", "fpl_extract_exception", "rule_recalculation"}
    if len(rows) != current["open_fields"] or {r["status"] for r in rows} - allowed:
        raise ValueError("Unexpected ledger size/status; review classification")
    selected = sorted(
        (r for r in rows if r["status"] != "rule_recalculation"),
        key=lambda r: (r["field"], r["status"], r["season"], int(r["fixture"]), r["code"]),
    )
    fields = ["season", "fixture", "code", "field", "status", "name", "position", "date", "home", "away", "match_id", "player_id", "provenance", "source_disagreement", "assist_reason"]
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(selected)
    (out / "data_acquisition_requirements.csv.xz").write_bytes(lzma.compress(buf.getvalue().encode()))
    groups = Counter((r["field"], r["status"], r["season"]) for r in selected)
    with (out / "data_acquisition_groups.csv").open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["field", "status", "season", "open_requirements"])
        for key, count in sorted(groups.items()):
            writer.writerow([*key, count])
    manifest = {
        "source": current["remaining_fields"],
        "source_sha256": digest,
        "total_open_requirements": len(rows),
        "acquisition_or_source_resolution_requirements": len(selected),
        "counts_by_status": dict(sorted(Counter(r["status"] for r in rows).items())),
        "rule_recalculation_requirements_retained": len(rows) - len(selected),
        "rule_recalculation_note": "Deferred rule outputs may still require missing causal event evidence. Acquire that evidence in phase 1; this view does not certify its completeness or remove those requirements.",
        "files": {name: hashlib.sha256((out / name).read_bytes()).hexdigest() for name in ["data_acquisition_requirements.csv.xz", "data_acquisition_groups.csv"]},
        "ledger_modified": False,
        "newly_closed_requirements": 0,
    }
    (out / "ACQUISITION_CURRENT.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
