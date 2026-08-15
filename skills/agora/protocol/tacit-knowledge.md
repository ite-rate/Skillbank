# Tacit Knowledge Extraction Protocol (Polanyi)

> Referenced by `protocol/deliberation.md` Step 2b. Invoke when Tacit Signal is detected.

---

## Trigger Signal Words

Scan the user's input for these patterns (list is illustrative, not exhaustive):

- 就是那种感觉
- 说不清楚，但我知道
- 像 X 那种风格 / 像 X 那样
- 你懂的那种
- 不想要那种（感觉/风格/结果）
- 感觉不对，但说不出哪里不对
- 差那么一点点，但我不知道是什么
- 我看到过/用过/体验过，就想要那种
- 凭直觉觉得这个方向不对
- 总之就是那种……（句子未完成）

If any of these patterns appear, do NOT proceed to standard deliberation. Run the 3-Step Extraction below first.

---

## 3-Step Tacit Knowledge Extraction

State to the user:

> "我注意到你的描述包含难以直接说清楚的感受，先把它变得清晰，审议会更准确。帮我完成三个简单的问题："

### Step 1 — Exemplar Extraction（示范提取）

> "给我一个你觉得**'对'**的例子——可以是你见过的、用过的、体验过的任何东西（不必和你的问题完全一致）。"

- Purpose: Externalize the tacit standard through a concrete reference
- Coordinator notes: What specific properties does this example have? List them.
- If user can't provide an example → proceed to Step 2 first

### Step 2 — Negative Extraction（反面提取）

> "告诉我你**绝对不想要**的是什么——一个反例，或者你见过的让你觉得'不对'的东西。"

- Purpose: Boundary definition is often easier than positive definition
- Coordinator notes: What properties does this anti-example have? These become constraints.
- The contrast between Step 1 and Step 2 reveals the core distinction the user cannot articulate

### Step 3 — Behavioral Extraction（行为提取）

> "你之前做过类似的决定或创作吗？那次你是怎么选的？结果感觉怎么样？"

- Purpose: Recover embodied knowledge from past decisions
- Coordinator notes: What decision logic is revealed? What did the user optimize for without knowing it?
- If no prior experience → skip this step

---

## Output Format: Tacit Knowledge Brief

After running the extraction, compile:

```
### Tacit Knowledge Brief

**Exemplar** (正例):
{The concrete example the user provided, and the properties extracted from it}

**Anti-exemplar** (反例):
{The concrete counter-example, and the constraints it reveals}

**Behavioral inference** (行为推断):
{What the user's past decisions reveal about their implicit criteria}

**Articulated requirement** (提炼出的明确需求):
{The explicit statement of what the user actually wants — formulated as a clear problem input}
```

---

## Termination Conditions

- **Stop** when the user can state their requirement in clear, specific language without hedging
- **Stop** when the Coordinator can write the Articulated Requirement without guessing
- **Stop** after 3 steps maximum — do not add more extraction rounds
- **Replace** the original vague input with the Articulated Requirement before proceeding to deliberation
- The original vague input is preserved in the Brief as context, but deliberation uses the Articulated Requirement

---

## Integration with Deliberation

- The **Tacit Knowledge Brief** is injected into Step 1's Evidence Brief under a new subsection: `Tacit Knowledge Brief`
- The **Articulated Requirement** replaces the original problem statement in Step 2a and all downstream steps
- The extraction interaction does NOT count toward the 2-AskUser limit of the 8-step protocol
- Panel members are informed: "The user's original statement was tacit; the following is the extracted requirement: {Articulated Requirement}"
