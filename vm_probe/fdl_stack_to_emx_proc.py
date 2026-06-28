from __future__ import annotations

import ast
import math
from pathlib import Path
from typing import Any


CADENCE_GDS = {
    "m1": (61, 0),
    "m2": (62, 0),
    "m3": (63, 0),
    "m4": (64, 0),
    "m5": (65, 0),
    "m6": (66, 0),
    "v1": (70, 0),
    "v2": (71, 0),
    "v3": (72, 0),
    "v4": (73, 0),
    "v5": (74, 0),
}


def literal(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [literal(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(literal(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return {literal(k): literal(v) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -literal(node.operand)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd):
        return literal(node.operand)
    if isinstance(node, ast.Name):
        if node.id == "True":
            return True
        if node.id == "False":
            return False
        if node.id == "None":
            return None
        return node.id
    raise ValueError(ast.dump(node, include_attributes=False))


def parse_stack(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    metals: list[dict[str, Any]] = []
    dielectrics: list[dict[str, Any]] = []
    for node in tree.body:
        call: ast.Call | None = None
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call = node.value
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
        if call is None:
            continue
        func = call.func
        if not isinstance(func, ast.Name) or func.id not in {"MetalLayer", "Layer"}:
            continue
        kwargs = {kw.arg: literal(kw.value) for kw in call.keywords if kw.arg}
        if func.id == "MetalLayer":
            metals.append(kwargs)
        else:
            dielectrics.append(kwargs)
    return metals, dielectrics


def fmt(value: float) -> str:
    if math.isclose(value, round(value), abs_tol=1e-9):
        return str(int(round(value)))
    return f"{value:.9g}"


def metal_resistance(metal: dict[str, Any]) -> str:
    if "RPSQ" in metal:
        return fmt(float(metal["RPSQ"]))
    conductivity = metal.get("conductivity")
    thickness_um = float(metal["thickness"])
    if conductivity and thickness_um > 0:
        rpsq = 1.0 / (float(conductivity) * thickness_um * 1e-6)
        return fmt(rpsq)
    return "0.01"


def dielectric_segments(
    dielectrics: list[dict[str, Any]], z0: float, z1: float
) -> list[tuple[float, float, str]]:
    segments: list[tuple[float, float, str]] = []
    for diel in dielectrics:
        thickness = diel.get("thickness")
        start = float(diel["zStart"])
        stop = float("inf") if thickness == "infinity" else start + float(thickness)
        a = max(z0, start)
        b = min(z1, stop)
        if b - a > 1e-6:
            er = float(diel.get("er", 1.0))
            name = str(diel.get("name", "dielectric"))
            segments.append((a, b, f"# {name}"))
    segments.sort(key=lambda item: item[0])
    if not segments and z1 > z0:
        segments.append((z0, z1, "# inferred air gap"))
    return segments


def dielectric_line(thickness: float, er: float, comment: str = "") -> str:
    suffix = f" {comment}" if comment else ""
    return f"layer {fmt(thickness)} {fmt(er)}{suffix}"


def build_proc(metals: list[dict[str, Any]], dielectrics: list[dict[str, Any]]) -> str:
    real_metals = [
        m
        for m in metals
        if not m.get("isGND") and not m.get("isVia") and str(m["name"]).lower() in CADENCE_GDS
    ]
    vias = [
        m
        for m in metals
        if m.get("isVia") and str(m["name"]).lower() in CADENCE_GDS
    ]
    real_metals.sort(key=lambda m: float(m["zStart"]))

    lines = [
        "# Auto-generated from FDL stack for EMX.",
        "# Source stack uses microns; Cadence GDS layer mapping comes from smic13mmrf_1233.layermap.",
        "# FDL dielectric eLossTan is recorded in comments; this EMX 6.0 proc uses supported layer/conductor/via primitives.",
        "",
        "assume microns",
        "assume ohms/sq",
        "assume ohms/via",
        "",
    ]
    for key, (layer, datatype) in CADENCE_GDS.items():
        lines.append(f"define {key} = L{layer}T{datatype}")
    lines.append("")

    # Substrate / bottom dielectric.
    bottom_diels = [d for d in dielectrics if math.isclose(float(d["zStart"]), 0.0, abs_tol=1e-9)]
    if bottom_diels:
        d = bottom_diels[0]
        thickness = d["thickness"]
        er = float(d.get("er", 1.0))
        if "resistivity" in d:
            lines.append(
                f"layer {fmt(float(thickness))} {fmt(er)} 1 {fmt(float(d['resistivity']))} ohm-cm # {d.get('name', 'substrate')}"
            )
        else:
            lines.append(dielectric_line(float(thickness), er, f"# {d.get('name', 'substrate')}"))
    else:
        first_z = float(real_metals[0]["zStart"]) if real_metals else 0.0
        if first_z > 0:
            lines.append(dielectric_line(first_z, 11.9, "# inferred substrate"))

    previous_top = float(real_metals[0]["zStart"]) if real_metals else 0.0
    if bottom_diels:
        previous_top = float(bottom_diels[0]["zStart"]) + float(bottom_diels[0]["thickness"])

    for metal in real_metals:
        name = str(metal["name"]).lower()
        z_start = float(metal["zStart"])
        thickness = float(metal["thickness"])
        if z_start > previous_top + 1e-6:
            for a, b, comment in dielectric_segments(dielectrics, previous_top, z_start):
                mid = (a + b) / 2.0
                overlapping = [
                    d
                    for d in dielectrics
                    if float(d["zStart"]) <= mid < (float("inf") if d["thickness"] == "infinity" else float(d["zStart"]) + float(d["thickness"]))
                ]
                er = float(overlapping[0].get("er", 1.0)) if overlapping else 1.0
                loss = overlapping[0].get("eLossTan") if overlapping else None
                extra = f"{comment}, tanD={loss}" if loss is not None else comment
                lines.append(dielectric_line(b - a, er, extra))
        lines.append(f"conductor {fmt(thickness)} {metal_resistance(metal)} {name} # z={fmt(z_start)} {metal.get('material', '')}")
        previous_top = z_start + thickness

    # Top air/passivation above highest metal.
    top_segments = dielectric_segments(dielectrics, previous_top, previous_top + 2.0)
    for a, b, comment in top_segments:
        mid = (a + b) / 2.0
        overlapping = [
            d
            for d in dielectrics
            if float(d["zStart"]) <= mid < (float("inf") if d["thickness"] == "infinity" else float(d["zStart"]) + float(d["thickness"]))
        ]
        er = float(overlapping[0].get("er", 1.0)) if overlapping else 1.0
        lines.append(dielectric_line(b - a, er, comment))
    lines.append("layer infinity 1 # air")
    lines.append("")

    via_by_name = {str(v["name"]).lower(): v for v in vias}
    metal_names = [str(m["name"]).lower() for m in real_metals]
    for lower, upper in zip(metal_names, metal_names[1:]):
        via_name = f"v{int(lower[1:])}" if lower.startswith("m") else ""
        via = via_by_name.get(via_name)
        if via:
            resistance = None
            vr = via.get("via_resistance")
            if isinstance(vr, dict):
                eql = vr.get("EQL")
                if isinstance(eql, dict):
                    for key in ("5", "40"):
                        if key in eql:
                            resistance = eql[key]
                            break
            if resistance is None and "conductivity" in via:
                resistance = float(via["conductivity"])
                lines.append(f"via {lower} {upper} {fmt(resistance)} {via_name}")
            else:
                lines.append(f"via {lower} {upper} {fmt(float(resistance or 0.1))} Ohms/via {via_name}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    input_path = Path("fdl_first_batch/ind4b.py")
    output_path = Path("vm_probe/fdl_stack.proc")
    metals, dielectrics = parse_stack(input_path)
    output_path.write_text(build_proc(metals, dielectrics), encoding="ascii", newline="\n")
    print(output_path)


if __name__ == "__main__":
    main()
