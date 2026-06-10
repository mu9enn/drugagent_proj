# Contract Catalog

[`catalog.json`](catalog.json) is an inventory of contracts already present in
the repository. Producers continue to own their contracts. The catalog does
not create schemas that the implementation does not have.

Contract levels:

- `model`: an explicit code model exists.
- `validator`: executable validation exists.
- `doc-only`: only a documented or implementation-implied shape exists.

The catalog is intended to make producer/consumer relationships visible while
keeping current behavior unchanged.

For change procedures, compatibility expectations, and golden-sample guidance,
see [Contract Guide](contract-guide.md). The JSON catalog remains the unique
contract inventory.
