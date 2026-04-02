# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
# ]
# ///

import marimo

__generated_with = "0.22.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import csv
    import io
    from pathlib import Path
    return csv, io, mo, Path


@app.cell
def _(csv, io, mo, Path):
    _csv_path = mo.notebook_location() / "public" / "sample.csv"
    _path_str = str(_csv_path)

    if _path_str.startswith("http"):
        from urllib.request import urlopen
        _text = urlopen(_path_str).read().decode("utf-8")
        _reader = csv.DictReader(io.StringIO(_text))
    else:
        _reader = csv.DictReader(Path(_path_str).open())

    raw = [
        {
            "date": _r["date"],
            "product": _r["product"],
            "region": _r["region"],
            "units_sold": int(_r["units_sold"]),
            "revenue": float(_r["revenue"]),
            "cost": float(_r["cost"]),
            "profit": float(_r["revenue"]) - float(_r["cost"]),
        }
        for _r in _reader
    ]
    return (raw,)


@app.cell
def _(mo, raw):
    _product_stats: dict[str, dict] = {}
    for _r in raw:
        _p = _r["product"]
        if _p not in _product_stats:
            _product_stats[_p] = {"units": 0, "revenue": 0.0, "cost": 0.0, "profit": 0.0}
        _product_stats[_p]["units"] += _r["units_sold"]
        _product_stats[_p]["revenue"] += _r["revenue"]
        _product_stats[_p]["cost"] += _r["cost"]
        _product_stats[_p]["profit"] += _r["profit"]

    _rows = [
        {
            "Product": _p,
            "Units Sold": _s["units"],
            "Revenue": f"${_s['revenue']:,.2f}",
            "Cost": f"${_s['cost']:,.2f}",
            "Profit": f"${_s['profit']:,.2f}",
            "Margin": f"{_s['profit'] / _s['revenue'] * 100:.1f}%",
        }
        for _p, _s in _product_stats.items()
    ]

    mo.vstack([
        mo.md("## Sales Summary by Product"),
        mo.ui.table(_rows),
    ])
    return


@app.cell
def _(mo, raw):
    _region_stats: dict[str, dict] = {}
    for _r in raw:
        _reg = _r["region"]
        if _reg not in _region_stats:
            _region_stats[_reg] = {"units": 0, "revenue": 0.0, "profit": 0.0}
        _region_stats[_reg]["units"] += _r["units_sold"]
        _region_stats[_reg]["revenue"] += _r["revenue"]
        _region_stats[_reg]["profit"] += _r["profit"]

    _rows = [
        {
            "Region": _reg,
            "Units Sold": _s["units"],
            "Revenue": f"${_s['revenue']:,.2f}",
            "Profit": f"${_s['profit']:,.2f}",
        }
        for _reg, _s in _region_stats.items()
    ]

    mo.vstack([
        mo.md("## Sales Summary by Region"),
        mo.ui.table(_rows),
    ])
    return


@app.cell
def _(mo, raw):
    _weekly: dict[str, float] = {}
    for _r in raw:
        _d = _r["date"]
        _weekly[_d] = _weekly.get(_d, 0.0) + _r["revenue"]

    _chart_data = [{"Week": _d, "Revenue": f"${_v:,.2f}"} for _d, _v in sorted(_weekly.items())]

    mo.vstack([
        mo.md("## Weekly Revenue Trend"),
        mo.ui.table(_chart_data),
    ])
    return


if __name__ == "__main__":
    app.run()
