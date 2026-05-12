from crawler import Crawler
from indexer import Indexer
from search import SearchEngine

def print_help() -> None:
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
        --ascending     Reverses the sorting order (print/find)
        --verbose       Shows wait times during crawl (build)
        --silent        Silences all output bar errors (build/load)
    """
    print(help_text.strip())

def parse_flags(
        args: list[str], 
        value_flags: set[str], 
        bool_flags: set[str]
    ) -> tuple[list[str] | None, dict[str, int | bool] | None]:
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

def calculate_verbosity_level(is_verbose: bool, is_silent: bool) -> int:
    '''Can have both flags. Silencing overrides.'''
    if is_silent:
        return 0
    elif is_verbose:
        return 2
    return 1

def main() -> None:
    crawler = Crawler("https://quotes.toscrape.com/")
    indexer = Indexer()
    searcher = SearchEngine()

    print("COMP3011 Coursework 2 - Web Crawler")

    while True:
        try:
            user_input = input("> ").strip().split()
            if not user_input:
                continue
            
            command = user_input[0].lower()
            args = user_input[1:]

            if command == "build":
                _, flags = parse_flags(args, {}, {"--verbose", "--silence"})
                if flags is None: # error in parsing
                    continue

                verbosity = calculate_verbosity_level(flags["--verbose"], flags["--silence"])
                pages_data = crawler.crawl(verbosity)
                
                # create and save inverted index
                indexer.build_index(pages_data)
                searcher.load(indexer.index, indexer.doc_lengths, indexer.urls)
                
                if verbosity > 0:
                    print(f"Build complete. {len(pages_data)} pages indexed.")

            elif command == "load":
                _, flags = parse_flags(args, {}, {"--silence"})
                if flags is None:
                    continue
                verbosity = calculate_verbosity_level(False, flags["--silence"])

                if indexer.load():
                    searcher.load(indexer.index, indexer.doc_lengths, indexer.urls)

                    if verbosity > 0:
                        print(f"Index loaded successfully, {len(indexer.index)} unique words over {len(indexer.urls)} webpages")

            elif command == "print":
                positional, flags = parse_flags(args, {"--top"}, {"--ascending"})
                if flags is None:
                    continue
                if not positional or len(positional) > 1:
                    print("Usage: print <word>")
                    continue
                if not indexer.index:
                    print("Error: Index not loaded. Please 'load' or 'build' first.")
                    continue
                
                word = positional[0].lower()
                results = indexer.get_word_stats(word, flags["--ascending"], flags.get("--top"))
                if results:
                    max_url_len = max(len(url) for url, _ in results)
                    for url, count in results:
                        print(f" - {url:<{max_url_len + 1}} Frequency: {count}")
                else:
                    print(f"Word '{word}' not found in index.")
                    

            elif command == "find":
                positional, flags = parse_flags(args, {"--top"}, {"--ascending", "--connected"})
                if flags is None:
                    continue
                if not positional:
                    print("Usage: find <phrase>")
                    continue
                if not indexer.index or not searcher.loaded:
                    print("Error: Index not loaded. Please 'load' or 'build' first.")
                    continue

                results = searcher.find(positional, flags["--connected"], flags["--ascending"])

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