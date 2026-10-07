---
name: ruling-session
description: Use when the maintainer's open decisions on os-ai-map need clearing in one pass — preparing a walk-and-talk session from the live review queue, running it one spoken question at a time with a recommendation attached, and recording the answers in docs/rulings/log.yaml through a PR. Two modes, prepare and run; a routine can prepare, and only a person can be run with.
---

# Ruling session

The corpus waits on the maintainer for a small number of decisions, and each one blocks work an
agent could otherwise finish. This skill clears them in one sitting that works while the maintainer
is on their feet: one question at a time, spoken, each with a recommendation they can answer in
a word.
The answers become entries in `docs/rulings/log.yaml`, which is the record every agent reads
before it asks anything (`docs/rulings/README.md` has the format and its rules).

## Two modes

- **prepare**: build the question list and write the session prompt. This takes the research
  and the reading, and it can run unattended, as a routine or an OSO agent task. Its output is
  a prompt someone pastes into a voice session.
- **run**: hold the conversation, get the confirmation, write the log. This needs the person.

The split matters because the run has one rule the prepare exists to satisfy: **nothing is
looked up mid-session.** Everything the run needs is in the prompt.

## Prepare

### 1. Gather what waits on a ruling

```bash
uv run python -m build.review_queue --waits-on ruling --json
uv run python -m build.review_queue --waits-on ruling --live --json   # adds contradictions
```

Add three sources the builder does not read:

- open GitHub issues in `currentai-org/os-ai-map` whose last status names a decision someone
  else has to make, and the `category-proposal` backlog when a category's review is due;
- "Needs a ruling" sections in open PRs;
- blocked OSO agent tasks in the `currentai` org (`ListAgentTasks` with status `BLOCKED`) whose
  questions concern the map.

### 2. Drop what is already ruled

Read `docs/rulings/log.yaml` in full. A question whose substance an `in-force` ruling answers is
not asked again. Apply that ruling to the case, and list it in the prompt's appendix as "settled
by R-…" so the maintainer can see what was not put to them. A `deferred` ruling comes back only
if the reason it was deferred has changed. Say what changed.

### 3. Choose and order

- **At most eighteen questions.** More than that and the later answers get worse. Carry the rest
  to the next session, and say how many were carried.
- **Prefer the question that unblocks the most.** A rule that settles a class of holds beats
  one hold. Where several holds share a shape, ask the class question ("should a dataset card
  that allows unlicensed files read as permissive?"), not each case.
- **Dependency order.** An answer that changes a later recommendation goes first. Mark the
  dependency on the later question so the run confirms it rather than asking again.
- **Group into blocks** of related questions, the way `docs/workflows/` groups a procedure.

### 4. Write each question

For each one: at most forty words of context, then the question, then a recommendation with the
reason ("I'd say X, because Y — agree?"). Name the issue, product or hold id. Everything the
recommendation rests on is gathered now, from primary sources where it is a question of fact,
because the run cannot look it up. Where a question needs them to see a file or a figure, say
that it will be parked, and put it at the end of the list.

Read the ruling's normative home before recommending. A license question reads
`docs/reference/openness.md` and the category's `scoring_recipe`, an adoption question
`docs/reference/adoption.md`, an identity question `docs/reference/identity.md`. A
recommendation that contradicts a rule in force is a proposal to change the rule, and says so.

### 5. Emit the prompt

The prompt carries: the run rules below, verbatim; the blocks and questions; an out-of-scope
list (what was carried, what needs a screen, what an agent can do without them); and the
appendix of questions settled by an existing ruling. Deliver it where they will pick it up: a
PR comment, an OSO memory named `temp.ruling-session-<date>.md`, or the chat that asked for it.

## Run

The maintainer is walking and talking, not reading. These rules exist because they are on
their feet:

- **Lead with the question.** One or two sentences of context, then the question, then your
  recommendation. Never more than about forty words before they can answer.
- **Always recommend.** They should be able to answer in one word. A bare open question is a
  failure of this session.
- **No code, no tables, no lists to read.** If a decision needs their eyes on something, park it.
- **Accept fuzzy answers.** "Yeah, the second one" is an answer. Reflect it back in one line, in
  your words, and move on. Ask for precision only when the imprecision changes what gets built.
- **Let them skip.** "Skip", "later" and "I don't know yet" are answers. Record the question as
  deferred with the reason they gave, and never re-ask it in the same session.
- **Track position.** Say "that's six of fourteen" every few questions.
- **Do not look things up.** If a question turns on a fact that is not in the prompt, defer it
  rather than going quiet while you read.
- **Follow the thread.** If an answer implies a ruling on a later question, say so and confirm
  it rather than asking again.

Say at the start that they do not have to accept any recommendation. Several are close calls,
and the recommendation is there to react to, not to ratify.

### Confirm, then record

1. **Read back every ruling** in one or two sentences each, and get an explicit yes before
   writing anything.
2. **Append one entry per question** to `docs/rulings/log.yaml`, including every deferral, in
   the format `docs/rulings/README.md` gives: `venue: walk-and-talk`, the ruling in their voice,
   their reasoning in their words where they gave one, and `executor` set to who carries it out.
   Nothing they did not say goes in `ruling` or `reasoning`.
3. **Open one PR** with the log entries and nothing else. The rulings are applied in their own
   PRs, by the applier routine or by the skill each ruling routes to (`update-product`,
   `edit-category`, `build-rubric`, `migrate-axis`), and each of those cites the ruling id.
4. **Offer, do not do unprompted,** to post each ruling as a comment on its issue or PR thread.

## Validation

```bash
uv run pytest tests/test_rulings.py -q
```
