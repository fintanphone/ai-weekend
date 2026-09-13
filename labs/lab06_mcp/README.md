# Lab 6 — MCP

**75 minutes · pairs**

## Goal

Understand why tools became a protocol, then write a server.

## The idea

In Lab 3 you wrote tools *into* your agent. They worked only inside that script.
If you wanted the same three tools in a different app, you'd copy the code.

MCP inverts that. A server exposes capabilities; any client can consume them.
Write once, use from Claude Code, Claude Desktop, your own agent, or someone
else's.

> **Friend 2 will recognise this immediately** as service discovery and a
> capability registry for models, which is exactly what it is. Let him make the
> comparison out loud — the analogy is genuinely correct and it will help
> Friend 1 more than the spec docs will.

Three primitives, of which one matters most:

| Primitive | What it is |
|---|---|
| **Tools** | Functions the model can call. This is 90% of what people use |
| **Resources** | Data the client can read into context |
| **Prompts** | Reusable templates the user can invoke |

## Part 1 — Use a server (25 min)

The filesystem server is the easiest thing to see working.

```bash
claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem ~/Documents
claude mcp list
```

Then start Claude Code and ask it something about those files:

```bash
claude
> What are the largest files in that directory, and when were they last modified?
```

Watch which tools it calls. Notice you didn't write any of them, and notice the
client asks your permission before running them. **That permission prompt is the
main security boundary in practice** — discuss whether that's sufficient.

Browse what else exists: <https://github.com/modelcontextprotocol/servers>

## Part 2 — Write a server (50 min)

### 1. Seed the database

```bash
python seed_db.py
```

Ten shipments, ten inventory lines, in SQLite.

### 2. Read `freight_server.py`

Sixty lines. The whole thing is:

```python
mcp = FastMCP("aurora-freight")

@mcp.tool()
def list_shipments(status: str = "all", limit: int = 20) -> str:
    """List shipments, optionally filtered by status. ..."""
```

The decorator turns the function signature into a JSON Schema and the docstring
into the tool description. **This is Lab 2 and Lab 3 wearing a protocol.** Same
contract, standard transport.

Now find the comment near the bottom about what's deliberately *not* there.
There is no `run_sql` tool taking arbitrary SQL. That would be far more flexible
and a genuinely bad idea. Spend five minutes on why — it's the most important
design conversation in this lab.

### 3. Register it

```bash
claude mcp add freight -- python /absolute/path/to/labs/lab06_mcp/freight_server.py
claude mcp list
```

Use the absolute path, and if you're in a virtualenv use the venv's Python
explicitly: `/absolute/path/.venv/bin/python`.

### 4. Use it

```bash
claude
> Which shipments are delayed, and is there a pattern in why?
> What's the total stock value in Cork?
> We need 100 units of anything strapping-related. Can we fulfil that from stock?
```

That last question requires searching, checking quantities across warehouses,
and reasoning about the result. Three tool calls the model sequenced itself.

### 5. Extend it

Twenty minutes. Add one tool each:

- `carrier_performance()` — average transit days and delay rate per carrier
- `low_stock(threshold)` — items below a reorder point
- `warehouse_summary()` — line count and total value per warehouse

Restart the client to pick up changes. Then check the docstring is doing its
job: does the model call your tool when it should?

**Then try the important experiment.** Write a tool with a deliberately vague
docstring — `"""Gets data."""` — and watch the model fail to use it correctly.
The docstring is not documentation. It's the interface.

## Expected output

Claude Code discovers your tools, asks permission, calls them, and chains them.
The moment it answers a business question by combining two of your tools
unprompted is the one worth pausing on.

## Discussion (10 min)

1. Why not just give it `run_sql`? (Because the model would then have the
   database's full authority, including `DROP TABLE`. Narrow tools are a
   permissioning mechanism, not a convenience.)
2. What happens if an MCP server returns text containing instructions? Who is
   trusting whom? (Lab 3's injection experiment, at protocol scale.)
3. Friend 2: how would you run this for a company — auth, secrets, audit,
   multi-tenancy, rate limits? Almost none of that is solved in the ecosystem
   yet. **That gap is a portfolio project**; see `PORTFOLIO.md`.
4. What in your own work could be an MCP server? Write it down; it's a candidate
   for tomorrow's scoping session.

## If it breaks

**Server won't start** — run `python freight_server.py` directly. It should hang
silently waiting on stdio; that means it's fine. An import error means it isn't.

**Client can't see the tools** — almost always the Python path. Use the
virtualenv's absolute Python path in `claude mcp add`. Check `claude mcp list`.

**`freight.db missing`** — run `python seed_db.py`.

**Changes not picked up** — restart the client. Tool schemas are read at connect
time.

## Takeaway

> A tool is a contract. MCP is that contract with a standard transport, so it
> stops belonging to one application.
