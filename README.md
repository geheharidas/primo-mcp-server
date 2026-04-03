# primo-mcp-server

MCP server for Ex Libris Primo library discovery -- search university catalogues and subscribed databases (ProQuest, Elsevier, Crossref, Gale, Springer, IEEE, etc.) via the Model Context Protocol.

## Features

- **Search** the full university catalogue and Primo Central Index (millions of records)
- **Get record details** including abstract, authors, identifiers, and availability
- **Autocomplete** search suggestions
- **Generate citations** in APA 7th, Harvard, Chicago, IEEE, and Vancouver styles
- **Export** to BibTeX, RIS, or CSV for import into reference managers

## Installation

```bash
git clone https://github.com/geheharidas/primo-mcp-server.git
cd primo-mcp-server
pip install -e .
```

## Register in Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "primo": {
      "command": "python",
      "args": ["-m", "primo_mcp_server"]
    }
  }
}
```

Restart Claude Code. The tools will appear as `mcp__primo__primo_search`, etc.

## Tools

| Tool | Description |
|------|-------------|
| `primo_search` | Search the library catalogue with filters (type, date, peer-reviewed) |
| `primo_get_record` | Get full details for a record by ID |
| `primo_suggest` | Autocomplete search suggestions |
| `primo_cite` | Generate formatted citations (APA7, Harvard, Chicago, IEEE, Vancouver) |
| `primo_export` | Export records as BibTeX, RIS, or CSV |

## Usage Examples

From a Claude Code conversation:

- "Search the library for articles about machine learning in entrepreneurship published after 2020"
- "Get the full details for record cdi_crossref_primary_10_1234"
- "Generate APA7 citations for these records"
- "Export the search results as BibTeX"

## Configuration

Defaults are set for UWA (University of Western Australia). Override via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PRIMO_BASE_URL` | `https://onesearch.library.uwa.edu.au/primaws/rest/pub` | Primo API base URL |
| `PRIMO_VID` | `61UWA_INST:NDE_UWA` | Primo View ID |
| `PRIMO_INSTITUTION_NAME` | `UWA` | Display name |
| `PRIMO_REQUEST_TIMEOUT` | `30.0` | HTTP timeout in seconds |
| `PRIMO_MAX_RESULTS_PER_REQUEST` | `50` | Maximum results per search |
| `PRIMO_DEFAULT_RESULTS` | `10` | Default results per search |

See `.env.example` for the full list.

## Running Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Licence

MIT
