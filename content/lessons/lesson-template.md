---
type: Template
title: Lesson-learned template
description: Copy this file to write a new lesson learned — keep the five sections, keep it under a page.
tags: [lesson, template]
timestamp: 2026-07-01
---

# YYYY: One-line description of what went wrong

## What happened

Two or three sentences. Plain language. What was wrong, for how long, with what impact.

## How it was caught

Be honest — "by luck" and "by a validator, not by our controls" are common and useful answers.

## Root cause

Bullet the causes. Prefer *process* causes over *person* causes: "the check didn't exist" beats "X didn't check."

## What changed

Numbered list of concrete controls that now exist. Each one should link to where it lives (a user guide step, a monitoring metric, a policy line). A lesson with no changed control isn't finished.

## The transferable lesson

One paragraph: the general principle someone on a *different* model should take away.
