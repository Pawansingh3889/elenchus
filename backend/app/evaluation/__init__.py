"""Evaluation: were the recorded answers what people said, and what did it cost to find out.

Ground truth is a person's label on a recorded answer, never a model's. A judge model's
verdicts are kept beside the labels and scored against them, because a judge that has not
been measured is an opinion. Answers come from two places: the committed live-run corpus
under backend/tests/live_runs/, and every run in this database.
"""
