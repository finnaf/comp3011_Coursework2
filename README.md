# COMP3011 Search Engine Tool

[![Tests](https://github.com/finnaf/comp3011_Coursework2/actions/workflows/tests.yml/badge.svg)](https://github.com/finnaf/comp3011_Coursework2/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)

A command-line search engine that crawls [quotes.toscrape.com](https://quotes.toscrape.com) in order to build an inverted index for querying.

The tool is split into three components.

### Crawler
Crawls the target website, respecting the `robots.txt` and a minimum 6-second politeness window between requests. URLs are normalised to a pattern consistent with [quotes.toscrape.com](https://quotes.toscrape.com), so for example, the main page and [quotes.toscrape.com/page/1/](https://quotes.toscrape.com/page/1/) are treated as the same location.

### Indexer
Builds an inverted index, storing each word's positions across all pages and total page sizes as a JSON. Uses a URL vocabulary which reduces file size by more than 10 times.

### Searcher
Can query the collected data using two commands, which sort matching patterns by relevance using TF-IDF and frequency. Flags support the visualisation of data output.

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

### Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP requests during crawling |
| `beautifulsoup4` | HTML parsing |

Install with:
```bash
pip install -r requirements.txt
```

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
This will take several minutes due to the 6-second politeness window between requests. Use Ctrl+C to safely exit early.

#### `load`
Loads a previously built index from disk.
```
> load
```

#### `print <word>`
Shows every page containing a word, ordered by frequency (most frequent first).
```
> print foo
> print bar --top 5
> print friends --ascending
```

#### `find <query>`
Finds all pages containing **all** terms in the query, ranked by TF-IDF relevance. Default behaviour prints in descending order.
```
> find foo
> find science great
> find good friends --top 10
> find good friends laugh together --ascending
```

### Flags

| Flag | Commands | Description |
|---|---|---|
| `--top <n>` | `print`, `find` | Limit output to top n results |
| `--ascending` | `print`, `find` | Sort results lowest-first |
| `--connected` | `find` | Searches for connected phrases |
| `--verbose` | `build` | Prints extra debug information |
| `--silent` | `build`, `load` | Silences output (other than errors) |

### Other Commands

| Command | Description |
|---|---|
| `help` | Show available commands |
| `quit` / `exit` / `q` | Exit the program |

## Project Structure

```
repository/
├── src/
│   ├── crawler.py
│   ├── indexer.py
│   ├── search.py
│   └── main.py
├── tests/
│   ├── test_crawler.py
│   ├── test_indexer.py
│   └── test_search.py
├── data/
│   └── index.json
├── requirements.txt
└── README.md
```

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