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
        build           Crawl the base URL and build the inverted index
        load            Load an existing index from disk
        print <word>    Show the inverted index entry for a given word
        find <query>    Search for pages matching all terms in the query
        help            Show this help message
        quit            Exit the program
    Flags:
        --top <n>       Show only top n results (print/find)
        --reverse       Reverses the sorting order (print/find)
    """
    print(help_text.strip())

def parse_flags(args, value_flags, bool_flags):
    """
    Separates positional args from flags.\n
    value flags take values, bool flags do not\n
    Returns (positional_args, flag_values)
    """
    positional = []
    flags = {}
    bool_flags = bool_flags or set()
    for f in bool_flags:
        flags[f] = False # default off

    i = 0
    while i < len(args):
        if args[i] in bool_flags:
            flags[args[i]] = True
            i += 1
        elif args[i] in value_flags:
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
                _, flags = parse_flags(args, {}, {})
                if flags is None: # error in parsing
                    continue

                print(f"Building index of {crawler.base_url}")
                pages_data = crawler.crawl()
                
                # create and save inverted index
                indexer.build_index(pages_data)
                print(f"Build complete. {len(pages_data)} pages indexed.")

            elif command == "load":
                if indexer.load():
                    print("Index loaded successfully")

            elif command == "print":
                positional, flags = parse_flags(args, {"--top"}, {"--reverse"})
                if flags is None:
                    continue
                if not positional:
                    print("Usage: print <word>")
                    continue
                if not indexer.index:
                    print("Error: Index not loaded. Please 'load' or 'build' first.")
                    continue
                
                word = positional[0].lower()
                if word in indexer.index:
                    entries = sorted(
                        [(indexer.id_to_url[int(uid)], len(pos)) for uid, pos in indexer.index[word].items()],
                        key=lambda x: x[1], 
                        reverse=not flags["--reverse"]
                    )[:flags.get("--top")]

                    print(f"Inverted index of {len(entries)} entries for '{word}':")

                    max_url_len = max(len(url) for url, _ in entries)
                    for url, count in entries:
                        print(f" - {url:<{max_url_len + 1}} Frequency: {count}")
                else:
                    print(f"Word '{word}' not found in index.")

            elif command == "find":
                positional, flags = parse_flags(args, {"--top"}, {"--reverse"})
                if flags is None:
                    continue
                if not positional:
                    print("Usage: find <word>")
                    continue
                if not indexer.index:
                    print("Error: Index not loaded. Please 'load' or 'build' first.")
                    continue

                searcher = SearchEngine(indexer.index, indexer.doc_lengths, indexer.id_to_url)
                results = searcher.find(positional)
                if flags["--reverse"]:
                    results.reverse()

                if results:
                    results = results[:flags.get("--top")]
                    print(f"Showing top {len(results)} results:")
                    max_url_len = max(len(url) for url, _ in results)
                    for url, score in results:
                        print(f" - {url:<{max_url_len + 1}}  Relevance: {score}")
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