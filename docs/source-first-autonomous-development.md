# Source-first autonomous MySugya development

Status: proposed operating workflow; the source-only packet implementation is available, but this document does not authorize a running campaign or replace the current certification gate.

## Mission and authority

Rabbi is the autonomous MySugya owner/operator running INSIDE OpenClaw. Once separately admitted through the existing operator-stop, quota, and watchdog controls, Rabbi may select the next authorized unit, route coding and scholarly tasks to capable workers, perform independent review, create scoped PRs, check CI, merge under existing policy, record evidence, and proceed without a human for routine work. The user approves new tractates and exceptional risk decisions. GitHub is the public durable authority for product code, instructions and nonsecret decisions, NOT for private OpenClaw state.

The existing Yoma corpus has 173 daf and 492 sugyot; its existing schema-2.0 certificates are historical attestations, NOT an unquestionable truth oracle. Do not delete, downgrade, overwrite, or skip these records through this design proposal. The current `CLAUDE.md` and semantic campaign runbook remain controlling until an explicit, tested migration PR changes them. A newly trusted source-backed result must pass the full existing semantic gate as well as the new source comparison.

## Daf-ordered source verification, independent of previous certifications

Start at 2a for an approved Yoma source-verification campaign. Use the same steps, module paths and validators for the next operator-approved tractate:

1. Check the OpenClaw operator stop, quota, reserve, campaign mode, watchdogs and recorded decision. If not admitted, do no agent execution. Stop periodic inference-consuming polling.
2. Build the SOURCE-ONLY packet: `python3 scripts/campaign_packet.py --module yoma --daf 2a --mode source`. It contains cached talmud.dev Hebrew, locally cached Sefaria Gemara Hebrew/English in their original sequential order, a physical-line start hint and an evidence hash. It deliberately contains NO existing sugya boundaries, enriched IDs, authored sourceRefs, AI-authored explanations, old review findings or certificate labels. It reads locally and makes no external API requests.
3. Verify the complete physical daf and the boundaries with adjacent daf; independently establish the sugya's real speakers, claims, evidence, sources, objections, conclusions and remaining open issues from original Hebrew. Published English is corroboration, not automatic semantic proof. The initial source packet does not expose the existing sugya map at all. Reconstruct page flow and boundaries independently; compare those findings to the candidate map only in phase two. A matching segment count cannot prove correct meaning.
4. Compare the established source facts to existing MySugya authored content (candidate packet), including daf-wide summary, glossary, argumentFlow, quizzes, misconception corrections, reference links and interpretive claims. Preserve every supported value. Flag only concrete incorrect, misplaced, unsupported, or ambiguous claims with exact references. Do not treat an earlier certificate as proof of correctness or rewrite valid text for style.
5. Repair demonstrable defects holistically, then use the genuinely isolated reviewer and machine-enumerated final audit required by schema 2.0. Preserve existing source hashes and certificate history; never claim automatic semantic correctness based on matching English strings.
6. Submit one scoped PR per daf under current CI, validator, independent review and quota constraints. Advance the new verification cursor only after evidence, successful merge and post-merge verification; make the cursor independent from the older earliest-uncertified queue. Store no private model transcripts.
7. When interpretation is uncertain, mark it BLOCKED with concise evidence. After the controller's permitted correction attempt, escalate and do not silently retry the same fingerprint. A blocked daf should not cause repetitive updates or endless model usage.

Before production, benchmark 2a, 7a/7b, 8a and other documented difficult boundary cases in shadow mode. A benchmark needs supported true positives, false positives, reviewer disagreement, corrected-field counts, token usage by provider, and cost per verified daf. No automatic mass recertification until the new evidence standard has been demonstrated.

## Token and provider optimization

- Implement mechanical fetch, source mapping, SHA/hash, cache lookup, JSON validation, scope verification, CI, scheduler checks and structured reporting as deterministic code; avoid paying a model for polling or known values.
- Build source packet once per daf from immutable cached inputs. Persist content-addressed hashes; do not resend the entire corpus or historical incident reports to every agent.
- Use two-phase review: source-only first, candidate comparison second. The independent reviewer receives the actual source but not the first review's reasoning. The final auditor receives the enumerated exact final record, never a summary in place of required fields.
- OpenClaw privately maps required CAPABILITY tiers to suitable Codex or Claude models and subagents, benchmarked by accepted work / cost rather than model brand. Never put live provider IDs, model routing secrets, credentials or quota readings in this public repo.
- Preserve configured 35% admission floor and 30% weekly reserve unless an explicit separate operator decision changes those values. Fail closed on missing quota evidence and stop if no permitted provider has capacity. Do not divert through a different provider to evade the reserve.
- For each unit log only nonsecret aggregate provider, model capability tier, input/output tokens, estimated cost, retries, cache hits, elapsed duration, errors found, and review outcomes. Define per-unit budget before admission, and cap nonproductive retries.
- Report only a meaningful state change, verified new deliverable, blocker requiring operator authority, or a requested digest. Deterministic heartbeat health checks should not invoke an LLM.

## New tractate contract

The pipeline is parameterized by `module`. Every module supplies the canonical source adapter `modules/<module>/scripts/build_learning_data.py:load_source_daf(daf)`, `assets/talmuddev/<daf>.json`, `assets/learning/<module>/<daf>.learning.json`, and normal module resolution/validation. The source-only packet intentionally fails if a module cannot satisfy the source contract. Existing Yoma source data is never rewritten by source-packet creation. Do not create other tractate directories until the user explicitly chooses the next tractate and scope.

## Source provenance and future paid use

Maintain version, attribution and rights metadata separately for each source layer. Use published text as corroboration without copying its protected wording into authored enrichment. Existing licensed content is preserved while its commercial usage requirements are tracked at release time; do not perform a destructive content migration without an explicit scoped decision. A source reference or license note is not evidence that a commentary's interpretation is necessarily correct.

## Public repository and disaster recovery

The repository is PUBLIC. Commit the runnable code, tests, sanitized policy templates, commands, instructions, release evidence and decisions. Do NOT commit .openclaw directories, auth files, tokens, chat transcripts, hostnames, network addresses, private service URLs, personal data, private agent soul/memory, runtime stops, quota snapshots, or real credentials. Keep encrypted private recovery data in user-controlled storage outside GitHub. A clean-clone recovery test must demonstrate that documented dependencies and templates can restore a new Rabbi agent once the operator supplies private secrets. See `docs/openclaw-rabbi-recovery.md`.

When a workflow changes, update this guide and `CLAUDE.md` / the governing module SOP in the same PR. Documentation must distinguish live implemented behavior from plans. GitHub PRs, not private assistant memory, are the lasting decisions.

## Rollout boundary

This PR adds a new deterministic source-only packet and documentation. It neither alters the source or learning content, nor changes previous certificates, quota policies, the operator safety hold, runtime scheduler, CI safety gates, or the existing semantic campaign queue. Enabling a revised autonomous campaign requires passing benchmark/canary reviews and a separate explicit authorization for safely retiring the operator stop.
