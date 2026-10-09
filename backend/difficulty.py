"""
Tutor Portal — difficulty progression layer.

Gives every unit, quiz question, worked example and practice problem a level
(1 Foundational · 2 Intermediate · 3 Advanced) so the portal can present
material easy → hard, and adds a HARDER second worked example plus extra
practice problems to every unit so the ladder is real, not just a label.

content.py merges this at import time; nothing else needs to know about it.
"""

# ---------------------------------------------------------------------------
# Level metadata (single source of truth for labels/colors)
# ---------------------------------------------------------------------------

LEVELS = {
    1: {"name": "Foundational", "short": "Easy", "hint": "Start here"},
    2: {"name": "Intermediate", "short": "Medium", "hint": "Apply the concept"},
    3: {"name": "Advanced", "short": "Hard", "hint": "Multi-step / exam level"},
}

# ---------------------------------------------------------------------------
# Unit difficulty tier  (drives ordering across the course)
# ---------------------------------------------------------------------------

UNIT_LEVELS = {
    # Calculus II — integration -> series -> vector/ODE territory
    "mth-1": 1, "mth-2": 2, "mth-3": 2, "mth-4": 3, "mth-5": 3, "mth-6": 3,
    # Physics II — fields -> circuits -> induction/AC
    "phy-1": 1, "phy-2": 2, "phy-3": 2, "phy-4": 2, "phy-5": 3, "phy-6": 3,
    # Career & Self Dev
    "ccd-1": 1, "ccd-2": 1, "ccd-3": 2, "ccd-4": 2, "ccd-5": 2,
    # Modeling & Design — process/sketching -> CAD -> drawings/DFM
    "md-1": 1, "md-2": 1, "md-3": 2, "md-4": 3, "md-5": 3,
    # Statics — vectors/particles -> rigid bodies/trusses -> friction/inertia
    "sm-1": 1, "sm-2": 1, "sm-3": 2, "sm-4": 2, "sm-5": 3, "sm-6": 3,
    # Materials — bonding -> structure/properties -> phase diagrams/failure
    "em-1": 1, "em-2": 2, "em-3": 2, "em-4": 3, "em-5": 3, "em-6": 2,
}

# ---------------------------------------------------------------------------
# Quiz question levels — aligned to the order in content.QUIZ_BANK
# 1 = recall, 2 = apply/compute, 3 = multi-step analysis
# ---------------------------------------------------------------------------

QUIZ_LEVELS = {
    "MTH-202": [1, 1, 2, 1, 2, 2, 2, 2, 2, 3],
    "PHY-202": [1, 1, 2, 2, 1, 1, 1, 1, 2, 2, 3, 2],
    "CCD-101": [1, 2, 1, 1, 2, 2, 2, 1],
    "MD-102":  [1, 2, 1, 1, 2, 3, 2, 2],
    "SM-201":  [1, 1, 2, 1, 2, 2, 2, 2, 2],
    "EM-202":  [1, 2, 1, 1, 2, 2, 2, 3],
}

# Existing practice problems are ordered easy-first within a unit; these tag them.
# (index -> level). Anything beyond the list defaults to the unit's level + 1.
PRACTICE_TAGS = {
    "mth-1": [1, 2], "mth-2": [1, 2], "mth-3": [2, 2], "mth-4": [2, 2],
    "mth-5": [1, 2], "mth-6": [1, 2],
    "phy-1": [1, 2], "phy-2": [1, 2], "phy-3": [1, 2], "phy-4": [1, 2],
    "phy-5": [1, 2], "phy-6": [1, 2],
    "ccd-1": [1, 1], "ccd-2": [1, 1], "ccd-3": [1, 1], "ccd-4": [1, 2], "ccd-5": [1, 1],
    "md-1": [1, 1], "md-2": [1, 1], "md-3": [1, 1], "md-4": [1, 1], "md-5": [1, 1],
    "sm-1": [1, 2], "sm-2": [1, 1], "sm-3": [1, 1], "sm-4": [1, 1],
    "sm-5": [1, 1], "sm-6": [1, 1],
    "em-1": [1, 1], "em-2": [1, 1], "em-3": [2, 2], "em-4": [1, 1],
    "em-5": [1, 1], "em-6": [1, 1],
}

# ---------------------------------------------------------------------------
# UNIT_EXTRA — a HARDER worked example + extra practice for every unit.
# ---------------------------------------------------------------------------

UNIT_EXTRA = {
    # ------------------------------- CALCULUS II -------------------------- #
    "mth-1": {
        "example": {
            "level": 3,
            "problem": "Evaluate ∫ x² ln x dx.",
            "steps": [
                "By parts with u = ln x (LIATE: log before algebraic) and dv = x² dx.",
                "Then du = (1/x) dx and v = x³/3.",
                "∫ x² ln x dx = (x³/3) ln x − ∫ (x³/3)(1/x) dx = (x³/3) ln x − (1/3)∫ x² dx.",
                "∫ x² dx = x³/3, so the result is (x³/3) ln x − x³/9 + C = (x³/3)(ln x − 1/3) + C.",
                "Check by differentiating: d/dx[(x³/3)ln x − x³/9] = x² ln x + x²/3 − x²/3 = x² ln x ✓.",
            ],
            "answer": "∫ x² ln x dx = (x³/3)(ln x − 1/3) + C.",
        },
        "practice": [
            {"level": 3, "q": "Evaluate ∫ eˣ sin x dx (the 'cyclic' by-parts integral).",
             "a": "Apply by parts twice; the original integral reappears. I = eˣ(sin x − cos x)/2 + C. Check by differentiating."},
        ],
    },
    "mth-2": {
        "example": {
            "level": 3,
            "problem": "Evaluate the improper integral ∫₀^∞ x e^(−x) dx.",
            "steps": [
                "Replace the infinite limit: ∫₀^b x e^(−x) dx, then let b → ∞.",
                "By parts with u = x, dv = e^(−x) dx: du = dx, v = −e^(−x).",
                "∫₀^b x e^(−x) dx = [−x e^(−x)]₀^b + ∫₀^b e^(−x) dx = −b e^(−b) + [−e^(−x)]₀^b.",
                "= −b e^(−b) − e^(−b) + 1 = 1 − e^(−b)(b + 1).",
                "As b → ∞, e^(−b)(b+1) → 0 (exponential beats any polynomial), so the value is 1.",
            ],
            "answer": "∫₀^∞ x e^(−x) dx = 1 — the integral converges.",
        },
        "practice": [
            {"level": 3, "q": "Use cylindrical shells to find the volume when y = 1/x on [1, 3] is revolved about the y-axis.",
             "a": "V = 2π∫₁³ x·(1/x) dx = 2π∫₁³ dx = 2π(3−1) = 4π ≈ 12.57 units³. Note the radius is x and the height is 1/x."},
        ],
    },
    "mth-3": {
        "example": {
            "level": 3,
            "problem": "Determine whether Σ_{n=1}^∞ n²/2ⁿ converges.",
            "steps": [
                "Terms involve both a power n² and an exponential 2ⁿ → ratio test.",
                "aₙ = n²/2ⁿ, aₙ₊₁ = (n+1)²/2^(n+1).",
                "|aₙ₊₁/aₙ| = [(n+1)²/2^(n+1)] · [2ⁿ/n²] = (1/2)·((n+1)/n)².",
                "lim as n→∞: (1/2)·1² = 1/2.",
                "L = 1/2 < 1 → the series converges (absolutely).",
            ],
            "answer": "Converges by the ratio test (L = 1/2 < 1).",
        },
        "practice": [
            {"level": 3, "q": "Does Σ (−1)ⁿ/√n converge absolutely, conditionally, or not at all?",
             "a": "Alternating series test: 1/√n decreases to 0 → converges. But Σ1/√n is a p-series with p = 1/2 ≤ 1 → diverges. So it converges CONDITIONALLY, not absolutely."},
        ],
    },
    "mth-4": {
        "example": {
            "level": 3,
            "problem": "Find the Taylor series for ln(1+x) about 0 and state its radius of convergence.",
            "steps": [
                "f(x) = ln(1+x) → f(0) = 0.",
                "Derivatives: f′ = 1/(1+x) → 1; f″ = −1/(1+x)² → −1; f‴ = 2/(1+x)³ → 2; f⁗ = −6/(1+x)⁴ → −6.",
                "f⁽ⁿ⁾(0) = (−1)^(n−1)(n−1)!, so the term is (−1)^(n−1)(n−1)!xⁿ/n! = (−1)^(n−1)xⁿ/n.",
                "Series: x − x²/2 + x³/3 − x⁴/4 + … = Σ_{n≥1} (−1)^(n−1)xⁿ/n.",
                "Ratio test gives |x| < 1; at x = 1 the alternating harmonic converges, at x = −1 the harmonic diverges.",
            ],
            "answer": "ln(1+x) = Σ (−1)^(n−1)xⁿ/n for −1 < x ≤ 1 (radius R = 1).",
        },
        "practice": [
            {"level": 3, "q": "Use the series for eˣ to approximate ∫₀^{0.5} e^(−x²) dx with three terms, and bound the error.",
             "a": "e^(−x²) = 1 − x² + x⁴/2 − … Integrating: x − x³/3 + x⁵/10 at x = 0.5 → 0.5 − 0.041667 + 0.003125 = 0.461458. Next term is −x⁷/42 → magnitude at 0.5 is 7.4×10⁻⁴/… ≈ 1.86×10⁻⁴, which bounds the error."},
        ],
    },
    "mth-5": {
        "example": {
            "level": 3,
            "problem": "Find the slope dy/dx of the polar curve r = 1 + cos θ at θ = π/2.",
            "steps": [
                "Treat as parametric: x = r cos θ = (1+cos θ)cos θ, y = r sin θ = (1+cos θ)sin θ.",
                "dx/dθ = −sin θ(1+2cos θ)? — differentiate directly: x = cos θ + cos²θ → dx/dθ = −sin θ − 2cos θ sin θ = −sin θ(1 + 2cos θ).",
                "y = sin θ + sin θ cos θ → dy/dθ = cos θ + cos²θ − sin²θ = cos θ + cos 2θ.",
                "At θ = π/2: sin = 1, cos = 0 → dx/dθ = −1(1+0) = −1; dy/dθ = 0 + cos π = −1.",
                "dy/dx = (dy/dθ)/(dx/dθ) = (−1)/(−1) = 1.",
            ],
            "answer": "dy/dx = 1 at θ = π/2 (a 45° upward tangent there).",
        },
        "practice": [
            {"level": 3, "q": "Find the area inside r = 1 and outside r = 2cos θ.",
             "a": "They intersect where 1 = 2cos θ → θ = ±π/3. A = 2·½∫₀^{π/3}(1² − (2cos θ)²) dθ = ∫₀^{π/3}(1 − 4cos²θ) dθ = ∫₀^{π/3}(1 − 2(1+cos2θ)) dθ = ∫₀^{π/3}(−1 − 2cos2θ) dθ. Evaluate: [−θ − sin2θ]₀^{π/3} = (−π/3 − √3/2) − 0 → take the absolute magnitude ≈ 1.913 (2π/3 − √3/2 ≈ 2.094 − 0.866 = 1.228; check bounds) — the standard result is 2π/3 − √3/2 ≈ 1.228."},
        ],
    },
    "mth-6": {
        "example": {
            "level": 3,
            "problem": "Solve the first-order linear ODE y′ + 2y = 4x with y(0) = 1.",
            "steps": [
                "Identify P(x) = 2, Q(x) = 4x. Integrating factor μ = e^{∫2 dx} = e^{2x}.",
                "Multiply through: e^{2x}y′ + 2e^{2x}y = 4x e^{2x}, i.e. (e^{2x} y)′ = 4x e^{2x}.",
                "Integrate both sides: e^{2x}y = ∫4x e^{2x} dx.",
                "By parts (u = x, dv = e^{2x}dx): ∫4x e^{2x} dx = 4[x e^{2x}/2 − e^{2x}/4] = 2x e^{2x} − e^{2x} + C.",
                "So y = 2x − 1 + C e^{−2x}. Apply y(0) = 1: 1 = −1 + C → C = 2.",
            ],
            "answer": "y = 2x − 1 + 2e^(−2x).",
        },
        "practice": [
            {"level": 3, "q": "A cup of coffee at 90 °C sits in a 20 °C room. After 10 min it is 65 °C. Find the temperature after 30 min (Newton's law of cooling).",
             "a": "T − 20 = (90−20)e^(−kt) → 45 = 70e^(−10k) → k = −ln(45/70)/10 ≈ 0.0442 /min. At 30 min: T = 20 + 70e^(−0.0442·30) = 20 + 70(0.2654) ≈ 38.6 °C."},
        ],
    },

    # ------------------------------- PHYSICS II --------------------------- #
    "phy-1": {
        "example": {
            "level": 3,
            "problem": "Charges +2.0 μC at the origin and −3.0 μC at x = 0.40 m. Find the net force on a +1.0 μC charge at x = 0.10 m.",
            "steps": [
                "The +1.0 μC at x = 0.10 is pulled LEFT by the +2.0 μC (like charges) and RIGHT by the −3.0 μC (unlike attract).",
                "Force from the left charge: F₁ = k(2e-6)(1e-6)/(0.10)² = 1.798×10⁻²/0.01 = 1.80 N, to the left (−x).",
                "Distance to the right charge: 0.40 − 0.10 = 0.30 m. F₂ = k(3e-6)(1e-6)/(0.30)² = 2.697×10⁻²/0.09 = 0.30 N, to the right (+x).",
                "Net: 1.80 − 0.30 = 1.50 N, directed toward the origin (−x).",
            ],
            "answer": "F_net = 1.50 N in the −x direction (toward the +2.0 μC charge).",
        },
        "practice": [
            {"level": 3, "q": "Two +4.0 nC charges sit at (0,0) and (0.20, 0) m. Find the electric field at (0.10, 0.10) m.",
             "a": "By symmetry the x-components cancel and only the y-component adds. r = √(0.10²+0.10²) = 0.1414 m; E per charge = kq/r² = (8.99e9)(4e-9)/0.02 = 1798 N/C. The y-component of each is 1798·(0.10/0.1414) = 1271 N/C, so E_y = 2×1271 = 2.54×10³ N/C upward."},
        ],
    },
    "phy-2": {
        "example": {
            "level": 3,
            "problem": "A solid insulating sphere of radius R has uniform charge density ρ. Find E for r < R and r > R.",
            "steps": [
                "Spherical symmetry → a Gaussian sphere of radius r works in both regions.",
                "Inside (r < R): enclosed charge Q_enc = ρ·(4/3)πr³. Gauss: E(4πr²) = ρ(4/3)πr³/ε₀.",
                "Solve: E = ρr/(3ε₀) — grows linearly with r.",
                "Outside (r > R): Q_enc = ρ(4/3)πR³ = Q_total. Gauss gives E(4πr²) = Q/ε₀ → E = Q/(4πε₀r²) = kQ/r² — same as a point charge.",
            ],
            "answer": "Inside: E = ρr/(3ε₀) (linear). Outside: E = kQ/r² (point-charge). They match at r = R.",
        },
        "practice": [
            {"level": 3, "q": "A point charge sits at one corner of a cube. What is the flux through the OPPOSITE face?",
             "a": "The charge at a corner is shared by 8 cubes, so each cube encloses Q/8. Within that cube the three faces meeting at the charge carry zero flux (E ∥ face), leaving the three far faces to share Q/8 equally: each gets Q/48 = Q/(48ε₀)·… flux = Q/(48ε₀)? Careful: flux per far face = (Q/8)/(3) /ε₀ = Q/(24ε₀)."},
        ],
    },
    "phy-3": {
        "example": {
            "level": 3,
            "problem": "A 4.0 μF capacitor (charged to 12 V) is connected across an uncharged 8.0 μF capacitor. Find the final voltage and the energy lost.",
            "steps": [
                "Initial charge: Q = C₁V = (4.0 μF)(12 V) = 48 μC; stored energy U_i = ½C₁V² = ½(4e-6)(144) = 288 μJ.",
                "After connection the capacitors are in parallel, so the charge redistributes: V_f = Q_total/C_total = 48/(4+8) = 4.0 V.",
                "Final energy: U_f = ½C_totalV_f² = ½(12e-6)(16) = 96 μJ.",
                "Energy lost = 288 − 96 = 192 μJ (dissipated as heat/radiation in the connecting wires).",
            ],
            "answer": "V_f = 4.0 V; 192 μJ of the 288 μJ is lost — charge is conserved, energy is not.",
        },
        "practice": [
            {"level": 3, "q": "How much work is needed to move a +3.0 μC charge from a point at 200 V to a point at 50 V?",
             "a": "W = qΔV = (3e-6)(50 − 200) = (3e-6)(−150) = −4.5×10⁻⁴ J. Negative means the field does the work — the charge speeds up moving to lower potential."},
        ],
    },
    "phy-4": {
        "example": {
            "level": 3,
            "problem": "Two-loop circuit: a 12 V battery with 2 Ω in series, splitting into a 4 Ω and a 6 Ω branch that rejoin. Find each branch current.",
            "steps": [
                "The 4 Ω and 6 Ω are in parallel: R_p = (4·6)/(4+6) = 2.4 Ω.",
                "Total resistance = series 2 Ω + 2.4 Ω = 4.4 Ω → total current I = 12/4.4 = 2.73 A.",
                "Voltage across the parallel pair: V_p = I·R_p = 2.73 × 2.4 = 6.55 V.",
                "Branch currents: I₄ = 6.55/4 = 1.64 A; I₆ = 6.55/6 = 1.09 A. Check: 1.64 + 1.09 = 2.73 A ✓.",
            ],
            "answer": "Total 2.73 A; 1.64 A through the 4 Ω, 1.09 A through the 6 Ω. The smaller resistance carries the larger current.",
        },
        "practice": [
            {"level": 3, "q": "A battery reads 9.0 V open-circuit and 8.4 V when delivering 0.60 A. Find its internal resistance and EMF.",
             "a": "V = ε − Ir → 8.4 = 9.0 − 0.60r → r = 0.6/0.6 = 1.0 Ω. EMF ε = 9.0 V (the open-circuit reading)."},
        ],
    },
    "phy-5": {
        "example": {
            "level": 3,
            "problem": "A proton (m = 1.67×10⁻²⁷ kg, q = 1.60×10⁻¹⁹ C) moves at 2.0×10⁶ m/s perpendicular to a 0.50 T field. Find the radius of its circular path and the period.",
            "steps": [
                "The magnetic force supplies the centripetal force: qvB = mv²/r.",
                "Solve for r: r = mv/(qB) = (1.67e-27)(2.0e6)/[(1.60e-19)(0.50)].",
                "Numerator 3.34×10⁻²¹; denominator 8.0×10⁻²⁰ → r = 0.0418 m ≈ 4.2 cm.",
                "Period T = 2πr/v = 2π(0.0418)/(2.0e6) = 1.31×10⁻⁷ s.",
            ],
            "answer": "r ≈ 4.2 cm; T ≈ 1.3×10⁻⁷ s (the period is independent of speed for a fixed qB/m).",
        },
        "practice": [
            {"level": 3, "q": "A 0.60 m conducting rod slides at 3.0 m/s along rails in a 0.40 T field perpendicular to the plane. Find the motional EMF.",
             "a": "EMF = BLv = (0.40)(0.60)(3.0) = 0.72 V."},
        ],
    },
    "phy-6": {
        "example": {
            "level": 3,
            "problem": "An RL circuit has ε = 12 V, R = 6.0 Ω and L = 1.5 H. Find the time constant, the final current, and the current at t = 1τ.",
            "steps": [
                "Time constant τ = L/R = 1.5/6.0 = 0.25 s.",
                "Final (steady) current I_max = ε/R = 12/6.0 = 2.0 A.",
                "Current growth: I(t) = I_max(1 − e^(−t/τ)). At t = τ: I = 2.0(1 − e^(−1)) = 2.0(1 − 0.368).",
                "I = 2.0 × 0.632 = 1.26 A.",
            ],
            "answer": "τ = 0.25 s; I_max = 2.0 A; at one time constant I = 1.26 A (63.2% of final).",
        },
        "practice": [
            {"level": 3, "q": "A transformer steps 120 V down to 12 V. If the secondary delivers 3.0 A, and it is ideal, what is the primary current?",
             "a": "Ideal transformer conserves power: V_pI_p = V_sI_s → (120)I_p = (12)(3.0) = 36 → I_p = 0.30 A."},
        ],
    },

    # --------------------------- CAREER & SELF DEV ------------------------ #
    "ccd-1": {
        "example": {
            "level": 3,
            "problem": "You discover a colleague signed off on test results that were never run, and a product is about to ship. Analyse fully.",
            "steps": [
                "Stakeholders: the public (safety), your employer (liability/reputation), the colleague (job), you (job, licence, duty).",
                "Utilitarian: shipping untested product risks serious harm — the expected harm outweighs the schedule or loyalty benefit.",
                "Rights/duty: users have a right not to be exposed to an untested hazard; NSPE places public safety paramount.",
                "Virtue: a person of good character does not stay silent to protect a colleague.",
                "Action ladder: verify your understanding → raise it directly and privately → escalate to the supervisor → document in writing → escalate further / regulator if unresolved.",
            ],
            "answer": "Escalate with written documentation, starting privately, and continue up the chain if unresolved — the untested sign-off is falsified data, not a judgement call, and public safety outranks loyalty.",
        },
        "practice": [
            {"level": 3, "q": "Your manager asks you to omit a known failure mode from a report to a regulator, saying 'it's not material'. How do you respond?",
             "a": "Refuse to omit it. Frame it as a professional and legal exposure, not a personal objection: misrepresenting a known hazard to a regulator breaches the paramount-safety canon and can be fraud. Offer to document the risk with mitigations so the report is complete AND constructive; escalate if pressed."},
        ],
    },
    "ccd-2": {
        "example": {
            "level": 3,
            "problem": "A 12-page report buries its recommendation on page 11. Restructure it and explain the changes.",
            "steps": [
                "Identify the single most important sentence (the recommendation) and everything supporting it.",
                "Apply the inverted pyramid: executive summary with problem → finding → recommendation → cost/next step.",
                "Move the detailed method and raw data to appendices; keep evidence for the recommendation in the body.",
                "Number and caption every figure, reference each in the text, and label axes with units.",
                "Cut nominalisations and passive voice: 'an evaluation was undertaken' → 'we evaluated'.",
            ],
            "answer": "Lead with the recommendation in a one-page executive summary, keep supporting evidence in the body, move method/raw data to appendices, and rewrite in active voice — the reader must be able to act after the first page.",
        },
        "practice": [
            {"level": 3, "q": "Critique this figure caption: 'Fig 3. Results.'",
             "a": "It fails on every count: no figure number convention issue but no description of what is plotted, no axes/units statement, no takeaway, and no in-text reference. A good caption reads what is shown, the conditions, and the key result — e.g. 'Figure 3. Pump efficiency vs. flow rate at 25 °C. Efficiency peaks at 68% near 40 L/min.'"},
        ],
    },
    "ccd-3": {
        "example": {
            "level": 3,
            "problem": "One teammate has stopped contributing; the other two are resentful and the deadline is in a week. Diagnose and act.",
            "steps": [
                "Diagnose the Tuckman stage: this is Storming pressure surfacing as resentment — normal, not terminal.",
                "Check your assumptions first: is it capability, capacity, clarity, or motivation? Different causes, different fixes.",
                "Hold a private SBI conversation: 'At the last two stand-ups (S), the model file wasn't updated (B), which blocked my part (I).'",
                "Choose Collaborating in Thomas-Kilmann — both the relationship and the deadline matter.",
                "Agree a concrete, small, earlier checkpoint and re-split the remaining work explicitly; set a review date.",
            ],
            "answer": "Private SBI conversation to find the real cause, Collaborating mode, then re-contract with smaller checkpoints — and escalate only if a documented agreement is broken, not to 'fix' the person.",
        },
        "practice": [
            {"level": 3, "q": "A quiet team member's correct objection is being ignored in design meetings. What do you do as the lead?",
             "a": "Protect psychological safety explicitly: name the objection, ask the person to expand, and record it in the decision log. If the team still overrides it, require the decision record to state WHY it was overridden — this makes dissent safe and traceable, and often changes the outcome."},
        ],
    },
    "ccd-4": {
        "example": {
            "level": 3,
            "problem": "Build a STAR answer to 'Tell me about a time you disagreed with a teammate.'",
            "steps": [
                "Situation (15s): set the context — a 4-person design project, two weeks out.",
                "Task (10s): you needed an agreed material choice to finish the analysis.",
                "Action (45s): you asked for the reasoning, built a weighted comparison of the two options, presented data in a joint review, and proposed a test to settle it.",
                "Result (20s): the team chose the alternative on the evidence; you delivered on time and the part passed the later test.",
                "Then stop — do not ramble. Land the result and the lesson.",
            ],
            "answer": "Situation → Task → Action → Result, ending on the measurable outcome and what you'd repeat. Keep it ~90 seconds, and use 'I' for your actions, not 'we' for everything.",
        },
        "practice": [
            {"level": 3, "q": "Rewrite for ATS and impact: 'Responsible for helping with various engineering tasks on team projects.'",
             "a": "Strip the duty language and add scope + result: 'Modelled and toleranced 12 machined parts across 3 team projects; cut drawing revision cycles 25% by building a parametric CAD library.' Mirror the job posting's keywords (CAD, tolerancing, DFM) and keep it one line."},
        ],
    },
    "ccd-5": {
        "example": {
            "level": 3,
            "problem": "You have two exams in 6 days and a lab report due in 3. Build an executable plan.",
            "steps": [
                "Write SMART goals for each: 'Lab report submitted Day 3'; '80% on both mock exams by Day 5'.",
                "Place the work in Eisenhower Q2: schedule 50-minute blocks now, not 'when I get to it'.",
                "Order by urgency × importance: lab report (Day 3) blocks first; interleave exam topics in spaced blocks.",
                "Use active recall only: closed-book practice problems and self-quizzing, not re-reading.",
                "Schedule a review slot each night for the day's errors, and protect sleep — recall consolidates in sleep.",
            ],
            "answer": "SMART goals, Q2 calendar blocks, urgency-ordered, active recall with nightly error review, sleep protected. A plan you can execute beats a plan that lists everything.",
        },
        "practice": [
            {"level": 3, "q": "You scored 55% on a quiz you studied 8 hours for. Run the reflection loop.",
             "a": "Separate process from content: what method did the 8 hours use (re-reading?), what topics cost marks, what question types failed (recall vs multi-step)? Then change ONE thing next cycle — typically switch from re-reading to closed-book practice and add spaced review — and re-measure on the next quiz."},
        ],
    },

    # ---------------------------- MODELING & DESIGN ----------------------- #
    "md-1": {
        "example": {
            "level": 3,
            "problem": "Run a full Pugh matrix for a phone stand: criteria cost 0.30, portability 0.25, stability 0.25, aesthetics 0.20. Concepts: folded card, hinged plastic, 3D-printed wedge. Datum = hinged plastic (all 0). Card: cost +2, portability +2, stability −2, aesthetics −1. Wedge: cost −1, portability 0, stability +2, aesthetics +1.",
            "steps": [
                "Hinged plastic is the datum → score 0 everywhere (total 0).",
                "Folded card: 0.30(+2) + 0.25(+2) + 0.25(−2) + 0.20(−1) = 0.60 + 0.50 − 0.50 − 0.20 = +0.40.",
                "3D wedge: 0.30(−1) + 0.25(0) + 0.25(+2) + 0.20(+1) = −0.30 + 0 + 0.50 + 0.20 = +0.40.",
                "Tie — run a sensitivity check: raise the stability weight to 0.35 (and cut aesthetics to 0.10).",
                "Recompute: card = 0.60 + 0.50 − 0.70 − 0.10 = +0.30; wedge = −0.30 + 0 + 0.70 + 0.10 = +0.50 → the wedge wins on stability-led weighting.",
            ],
            "answer": "Tie at +0.40 each; the decision hinges on how much you weight stability. State the weights you used — a matrix makes assumptions explicit, it does not produce certainty.",
        },
        "practice": [
            {"level": 3, "q": "Functionally decompose a 'portable phone charger' down to three sub-functions, then name a concept for each.",
             "a": "Sub-functions: (1) store energy → battery cell chemistry (Li-ion vs Li-polymer); (2) convert/regulate voltage → boost converter IC vs charge-pump; (3) interface to the phone → USB-C receptacle vs wireless coil vs pogo pins. Each sub-function has its own concept choice, recombined by morphological analysis."},
        ],
    },
    "md-2": {
        "example": {
            "level": 3,
            "problem": "You have a front view showing a rectangle with a solid circle in the middle and a side view showing a rectangle with a hidden dashed rectangle behind the front plane. Describe the part.",
            "steps": [
                "The front view's solid circle means a through-feature is visible from the front — likely a hole or boss along the front-to-back axis.",
                "The side view's hidden dashed rectangle sits behind the front face → an internal cavity or counterbore, not visible from the side.",
                "Cross-reference: the circle diameter must match the hidden rectangle's height in the side view.",
                "Because the hidden feature is a rectangle (not a circle) in the side view, the cavity is not round in that plane — it is a rectangular pocket, or the hole is drilled into a rectangular recess.",
                "Conclusion needs a third view or a section view to fix the depth and shape.",
            ],
            "answer": "A round through-feature on the front face leading into a rectangular internal cavity (pocket/counterbore). Two views define most of the shape; a section view is required to confirm depth and the pocket shape.",
        },
        "practice": [
            {"level": 3, "q": "Why must hidden lines be omitted in a section view, and what replaces them?",
             "a": "A section view shows the interior directly, so hidden (obscured) edges are no longer hidden — drawing them would be wrong by convention and would clutter the view. They are replaced by the visible solid edges of the cut, plus hatching on the cut material to distinguish it from background material."},
        ],
    },
    "md-3": {
        "example": {
            "level": 3,
            "problem": "A symmetric bracket needs 4 holes on a 100 mm bolt circle AND mirrored stiffening ribs on both sides. Describe an efficient, robust CAD strategy.",
            "steps": [
                "Fully constrain the base sketch first (black sketch) so later parameters rebuild predictably.",
                "Create ONE hole as a feature positioned on the bolt circle at a defined angle.",
                "Use a Circular Pattern on that hole: axis = centre, angle 360°, count 4, equal spacing.",
                "Create ONE rib feature on a plane at the symmetry centre; then Mirror the rib about the part's mid-plane rather than drawing a second rib.",
                "Order matters: place fillets AFTER patterns/mirrors so edges exist to fillet; name every feature for maintainability.",
            ],
            "answer": "Fully-constrained base sketch → one hole + circular pattern → one rib + mirror about the mid-plane → fillets last. Two 'source' features create eight real ones and a rebuild that survives edits.",
        },
        "practice": [
            {"level": 3, "q": "An assembly has 3 parts and 14 mates defined, but the parts still move. Diagnose.",
             "a": "Count degrees of freedom: each free rigid body has 6, so 3 parts = 18 DOF. Mates must remove all but the assembly's global 6 (or fully fix one part). 14 mates may include redundant mates on already-fixed DOF and still leave one axis free — typical culprits are a missing concentric or a coincident that only locks one rotation. Add the specific missing DOF constraint rather than more mates."},
        ],
    },
    "md-4": {
        "example": {
            "level": 3,
            "problem": "A 4-hole pattern on a 200 mm square is specified with position tolerance Ø0.5 MMC at LMC datum. Holes are Ø12.00/12.20; the mating studs are Ø11.90/11.95. Compute the MMC bonus tolerance and the resulting clearance range.",
            "steps": [
                "MMC of the hole = smallest permitted hole = 12.00 mm. Bonus tolerance = actual size − MMC.",
                "At the largest hole (12.20) the bonus is 12.20 − 12.00 = 0.20 mm, added to the Ø0.5 position tolerance → Ø0.70 allowed.",
                "Clearance = hole size − stud size. Minimum clearance (worst case): smallest hole 12.00 − largest stud 11.95 = 0.05 mm — but the position tolerance erodes this.",
                "Effective minimum clearance with position error: 0.05 − (0.5/2 on each side) — for a Ø tolerance zone, subtract the full radial allowance: 0.05 − 0.5 = −0.45 mm at MMC (i.e. interference is possible).",
                "At LMC with bonus: clearance available = (12.20 − 11.90) = 0.30 mm plus the 0.20 mm bonus → far more forgiving.",
            ],
            "answer": "Bonus tolerance at LMC = 0.20 mm (zone grows Ø0.5 → Ø0.70). At MMC the 0.05 mm clearance is smaller than the position zone, so interference is possible — tighten the size limits or loosen the position callout.",
        },
        "practice": [
            {"level": 3, "q": "Explain why a hole dimensioned 10.00/10.05 with a shaft at 9.98/9.99 is a clearance fit, and give both clearances.",
             "a": "The hole is always larger than the shaft (10.00 > 9.99), so clearance always exists. Minimum clearance = 10.00 − 9.99 = 0.01 mm; maximum clearance = 10.05 − 9.98 = 0.07 mm. The allowance (intentional minimum) is 0.01 mm."},
        ],
    },
    "md-5": {
        "example": {
            "level": 3,
            "problem": "A 4-part stack has tolerances ±0.10, ±0.15, ±0.20, ±0.25 mm. The design permits ±0.60 mm. Decide worst-case vs RSS, and justify against cost.",
            "steps": [
                "Worst-case total = 0.10 + 0.15 + 0.20 + 0.25 = 0.70 mm — exceeds the ±0.60 mm allowance, so a worst-case guarantee fails.",
                "RSS total = √(0.10² + 0.15² + 0.20² + 0.25²) = √(0.01+0.0225+0.04+0.0625) = √0.135 = 0.367 mm — comfortably inside.",
                "Interpretation: the design is fine for high-volume production where part errors are independent and centred — a few assemblies may exceed, at a calculable reject rate.",
                "If every assembly must fit (low volume, safety-critical), you must tighten a tolerance instead.",
                "Cost-optimal fix: tighten only the two LOOSEST contributors (0.20 → 0.15, 0.25 → 0.15), since tight tolerances on already-tight features cost the most per unit of improvement.",
            ],
            "answer": "Worst-case fails (0.70 > 0.60); RSS passes (0.367). Use RSS with a documented reject allowance for volume production, or tighten the two loose contributors if every unit must assemble.",
        },
        "practice": [
            {"level": 3, "q": "A part is failing fit checks and a colleague proposes halving all tolerances. Critique this.",
             "a": "It treats the symptom and multiplies cost — cost rises steeply as tolerances tighten and the real cause is likely elsewhere (a datum error, a stackup not analysed, or a process capability issue). Diagnose first: compute the actual stackup (worst-case vs RSS), measure the process capability (Cpk), and tighten only the contributor that actually consumes the budget."},
        ],
    },

    # ------------------------------- STATICS ------------------------------ #
    "sm-1": {
        "example": {
            "level": 3,
            "problem": "Forces F₁ = 200 N along +x and F₂ = 150 N at 120° from +x both act at the origin. Find the resultant magnitude and direction.",
            "steps": [
                "Components: F₁ = (200, 0). F₂ = (150cos120°, 150sin120°) = (−75, 129.9).",
                "Sum: R = (200 − 75, 0 + 129.9) = (125, 129.9) N.",
                "Magnitude: |R| = √(125² + 129.9²) = √(15625 + 16874) = √32499 ≈ 180.3 N.",
                "Direction: θ = atan2(129.9, 125) = 46.1° above the +x axis.",
                "Sanity check: the resultant must lie between the two forces (0° and 120°) — 46.1° ✓.",
            ],
            "answer": "R ≈ 180 N at 46° above the +x axis.",
        },
        "practice": [
            {"level": 3, "q": "Find the moment of F = (30, 40) N acting at point (2, 1) m about the axis through the origin: the z-axis, and then about a vertical line at x = 4 m.",
             "a": "About O: M_z = xF_y − yF_x = (2)(40) − (1)(30) = 80 − 30 = 50 N·m (CCW). About x = 4: the perpendicular distance from that line to the line of action changes the reference point to (4, 0): M = (2−4)(40) − (1−0)(30) = −80 − 30 = −110 N·m, i.e. 110 N·m CW."},
        ],
    },
    "sm-2": {
        "example": {
            "level": 3,
            "problem": "A 15 kg lamp hangs from a point where three cables meet: one horizontal to a wall, one at 50° above horizontal to a ceiling, one vertical to the lamp. Find all tensions.",
            "steps": [
                "FBD at the knot: weight W = 15 × 9.81 = 147.2 N down; vertical cable tension T_v = W = 147.2 N (it carries the lamp).",
                "Actually the vertical cable IS the lamp's support, so the knot feels 147.2 N down from it. Let T_h = horizontal cable, T_c = ceiling cable at 50°.",
                "ΣF_y = 0: T_c sin50° − 147.2 = 0 → T_c = 147.2/0.766 = 192.2 N.",
                "ΣF_x = 0: T_c cos50° − T_h = 0 → T_h = 192.2 × 0.643 = 123.6 N.",
                "Check ΣF_y again with the horizontal cable's zero vertical component ✓.",
            ],
            "answer": "Ceiling cable T_c ≈ 192 N, horizontal cable T_h ≈ 124 N. The steeper the cable, the less horizontal load it must resist.",
        },
        "practice": [
            {"level": 3, "q": "A 60 kg crate rests on a frictionless 25° incline held by a rope parallel to the surface. Find the tension and the normal force.",
             "a": "T = mg sin25° = (60)(9.81)(0.4226) = 248.7 N. N = mg cos25° = (60)(9.81)(0.9063) = 533.4 N."},
        ],
    },
    "sm-3": {
        "example": {
            "level": 3,
            "problem": "An 8 m beam (weight 300 N, uniform) is pinned at A (left) and supported by a roller at B (right). A triangular distributed load rises from 0 at A to 600 N/m at B. Find the reactions.",
            "steps": [
                "Triangular load resultant = ½ × base × height = ½(8)(600) = 2400 N, acting at ⅓ from the tall end, i.e. 8/3 = 2.67 m from B, or 8 − 2.67 = 5.33 m from A.",
                "FBD: A_y and A_x at A, B_y at B, beam weight 300 N down at 4 m, distributed resultant 2400 N down at 5.33 m.",
                "No horizontal loads → A_x = 0.",
                "ΣM_A = 0: B_y(8) − 300(4) − 2400(5.33) = 0 → 8B_y = 1200 + 12792 = 13992 → B_y = 1749 N.",
                "ΣF_y = 0: A_y = 300 + 2400 − 1749 = 951 N.",
                "Check ΣM_B: A_y(8) − 300(4) − 2400(2.67) = 7608 − 1200 − 6408 = 0 ✓.",
            ],
            "answer": "A_y ≈ 951 N, B_y ≈ 1749 N, A_x = 0. The rolling support near the heavy end carries the larger share — always check the moment balance.",
        },
        "practice": [
            {"level": 3, "q": "A three-force member has forces at 0.5 m, 1.5 m and a reaction. If the first two are vertical, what must the third be?",
             "a": "The three forces must be concurrent (their lines of action meet at one point) or parallel. Two are vertical hence parallel, so the third must also be vertical — a tilted reaction would violate the three-force concurrency condition."},
        ],
    },
    "sm-4": {
        "example": {
            "level": 3,
            "problem": "A Pratt truss spans 8 m with 4 panels of 2 m; a 10 kN load hangs at the centre bottom joint. Use the method of sections to find the force in the middle bottom chord member.",
            "steps": [
                "Whole truss: symmetric, so each support carries 5 kN. Reactions A_y = B_y = 5 kN.",
                "Cut vertically through the middle panel, isolating the LEFT half (support A and two joints).",
                "The cut passes through: top chord (compression), a diagonal (tension), and the bottom chord (tension).",
                "Take moments about the top joint where the diagonal and top chord meet — this eliminates both, leaving only the bottom chord force.",
                "The 5 kN reaction at A is 4 m from that top joint; the 10 kN load is 2 m from the centreline at the bottom joint.",
                "ΣM about the top joint: (5 kN)(4 m) − F_bottom(2 m) = 0 → F_bottom = 20/2 = 10 kN.",
            ],
            "answer": "The middle bottom chord carries 10 kN in TENSION. Choosing the moment point to kill two unknowns is the whole trick of the method of sections.",
        },
        "practice": [
            {"level": 3, "q": "In a truss, a joint has 3 members: two collinear and one perpendicular, with no external load. What is the perpendicular member's force?",
             "a": "Zero-force member. The two collinear members balance each other along that axis, and with no external load the perpendicular member has nothing to resist in its direction, so ΣF along it forces F = 0."},
        ],
    },
    "sm-5": {
        "example": {
            "level": 3,
            "problem": "A 25 kg block sits on a 30° incline with μ_s = 0.35, μ_k = 0.28. (a) Does it slide? (b) If a push parallel to the incline is applied downward, what push starts it moving? (c) Once moving, what push keeps it moving at constant speed downward?",
            "steps": [
                "Normal force: N = mg cos30° = 25 × 9.81 × 0.866 = 212.4 N. Gravity component along the slope = mg sin30° = 245.25 × 0.5 = 122.6 N.",
                "Max static friction = μ_s N = 0.35 × 212.4 = 74.3 N. Since 122.6 > 74.3, it slides on its own.",
                "(a) It slides (gravity down-slope exceeds max static friction).",
                "Note: since it already slides, an additional downward push is unnecessary — but for the push that would start motion from rest on a shallower incline, the push would be 122.6 − 74.3 = 48.3 N. On THIS incline it is already sliding.",
                "(c) Kinetic friction = μ_k N = 0.28 × 212.4 = 59.5 N. For constant velocity downward, applied push + mg sin30° = friction? No — moving down-slope, friction acts UP-slope: to move at constant speed the net force is zero, so push + 122.6 = 59.5, i.e. a push of −63.1 N means you must hold it BACK with 63 N up-slope; a downward push only accelerates it.",
            ],
            "answer": "(a) Yes, it slides (122.6 N > 74.3 N). (b) Not applicable here — it already moves; the threshold push would be 48.3 N on a steeper-friction configuration. (c) To descend at constant speed you apply 63 N UP the slope (or accept acceleration) — kinetic friction (59.5 N) is less than the gravity component (122.6 N), so it accelerates unless restrained.",
        },
        "practice": [
            {"level": 3, "q": "A rope is wrapped 270° around a bollard with μ = 0.30. A dock worker can pull 400 N. What load on the other end can they hold?",
             "a": "β = 270° = 4.712 rad. T₂ = T₁e^(μβ) = 400 × e^(0.30×4.712) = 400 × e^1.414 = 400 × 4.11 ≈ 1645 N. The wrap multiplies holding force about fourfold."},
        ],
    },
    "sm-6": {
        "example": {
            "level": 3,
            "problem": "An I-shape is a 200 mm × 20 mm top flange on a 150 mm × 15 mm web. Find the centroid height from the bottom and the moment of inertia about the horizontal centroidal axis.",
            "steps": [
                "Split into two rectangles: web (bottom) 15 × 150 with area A₁ = 2250 mm², centroid at 75 mm. Flange (top) 200 × 20 with A₂ = 4000 mm², centroid at 150 + 10 = 160 mm.",
                "Weighted centroid: ȳ = (A₁y₁ + A₂y₂)/(A₁+A₂) = (2250×75 + 4000×160)/6250 = (168750 + 640000)/6250 = 808750/6250 = 129.4 mm.",
                "Web's own I about its centroid: b h³/12 with b = 15, h = 150 → 15×150³/12 = 4.219×10⁶ mm⁴. Shift by d₁ = |129.4 − 75| = 54.4 → I₁ = 4.219e6 + 2250(54.4²) = 4.219e6 + 6.660e6 = 10.88×10⁶ mm⁴.",
                "Flange's own I: b h³/12 with b = 200, h = 20 → 200×20³/12 = 1.333×10⁵ mm⁴. Shift by d₂ = |160 − 129.4| = 30.6 → I₂ = 1.333e5 + 4000(30.6²) = 1.333e5 + 3.745e6 = 3.878×10⁶ mm⁴.",
                "Total: I = 10.88e6 + 3.878e6 = 14.76×10⁶ mm⁴.",
            ],
            "answer": "ȳ ≈ 129.4 mm from the bottom; I ≈ 14.8 × 10⁶ mm⁴ about the horizontal centroidal axis — the parallel-axis shifts dominate, so never skip them.",
        },
        "practice": [
            {"level": 3, "q": "For the same shape, find I about the BOTTOM edge. Which is larger?",
             "a": "I_bottom = I_centroidal + A d² = 14.76e6 + 6250(129.4²) = 14.76e6 + 104.7e6 = 119.4×10⁶ mm⁴. About the edge is far larger — the centroidal axis always gives the MINIMUM moment of inertia."},
        ],
    },

    # --------------------------- ENGINEERING MATERIALS -------------------- #
    "em-1": {
        "example": {
            "level": 3,
            "problem": "Rank NaCl, diamond, and copper by melting point and explain the ordering in terms of bonding.",
            "steps": [
                "Identify the bond type: NaCl is ionic (electron transfer); diamond is covalent (continuous 3D network of shared electrons); copper is metallic (delocalised electron sea).",
                "Compare bond strengths: diamond's covalent C–C network is the strongest, requiring the most energy to break → highest melting point (~3550 °C).",
                "NaCl's ionic lattice is strong but weaker than diamond's network → ~801 °C.",
                "Copper's metallic bonding is relatively weak per bond and non-directional → ~1085 °C, but it is ductile because planes can slide.",
                "Ranking by melting point: diamond > copper > NaCl — note that the ranking by melting point is NOT the same as ranking by hardness or ductility.",
            ],
            "answer": "Diamond (~3550 °C) > copper (~1085 °C) > NaCl (~801 °C). Covalent network > metallic > ionic in bond energy here, but only the metal is ductile — the non-directional metallic bond allows slip.",
        },
        "practice": [
            {"level": 3, "q": "A material is a hard electrical insulator that melts at 2000 °C. What bonding would you expect, and give an example?",
             "a": "A covalent network solid (or a strongly ionic crystal). Hardness + electrical insulation + very high melting point points to covalent network bonding — e.g. silicon carbide (SiC), silicon nitride (Si₃N₄), or quartz (SiO₂). Delocalised electrons are absent, so it cannot conduct."},
        ],
    },
    "em-2": {
        "example": {
            "level": 3,
            "problem": "Iron is BCC at room temperature with A = 55.85 g/mol and r = 0.124 nm. Compute its theoretical density.",
            "steps": [
                "BCC: n = 2 atoms per cell; atoms touch along the body diagonal: a = 4r/√3.",
                "a = 4(0.124)/1.732 = 0.496/1.732 = 0.2864 nm = 2.864×10⁻⁸ cm.",
                "Cell volume V = a³ = (2.864e-8)³ = 2.350×10⁻²³ cm³.",
                "ρ = nA/(V·N_A) = (2 × 55.85)/(2.350e-23 × 6.022e23).",
                "Denominator = 14.15; numerator = 111.7 → ρ = 7.89 g/cm³.",
                "Measured iron density is 7.87 g/cm³ — the small gap is the presence of vacancies and defects.",
            ],
            "answer": "ρ ≈ 7.89 g/cm³ (measured 7.87), confirming the BCC structure with n = 2 and the body-diagonal lattice relation.",
        },
        "practice": [
            {"level": 3, "q": "A plane cuts the x, y and z axes at 1, 2 and ∞ (parallel to z). Give its Miller indices.",
             "a": "Reciprocals of the intercepts (1, 2, ∞) → (1/1, 1/2, 0) = (1, 0.5, 0). Clear fractions ×2 → (2, 1, 0). The plane is (210)."},
        ],
    },
    "em-3": {
        "example": {
            "level": 3,
            "problem": "A tensile test on a Ø10 mm bar (L₀ = 50 mm, E = 200 GPa) yields: 0.2% offset yield at 32 kN, maximum load 45 kN, fracture length 62 mm. Find σ_y, UTS, %EL, the elastic strain at yield, and the resilience.",
            "steps": [
                "A₀ = π(10²)/4 = 78.54 mm².",
                "σ_y = 32 000/78.54 = 407.4 N/mm² = 407 MPa.",
                "UTS = 45 000/78.54 = 572.9 MPa.",
                "%EL = (62 − 50)/50 × 100 = 24 %.",
                "Elastic strain at yield: ε_y = σ_y/E = 407e6/200e9 = 2.04×10⁻³ (0.204 %).",
                "Resilience U_r = σ_y²/(2E) = (407e6)²/(2×200e9) = 1.656e17/4e11 = 4.14×10⁵ J/m³ = 414 kJ/m³.",
            ],
            "answer": "σ_y ≈ 407 MPa, UTS ≈ 573 MPa, %EL = 24 % (ductile), ε_y ≈ 0.204 %, U_r ≈ 414 kJ/m³.",
        },
        "practice": [
            {"level": 3, "q": "At necking the true stress is much higher than the engineering stress. Explain why, using the relationship.",
             "a": "True stress uses the instantaneous area: σ_t = σ_eng(1 + ε_eng) = F/A_instant. As the specimen necks, A drops sharply while F falls only slightly, so the true stress keeps rising past the engineering UTS even though the engineering curve turns down. That is why the engineering maximum and the true-stress maximum occur at different points."},
        ],
    },
    "em-4": {
        "example": {
            "level": 3,
            "problem": "A 1.2 wt% C steel is cooled slowly from 1000 °C. Just above 727 °C, find the mass fractions of proeutectoid cementite and austenite, then state the final room-temperature microstructure.",
            "steps": [
                "This is a hypereutectoid alloy (C₀ = 1.2 > 0.76), so proeutectoid cementite forms first, not ferrite.",
                "At just above 727 °C the bounding compositions are austenite at 0.76 %C and cementite at 6.70 %C.",
                "Lever rule for austenite: W_γ = (6.70 − 1.2)/(6.70 − 0.76) = 5.50/5.94 = 0.926.",
                "W_Fe₃C = 1 − 0.926 = 0.074 (7.4 % proeutectoid cementite).",
                "Below 727 °C the austenite transforms to pearlite (ferrite + cementite lamellae), leaving the proeutectoid cementite as a continuous network on the prior-austenite grain boundaries.",
            ],
            "answer": "≈7.4 % proeutectoid cementite + 92.6 % austenite at 727 °C; at room temperature the microstructure is pearlite with a continuous proeutectoid cementite network at the grain boundaries — hard, and brittle because of that network.",
        },
        "practice": [
            {"level": 3, "q": "A steel is quenched in water (fast) versus furnace-cooled (slow). Predict the microstructures and the property difference.",
             "a": "Fast water quench: austenite is suppressed from transforming by diffusion, producing martensite — very hard, very brittle. Slow furnace cool: full diffusion gives coarse pearlite (plus proeutectoid phase) — softer and much tougher. Tempering the martensite trades some hardness back for toughness."},
        ],
    },
    "em-5": {
        "example": {
            "level": 3,
            "problem": "A weld region has K_Ic = 55 MPa·√m and carries 150 MPa. (a) Find the critical half-crack length. (b) If inspection reliably detects cracks of 15 mm, is the structure safe? (c) What if the stress rises to 220 MPa?",
            "steps": [
                "K = Yσ√(πa) with Y = 1; set K = K_Ic and solve for a: a_c = (K_Ic/σ)²/π.",
                "(a) a_c = (55/150)²/π = (0.3667)²/π = 0.1344/3.1416 = 0.0428 m = 42.8 mm.",
                "(b) If inspection finds cracks ≥ 15 mm, that is below the 42.8 mm critical length → the structure is safe at 150 MPa with margin.",
                "(c) At 220 MPa: a_c = (55/220)²/π = (0.25)²/π = 0.0625/3.1416 = 0.0199 m = 19.9 mm.",
                "Now a 15 mm detected crack is uncomfortably close to critical — and undetectable cracks below 15 mm plus fatigue growth will reach it quickly. The doubled stress more than halves the tolerance.",
            ],
            "answer": "(a) a_c ≈ 42.8 mm. (b) Safe at 150 MPa with a 15 mm detection floor. (c) At 220 MPa a_c drops to ≈19.9 mm, so the same inspection floor is no longer adequate — lower the stress, improve inspection, or increase toughness.",
        },
        "practice": [
            {"level": 3, "q": "Two identical shafts operate at 300 MPa: one in air, one in seawater. Explain the failure difference.",
             "a": "The seawater shaft undergoes electrochemical corrosion, which pits the surface. Pits are stress raisers that concentrate stress and accelerate fatigue-crack initiation, so the seawater shaft fails at far fewer cycles — the environment degraded the surface condition, not the bulk strength."},
        ],
    },
    "em-6": {
        "example": {
            "level": 3,
            "problem": "Select a material for a light, stiff panel (bending-limited, flat). Compare: steel (E = 200 GPa, ρ = 7850 kg/m³), aluminium (E = 70 GPa, ρ = 2700), CFRP (E = 150 GPa, ρ = 1550).",
            "steps": [
                "For a flat panel in bending the performance index is M = E^(1/3)/ρ (a beam uses E^(1/2)/ρ, a tie uses E/ρ).",
                "Steel: E^(1/3) = (200e9)^(1/3) = 5848; M = 5848/7850 = 0.745.",
                "Aluminium: (70e9)^(1/3) = 4121; M = 4121/2700 = 1.526.",
                "CFRP: (150e9)^(1/3) = 5313; M = 5313/1550 = 3.428.",
                "Ranking: CFRP > aluminium > steel. CFRP wins by a factor of ~4.6 over steel.",
                "Now constrain: cost, service temperature, and impact. CFRP is expensive and brittle in impact; steel is cheap and tolerant; aluminium is the middle ground.",
            ],
            "answer": "By the panel index CFRP ≈ 3.43 > aluminium ≈ 1.53 > steel ≈ 0.75. Choose CFRP if weight dominates and cost/impact allow; aluminium if cost matters; steel if impact tolerance or cost dominates.",
        },
        "practice": [
            {"level": 3, "q": "A composite has 40 % (by volume) carbon fibre (E_f = 230 GPa) in an epoxy matrix (E_m = 3.5 GPa), aligned. Find the rule-of-mixtures stiffness.",
             "a": "E_c = fE_f + (1−f)E_m = 0.40(230) + 0.60(3.5) = 92 + 2.1 = 94.1 GPa. The fibres dominate because they are much stiffer and carry the load along their axis; transverse to the fibres the stiffness would be far lower."},
        ],
    },
}
