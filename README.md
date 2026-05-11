# COMP3011 Search Engine Tool

A command-line search engine that crawls [quotes.toscrape.com](https://quotes.toscrape.com), builds an inverted index, and lets you query it.

## How It Works

The tool is split into three components:

- **Crawler**: crawls the target website while respecting the `robots.txt` with a minimum 6-second politeness window
- **Indexer**: builds an inverted index storing each word's positions across all pages, saved as JSON
- **SearchEngine**: scores and ranks results using TF-IDF for relevance

---

## Installation

**Requirements:** Python 3.8+

1. Clone the repository:
    ```bash
    git clone https://github.com/finnaf/comp3011_Coursework2
    ```

2. (Recommended) Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate      # macOS/Linux
    venv\Scripts\activate         # Windows
    ```
---

### Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP requests during crawling |
| `beautifulsoup4` | HTML parsing |

Install with:
```bash
pip install -r requirements.txt
```

---

## Usage

Run `main.py` from any directory as a python file

```bash
python src/main.py
```

This opens an interactive shell:

```
COMP3011 Coursework 2 - Web Crawler
>
```

### Commands

#### `build`
Crawls the website, builds the inverted index, and saves it to `data/index.json`.
```
> build
```
This will take several minutes due to the 6-second politeness window between requests.

#### `load`
Loads a previously built index from disk, ready for querying.
```
> load
```

#### `print <word>`
Shows every page containing a word, ordered by frequency (most frequent first).
```
> print love
> print life --top 5
> print the --ascending
```

#### `find <query>`
Finds all pages containing **all** terms in the query, ranked by TF-IDF relevance.
```
> find truth
> find good friends
> find life love --top 10
> find books --ascending
```

### Flags

| Flag | Commands | Description |
|---|---|---|
| `--top <n>` | `print`, `find` | Limit output to top n results |
| `--ascending` | `print`, `find` | Sort results lowest-first |

### Other Commands

| Command | Description |
|---|---|
| `help` | Show available commands |
| `quit` / `exit` / `q` | Exit the program |

---

## Project Structure

```
repository/
├── src/
│   ├── crawler.py      # Web crawler with politeness and robots.txt support
│   ├── indexer.py      # Inverted index builder and persistence
│   ├── search.py       # TF-IDF search and ranking
│   └── main.py         # CLI shell
├── tests/
│   ├── test_crawler.py
│   ├── test_indexer.py
│   └── test_search.py
├── data/
│   └── index.json      # Generated index file (created by build)
├── requirements.txt
└── README.md
```

---

## Testing

Run the full test suite from the project root:

```bash
python -m pytest tests/
```

To see test coverage:

```bash
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=term-missing
```

Tests cover:
- Crawler URL normalisation, politeness timing, and robots.txt handling
- Indexer build, save, load, and word statistics
- Search engine intersection logic and TF-IDF ranking
- Edge cases: unknown words, empty queries, single-page results