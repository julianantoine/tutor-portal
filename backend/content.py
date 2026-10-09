"""
Tutor Portal — curriculum content.

Four sophomore engineering-technology courses. For each course: units with
key concepts, formulas, a worked example, common traps, and practice problems.
A separate MCQ bank feeds the quiz engine; flashcards are generated from the
concepts + formulas so there is one source of truth.

NOTE: the unit breakdown follows the standard catalog treatment of each
course title. Swap in the actual syllabus topics where they differ — the
data model is plain dicts, so edits here flow to every surface.
"""

# ---------------------------------------------------------------------------
# COURSES
# ---------------------------------------------------------------------------

COURSES = [
    {
        "code": "CCD-101",
        "title": "Character, Career and Self Development",
        "short": "Career & Self Dev",
        "credits": 2,
        "accent": "#52525b",
        "blurb": "Engineering ethics, professional communication, teamwork, and career readiness.",
        "units": [
            {
                "id": "ccd-1",
                "title": "Professional Identity & Engineering Ethics",
                "summary": "What it means to be a professional engineer, and how to reason through an ethical dilemma.",
                "concepts": [
                    {"t": "Profession vs. job", "d": "A profession has a code of ethics, a licensure/credentialing path, and a duty to public safety — not just an employer."},
                    {"t": "NSPE Code of Ethics", "d": "Fundamental canons: hold public safety paramount, perform only in your competence, be truthful and objective, act as a faithful agent of each employer, avoid conflicts of interest, enhance the profession's honor."},
                    {"t": "Three ethical frameworks", "d": "Utilitarian (greatest good — outcomes), Rights/Duty (respect rights & rules — Kant), Virtue (what would a person of good character do). Most cases look different under each."},
                    {"t": "Public safety paramount", "d": "The NSPE canon that overrides others: when public safety is at risk, that wins over employer loyalty or profit."},
                    {"t": "Whistleblowing", "d": "Disclosing wrongdoing. Justified when there is serious harm, you have exhausted internal channels, and you have documented evidence. A near-universal sign-on to every code."},
                    {"t": "Conflicts of interest", "d": "Disclose, recuse, or get written approval. Never let a personal interest quietly steer a technical judgement."},
                ],
                "formulas": [
                    {"n": "Ethical test (utilitarian)", "e": "Compare Σ Benefits − Σ Harms for each option", "note": "Quantify only to compare; the hard part is valuing safety and lives honestly."},
                    {"n": "Rights test", "e": "Ask: does the action respect the rights of all stakeholders?", "note": "Kant: would you accept this as a universal rule?"},
                    {"n": "Disclosure test", "e": "Would I be comfortable if this decision were public?", "note": "A quick smell test for conflicts of interest."},
                ],
                "example": {
                    "problem": "A supervisor tells you to sign off on a structural weld you believe is undersized because the inspection deadline is today. What do you do?",
                    "steps": [
                        "Identify stakeholders: public/users (safety), employer (schedule/reputation), you (job, license, integrity).",
                        "Framework check — utilitarian: risk of failure (serious harm) outweighs a schedule delay. Rights: users have a right to safe structures. Virtue: a competent engineer does not falsify a judgement.",
                        "NSPE canon: public safety is paramount — it overrides the deadline pressure.",
                        "Action: do not sign; document the concern in writing; propose a fix (re-weld, re-inspect) and escalate to the next level if refused.",
                    ],
                    "answer": "Refuse to sign, document in writing, propose remediation, escalate. Safety > schedule; your licence and the public depend on an honest technical call.",
                },
                "traps": [
                    "'Just following orders' — acting under instruction is NOT a defence for a professional judgement.",
                    "Choosing one framework and ignoring the others: state which you used and why.",
                    "Treating ethics as opinion — the codes and canon give a defensible standard.",
                ],
                "practice": [
                    {"q": "A vendor offers you free equipment for your lab if you recommend their product. Which canon applies?", "a": "Conflict of interest — disclose it and recuse from the recommendation; free goods must not steer a technical judgement."},
                    {"q": "Which NSPE canon overrides the rest when they conflict?", "a": "Hold paramount the safety, health, and welfare of the public."},
                    {"q": "Give the three frameworks and one case where they disagree.", "a": "Utilitarian, rights, virtue. A bridge-cost cut that harms a few but saves money: utilitarian may favour the cut; rights/virtue object."},
                ],
            },
            {
                "id": "ccd-2",
                "title": "Technical Communication",
                "summary": "Writing and presenting engineering work so a decision-maker can act on it.",
                "concepts": [
                    {"t": "Audience analysis", "d": "Before writing, name the reader: technical peer, manager (wants decisions/cost), or public (wants plain language). Same facts, different framing."},
                    {"t": "The inverted pyramid", "d": "Engineering reports lead with the conclusion/recommendation, then evidence, then method. Busy readers stop after the first paragraph."},
                    {"t": "Executive summary", "d": "One page: problem, what you did, key result, recommendation/next step. Written last, read first."},
                    {"t": "Figures and tables", "d": "Every figure needs a number, a caption, and an in-text reference. Axis labels carry units. A figure the reader can't read is a defect."},
                    {"t": "Plain-language rules", "d": "Active voice, short sentences, one idea per sentence, define jargon on first use, no nominalisations ('utilise' → 'use')."},
                    {"t": "Presentation structure", "d": "Tell them what you'll say, say it, tell them what you said. One message per slide; slides support you, not the reverse."},
                ],
                "formulas": [
                    {"n": "Inverted pyramid", "e": "Recommendation → Evidence → Method → Appendix", "note": "Reverse of how most people write. Reorder after drafting."},
                    {"n": "Slide rule of thumb", "e": "≈ 1 idea / slide, ≤ 6 lines, font ≥ 24 pt", "note": "If it doesn't fit, it belongs in the appendix or a handout."},
                ],
                "example": {
                    "problem": "Rewrite for a busy plant manager: 'An investigation of the failure modes of the pump was undertaken and it was determined that cavitation was the causative mechanism.'",
                    "steps": [
                        "Find the recommendation/result: the pump failed by cavitation.",
                        "Lead with it; drop passive voice and nominalisations.",
                        "Keep the evidence available below: NPSH margin too low, impeller erosion pattern.",
                    ],
                    "answer": "'The pump failed by cavitation. The cause is a low NPSH margin at high flow.' — result first, mechanism second, evidence in the body.",
                },
                "traps": [
                    "Burying the conclusion on page 8 — the manager never gets there.",
                    "Unlabelled axes or a missing unit — makes the figure meaningless and loses trust.",
                    "Slides with paragraphs — the audience reads instead of listening.",
                ],
                "practice": [
                    {"q": "What goes in the first sentence of an engineering memo?", "a": "The conclusion or recommendation (inverted pyramid)."},
                    {"q": "Name three checks for a good technical figure.", "a": "Numbered + captioned, axes labelled with units, referenced in the text."},
                ],
            },
            {
                "id": "ccd-3",
                "title": "Teamwork, Leadership & Conflict",
                "summary": "How engineering teams form, why they fight, and how to resolve it cheaply.",
                "concepts": [
                    {"t": "Tuckman stages", "d": "Forming → Storming → Norming → Performing (→ Adjourning). Conflict in Storming is normal, not failure."},
                    {"t": "Belbin team roles", "d": "Effective teams cover nine behaviours (Plant, Coordinator, Shaper, Monitor-Evaluator, Implementer, Completer-Finisher, Resource Investigator, Teamworker, Specialist). Gaps cause predictable failure."},
                    {"t": "Thomas-Kilmann conflict modes", "d": "Competing, Collaborating, Compromising, Avoiding, Accommodating — chosen by assertiveness × cooperativeness. Collaborate for important + trust; avoid only for trivial."},
                    {"t": "Feedback: SBI", "d": "Situation–Behaviour–Impact. Describe observable behaviour and its effect; avoid character judgements."},
                    {"t": "Psychological safety", "d": "A shared belief it's safe to speak up. It is the strongest predictor of team learning; build it with questions, not blame."},
                ],
                "formulas": [
                    {"n": "Conflict choice", "e": "Importance ↑ & relationship ↑ → Collaborate", "note": "Assertive + cooperative quadrant."},
                    {"n": "SBI feedback", "e": "In <situation>, when you <behaviour>, the impact was <impact>", "note": "Behaviour = observable; impact = effect, not judgement."},
                ],
                "example": {
                    "problem": "A teammate keeps missing deadlines, and the team is falling behind. Your report is due tomorrow.",
                    "steps": [
                        "Diagnose stage: this is Storming pressure, not yet a people problem.",
                        "Use SBI privately: 'At the last two stand-ups (S), the design file wasn't updated (B), which blocked my analysis (I).'",
                        "Choose a mode: Collaborating — the relationship and the deadline both matter.",
                        "Agree a concrete change (smaller, earlier checkpoints) and a review date.",
                    ],
                    "answer": "Private SBI conversation, collaborative mode, agree a concrete checkpoint change and follow up — do not escalate or absorb the work silently.",
                },
                "traps": [
                    "Avoiding conflict to 'keep the peace' — it reappears worse at the deadline.",
                    "Feedback that attacks the person ('you're lazy') instead of the behaviour.",
                    "Escalating before trying a direct, respectful conversation.",
                ],
                "practice": [
                    {"q": "Which conflict mode fits a trivial issue you'll never see again?", "a": "Avoiding (or Accommodating) — low importance, low stakes."},
                    {"q": "Expand SBI and give one example.", "a": "Situation–Behaviour–Impact. e.g. 'In stand-up today, when you cut the checklist step, it worried the client.'"},
                ],
            },
            {
                "id": "ccd-4",
                "title": "Career Readiness",
                "summary": "Résumés, interviewing, and the path from student to licensed engineer.",
                "concepts": [
                    {"t": "Résumé structure", "d": "One page: contact, education, relevant experience/projects (bulleted, results first), skills, leadership. No photo, no 'references on request'."},
                    {"t": "STAR bullets", "d": "Situation–Task–Action–Result. Lead with a strong verb and quantify the result ('Cut model-prep time 30% by scripting a macro')."},
                    {"t": "Behavioural interviews", "d": "Interviewers ask for stories ('tell me about a conflict'); answer with STAR, keep it 90 seconds, end on the result/lesson."},
                    {"t": "ATS reality", "d": "Applicant Tracking Systems parse your file: mirror the job's keywords, use a simple single-column layout, avoid tables/graphics columns."},
                    {"t": "Licensure path", "d": "ABET degree → FE exam (Fundamentals of Engineering, often senior year) → ~4 years supervised experience → PE exam. FE/PE matter for public-works and consulting roles."},
                    {"t": "Networking & follow-up", "d": "Most roles are filled through people. Send a specific thank-you within 24 h referencing something you discussed."},
                ],
                "formulas": [
                    {"n": "STAR", "e": "Situation → Task → Action → Result", "note": "Every résumé bullet and interview answer follows this shape."},
                    {"n": "Bullet formula", "e": "Strong verb + what you did + measurable result", "note": "'Reduced X by Y% by doing Z.'"},
                ],
                "example": {
                    "problem": "Turn 'worked on a bridge project' into a résumé bullet.",
                    "steps": [
                        "Name the task and your specific action, not the team's.",
                        "Add a number if you can (scope, cost, time, %).",
                        "Lead with the strongest verb; keep to one line.",
                    ],
                    "answer": "“Modelled a 40-ft pedestrian bridge in CAD; cut drawing revision cycles 25% by building a parametric assembly.”",
                },
                "traps": [
                    "Duties instead of results — 'responsible for' tells the reader nothing.",
                    "A two-column template that ATS software mangles; you never get seen.",
                    "No follow-up after the interview — a large share of offers are won there.",
                ],
                "practice": [
                    {"q": "What do the letters FE and PE stand for and when do you take them?", "a": "Fundamentals of Engineering (typically near graduation) and Principles and Practice of Engineering (after ~4 years supervised experience)."},
                    {"q": "Give the STAR expansion and what each part must contain.", "a": "Situation (context), Task (your goal), Action (what YOU did), Result (measurable outcome/lesson)."},
                ],
            },
            {
                "id": "ccd-5",
                "title": "Self-Management & Growth Mindset",
                "summary": "The habits that keep a heavy engineering load from crushing you.",
                "concepts": [
                    {"t": "SMART goals", "d": "Specific, Measurable, Achievable, Relevant, Time-bound. 'Do better in statics' is not a goal; 'finish 10 practice problems per unit before each quiz' is."},
                    {"t": "Eisenhower matrix", "d": "Sort by urgency × importance. Spend time in Quadrant II (important, not urgent): studying early, sleep, exercise."},
                    {"t": "Deep work blocks", "d": "Study in 50-minute focus blocks with phones out of the room. Multitasking raises mistakes on problem sets."},
                    {"t": "Growth mindset", "d": "Ability grows with effort and strategy. 'I can't do statics' → 'I haven't found the right method yet.' Effort + feedback = learning."},
                    {"t": "Reflection loop", "d": "After each exam: what worked, what failed, one change next time. A 10-minute review beats another hour of aimless reading."},
                ],
                "formulas": [
                    {"n": "SMART", "e": "Specific · Measurable · Achievable · Relevant · Time-bound", "note": "Test every goal against all five."},
                    {"n": "Eisenhower quadrants", "e": "Q1 urgent+important (do) · Q2 not-urgent+important (schedule) · Q3 urgent+not-important (delegate) · Q4 neither (delete)", "note": "Win by living in Q2."},
                ],
                "example": {
                    "problem": "You have a statics quiz in 5 days and keep cramming the night before. Build a plan.",
                    "steps": [
                        "SMART goal: 'Complete the truss and friction practice sets (10 problems each) by Day 3, and a full mock quiz on Day 4.'",
                        "Place in Q2: schedule 50-minute blocks Days 1-3 in your calendar, not 'when I get to it'.",
                        "Active recall: redo problems closed-book, then check; flashcards for formulas.",
                        "Reflect after the quiz: note the two topics that cost the most marks; target them next cycle.",
                    ],
                    "answer": "Schedule Q2 focus blocks, do closed-book practice sets (not re-reading), then a timed mock quiz, then a short reflection to retarget.",
                },
                "traps": [
                    "Confusing busy with productive — highlighting a textbook is not studying.",
                    "All-night cramming: recall collapses within days; spaced practice wins.",
                    "Setting a vague goal you can never tell you've met.",
                ],
                "practice": [
                    {"q": "Which Eisenhower quadrant should most study time live in, and why?", "a": "Quadrant II (important, not urgent) — that's where prevention and real learning happen."},
                    {"q": "Rewrite 'study more' as a SMART goal.", "a": "e.g. 'Finish 12 statics practice problems per week, tracked in a log, through the end of the term.'"},
                ],
            },
        ],
    },
    {
        "code": "MD-102",
        "title": "Modeling and Design",
        "short": "Modeling & Design",
        "credits": 3,
        "accent": "#71717a",
        "blurb": "The engineering design process, visualization, CAD solid modeling, and engineering drawings.",
        "units": [
            {
                "id": "md-1",
                "title": "The Engineering Design Process",
                "summary": "From a vague need to a justified concept choice.",
                "concepts": [
                    {"t": "Design vs. analysis", "d": "Analysis has one right answer given assumptions; design has many defensible answers and needs a rationale. You justify, you don't 'solve'."},
                    {"t": "Problem definition", "d": "Write the need as a problem statement plus a requirements list: functional (what it must do) and constraints (limits: budget, size, safety codes)."},
                    {"t": "Functional decomposition", "d": "Break the top function into sub-functions (e.g. 'transmit torque' → 'couple input', 'reduce speed', 'seal lubricant'). Each sub-function gets its own concepts."},
                    {"t": "Concept generation", "d": "Diverge before you converge: brainstorm, morphological analysis (combine sub-solution options), reverse-engineer, benchmark competitors."},
                    {"t": "Pugh matrix (decision matrix)", "d": "Score concepts against weighted criteria; a datum concept anchors the scale (−1/0/+1 or 1-5). Choose the highest weighted total; document why."},
                    {"t": "Iteration & design reviews", "d": "Design is a loop: define → concept → model → test → revise. A design review is a scheduled, documented checkpoint with fresh eyes."},
                ],
                "formulas": [
                    {"n": "Weighted decision score", "e": "S = Σ (weightᵢ × scoreᵢ)", "note": "Weights must sum to 1 (or 100%). Keep units consistent."},
                    {"n": "Pugh datum rule", "e": "Datum concept = all zeros; others scored relative to it", "note": "Forces you to define 'good' once."},
                ],
                "example": {
                    "problem": "Pick a bicycle frame material among steel, aluminium, and carbon using a Pugh matrix. Criteria weights: cost 0.35, weight 0.30, strength 0.20, repairability 0.15. Scores (1-5): steel 5/2/4/5, alu 4/3.5/3.5/3, carbon 1/5/5/1.",
                    "steps": [
                        "Steel: 0.35·5 + 0.30·2 + 0.20·4 + 0.15·5 = 1.75 + 0.60 + 0.80 + 0.75 = 3.90",
                        "Aluminium: 0.35·4 + 0.30·3.5 + 0.20·3.5 + 0.15·3 = 1.40 + 1.05 + 0.70 + 0.45 = 3.60",
                        "Carbon: 0.35·1 + 0.30·5 + 0.20·5 + 0.15·1 = 0.35 + 1.50 + 1.00 + 0.15 = 3.00",
                        "Highest score wins; sensitivity-check by nudging the top weights.",
                    ],
                    "answer": "Steel = 3.90, Aluminium = 3.60, Carbon = 3.00 → steel wins under these weights. Always state the weights and note that changing them can flip the result.",
                },
                "traps": [
                    "Jumping to a concept before writing requirements — you can't justify what you didn't define.",
                    "Weights that don't sum to 1 (or 100%) → scores are meaningless.",
                    "Treating the matrix as objective truth: it makes assumptions explicit, it doesn't remove judgement.",
                ],
                "practice": [
                    {"q": "What's the difference between a functional requirement and a constraint?", "a": "Functional = what the design must DO (transmit torque). Constraint = a limit on the solution (budget, envelope, code)."},
                    {"q": "Why keep a datum concept in a Pugh matrix?", "a": "It anchors the scale so every other concept is judged against one known baseline."},
                ],
            },
            {
                "id": "md-2",
                "title": "Visualization & Sketching",
                "summary": "Reading and drawing the shapes that describe a part.",
                "concepts": [
                    {"t": "Orthographic projection", "d": "Front, top, right-side views arranged in standard (third-angle, US) positions. Each view shows two of the three dimensions — together they define the shape."},
                    {"t": "Isometric drawings", "d": "All three axes at 120°; true lengths along the axes. Great for 'what does it look like', poor for dimensions."},
                    {"t": "Line conventions", "d": "Visible = thick solid; hidden = dashed; centre = chain; and the rule 'no hidden lines in section views'."},
                    {"t": "Section views", "d": "Cut the part to show internal features; hatch the cut material. Full, half, and offset sections each reveal different internals."},
                    {"t": "Auxiliary & detail views", "d": "Auxiliary views show a true shape on an angled face; detail views enlarge a busy region with its own scale."},
                ],
                "formulas": [
                    {"n": "Third-angle placement", "e": "Front (centre) · Top (above front) · Right side (right of front)", "note": "US standard. First-angle (EU) mirrors the top/side."},
                    {"n": "Isometric axes", "e": "Three axes 120° apart; vertical axis true-vertical", "note": "Circles become ellipses on the isometric planes."},
                ],
                "example": {
                    "problem": "You see one view: a rectangle with a hidden dashed square in the middle and a centreline. What feature is hidden and in what direction?",
                    "steps": [
                        "Dashed line = hidden edge → the feature is behind the visible face.",
                        "Centreline through it = a symmetric feature, typically a hole or slot.",
                        "Need at least one other view to fix depth and shape.",
                    ],
                    "answer": "A symmetric hidden internal feature (commonly a through-hole) perpendicular to that face; the second view locks the shape and depth.",
                },
                "traps": [
                    "Drawing hidden lines in a section view — wrong by convention.",
                    "Mixing first- and third-angle placement on one sheet.",
                    "Assuming one view defines a part — it never does.",
                ],
                "practice": [
                    {"q": "What does a dashed line mean, and when is it omitted?", "a": "A hidden (obscured) edge; omitted in section views."},
                    {"q": "Which view type shows an angled face at true size?", "a": "An auxiliary view."},
                ],
            },
            {
                "id": "md-3",
                "title": "CAD & Solid Modeling",
                "summary": "Parametric features, sketches, and assemblies — how modern parts are built.",
                "concepts": [
                    {"t": "Parametric feature tree", "d": "A model is a history of features (sketch → extrude → fillet → pattern). Edit an early sketch and later features rebuild — that's the power and the fragility."},
                    {"t": "Fully-constrained sketches", "d": "A sketch is 'black' when all degrees of freedom are removed by dimensions/relations; blue = under-constrained. Always fully constrain before extruding."},
                    {"t": "Sketch relations", "d": "Coincident, horizontal/vertical, parallel/perpendicular, tangent, equal, symmetric, concentric. Relations encode design intent so edits behave predictably."},
                    {"t": "Feature operations", "d": "Extrude (linear), revolve (about an axis), sweep (profile along a path), loft (blend between profiles), hole, fillet/round, chamfer, shell, pattern/mirror."},
                    {"t": "Assembly mates", "d": "Mates remove degrees of freedom: coincident, concentric, distance, angle, tangent. Count DOF to see if an assembly is over- or under-constrained (a part has 6 DOF)."},
                    {"t": "Design intent & rebuild", "d": "Model so the features you expect to change are the easiest to change. Name features; avoid references to geometry you might delete."},
                ],
                "formulas": [
                    {"n": "Degrees of freedom (3D part)", "e": "6 DOF = 3 translation + 3 rotation", "note": "Fully define a part when constrained mates = 0 remaining DOF."},
                    {"n": "Pattern count", "e": "Total instances = count × (1 + number of directions)", "note": "Watch for overlapping instances in linear/circular patterns."},
                ],
                "example": {
                    "problem": "A bracket must have 4 bolt holes equally spaced on a 100 mm bolt circle. Describe the efficient CAD method.",
                    "steps": [
                        "Sketch one hole on the bolt circle, dimension its position (e.g. on the X-axis at R = 50 mm).",
                        "Use a Circular Pattern feature: axis = centre, angle = 360°, count = 4, equal spacing.",
                        "Fully constrain the base sketch first so a diameter change rebuilds cleanly.",
                    ],
                    "answer": "One hole feature + circular pattern (count 4, 360°) about the centre axis — never 4 hand-placed holes (unmaintainable).",
                },
                "traps": [
                    "Extruding an under-constrained (blue) sketch — the model drifts when edited.",
                    "Over-constraining with redundant dimensions → solver errors you can't fix.",
                    "Referencing a fillet face that a later edit deletes → broken rebuild.",
                ],
                "practice": [
                    {"q": "How many degrees of freedom does a free body have in 3D?", "a": "Six: three translations and three rotations."},
                    {"q": "What does it mean when a sketch turns black and why does it matter?", "a": "It is fully constrained — all DOF removed; safe to extrude and stable under edits."},
                ],
            },
            {
                "id": "md-4",
                "title": "Engineering Drawings & Tolerances",
                "summary": "Turning a 3D model into a manufacturing document.",
                "concepts": [
                    {"t": "Dimensioning rules", "d": "Dimension to a feature once, from datums, never duplicate, and never dimension to a hidden line if avoidable. Dimensions carry units and the required precision."},
                    {"t": "Tolerance & fit", "d": "A dimension without a tolerance is undefined. Clearance fit (hole larger), interference fit (shaft larger), transition (either)." },
                    {"t": "Limits vs. plus/minus", "d": "Limits give the two extreme sizes directly; bilateral (±) is symmetric; unilateral applies one side (common for holes)."},
                    {"t": "GD&T basics", "d": "Geometric tolerancing controls form (flatness, straightness), orientation (perpendicularity), location (position/true position), and runout. Read a feature control frame: symbol | tolerance | datum(s)."},
                    {"t": "Surface finish & title block", "d": "Ra (µm) specifies roughness; the title block holds part number, material, scale, revision, and who approved."},
                ],
                # NOTE: the position-formula braces are doubled so Python .format() on
                # this string is a no-op; the literal shown to users is single-braced.
                "formulas": [
                    {"n": "Tolerance band", "e": "Tolerance = max size − min size", "note": "MMC/LMC shift the band for geometric controls."},
                    {"n": "True-position zone dia.", "e": "Ø tol = 2 × √(Δx² + Δy²)", "note": "Applies to a hole located by rectangular coordinates."},
                ],
                "example": {
                    "problem": "A Ø10 mm hole is dimensioned 10.00 / 10.05 mm. Classify the fit against a shaft made 9.98 / 9.99 mm, and state the allowance.",
                    "steps": [
                        "Hole range 10.00-10.05; shaft range 9.98-9.99.",
                        "The hole is always larger than the shaft (10.00 > 9.99) → clearance fit.",
                        "Allowance = minimum clearance = hole min − shaft max = 10.00 − 9.99 = 0.01 mm.",
                        "Maximum clearance = hole max − shaft min = 10.05 − 9.98 = 0.07 mm.",
                    ],
                    "answer": "Clearance fit; allowance (min clearance) = 0.01 mm, max clearance = 0.07 mm.",
                },
                "traps": [
                    "Over-dimensioning (same feature twice) → contradictory tolerances, rejected by the shop.",
                    "Leaving a dimension untoleranced — the machinist then invents one.",
                    "Reading a feature-control frame left-to-right wrongly; the datum order changes the meaning.",
                ],
                "practice": [
                    {"q": "Define 'allowance' in a fit.", "a": "The intentional difference between the sizes of mating parts — minimum clearance (or maximum interference)."},
                    {"q": "What are the four GD&T control families?", "a": "Form, orientation, location, and runout."},
                ],
            },
            {
                "id": "md-5",
                "title": "Design for Manufacturing & Prototyping",
                "summary": "Designs that are cheap and easy to build — and how to test them fast.",
                "concepts": [
                    {"t": "DFM / DFA", "d": "Design for Manufacturing = easy to make (few operations, standard tools). Design for Assembly = few parts, self-aligning, one-direction insertion. Both cut cost dramatically, and cheapest to apply at concept stage."},
                    {"t": "Tolerance vs. cost", "d": "Cost rises steeply as tolerances tighten. Specify the loosest tolerance the function allows — not the tightest the machine can hold."},
                    {"t": "Process selection", "d": "Match the design to a process: casting (complex, high volume), machining (accurate, low-moderate), injection moulding (high volume plastics, needs draft), sheet metal (thin, cheap)."},
                    {"t": "Additive & rapid prototyping", "d": "3D printing (FDM/SLA/SLS) builds from a model in hours — ideal for form/fit checks. Weak in the build direction and anisotropic; reinforce or use it as a fit check only."},
                    {"t": "Tolerance stackup", "d": "Worst-case: sum the individual tolerances. Statistical (RSS): √(Σ tolᵢ²). RSS explains why most assemblies fit even when worst-case says they shouldn't."},
                ],
                "formulas": [
                    {"n": "Worst-case stackup", "e": "T_total = Σ tᵢ", "note": "Guarantees assembly for every part; conservative."},
                    {"n": "Statistical (RSS) stackup", "e": "T_total = √(t₁² + t₂² + … + tₙ²)", "note": "Realistic for large volumes if the distributions are centred."},
                ],
                "example": {
                    "problem": "A stack of 3 parts has tolerances ±0.2, ±0.1, ±0.15 mm. Find worst-case and RSS total gap tolerance.",
                    "steps": [
                        "Worst-case: 0.2 + 0.1 + 0.15 = 0.45 mm.",
                        "RSS: √(0.2² + 0.1² + 0.15²) = √(0.04 + 0.01 + 0.0225) = √0.0725 ≈ 0.269 mm.",
                        "Compare against the allowed gap and pick the method your production volume justifies.",
                    ],
                    "answer": "Worst-case = 0.45 mm; RSS ≈ 0.269 mm. RSS is tighter because random errors partially cancel.",
                },
                "traps": [
                    "Tightening tolerances to fix a problem it wasn't causing — cost explodes, real cause remains.",
                    "Using an FDM print to check a sliding fit at full size — build shrink/anisotropy misleads you.",
                    "Designing for one-off prototype methods when the product needs high-volume production.",
                ],
                "practice": [
                    {"q": "When is RSS tolerance stackup appropriate vs. worst-case?", "a": "RSS for high-volume production where per-part errors are independent and centred; worst-case when every assembly must fit (low volume, safety-critical)."},
                    {"q": "Why is DFM best applied at the concept stage?", "a": "Cost is locked in early; changing a concept is cheap, changing a shipped design is not."},
                ],
            },
        ],
    },
    {
        "code": "SM-201",
        "title": "Static Modeling of Mechanical Systems (Statics)",
        "short": "Statics / Mech Systems",
        "credits": 3,
        "accent": "#3f3f46",
        "blurb": "Equilibrium of particles and rigid bodies, trusses, frames, friction, centroids and moments of inertia.",
        "units": [
            {
                "id": "sm-1",
                "title": "Vectors & Force Systems",
                "summary": "Adding, resolving, and taking moments of forces in 2D and 3D.",
                "concepts": [
                    {"t": "Vector components", "d": "A force at angle θ: Fx = F cosθ, Fy = F sinθ. Sum components per axis before combining."},
                    {"t": "Unit vectors", "d": "F = F·û where û = (dx, dy, dz)/|d|. Use them to write 3D forces cleanly."},
                    {"t": "Dot product (angle)", "d": "A·B = |A||B|cosθ → cosθ = (A·B)/(|A||B|). Used for the angle between a force and an axis."},
                    {"t": "Moment of a force", "d": "M = r × F (vector) or M = F·d (scalar, d = perpendicular distance). Sign by convention (CCW positive in 2D)."},
                    {"t": "Couples & resultants", "d": "A couple is two equal, opposite, non-collinear forces — pure moment, no net force. Any force system reduces to one force + one couple at a chosen point."},
                    {"t": "3D moment components", "d": "M = r × F expands to Mx = yFz − zFy, etc. Compute with the determinant."},
                ],
                "formulas": [
                    {"n": "Components", "e": "Fₓ = F cos θ, F_y = F sin θ", "note": "θ measured from +x."},
                    {"n": "Resultant magnitude", "e": "R = √(Rₓ² + R_y²)", "note": "Direction θ_R = atan2(R_y, Rₓ)."},
                    {"n": "Moment (scalar)", "e": "M = F · d", "note": "d = perpendicular distance from the point to the line of action."},
                    {"n": "Moment (vector)", "e": "M = r × F", "note": "r from the moment point to any point on the force's line of action."},
                    {"n": "Dot product", "e": "A·B = AₓBₓ + A_yB_y + A_zB_z = |A||B|cosθ", "note": "Scales to any dimension."},
                ],
                "example": {
                    "problem": "Force F = 100 N acts at 30° above the +x axis on a point A = (3, 0) m. Find its moment about the origin.",
                    "steps": [
                        "Components: Fₓ = 100 cos30° = 86.6 N; F_y = 100 sin30° = 50.0 N.",
                        "Vector moment about O: M_O = r × F with r = (3, 0).",
                        "M_O = (3)(50) − (0)(86.6) = 150 N·m (CCW, +z).",
                        "Check by scalar: perpendicular distance d, M = F·d gives the same value.",
                    ],
                    "answer": "M_O = 150 N·m counter-clockwise (+z). The horizontal component passes through O and contributes no moment.",
                },
                "traps": [
                    "Using sin for the wrong axis — always resolve along +x and +y first.",
                    "Forgetting the sign convention on moments; state CCW = + before you start.",
                    "Using the position vector to a point NOT on the line of action — moment is the same only for points on that line.",
                ],
                "practice": [
                    {"q": "Two 50 N forces, opposite and 0.4 m apart, act on a beam. What is the resultant force and moment?", "a": "Resultant force = 0; couple moment = 50 × 0.4 = 20 N·m."},
                    {"q": "Find the angle between A = (2, 1, 0) and B = (0, 1, 2).", "a": "A·B = 1; |A|=|B|=√5 → cosθ = 1/5 → θ ≈ 78.5°."},
                ],
            },
            {
                "id": "sm-2",
                "title": "Equilibrium of Particles",
                "summary": "Forces through a point — the workhorse of cables, springs and pulleys.",
                "concepts": [
                    {"t": "Free-body diagram (FBD)", "d": "Isolate one body, draw EVERY external force (its weight, contact/push, cable tension, spring, reaction), label axes. The FBD is 80% of the mark."},
                    {"t": "Equilibrium of a particle", "d": "A particle has no rotation: ΣFₓ = 0 and ΣF_y = 0 (add ΣF_z = 0 in 3D). Two equations, two unknowns."},
                    {"t": "Cables/pulleys", "d": "An ideal cable pulls along its length (tension only, never pushes). Over a frictionless pulley, tension is the same on both sides."},
                    {"t": "Springs", "d": "F = k·s where s = deformation = L − L₀. Stretch → pull; compression → push, along the spring's axis."},
                    {"t": "Smooth surfaces", "d": "A frictionless contact force is normal (perpendicular) to the surface."},
                ],
                "formulas": [
                    {"n": "Particle equilibrium", "e": "ΣFₓ = 0, ΣF_y = 0 (and ΣF_z = 0 in 3D)", "note": "Gives as many equations as there are axes — count unknowns first."},
                    {"n": "Hooke's law (spring)", "e": "F = k (L − L₀)", "note": "Sign of the force follows the deformation."},
                    {"n": "Weight", "e": "W = m g", "note": "g = 9.81 m/s². Mass (kg) ≠ weight (N)."},
                ],
                "example": {
                    "problem": "A 10 kg sign hangs from two cables: one at 30° and one at 45° to the ceiling. Find both tensions.",
                    "steps": [
                        "FBD at the knot: weight W = 10 × 9.81 = 98.1 N down; T₁ at 30°, T₂ at 45° from the ceiling (up-and-inward).",
                        "Vertical (note both cables' vertical components act up): T₁ sin30° + T₂ sin45° = 98.1.",
                        "Horizontal: T₁ cos30° = T₂ cos45°.",
                        "From the horizontal equation T₂ = T₁ cos30°/cos45° = 1.225·T₁.",
                        "Substitute: 0.5 T₁ + 0.7071 × 1.225 T₁ = 98.1 → 0.5 T₁ + 0.866 T₁ = 98.1 → 1.366 T₁ = 98.1 → T₁ = 71.8 N.",
                        "T₂ = 1.225 × 71.8 = 88.0 N.",
                    ],
                    "answer": "T₁ (30°) ≈ 71.8 N, T₂ (45°) ≈ 88.0 N. The steeper-from-horizontal cable carries more.",
                },
                "traps": [
                    "Forgetting the sign that a cable above the load pulls UP (both vertical components positive).",
                    "Mixing mass (kg) and weight (N) — multiply by g before balancing forces.",
                    "Drawing the FBD of the whole system instead of the isolated knot; unknowns get entangled.",
                ],
                "practice": [
                    {"q": "A particle is in equilibrium under three forces. One is 30 N east, one is 40 N south. Find the third.", "a": "Third = −(30 east + 40 south) = 30 N west + 40 N north; magnitude √(30²+40²) = 50 N, at 53.1° north of west."},
                    {"q": "A spring of k = 500 N/m hangs a 2 kg mass. Extension?", "a": "F = 2 × 9.81 = 19.62 N; s = F/k = 19.62/500 = 0.0392 m ≈ 39 mm."},
                ],
            },
            {
                "id": "sm-3",
                "title": "Equilibrium of Rigid Bodies",
                "summary": "When size matters: moments join the force equations.",
                "concepts": [
                    {"t": "Rigid-body equilibrium", "d": "ΣF = 0 AND ΣM = 0 about any point. That gives 3 equations in 2D (2 force + 1 moment) and 6 in 3D."},
                    {"t": "Support reactions", "d": "Roller (1 unknown, perpendicular), pin/hinge (2 unknowns, any direction), fixed/wall (3 unknowns: two forces + a moment)."},
                    {"t": "Two- and three-force members", "d": "A two-force member with no loads between its ends carries equal, opposite, collinear forces. A three-force member's three forces must be concurrent (or parallel)."},
                    {"t": "Distributed loads", "d": "Replace a distributed load by its resultant (area under the load curve) applied at the centroid of that area — then use point-force methods."},
                    {"t": "Choosing the moment point", "d": "Pick the point where the most unknown lines-of-action pass — it eliminates those unknowns from the equation and saves algebra."},
                ],
                "formulas": [
                    {"n": "2D equilibrium", "e": "ΣFₓ = 0, ΣF_y = 0, ΣM = 0", "note": "Three equations → three unknowns."},
                    {"n": "Moment of a couple", "e": "M = F · d", "note": "Same about every point — free vector."},
                    {"n": "Point load resultant", "e": "R = ∫w(x) dx (or load area), at x̄ = ∫x·w dx / R", "note": "For a uniform rectangle: R = w·L at the midpoint."},
                    {"n": "3D equilibrium", "e": "ΣFₓ=ΣF_y=ΣF_z=0 and ΣMₓ=ΣM_y=ΣM_z=0", "note": "Six equations, six unknowns."},
                ],
                "example": {
                    "problem": "A 6 m uniform beam weighs 200 N. It rests on a pin at the left end (A) and a roller at the right end (B). A 500 N load hangs 2 m from A. Find the reactions.",
                    "steps": [
                        "FBD: at A, Aₓ and A_y; at B a vertical roller reaction B_y; weight 200 N down at 3 m; load 500 N down at 2 m.",
                        "No horizontal loads → Aₓ = 0.",
                        "Moments about A (kills Aₓ, A_y): B_y(6) − 200(3) − 500(2) = 0 → 6B_y = 600 + 1000 = 1600 → B_y ≈ 266.7 N.",
                        "Vertical: A_y + B_y = 200 + 500 = 700 → A_y = 700 − 266.7 = 433.3 N.",
                        "Check moments about B: A_y(6) − 200(3) − 500(4) = 2600 − 600 − 2000 = 0 ✓.",
                    ],
                    "answer": "Aₓ = 0, A_y ≈ 433 N, B_y ≈ 267 N. The load near A loads A more heavily.",
                },
                "traps": [
                    "Leaving out a support reaction or a distributed load in the FBD.",
                    "Forgetting the beam's own weight (uniform → at its midpoint).",
                    "Using a moment equation about a point that doesn't eliminate the unknown you're avoiding.",
                ],
                "practice": [
                    {"q": "How many reaction unknowns does a fixed support add in 2D?", "a": "Three: a force in x, a force in y, and a moment (couple)."},
                    {"q": "Where does the resultant of a triangular distributed load from 0 to w over length L act?", "a": "At L/3 from the zero end; magnitude = ½·w·L."},
                ],
            },
            {
                "id": "sm-4",
                "title": "Analysis of Trusses",
                "summary": "Pin-jointed frameworks — joints and sections.",
                "concepts": [
                    {"t": "Truss assumptions", "d": "Members are pin-connected, loads only at joints, members carry axial force only (tension or compression)."},
                    {"t": "Method of joints", "d": "Apply ΣF = 0 at each joint in turn; two equations per joint. Start at a joint with ≤ 2 unknowns."},
                    {"t": "Method of sections", "d": "Cut through ≤ 3 members of interest, draw the FBD of one part, apply the 3 equilibrium equations. Fastest when you need just a few members."},
                    {"t": "Zero-force members", "d": "A two-member joint with no load/external force → both are zero. A three-member joint with two collinear → the third is zero. Spotting these saves work."},
                    {"t": "Determinacy", "d": "For a planar truss: m + r = 2j for statically determinate (m members, r reactions, j joints). More → over-determinate; fewer → mechanism."},
                ],
                "formulas": [
                    {"n": "Determinacy (2D truss)", "e": "m + r = 2j", "note": "m = members, r = reaction components, j = joints."},
                    {"n": "Tension convention", "e": "Assume members pull away from the joint (+)", "d": "A negative result = compression", "note": "Sign is the whole answer — state T or C."},
                ],
                "example": {
                    "problem": "A simple triangular truss: joints A (left, pin) and B (right, roller) 4 m apart, apex C 3 m up. A 6 kN load acts down at C. Find the force in each member.",
                    "steps": [
                        "Whole truss: ΣM_A: B_y(4) − 6(2) = 0 → B_y = 3 kN; ΣF_y: A_y = 6 − 3 = 3 kN; Aₓ = 0.",
                        "Member lengths: AC = BC = √(2² + 3²) = √13 = 3.606 m.",
                        "Joint A: A_y = 3 up. Members AB (horizontal) and AC at angle θ where sinθ = 3/3.606 = 0.832, cosθ = 0.555.",
                        "ΣF_y at A: F_AC·sinθ + 3 = 0 → F_AC = −3/0.832 = −3.606 kN (compression).",
                        "ΣFₓ at A: F_AB + F_AC·cosθ = 0 → F_AB = 3.606 × 0.555 = 2.0 kN (tension).",
                        "By symmetry at B the same magnitudes on the other side; BC = 3.606 kN compression, AB carries 2.0 kN tension.",
                    ],
                    "answer": "AB = 2.0 kN tension; AC = BC ≈ 3.61 kN compression. Sloped members are in compression under a downward apex load.",
                },
                "traps": [
                    "Assuming a member is in tension — the sign from equilibrium decides.",
                    "Choosing the wrong first joint (start where ≤ 2 unknowns).",
                    "Mis-applying zero-force rules at joints that DO carry an external load.",
                ],
                "practice": [
                    {"q": "A truss has 7 members, 5 joints and 3 reaction components. Determinate?", "a": "m + r = 7 + 3 = 10; 2j = 10 → determinate."},
                    {"q": "Two non-collinear members meet at an unloaded joint not touching any support. What are their forces?", "a": "Both are zero-force members."},
                ],
            },
            {
                "id": "sm-5",
                "title": "Frames, Machines & Friction",
                "summary": "Structures that aren't trusses, and the forces that resist sliding.",
                "concepts": [
                    {"t": "Frames vs. machines", "d": "Frames are rigid, stationary multi-force structures; machines have moving parts. Both need dismembering and per-member FBDs."},
                    {"t": "Multi-force members", "d": "Unlike a two-force member, these carry loads along their length — you must know their shape/loads to draw them."},
                    {"t": "Dry friction", "d": "Static friction self-adjusts up to F_max = μ_s·N; once sliding, F_k = μ_k·N with μ_k < μ_s. The friction force OPPOSES impending/actual motion."},
                    {"t": "Angle of friction / friction cone", "d": "tanφ_s = μ_s; the resultant reaction lies on the edge of the cone only at impending motion."},
                    {"t": "Belt friction", "d": "When a belt/rope is about to slip over a drum, the tension ratio is exponential in the wrap angle."},
                    {"t": "Wedges, screws, rolling resistance", "d": "A wedge turns a small force into a large normal force; a screw is an inclined plane wrapped on a cylinder; rolling resistance resists a rolling wheel with a small moment."},
                ],
                "formulas": [
                    {"n": "Static friction (max)", "e": "F_max = μ_s N", "note": "Use for impending motion; otherwise F ≤ μ_s N is unknown."},
                    {"n": "Kinetic friction", "e": "F_k = μ_k N", "note": "μ_k < μ_s; friction opposes the motion."},
                    {"n": "Angle of friction", "e": "tan φ_s = μ_s", "note": "φ_s = angle of the friction cone."},
                    {"n": "Belt friction", "e": "T₂ = T₁ · e^(μ β)", "note": "β in RADIANS; T₂ = the side being pulled (larger tension)."},
                ],
                "example": {
                    "problem": "A 20 kg block sits on a horizontal floor with μ_s = 0.4. What horizontal push starts it sliding, and what is the friction force at 50 N of push?",
                    "steps": [
                        "Normal force: N = W = 20 × 9.81 = 196.2 N.",
                        "Max static friction: F_max = μ_s N = 0.4 × 196.2 = 78.5 N → the block starts sliding at a 78.5 N push.",
                        "At 50 N (below F_max) the block is static, so friction = the applied push = 50 N (it self-adjusts).",
                    ],
                    "answer": "It starts sliding at 78.5 N; at 50 N the friction equals 50 N (never use F_max for a body that isn't impending to move).",
                },
                "traps": [
                    "Applying F_max = μN when the body is NOT about to move — friction equals the balancing force instead.",
                    "Forgetting β must be in radians in T₂ = T₁e^(μβ).",
                    "Getting the friction direction wrong — it always opposes relative sliding.",
                ],
                "practice": [
                    {"q": "A rope is wrapped 180° (π rad) around a drum with μ = 0.25. What tension ratio holds at slipping?", "a": "T₂/T₁ = e^(0.25π) = e^0.785 ≈ 2.19."},
                    {"q": "On an incline at angle θ with no slip, how big is friction?", "a": "F = mg sinθ (static, self-adjusting) as long as mg sinθ ≤ μ_s mg cosθ."},
                ],
            },
            {
                "id": "sm-6",
                "title": "Centroids, Distributed Loads & Moments of Inertia",
                "summary": "Where the area 'sits' and how it resists bending.",
                "concepts": [
                    {"t": "Centroid of an area", "d": "The geometric centre: x̄ = ∫x dA / ∫dA. For composite shapes, use a table (Aᵢ, x̄ᵢ, ȳᵢ) and the weighted average."},
                    {"t": "Composite-area method", "d": "Split into rectangles/triangles/circles; treat a hole as a NEGATIVE area. Then x̄ = Σ(Aᵢx̄ᵢ)/ΣAᵢ."},
                    {"t": "Distributed load → resultant", "d": "Resultant = area under the load diagram; acts at the centroid of that area. Uniform: centre; triangular: ⅓ from the tall end."},
                    {"t": "Area moment of inertia", "d": "Iₓ = ∫y² dA — measures resistance to bending about the x-axis. Bigger I = stiffer beam."},
                    {"t": "Parallel-axis theorem", "d": "I = Ī + A d² — shift from the centroidal axis to any parallel axis; d = distance between axes, A = area."},
                    {"t": "Radius of gyration", "d": "k = √(I/A). Handy for buckling and for comparing shapes."},
                ],
                "formulas": [
                    {"n": "Centroid x̄", "e": "x̄ = ∫x dA / ∫dA", "note": "Composite: x̄ = Σ(Aᵢ x̄ᵢ) / ΣAᵢ."},
                    {"n": "Rectangle I (centroidal)", "e": "I = b h³ / 12", "note": "b is parallel to the axis you're bending about; watch which dimension is cubed."},
                    {"n": "Circle I (centroidal)", "e": "I = π r⁴ / 4 = π d⁴ / 64", "note": "Polar: J = π r⁴/2 (for torsion)."},
                    {"n": "Triangle I (centroidal)", "e": "I = b h³ / 36", "note": "About the axis parallel to the base, through the centroid."},
                    {"n": "Parallel-axis theorem", "e": "I = Ī + A d²", "note": "Ī is the centroidal value; d ≥ 0 so I only grows."},
                    {"n": "Radius of gyration", "e": "k = √(I / A)", "note": "Units of length."},
                ],
                "example": {
                    "problem": "Find I about the base for a rectangle 100 mm wide × 200 mm tall (base is the bottom edge).",
                    "steps": [
                        "Area A = 100 × 200 = 20 000 mm²; centroid is at h/2 = 100 mm from the base.",
                        "Centroidal moment of inertia: Ī = b h³/12 = 100 × 200³ / 12 = 66.67 × 10⁶ mm⁴.",
                        "Parallel-axis to the base: I = Ī + A d² = 66.67×10⁶ + 20 000 × 100² = 66.67×10⁶ + 200×10⁶ = 266.67 × 10⁶ mm⁴.",
                        "Check with the direct formula I_base = b h³/3 = 100 × 200³/3 = 266.7 × 10⁶ mm⁴ ✓.",
                    ],
                    "answer": "I_base ≈ 266.7 × 10⁶ mm⁴. The centroidal axis is the least moment of inertia, so I about any edge is larger.",
                },
                "traps": [
                    "Cubing the wrong dimension in b h³/12 (cube the dimension perpendicular to the axis).",
                    "Using the parallel-axis theorem with d measured from the wrong axis, or with Ī not the centroidal value.",
                    "Forgetting to subtract a hole's area/moment in a composite shape.",
                ],
                "practice": [
                    {"q": "Radius of gyration of the 100×200 rectangle about its base?", "a": "k = √(I/A) = √(266.7×10⁶ / 20 000) ≈ 115.5 mm."},
                    {"q": "Where does a uniform distributed load of w over L act, and where does a triangular one from 0 to w?", "a": "Uniform: at L/2, R = wL. Triangular: at L/3 from the zero end, R = wL/2."},
                ],
            },
        ],
    },
    {
        "code": "EM-202",
        "title": "Engineering Materials",
        "short": "Engineering Materials",
        "credits": 3,
        "accent": "#a1a1aa",
        "blurb": "Structure–property relationships, mechanical testing, phase diagrams, failure, and materials selection.",
        "units": [
            {
                "id": "em-1",
                "title": "Atomic Structure & Bonding",
                "summary": "Why metals bend and ceramics shatter — it starts with the bond.",
                "concepts": [
                    {"t": "Primary bonds", "d": "Ionic (electron transfer — ceramics), covalent (shared electrons — diamond, polymers backbone), metallic (delocalised electron sea — ductile, conductive). Strong, high melting points."},
                    {"t": "Secondary bonds", "d": "Van der Waals and hydrogen bonds — weak, cause low melting points (polymers, water)."},
                    {"t": "Bond energy vs. stiffness", "d": "The steeper/deeper the bond-energy curve at r₀, the higher the elastic modulus E and melting point. Stronger bond → stiffer, tougher-to-melt material."},
                    {"t": "Crystal vs. amorphous", "d": "Metals and ceramics solidify crystalline (ordered, long-range); glasses and many polymers solidify amorphous (short-range order)."},
                    {"t": "Periodic trend", "d": "Electronegativity difference drives ionic character; metallic character rises down a group and falls across a period."},
                ],
                "formulas": [
                    {"n": "Bond energy curve", "e": "E(r) minimum at equilibrium spacing r₀; slope at r₀ = 0", "note": "Curvature near r₀ sets E (stiffness)."},
                    {"n": "Elastic modulus from bond", "e": "E ∝ (d²E/dr²) at r₀", "note": "Deeper, steeper well → higher E."},
                ],
                "example": {
                    "problem": "Explain why NaCl has a very high melting point (~801 °C) but shatters when hit, while copper (1085 °C) bends.",
                    "steps": [
                        "NaCl: strong IONIC bonds → high melting point (lots of energy to break).",
                        "Ionic crystals require like-charges to pass on slip, which repels → brittle, no slip → shatters.",
                        "Copper: METALLIC bonds are non-directional, so planes can slide past each other without breaking bonds → ductile.",
                    ],
                    "answer": "Both have strong primary bonds (high Tm), but the non-directional metallic bond allows slip (ductile) while the ionic lattice resists it (brittle).",
                },
                "traps": [
                    "Confusing high melting point with ductility — both metals and ceramics melt high, but only metals slip.",
                    "Mixing covalent and ionic when the electronegativity difference is small (→ polar covalent).",
                    "Assuming a strong bond means a tough material — ceramic bonds are strong but brittle.",
                ],
                "practice": [
                    {"q": "Which bond type gives good electrical conductivity and why?", "a": "Metallic — delocalised electrons are free to carry current."},
                    {"q": "What does a steep bond-energy curve at r₀ imply about the material?", "a": "A high elastic modulus (stiff) and usually a high melting temperature."},
                ],
            },
            {
                "id": "em-2",
                "title": "Crystal Structures & Imperfections",
                "summary": "How atoms pack, and how the defects in the packing decide properties.",
                "concepts": [
                    {"t": "Common metal structures", "d": "FCC (Cu, Al, γ-Fe) — ductile, 12 slip systems. BCC (α-Fe, W) — stronger, less ductile, 12 slip systems but not close-packed. HCP (Mg, Zn, Ti) — few slip systems, brittle."},
                    {"t": "Packing factor & density", "d": "Atomic Packing Factor (APF) is the fraction of volume filled by atoms: FCC/HCP 0.74, BCC 0.68, simple cubic 0.52. Theoretical density from n·A/(V·N_A)."},
                    {"t": "Miller indices", "d": "Direction [u v w], plane (h k l) with reciprocals of intercepts; family {h k l} for equivalents (FCC slip = {111}<110>)."},
                    {"t": "Point defects", "d": "Vacancies, self-interstitials, and substitutional/interstitial solutes. Vacancies enable diffusion (temperature-activated)."},
                    {"t": "Dislocations", "d": "Line defects (edge/screw) whose motion = slip = plastic deformation. Obstacles to dislocation motion (grain boundaries, solutes, precipitates) strengthen the metal."},
                    {"t": "Grain boundaries", "d": "Surface defects separating grains/grains of different orientation. Small grains → more boundaries → stronger (Hall–Petch), but lower ductility."},
                ],
                "formulas": [
                    {"n": "APF", "e": "APF = (n · (4/3)πr³) / a³", "note": "n = atoms per cell; FCC n=4, BCC n=2, SC n=1."},
                    {"n": "Theoretical density", "e": "ρ = (n · A) / (V_cell · N_A)", "note": "N_A = 6.022×10²³ /mol; A = atomic weight."},
                    {"n": "FCC lattice parameter", "e": "a = 2√2 · r", "note": "Atoms touch along the face diagonal."},
                    {"n": "BCC lattice parameter", "e": "a = 4r / √3", "note": "Atoms touch along the body diagonal."},
                    {"n": "Hall–Petch", "e": "σ_y = σ₀ + k / √d", "note": "d = grain diameter; smaller grains → higher yield strength."},
                ],
                "example": {
                    "problem": "Compute the theoretical density of copper (FCC, A = 63.55 g/mol, r = 0.128 nm).",
                    "steps": [
                        "FCC: a = 2√2 r = 2 × 1.414 × 0.128 = 0.362 nm = 3.62 × 10⁻⁸ cm.",
                        "Cell volume V = a³ = (3.62×10⁻⁸)³ = 4.74 × 10⁻²³ cm³.",
                        "n = 4 atoms/cell; A = 63.55 g/mol; N_A = 6.022×10²³.",
                        "ρ = (4 × 63.55) / (4.74×10⁻²³ × 6.022×10²³) = 254.2 / 28.54 = 8.90 g/cm³.",
                    ],
                    "answer": "ρ ≈ 8.90 g/cm³ — matches the measured density of copper (8.96), a good sanity check.",
                },
                "traps": [
                    "Using n = 4 for BCC (it's 2) — the classic slip.",
                    "Mixing lattice parameter formulas (FCC uses the face diagonal, BCC the body diagonal).",
                    "Thinking 'closer packed = stronger' — HCP is the most densely packed but often the most brittle.",
                ],
                "practice": [
                    {"q": "How many atoms per unit cell in FCC, BCC, and SC?", "a": "FCC 4, BCC 2, SC 1."},
                    {"q": "Why do smaller grains strengthen a metal?", "a": "More grain boundaries impede dislocation motion (Hall–Petch: σ_y ∝ 1/√d)."},
                ],
            },
            {
                "id": "em-3",
                "title": "Mechanical Properties & Testing",
                "summary": "Stress, strain, and how we measure strength and ductility.",
                "concepts": [
                    {"t": "Engineering stress/strain", "d": "σ = F/A₀, ε = ΔL/L₀ — based on the ORIGINAL area/length. True stress uses the instantaneous area (σ_t = σ(1+ε))."},
                    {"t": "Elastic vs. plastic", "d": "Elastic = recovers on unloading (linear for metals up to the yield point, E = slope). Plastic = permanent deformation."},
                    {"t": "Yield & UTS", "d": "Yield strength = stress at 0.2% offset (where a line of slope E, offset 0.002 strain, meets the curve). UTS = maximum engineering stress."},
                    {"t": "Ductility", "d": "%EL = (L_f − L₀)/L₀ × 100; %RA = (A₀ − A_f)/A₀ × 100. High values = ductile, warns before failure."},
                    {"t": "Toughness & resilience", "d": "Resilience = energy absorbed elastically (area up to yield = ½σ_y ε_y). Toughness = total area under the stress-strain curve — energy to fracture."},
                    {"t": "Hardness & Poisson", "d": "Hardness (Rockwell/Brinell/Vickers/Vickers indentation) correlates with strength. Poisson's ratio ν = −ε_lateral/ε_axial ≈ 0.3 for metals."},
                ],
                "formulas": [
                    {"n": "Engineering stress", "e": "σ = F / A₀", "note": "A₀ = original cross-section."},
                    {"n": "Engineering strain", "e": "ε = (L − L₀) / L₀", "note": "Dimensionless; often given in %."},
                    {"n": "Hooke's law (uniaxial)", "e": "σ = E ε", "note": "E = Young's modulus = slope of the elastic region."},
                    {"n": "Poisson's ratio", "e": "ν = − ε_lat / ε_long", "note": "≈ 0.27–0.36 for metals; 0.5 = incompressible (rubber)."},
                    {"n": "Resilience", "e": "U_r = ½ σ_y ε_y = σ_y² / (2E)", "note": "Elastic energy per unit volume."},
                    {"n": "True stress", "e": "σ_true = σ_eng (1 + ε_eng)", "note": "Valid until necking (Considère point)."},
                ],
                "example": {
                    "problem": "A tensile test on a Ø12.5 mm bar (L₀ = 50 mm) fractures at F_max = 45 kN with final length 60 mm. Find UTS and %EL.",
                    "steps": [
                        "A₀ = π d²/4 = π × 12.5²/4 = 122.7 mm².",
                        "UTS = F_max / A₀ = 45 000 N / 122.7 mm² = 366.7 N/mm² = 366.7 MPa.",
                        "%EL = (60 − 50)/50 × 100 = 20 %.",
                    ],
                    "answer": "UTS ≈ 367 MPa; %EL = 20 % (a reasonably ductile metal).",
                },
                "traps": [
                    "Using the instantaneous area in engineering stress — engineering uses A₀.",
                    "Reading UTS off the true-stress curve (they peak differently; necking changes the story).",
                    "Treating hardness as a strength unit — it correlates, it isn't one.",
                ],
                "practice": [
                    {"q": "A steel has σ_y = 350 MPa and E = 200 GPa. Find the elastic strain at yield and the resilience.", "a": "ε_y = σ/E = 350e6/200e9 = 1.75×10⁻³ (0.175%). U_r = σ_y²/(2E) = (350e6)²/(2×200e9) = 306 kJ/m³."},
                    {"q": "What does the area under the entire stress-strain curve represent?", "a": "Toughness — the energy absorbed per unit volume up to fracture."},
                ],
            },
            {
                "id": "em-4",
                "title": "Phase Diagrams & Heat Treatment",
                "summary": "Reading the Fe–C map and turning it into hardness.",
                "concepts": [
                    {"t": "Phase diagram basics", "d": "Maps phases vs. temperature and composition at equilibrium. The liquidus is the boundary below which solid begins; the solidus where it completes."},
                    {"t": "The lever rule", "d": "Gives the mass fraction of each phase inside a two-phase region: Wα = (Cβ − C₀)/(Cβ − Cα)."},
                    {"t": "Fe–Fe₃C (iron–carbon)", "d": "Key phases: ferrite (α, soft, BCC, ~0.022 %C), austenite (γ, FCC, up to 2.14 %C), cementite (Fe₃C, hard/brittle), pearlite (ferrite+cementite lamellae). Eutectoid at 0.76 %C, 727 °C."},
                    {"t": "Martensite", "d": "A non-equilibrium, supersaturated, body-centred-tetragonal phase formed by rapid quenching — very hard, very brittle. Diffusion-free (shear) transformation."},
                    {"t": "Heat treatments", "d": "Annealing (soften, relieve stress), normalising (refine grains), quenching (form martensite, hard), tempering (reheat to trade hardness for toughness), austempering/martempering."},
                    {"t": "TTT / CCT curves & hardenability", "d": "Time-Temperature-Transformation tells you whether you get pearlite/bainite/martensite at a given cooling rate. Hardenability (Jominy test) = depth of hardening, driven by alloy content."},
                ],
                "formulas": [
                    {"n": "Lever rule (phase fraction)", "e": "Wα = (Cβ − C₀)/(Cβ − Cα), Wβ = (C₀ − Cα)/(Cβ − Cα)", "note": "C's are the phase compositions at that temperature; fraction, not %."},
                    {"n": "Eutectoid composition (Fe-C)", "e": "0.76 wt% C at 727 °C", "note": "Gives 100% pearlite on slow cooling."},
                    {"n": "Eutectic point", "e": "4.30 wt% C at 1147 °C", "note": "Forms ledeburite; relevant to cast irons."},
                ],
                "example": {
                    "problem": "At 727 °C just above the eutectoid line, an Fe–C alloy has C₀ = 0.40 wt% C. The bounding phases are ferrite (Cα = 0.022) and austenite (Cγ = 0.76). Find the mass fractions.",
                    "steps": [
                        "W_ferrite = (Cγ − C₀)/(Cγ − Cα) = (0.76 − 0.40)/(0.76 − 0.022) = 0.36/0.738 = 0.488.",
                        "W_austenite = 1 − 0.488 = 0.512 (or (C₀ − Cα)/(Cγ − Cα) = 0.378/0.738 = 0.512 ✓).",
                    ],
                    "answer": "About 48.8 % ferrite and 51.2 % austenite by mass; cooling further turns the austenite into pearlite.",
                },
                "traps": [
                    "Putting the compositions in the wrong side of the lever rule — the phase you want goes farthest in the numerator.",
                    "Reporting a fraction as a percentage (or vice-versa) without converting.",
                    "Confusing eutectic (1147 °C, 4.3 %C) with eutectoid (727 °C, 0.76 %C).",
                ],
                "practice": [
                    {"q": "What is martensite and why is it hard?", "a": "A supersaturated, distorted (body-centred-tetragonal) phase formed by rapid quenching; carbon trapped in the lattice creates strain that resists dislocation motion."},
                    {"q": "What does tempering do after quenching?", "a": "Reheating reduces hardness slightly but greatly increases toughness/ductility by relieving internal stress and precipitating carbides."},
                ],
            },
            {
                "id": "em-5",
                "title": "Failure: Fracture, Fatigue, Creep & Corrosion",
                "summary": "How materials actually break, and the conditions that accelerate it.",
                "concepts": [
                    {"t": "Ductile vs. brittle fracture", "d": "Ductile: substantial plastic deformation, cup-and-cone, fibrous; slow crack growth (warns). Brittle: little deformation, flat/cleavage, fast crack (sudden)."},
                    {"t": "Fracture mechanics", "d": "K = Y σ √(π a) is the stress-intensity factor; fracture when K ≥ K_Ic (fracture toughness). Longer crack or higher stress → sooner failure."},
                    {"t": "Ductile-to-brittle transition", "d": "BCC steels turn brittle below a transition temperature (Charpy energy drops); FCC metals don't. Critical for cold weather, ships, bridges."},
                    {"t": "Fatigue", "d": "Cyclic loads far below UTS cause failure after many cycles. S–N curve; some steels show an endurance limit (finite stress below which life is 'infinite'). Initiation at stress raisers."},
                    {"t": "Creep", "d": "Slow, permanent deformation under constant stress at high temperature (T ≥ ~0.4 Tm). Stages: primary, steady-state (minimum creep rate), tertiary (rupture)."},
                    {"t": "Corrosion", "d": "Electrochemical: an anode (dissolves), a cathode, an electrolyte, and a metallic path. Galvanic (dissimilar metals), pitting, crevice. Protect with coatings, cathodic protection, or alloying (Cr in stainless)."},
                ],
                "formulas": [
                    {"n": "Stress intensity factor", "e": "K = Y σ √(πa)", "note": "Y ≈ 1 for a centre crack; a = half-crack length. Failure when K = K_Ic."},
                    {"n": "Paris law (fatigue crack growth)", "e": "da/dN = C (ΔK)^m", "note": "Crack grows per cycle; m ≈ 3-4 for metals."},
                    {"n": "Steady-state creep (Arrhenius)", "e": "ε̇ = A σⁿ exp(−Q/RT)", "note": "Rate rises fast with temperature T."},
                ],
                "example": {
                    "problem": "A steel plate (K_Ic = 60 MPa·√m) carries a 200 MPa stress. What is the critical (half-)crack length for fast fracture?",
                    "steps": [
                        "Use K = Y σ √(π a) with Y = 1, set K = K_Ic.",
                        "a_c = (K_Ic / σ)² / π = (60/200)² / π = (0.3)²/π = 0.09/3.1416.",
                        "a_c = 0.0287 m ≈ 28.7 mm.",
                    ],
                    "answer": "A through-thickness half-crack of ≈ 29 mm causes fast fracture at 200 MPa — a reason for routine inspection of welds.",
                },
                "traps": [
                    "Comparing fatigue strength to yield strength as if the same quantity — fatigue is a cyclic, surface/stress-raiser phenomenon.",
                    "Ignoring the notch/stress raiser; fatigue almost always starts there.",
                    "Applying room-temperature toughness data to a cold or high-temperature service environment (DBTT / creep).",
                ],
                "practice": [
                    {"q": "What is an S–N curve and what is the endurance limit?", "a": "Stress amplitude vs. cycles-to-failure (log scale). The endurance limit is the stress below which some steels survive an effectively infinite number of cycles."},
                    {"q": "Four requirements for electrochemical corrosion?", "a": "An anode, a cathode, an electrolyte, and a metallic path connecting them."},
                ],
            },
            {
                "id": "em-6",
                "title": "Materials Classes & Selection",
                "summary": "Metals, ceramics, polymers, composites — and choosing between them.",
                "concepts": [
                    {"t": "Four families", "d": "Metals (strong, ductile, conductive), ceramics/glasses (hard, heat-resistant, brittle), polymers (light, cheap, low strength, temperature-limited), composites (tailored stiffness/strength, e.g. carbon fibre)."},
                    {"t": "Composites", "d": "Rule of mixtures blends properties: stiffness/strength of a fibre composite lies between fibre and matrix, weighted by volume fraction (and orientation)."},
                    {"t": "Ashby selection", "d": "Material property charts (E vs. ρ, strength vs. ρ) with performance indices (e.g. E/ρ for a light stiff beam) let you select by objective + constraint."},
                    {"t": "Property trade-offs", "d": "No material is best at everything: stiffness vs. toughness vs. cost vs. weight. Selection = optimise one index subject to constraints."},
                    {"t": "Recycling & sustainability", "d": "Metals recycle well, thermoplastics can be remelted, thermosets cannot; embodied energy matters. Increasing weight in design specifications."},
                ],
                "formulas": [
                    {"n": "Rule of mixtures (stiffness)", "e": "E_c = f E_f + (1 − f) E_m", "note": "f = fibre volume fraction; upper bound for aligned continuous fibre."},
                    {"n": "Light stiff beam index", "e": "M = E^(1/2) / ρ", "note": "Maximise to minimise mass for a given stiffness and length."},
                    {"n": "Light stiff panel index", "e": "M = E^(1/3) / ρ", "note": "Bending-limited flat panel."},
                    {"n": "Specific stiffness", "e": "E / ρ", "note": "Higher = better for stiffness-critical, weight-critical designs."},
                ],
                "example": {
                    "problem": "Choose between two alloys for a light, stiff beam: Alloy X (E = 70 GPa, ρ = 2700 kg/m³) and Alloy Y (E = 200 GPa, ρ = 7850 kg/m³).",
                    "steps": [
                        "Use the light stiff beam index M = √E / ρ.",
                        "X: √70e9 = 264 575; /2700 = 98.0.",
                        "Y: √200e9 = 447 214; /7850 = 57.0.",
                        "Higher index wins → Alloy X.",
                    ],
                    "answer": "Alloy X (aluminium-like) has the higher index (98 vs 57) → lighter for the same beam stiffness, despite lower E, because it is far less dense.",
                },
                "traps": [
                    "Choosing on strength alone, ignoring density when weight matters.",
                    "Using the wrong performance index for the loading case (beam vs. panel vs. tie).",
                    "Forgetting cost, service temperature, or corrosion environment in the constraint set.",
                ],
                "practice": [
                    {"q": "Why are ceramics used where metals fail?", "a": "High hardness, high-temperature stability, and chemical inertness — used in cutting tools, turbine coatings, and refractory linings."},
                    {"q": "Give the performance index for a lightweight tie (axial stiffness).", "a": "M = E / ρ (specific stiffness) — maximise it."},
                ],
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# MCQ QUIZ BANK  (unit, question, 4 options, correct index, explanation)
# ---------------------------------------------------------------------------

QUIZ_BANK = {
    "CCD-101": [
        {"unit": "ccd-1", "q": "Which NSPE canon overrides the others when they conflict?",
         "opts": ["Be a faithful agent of the employer", "Hold public safety, health and welfare paramount", "Avoid conflicts of interest", "Perform only in your competence"],
         "answer": 1, "explain": "Public safety is the paramount canon; it outranks employer loyalty and profit."},
        {"unit": "ccd-1", "q": "A vendor offers free equipment if you recommend their product. The correct action is to:",
         "opts": ["Accept — it saves money", "Accept and recommend", "Disclose the offer and recuse yourself from the recommendation", "Stay silent and recommend the other brand"],
         "answer": 2, "explain": "It is a conflict of interest; the ethical response is disclosure and recusal."},
        {"unit": "ccd-2", "q": "The 'inverted pyramid' in an engineering report means:",
         "opts": ["Method first, conclusion last", "Conclusion/recommendation first, then evidence", "Only diagrams, no text", "Chronological order of the project"],
         "answer": 1, "explain": "Busy readers stop after the first paragraph, so lead with the result."},
        {"unit": "ccd-3", "q": "Feedback using the SBI model focuses on:",
         "opts": ["The person's character", "Observable behaviour and its impact", "Past unrelated mistakes", "The team's overall performance"],
         "answer": 1, "explain": "Situation–Behaviour–Impact describes behaviour and effect, not character."},
        {"unit": "ccd-4", "q": "The FE exam is best described as:",
         "opts": ["A requirement to enter any engineering job", "The Fundamentals of Engineering exam, typically taken near graduation on the licensure path", "A university final-year project", "The exam for a PE licence, taken after 4 years of experience"],
         "answer": 1, "explain": "FE = Fundamentals of Engineering, near graduation; the PE comes later after supervised experience."},
        {"unit": "ccd-4", "q": "Most applicant-tracking systems will reject a résumé that:",
         "opts": ["Uses a simple single-column layout", "Mirrors the job's keywords", "Uses a two-column graphic template hard to parse", "Lists quantified results"],
         "answer": 2, "explain": "Complex multi-column/graphic résumés confuse ATS parsers and may never reach a human."},
        {"unit": "ccd-5", "q": "Which Eisenhower quadrant should most study time go to?",
         "opts": ["Q1 urgent + important", "Q2 important, not urgent", "Q3 urgent, not important", "Q4 neither"],
         "answer": 1, "explain": "Quadrant II is where prevention and real learning happen; living there prevents Q1 crises."},
        {"unit": "ccd-5", "q": "'SMART' goals are Specific, Measurable, Achievable, Relevant and:",
         "opts": ["Timely (Time-bound)", "Tested", "Technical", "Tracked by others"],
         "answer": 0, "explain": "The T is Time-bound — a deadline makes a goal checkable."},
    ],
    "MD-102": [
        {"unit": "md-1", "q": "The difference between a requirement and a constraint is:",
         "opts": ["A requirement is a limit, a constraint is a function", "A requirement is what the design must DO; a constraint limits the solution", "They are the same thing", "Constraints are only about cost"],
         "answer": 1, "explain": "Functional requirements = what it does; constraints = limits (cost, envelope, codes)."},
        {"unit": "md-1", "q": "In a Pugh matrix, the weights:",
         "opts": ["Can be any numbers", "Must sum to 1 (or 100%)", "Are all equal", "Are the scores"],
         "answer": 1, "explain": "Weights are normalised fractions so the weighted score is comparable across concepts."},
        {"unit": "md-2", "q": "A hidden (obscured) edge in a drawing is shown as:",
         "opts": ["A thick solid line", "A dashed line", "A chain line", "A hatched area"],
         "answer": 1, "explain": "Dashed = hidden edge; and it's omitted in section views."},
        {"unit": "md-3", "q": "A CAD sketch that turns black is one that is:",
         "opts": ["Under-constrained", "Fully constrained", "Over-constrained and broken", "Missing dimensions only"],
         "answer": 1, "explain": "Black = fully constrained (all degrees of freedom removed) — safe to extrude."},
        {"unit": "md-3", "q": "How many degrees of freedom does a free rigid body have in 3D?",
         "opts": ["3", "4", "6", "12"],
         "answer": 2, "explain": "Three translations + three rotations = six DOF."},
        {"unit": "md-4", "q": "A Ø10 hole 10.00/10.05 mm with a shaft 9.98/9.99 mm forms a:",
         "opts": ["Interference fit", "Transition fit", "Clearance fit", "Force fit"],
         "answer": 2, "explain": "The hole is always larger than the shaft → clearance fit (min clearance 0.01 mm)."},
        {"unit": "md-5", "q": "The RSS stackup is tighter than worst-case because:",
         "opts": ["It ignores tolerance", "Independent random errors partially cancel", "It assumes zero tolerance", "It uses larger numbers"],
         "answer": 1, "explain": "Statistical (root-sum-square) tolerancing accounts for the reduced probability of all errors being extreme at once."},
        {"unit": "md-5", "q": "The cheapest time to apply DFM is:",
         "opts": ["After prototyping", "At the concept stage", "At first production run", "After field failures"],
         "answer": 1, "explain": "Cost is locked in early; concept changes are cheap, production changes are not."},
    ],
    "SM-201": [
        {"unit": "sm-1", "q": "A force of 100 N acts at 60° above the horizontal. Its vertical component is:",
         "opts": ["50.0 N", "86.6 N", "60.0 N", "100 N"],
         "answer": 1, "explain": "Fy = 100 sin60° = 86.6 N (horizontal = 50 N)."},
        {"unit": "sm-1", "q": "The moment of a force about a point depends on:",
         "opts": ["Only the force magnitude", "Force magnitude and perpendicular distance", "The mass", "Time"],
         "answer": 1, "explain": "M = F·d; the perpendicular distance from the point to the line of action."},
        {"unit": "sm-2", "q": "A spring of k = 400 N/m extends 0.05 m. The force it applies is:",
         "opts": ["8 N", "20 N", "2000 N", "0.2 N"],
         "answer": 1, "explain": "F = k·s = 400 × 0.05 = 20 N."},
        {"unit": "sm-3", "q": "A fixed (cantilevered) support in 2D provides:",
         "opts": ["One vertical reaction", "Two forces and a moment", "A force perpendicular to the surface", "No reactions"],
         "answer": 1, "explain": "Fixed support = force in x, force in y, and a moment (3 unknowns)."},
        {"unit": "sm-4", "q": "For a planar truss with 7 members, 5 joints and 3 reaction components, m + r vs 2j gives:",
         "opts": ["Statical indeterminacy", "A mechanism", "Statically determinate", "Impossible truss"],
         "answer": 2, "explain": "m + r = 10 = 2j = 10 → statically determinate."},
        {"unit": "sm-4", "q": "A truss member at an unloaded joint with two non-collinear members has:",
         "opts": ["Both members in compression", "Both members zero-force", "Unknown forces", "One in tension, one in compression"],
         "answer": 1, "explain": "With no other force at the joint, both members are zero-force."},
        {"unit": "sm-5", "q": "A 200 N block sits on a floor with μ_s = 0.5. The push needed to start it sliding is:",
         "opts": ["50 N", "100 N", "200 N", "400 N"],
         "answer": 1, "explain": "F_max = μ_s N = 0.5 × 200 = 100 N."},
        {"unit": "sm-6", "q": "The moment of inertia of a rectangle b×h about its centroidal axis (parallel to b) is:",
         "opts": ["b h³/12", "b h³/3", "b³ h/12", "b h³/36"],
         "answer": 0, "explain": "I = b h³/12 about the centroidal axis parallel to the base b."},
        {"unit": "sm-6", "q": "The parallel-axis theorem states:",
         "opts": ["I = Ī − A d²", "I = Ī + A d²", "I = A d²", "I = Ī / A"],
         "answer": 1, "explain": "I = Ī + A d², shifting from the centroidal axis to a parallel axis at distance d."},
    ],
    "EM-202": [
        {"unit": "em-2", "q": "How many atoms per unit cell are there in BCC?",
         "opts": ["1", "2", "4", "8"],
         "answer": 1, "explain": "BCC has 2 atoms per cell (SC 1, FCC 4)."},
        {"unit": "em-2", "q": "The Hall–Petch relationship says that smaller grain size:",
         "opts": ["Lowers yield strength", "Raises yield strength", "Has no effect", "Only affects density"],
         "answer": 1, "explain": "σ_y = σ₀ + k/√d — more grain boundaries impede dislocations, raising strength."},
        {"unit": "em-3", "q": "Engineering stress uses:",
         "opts": ["Instantaneous area", "Original cross-sectional area", "Volume", "The fracture area"],
         "answer": 1, "explain": "σ = F/A₀, based on the original area (true stress uses instantaneous area)."},
        {"unit": "em-3", "q": "Poisson's ratio is:",
         "opts": ["ε_long / ε_lat", "− ε_lat / ε_long", "σ / ε", "ΔL / L"],
         "answer": 1, "explain": "ν = −ε_lateral/ε_axial, ≈ 0.3 for metals; the minus keeps it positive."},
        {"unit": "em-4", "q": "The eutectoid point in the Fe–Fe₃C diagram is:",
         "opts": ["4.30 wt% C at 1147 °C", "0.76 wt% C at 727 °C", "2.14 wt% C at 1147 °C", "0.022 wt% C at 727 °C"],
         "answer": 1, "explain": "Eutectoid: 0.76 wt% C at 727 °C → 100% pearlite on slow cooling."},
        {"unit": "em-4", "q": "Martensite forms by:",
         "opts": ["Slow cooling", "Rapid quenching", "Annealing", "Cold rolling"],
         "answer": 1, "explain": "Rapid quenching traps carbon → diffusion-free shear transformation to hard, brittle martensite."},
        {"unit": "em-5", "q": "Fatigue failure occurs:",
         "opts": ["Only above the UTS", "Under repeated cyclic stress, often far below the UTS", "Only at high temperature", "Only in ceramics"],
         "answer": 1, "explain": "Cyclic loading causes crack initiation/growth at stresses well below the ultimate strength."},
        {"unit": "em-6", "q": "The performance index for a light stiff beam is:",
         "opts": ["E / ρ", "E^(1/2) / ρ", "E^(1/3) / ρ", "ρ / E"],
         "answer": 1, "explain": "For a light stiff beam M = √E / ρ (tie = E/ρ, panel = E^⅓/ρ)."},
    ],
}


# ---------------------------------------------------------------------------
# Derived helpers
# ---------------------------------------------------------------------------

def course_by_code(code):
    for c in COURSES:
        if c["code"] == code:
            return c
    return None


def all_units():
    out = []
    for c in COURSES:
        for u in c["units"]:
            out.append((c, u))
    return out


def flashcards_for(course_code):
    """Generate flashcards from concepts + formulas (single source of truth)."""
    c = course_by_code(course_code)
    cards = []
    if not c:
        return cards
    for u in c["units"]:
        for i, con in enumerate(u["concepts"]):
            cards.append({"unit": u["id"], "uid": f"{u['id']}-c{i}", "front": con["t"], "back": con["d"]})
        for i, f in enumerate(u["formulas"]):
            cards.append({"unit": u["id"], "uid": f"{u['id']}-f{i}", "front": f["n"], "back": f"{f['e']}  —  {f['note']}"})
    return cards


def quiz_for_unit(course_code, unit_id):
    return [q for q in QUIZ_BANK.get(course_code, []) if q["unit"] == unit_id]


def course_context(course_code, unit_id=None):
    """Compact text context injected into the AI tutor's system prompt."""
    c = course_by_code(course_code)
    if not c:
        return ""
    lines = [f"COURSE: {c['title']} ({c['code']})", f"Overview: {c['blurb']}", ""]
    units = [u for u in c["units"] if (unit_id is None or u["id"] == unit_id)]
    for u in units:
        lvl = u.get("level", 2)
        lvlname = {1: "Foundational", 2: "Intermediate", 3: "Advanced"}.get(lvl, "Intermediate")
        lines.append(f"UNIT — {u['title']} [{lvlname}]: {u['summary']}")
        for con in u["concepts"]:
            lines.append(f"  • {con['t']}: {con['d']}")
        for f in u["formulas"]:
            lines.append(f"  = {f['n']}: {f['e']}  ({f['note']})")
        lines.append(f"  Worked example: {u['example']['problem']} -> {u['example']['answer']}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Additional courses (Calculus II, Physics II) live in content_extra.py; merge
# them here so every surface (courses, flashcards, quizzes, tutor context)
# picks them up from this one module.
# ---------------------------------------------------------------------------

try:
    from content_extra import CALC2, PHYS2, QUIZ_EXTRA
    # Calculus II and Physics II are foundational for the second-year load — list them first.
    COURSES[:0] = [CALC2, PHYS2]
    for _code, _qs in QUIZ_EXTRA.items():
        QUIZ_BANK.setdefault(_code, [])
        QUIZ_BANK[_code].extend(_qs)
except ImportError:  # pragma: no cover
    pass


# ---------------------------------------------------------------------------
# Difficulty progression merge (difficulty.py)
# Tags every unit / quiz question / practice problem with a level (1-3) and adds
# a harder worked example + extra practice per unit, so material can be worked
# easy -> hard. Degrades gracefully if difficulty.py is absent.
# ---------------------------------------------------------------------------

try:
    from difficulty import LEVELS, UNIT_LEVELS, QUIZ_LEVELS, PRACTICE_TAGS, UNIT_EXTRA
except ImportError:  # pragma: no cover
    LEVELS, UNIT_LEVELS, QUIZ_LEVELS, PRACTICE_TAGS, UNIT_EXTRA = {}, {}, {}, {}, {}

LEVEL_ORDER = (1, 2, 3)


def _apply_difficulty():
    for c in COURSES:
        for u in c["units"]:
            uid = u["id"]
            lvl = UNIT_LEVELS.get(uid, 2)
            u["level"] = lvl
            # tag the base practice problems
            tags = PRACTICE_TAGS.get(uid, [])
            for i, p in enumerate(u.get("practice", [])):
                p["level"] = tags[i] if i < len(tags) else min(3, lvl + 1)
            extra = UNIT_EXTRA.get(uid, {})
            # a harder second worked example
            if extra.get("example"):
                ex = dict(extra["example"])
                ex.setdefault("level", min(3, lvl + 1))
                u["example_hard"] = ex
            # extra practice, merged and ordered easy -> hard
            if extra.get("practice"):
                u["practice"] = u.get("practice", []) + list(extra["practice"])
            u["practice"] = sorted(u.get("practice", []), key=lambda p: p.get("level", 2))
        # quiz questions: tag + order easy -> hard within the course
        qs = QUIZ_BANK.get(c["code"], [])
        levels = QUIZ_LEVELS.get(c["code"], [])
        for i, q in enumerate(qs):
            q["level"] = levels[i] if i < len(levels) else 2
        QUIZ_BANK[c["code"]] = sorted(qs, key=lambda q: q["level"])


_apply_difficulty()
# NOTE: units keep their SYLLABUS order (the pedagogy is the sequence); the level
# badge shows the ramp. UNIT_LEVELS is authored monotonic per course so the ramp
# still reads easy -> hard.
