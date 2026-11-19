# Split a bill: split_bill(total_cents, people)

## Goal

Add `trial.bill.split_bill(total_cents: int, people: int) -> list[int]`, which splits an amount in integer cents evenly between `people` people. The shares always add up to the total.

This is a sensitive area (money): integer cents only, never floats.

## Done when

1. **Even split:** `split_bill(1000, 4)` returns `[250, 250, 250, 250]`.
2. **Remainder:** cents that don't divide evenly go one each to the first people. `split_bill(1001, 3)` returns `[334, 334, 333]`. For every valid input, the shares add up to `total_cents` and differ by at most one cent.
3. **Zero:** `split_bill(0, 3)` returns `[0, 0, 0]`.
4. **Too few people:** `people < 1` raises `ValueError` with exactly `people must be at least 1`.
5. **Negative total:** `total_cents < 0` raises `ValueError` with exactly `total_cents must not be negative`.
6. **Not integers:** when `total_cents` or `people` isn't an `int` (including `float` and `bool`), it raises `TypeError` with exactly `amounts must be integers in cents`.

## Depends on

None.

## Scope

- `src/trial/bill.py`
- `tests/test_bill.py`
