from pathlib import Path
import argparse
import math
import re


def fmt(value: float) -> str:
    text = f"{value:.15g}"
    return text if "." in text or "e" in text.lower() else text + "."


def replace_one(pattern: str, replacement: str, text: str, label: str) -> str:
    result, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"Expected one replacement for {label}, got {count}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--radius", type=float, default=600.0)
    parser.add_argument("--center-z", type=float, default=3.0)
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8", errors="ignore")
    start = text.find("$ORASpatialLumMeterObj create ->")
    if start < 0:
        raise SystemExit("Spatial luminance meter block not found")
    end = text.find("} restoreSpatialLumMeter:", start)
    if end < 0:
        raise SystemExit("Spatial luminance meter block end not found")
    end = text.find(";", end) + 1
    block = text[start:end]

    angle = math.radians(args.latitude)
    s, c = math.sin(angle), math.cos(angle)
    position = (-args.radius * s, 0.0, args.center_z + args.radius * c)
    orientation = (-c, 0.0, s, 0.0, 1.0, 0.0, -s, 0.0, -c)

    pos = "setPosition:  { " + " ".join(fmt(v) for v in position) + "  } ;"
    ori = "setOrientation: [3,3] { " + " ".join(fmt(v) for v in orientation) + "  } ;"
    lat = f"setLat: {fmt(args.latitude)};"
    block = replace_one(r"setPosition:\s*\{[^}]+\}\s*;", pos, block, "position")
    block = replace_one(r"setOrientation:\s*\[3,3\]\s*\{[^}]+\}\s*;", ori, block, "orientation")
    block = replace_one(r"setLat:\s*[-+0-9.eE]+;", lat, block, "latitude")

    args.output.write_text(text[:start] + block + text[end:], encoding="utf-8")
    print(f"patched latitude={args.latitude} output={args.output}")


if __name__ == "__main__":
    main()
