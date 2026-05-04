import sys
from crawler import Crawler
from indexer import Indexer
from search import SearchEngine

def print_help():
    print("Commands: build, load, print <word>, find <query>, quit")

def print_help():
    help_text = """
    Usage: [command] [arguments]
    Commands:
        build                   Crawl the base URL and build the inverted index
        load                    Load an existing index from disk
        print <word>            Show the inverted index entry for a given word
        find <query>            Search for pages matching all terms in the query
        help                    Show this help message
        quit                    Exit the program
    Flags:
        find --top <n>      Show only top n results (default: None)
    """
    print(help_text.strip())

def parse_flags(args, valid_flags):
    """
    Separates positional args from flags.
    valid_flags: dict of flag_name & default_value, e.g. {"--top": 10}
    Returns (positional_args, flag_values)
    """
    positional = []
    flags = dict(valid_flags)

    i = 0
    while i < len(args):
        if args[i] in valid_flags:
            flag = args[i]
            if i + 1 >= len(args):
                print(f"Error: Flag '{flag}' requires a value.")
                return None, None
            try:
                flags[flag] = int(args[i + 1])
            except ValueError:
                print(f"Error: Flag '{flag}' expects an integer, got '{args[i + 1]}'.")
                return None, None
            i += 2
        else:
            # is a regular argument
            positional.append(args[i])
            i += 1

    return positional, flags

def main():
    crawler = Crawler("https://quotes.toscrape.com/")
    indexer = Indexer()

    print("COMP3011 Coursework 2 - Web Crawler")

    while True:
        try:
            user_input = input("> ").strip().split()
            if not user_input:
                continue
            
            command = user_input[0].lower()
            args = user_input[1:]

            if command == "build":
                _, flags = parse_flags(args, {"--depth", None}, {"--limit": None})
                if flags is None: # error in parsing
                    continue

                depth = flags["--depth"]
                limit = flags["--limit"]

                print(f"Building index of {crawler.base_url}")
                pages_data = crawler.crawl()
                
                # create and save inverted index
                indexer.build_index(pages_data)
                print(f"Build complete. {len(pages_data)} pages indexed.")

            elif command == "load":
                if indexer.load():
                    print("Index loaded and ready for searching.")

            elif command == "print":
                positional, flags = parse_flags(args, {})
                if flags is None:
                    continue
                if not positional:
                    print("Usage: print <word>")
                    continue
                if not indexer.index:
                    print("Error: Index not loaded. Please 'load' or 'build' first.")
                    continue
                
                word = positional[0].lower()

                # print inverted index for a given word
                if word in indexer.index:
                    print(f"Inverted index for '{word}':")
                    for url, count in indexer.index[word].items():
                        print(f" - {url}: (frequency: {count})")
                else:
                    print(f"Word '{word}' not found in index.")

            elif command == "find":
                positional, flags = parse_flags(args, {"--top": None})
                if flags is None:
                    continue
                if not positional:
                    print("Usage: find <word>")
                    continue
                if not indexer.index:
                    print("Error: Index not loaded. Please 'load' or 'build' first.")
                    continue

                searcher = SearchEngine(indexer.index, indexer.doc_lengths)
                results = searcher.find(positional)

                if results:
                    results = results[:flags["--top"]]
                    print(f"Showing top {len(results)} results:")
                    max_url_len = max(len(url) for url, _ in results)
                    for url, score in results:
                        print(f" - {url:<{max_url_len}}  Relevance: {score}")
                else:
                    print("No pages found for that query.")
                
            elif command == "quit" or command == "exit" or command == "q":
                print("Exiting search tool")
                break

            elif command == "help":
                print_help()

            else:
                print(f"Unknown command: {command}")
        
        except KeyboardInterrupt:
            break
        except EOFError:
            # input interrupted by ctrl+c
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()