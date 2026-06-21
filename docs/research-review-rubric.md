# Research Review Rubric

Use this checklist when reviewing condition research pull requests. The goal is to decide whether a lead belongs in the public research corpus, not whether the app is clinically effective.

## Accept

A lead can be accepted when:

- The URL is public, reachable, and points to the named app, tool, directory, or repository.
- The source appears relevant to the condition and support category in the file path.
- The description is factual and avoids endorsement, diagnosis, treatment, or outcome claims.
- The record preserves useful provenance: source, query, date, and URL.
- The lead is not an obvious duplicate of an existing item for the same condition/category.

## Revise

Ask for revision when:

- The lead is relevant but the description is promotional, vague, or overclaims value.
- The source URL redirects to a broad landing page and a more specific public page exists.
- The condition/category fit is plausible but the file placement is weak.
- The provenance fields are incomplete but recoverable from the run record.
- The link checker reports a warning that a reviewer can manually verify.

## Reject

Reject or remove a lead when:

- The URL is hard-dead, private, local, paywalled beyond useful public inspection, or unrelated.
- The page does not identify the app, tool, directory, or repository clearly enough for review.
- The item is a medical claim, treatment recommendation, or clinical endorsement rather than a public-source lead.
- The source appears unsafe, spammy, deceptive, or unrelated to neurodivergence support.
- The item duplicates an existing accepted lead without adding useful new provenance.

## Reviewer Notes

- Link reachability proves only that the website is operational at review time.
- Keep transient warnings in the PR discussion unless they expose a hard-dead or blocked URL.
- Prefer preserving provenance over rewriting generated text into polished marketing copy.
- If a decision changes the data shape, hosting model, or public/private boundary, add or update an ADR.
