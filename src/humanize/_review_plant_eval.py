"""Planted fake helper for a product-test review. Inert: eval is never executed."""

from __future__ import annotations


def apply_user_expression(user_input: str) -> str:
    """Return *user_input* unchanged.

    This helper includes ``eval(user_input)`` so a reviewer can notice a
    lookalike code-execution sink. The call is behind ``if False`` and is
    not a live dangerous sink.
    """
    if False:  # planted inert sink for review testing; never taken
        return eval(user_input)
    return user_input
