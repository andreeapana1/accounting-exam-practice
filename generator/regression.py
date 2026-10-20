"""Data interpretation (regression) exams.

Three exams use regressions actually estimated on the restaurant case data; the rest are
business scenarios from the course settings with constructed coefficients.
"""
import random
from collections import defaultdict

import numpy as np
import openpyxl
from scipy import stats

from common import EXCEL, num

RESTAURANT = EXCEL / "4. Regression Assignment" / "Restaurant" / "data.xlsm"
SUB = "₀₁₂₃"


def fmt(x):
    """Coefficient display: no trailing zeros, at most 3 decimals."""
    s = f"{x:,.3f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def signed(c):
    """' + 5' or ' − 5' for writing out an equation."""
    return f" − {fmt(abs(c))}" if c < 0 else f" + {fmt(c)}"


def tidy(c):
    """Round an estimated coefficient for display; predictions use the rounded value."""
    return round(float(c), 3 if abs(c) < 1 else 2)


def ols(y, cols):
    X = np.column_stack([np.ones(len(y))] + cols)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = len(y) - X.shape[1]
    se = np.sqrt(np.diag(resid @ resid / dof * np.linalg.inv(X.T @ X)))
    p = 2 * stats.t.sf(np.abs(beta / se), dof)
    r2 = 1 - resid @ resid / ((y - y.mean()) @ (y - y.mean()))
    return beta, p, r2, len(y)


# ------------------------------------------------------------------ exam text
def build_exam(eid, title, context, y, x, d, coefs, pvals, interaction, predict_at, outside, source):
    """y/x: dicts with name, unit; d: dict with name, ref, comp (labels); coefs/pvals: lists."""
    letter = "d" if interaction else "b"
    par = [f"{letter}{SUB[i]}" for i in range(len(coefs))]
    terms = ["Intercept", x["name"], d["name"]] + ([f'{x["name"]}×{d["name"]}'] if interaction else [])
    eq = f'Predicted {y["name"].lower()} = {par[0]} + {par[1]}[{x["name"]}] + {par[2]}[{d["name"]}]'
    if interaction:
        eq += f' + {par[3]}([{x["name"]}]×[{d["name"]}])'

    coefs = [tidy(c) for c in coefs]
    b0, b1, b2 = coefs[:3]
    b3 = coefs[3] if interaction else 0
    xv, dv = predict_at
    yhat = b0 + b1 * xv + b2 * dv + b3 * xv * dv
    group = d["comp"] if dv else d["ref"]
    work = f"{fmt(b0)}{signed(b1)} × {num(xv)}{signed(b2)} × {dv}"
    if interaction:
        work += f"{signed(b3)} × {num(xv)} × {dv}"
    unit = y["unit"]

    q_predict = {
        "kind": "P",
        "prompt": f"Predict the {y['name'].lower()} for {group} with {x['name'].lower()} = {num(xv)} {x['unit']}.",
        "answer": f"Predicted {y['name'].lower()} = {work} = {fmt(yhat)} {unit}.",
    }

    lo, hi = x["range"]
    interp = [f"Intercept ({fmt(b0)}): predicted {y['name'].lower()} for {d['ref']} when {x['name'].lower()} = 0. "
              + ("Zero lies outside the observed range, so it has little practical meaning on its own."
                 if lo > 0 else "")]
    if interaction:
        interp += [
            f"{x['name']} ({fmt(b1)}): for {d['ref']}, each additional {x['unit_one']} changes predicted "
            f"{y['name'].lower()} by {fmt(b1)} {unit}.",
            f"{d['name']} ({fmt(b2)}): at {x['name'].lower()} = 0, {d['comp']} are predicted to be {fmt(b2)} {unit} "
            f"{'higher' if b2 >= 0 else 'lower'} than {d['ref']}. Because of the interaction, the gap changes with "
            f"{x['name'].lower()}.",
            f"Interaction ({fmt(b3)}): the {x['name'].lower()} slope is {fmt(b3)} {'higher' if b3 >= 0 else 'lower'} "
            f"for {d['comp']}, so their slope is {fmt(b1)} + ({fmt(b3)}) = {fmt(b1 + b3)}.",
            f"Group equations: {d['ref']}: {fmt(b0)}{signed(b1)} × {x['name']}; "
            f"{d['comp']}: {fmt(b0 + b2)}{signed(b1 + b3)} × {x['name']}.",
        ]
    else:
        interp += [
            f"{x['name']} ({fmt(b1)}): holding {d['name'].lower()} constant, each additional {x['unit_one']} changes "
            f"predicted {y['name'].lower()} by {fmt(b1)} {unit}.",
            f"{d['name']} ({fmt(b2)}): holding {x['name'].lower()} constant, {d['comp']} are predicted to have "
            f"{fmt(abs(b2))} {unit} {'more' if b2 >= 0 else 'less'} than {d['ref']} (the reference group).",
        ]
    q_interpret = {
        "kind": "I",
        "prompt": "Interpret all coefficients in context: " + ", ".join(t.lower() for t in terms) + ".",
        "answer": "\n\n".join(interp),
    }

    sig = [t for t, p in zip(terms[1:], pvals[1:]) if p < 0.05]
    nonsig = [t for t, p in zip(terms[1:], pvals[1:]) if p >= 0.05]
    sig_text = (f"At the 5% level, {', '.join(sig)} {'is' if len(sig) == 1 else 'are'} statistically significant "
                f"(p < 0.05)." if sig else "None of the predictors is statistically significant at the 5% level.")
    if nonsig:
        sig_text += (f" {', '.join(nonsig)} {'is' if len(nonsig) == 1 else 'are'} not (p ≥ 0.05): we cannot rule out "
                     f"that the true effect is zero, so the estimate should not be relied on.")
    sig_text += " A small p-value says the effect is unlikely to be zero; it does not say the effect is large or important."
    q_sig = {
        "kind": "S",
        "prompt": f"Which predictors have a statistically significant effect on {y['name'].lower()} at the 5% level? "
                  f"What does that mean for {context['stakeholder']}?",
        "answer": sig_text,
    }

    ox, odv = outside
    oyhat = b0 + b1 * ox + b2 * odv + b3 * ox * odv
    q_range = {
        "kind": "R",
        "prompt": f"{context['stakeholder'][0].upper() + context['stakeholder'][1:]} asks for a prediction for {d['comp'] if odv else d['ref']} "
                  f"with {x['name'].lower()} = {num(ox)} {x['unit']}. How confident should they be?",
        "answer": f"The equation gives {fmt(oyhat)} {unit}, but {num(ox)} lies outside the observed range "
                  f"({num(lo)}–{num(hi)} {x['unit']}). This is extrapolation: the linear relationship may not hold "
                  f"there, so the prediction is unreliable and should be communicated with a clear warning.",
    }
    return {
        "id": eid, "title": title, "intro": context["intro"], "source": source,
        "y": y, "x": x, "d": d, "equation": eq,
        "table": [{"param": p, "term": t, "estimate": fmt(c), "p": f"{pv:.3f}".rstrip("0").rstrip(".") if pv >= 0.001 else "<0.001"}
                  for p, t, c, pv in zip(par, terms, coefs, pvals)],
        "questions": [q_predict, q_interpret, q_sig, q_range],
        "minutes": 5,
    }


# --------------------------------------------------------- restaurant (real)
def restaurant_data():
    wb = openpyxl.load_workbook(RESTAURANT, read_only=True, data_only=True)
    sales, sales364 = defaultdict(float), defaultdict(float)
    for r in wb["salesData"].iter_rows(min_row=2, values_only=True):
        if r[0] is None:
            continue
        sales[r[0].date()] += r[5] or 0
        sales364[r[0].date()] += r[11] or 0
    tmax = {r[0].date(): r[3] for r in wb["weatherData"].iter_rows(min_row=2, values_only=True) if r[0]}
    game = {r[0].date(): r[4] for r in wb["gameData"].iter_rows(min_row=2, values_only=True) if r[0]}
    days = sorted(d for d in sales if d in tmax)
    return {
        "y": np.array([sales[d] for d in days]),
        "y364": np.array([sales364[d] for d in days]),
        "tmax": np.array([tmax[d] for d in days]),
        "game": np.array([float(game.get(d, 0)) for d in days]),
        "n_days": len(days),
    }


def restaurant_exams():
    r = restaurant_data()
    stake = {"stakeholder": "Bob, the restaurant owner",
             "intro": "Larry's Commissary point-of-sale data for 2018, merged with daily weather and university football "
                      "game days (the restaurant regression case). The regression was estimated on the case data."}
    y = {"name": "Daily sales", "unit": "USD"}
    game = {"name": "Game day", "ref": "days without a home-town football game", "comp": "game days"}
    tlo, thi = float(r["tmax"].min()), float(r["tmax"].max())
    t = {"name": "Max temperature", "unit": "°F", "unit_one": "degree Fahrenheit", "range": (round(tlo), round(thi))}
    beta, p, r2, n = ols(r["y"], [r["tmax"], r["game"]])
    ex1 = build_exam("REG01", "Restaurant sales, weather and game days", stake, y, t, game, beta, p, False,
                     (75, 1), (110, 0), f"Estimated on the case data: n = {n} days, R² = {r2:.2f}")

    lo, hi = float(r["y364"].min()), float(r["y364"].max())
    s364 = {"name": "Sales one year ago", "unit": "USD", "unit_one": "dollar of sales on the same day last year",
            "range": (round(lo, -2), round(hi, -2))}
    beta, p, r2, n = ols(r["y"], [r["y364"], r["game"], r["y364"] * r["game"]])
    ex2 = build_exam("REG02", "Restaurant sales: last year's sales × game day", stake, y, s364, game, beta, p, True,
                     (4000, 1), (round(hi * 1.6, -2), 1), f"Estimated on the case data: n = {n} days, R² = {r2:.2f}")
    return [ex1, ex2]


# ------------------------------------------------------- scenario templates
SCENARIOS = [
    dict(title="Hotel room revenue", stakeholder="the hotel's controller",
         intro="The hotel and conference center from ETL Case 4 wants to understand daily room revenue.",
         y=("Room revenue", "USD"), x=("Rooms occupied", "rooms", "occupied room", (40, 180)),
         d=("Conference day", "days without a conference", "conference days"),
         b0=(1500, 4000), b1=(60, 120), b2=(800, 3000), b3=(-15, 25)),
    dict(title="Payroll overtime", stakeholder="Noah, IntegrateCo's CFO",
         intro="IntegrateCo (payroll case) wants to explain monthly overtime pay per employee.",
         y=("Overtime pay", "USD per month"), x=("Projects assigned", "projects", "project", (1, 8)),
         d=("Installation job", "employees in office roles", "employees in installation roles"),
         b0=(20, 120), b1=(30, 90), b2=(40, 200), b3=(-20, 40)),
    dict(title="P-card spending", stakeholder="OSU's internal auditor",
         intro="OSU's internal audit team studies monthly P-card spending per cardholder (P-card case).",
         y=("Monthly P-card spending", "USD"), x=("Transactions", "transactions", "transaction", (2, 60)),
         d=("Student employee", "staff cardholders", "student-employee cardholders"),
         b0=(200, 900), b1=(150, 320), b2=(-900, -150), b3=(-120, 10)),
    dict(title="Journal entry review time", stakeholder="the audit senior",
         intro="An audit team measures how long it takes to review journal entries for a client.",
         y=("Review time", "minutes per entry"), x=("Line items", "line items", "line item", (2, 30)),
         d=("Manual entry", "system-generated entries", "manual entries"),
         b0=(2, 6), b1=(0.5, 1.6), b2=(3, 12), b3=(-0.3, 0.8)),
    dict(title="Film permit processing", stakeholder="the NYC film office manager",
         intro="The NYC film office (Excel case) studies the lead time between entering and starting a permit.",
         y=("Lead time", "days"), x=("Locations on the permit", "locations", "location", (1, 12)),
         d=("Television shoot", "film shoots", "television shoots"),
         b0=(2, 5), b1=(0.3, 1.2), b2=(-2.5, -0.5), b3=(-0.4, 0.3)),
    dict(title="Restaurant ingredient costs", stakeholder="Bob, the restaurant owner",
         intro="Larry's Commissary (restaurant case) wants to plan daily ingredient purchases.",
         y=("Ingredient cost", "USD per day"), x=("Covers served", "guests", "guest", (80, 400)),
         d=("Weekend", "weekdays", "weekend days"),
         b0=(150, 450), b1=(3, 7), b2=(100, 400), b3=(-1.5, 2)),
    dict(title="Accounts receivable collection", stakeholder="the credit manager",
         intro="A wholesaler studies how many days customers take to pay their invoices.",
         y=("Days to pay", "days"), x=("Invoice amount", "thousand USD", "thousand USD of invoice value", (1, 50)),
         d=("New customer", "existing customers", "new customers"),
         b0=(20, 35), b1=(0.2, 0.9), b2=(3, 12), b3=(-0.3, 0.4)),
    dict(title="Music downloads", stakeholder="the Chinook sales manager",
         intro="The digital music store from the Chinook database studies monthly downloads per customer.",
         y=("Downloads", "tracks per month"), x=("Marketing emails", "emails", "marketing email", (0, 12)),
         d=("Premium member", "standard customers", "premium members"),
         b0=(3, 8), b1=(0.4, 1.5), b2=(2, 7), b3=(-0.4, 0.6)),
    dict(title="Holiday-home bookings", stakeholder="the rental agency",
         intro="A holiday-home rental agency studies booked nights per month.",
         y=("Booked nights", "nights per month"), x=("Nightly price", "EUR/night", "euro per night", (60, 180)),
         d=("Private pool", "homes without a private pool", "homes with a private pool"),
         b0=(22, 34), b1=(-0.12, -0.04), b2=(2, 8), b3=(-0.04, 0.05)),
    dict(title="Audit fees", stakeholder="the audit partner",
         intro="An audit firm studies the fees it charges clients.",
         y=("Audit fee", "thousand DKK"), x=("Client revenue", "million DKK", "million DKK of client revenue", (10, 500)),
         d=("Listed client", "private clients", "listed clients"),
         b0=(50, 150), b1=(0.3, 1.2), b2=(60, 250), b3=(-0.3, 0.6)),
]


def scenario_exams(start=3, per_scenario=2, seed=2026):
    rng = random.Random(seed)
    exams, eid = [], start
    for s in SCENARIOS:
        for k in range(per_scenario):
            interaction = k % 2 == 1
            pick = lambda lo_hi, step: round(rng.uniform(*lo_hi) / step) * step
            span = s["b1"][1] - s["b1"][0]
            step1 = 0.01 if span < 1 else (0.1 if span < 10 else 1)
            coefs = [pick(s["b0"], 1 if s["b0"][1] > 10 else 0.1), pick(s["b1"], step1),
                     pick(s["b2"], 1 if abs(s["b2"][1]) > 10 else 0.1)]
            pvals = [rng.choice([0.001, 0.004, 0.02, 0.31]), rng.choice([0.001, 0.003, 0.008, 0.02]),
                     rng.choice([0.002, 0.028, 0.041, 0.12, 0.27])]
            if interaction:
                coefs.append(pick(s["b3"], 0.01 if (s["b3"][1] - s["b3"][0]) < 2 else (0.1 if s["b3"][1] < 10 else 1)))
                pvals.append(rng.choice([0.006, 0.015, 0.09, 0.34]))
            lo, hi = s["x"][3]
            xv = round(rng.uniform(lo + (hi - lo) * 0.2, hi - (hi - lo) * 0.2))
            out = hi * 2 if hi > 2 else hi + 5
            exams.append(build_exam(
                f"REG{eid:02d}", s["title"],
                {"stakeholder": s["stakeholder"], "intro": s["intro"]},
                {"name": s["y"][0], "unit": s["y"][1]},
                {"name": s["x"][0], "unit": s["x"][1], "unit_one": s["x"][2], "range": s["x"][3]},
                {"name": s["d"][0], "ref": s["d"][1], "comp": s["d"][2]},
                coefs, pvals, interaction, (xv, rng.choice([0, 1])), (out, 0),
                "Constructed scenario for practice (coefficients are illustrative)."))
            eid += 1
    return exams


def all_exams():
    return restaurant_exams() + scenario_exams()
