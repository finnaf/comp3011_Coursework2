import sys
from crawler import Crawler
from indexer import Indexer
from search import SearchEngine

def main():
    crawler = Crawler("https://quotes.toscrape.com/")
    indexer = Indexer()

    print("COMP3011 Coursework 2 - Web Crawler")
    print("Commands: build, load, print <word>, find <query>, quit")

    while True:
        try:
            user_input = input("> ").strip().split()
            if not user_input:
                continue
            
            command = user_input[0].lower()
            args = user_input[1:]

            if command == "build":
                print(f"Building index of {crawler.base_url}")
                pages_data = crawler.crawl()
                
                # create and save inverted index
                indexer.build_index(pages_data)
                print(f"Build complete. {len(pages_data)} pages indexed.")

            elif command == "load":
                # load index from file system
                success = indexer.load()
                if success:
                    print("Index loaded and ready for searching.")

            elif command == "print":
                if not args:
                    print("Usage: print <word>")
                    continue
                
                word = args[0].lower()

                # print inverted index for a given word
                if word in indexer.index:
                    print(f"Inverted index for '{word}':")
                    for url, count in indexer.index[word].items():
                        print(f" - {url}: (frequency: {count})")
                else:
                    print(f"Word '{word}' not found in index.")

            elif command == "find":
                if not args:
                    print("Usage: find <query phrase>")
                    continue
                
                if not indexer.index:
                    print("Error: Index not loaded. Please 'load' or 'build' first.")
                    continue

                searcher = SearchEngine(indexer.index)
                results = searcher.find(args)

                if results:
                    print(f"Found {len(results)} page(s) containing all terms:")
                    for url, score in results:
                        print(f" - {url} (Relevance Score: {score})")
                else:
                    print("No pages found for that query.")
                
            elif command == "quit" or command == "exit" or command == "q":
                print("Exiting search tool")
                break

            else:
                print(f"Unknown command: {command}")

        except KeyboardInterrupt:
            print("\nUse 'exit' to quit.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()