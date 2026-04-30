import sys
from crawler import Crawler
from indexer import Indexer

def main():
    crawler = Crawler("https://quotes.toscrape.com/")
    indexer = Indexer()

    print("COMP3011 Coursework 2 - Web Crawler")
    print("Available commands: build, load, print <word>, find <query>, exit")

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
                # Requirements: print the inverted index for a particular word
                if word in indexer.index:
                    print(f"Inverted index for '{word}':")
                    for url, count in indexer.index[word].items():
                        print(f" - {url}: (frequency: {count})")
                else:
                    print(f"Word '{word}' not found in index.")

            elif command == "find":
                # Placeholder for the find logic (multi-word queries)[cite: 1]
                if not args:
                    print("Usage: find <query phrase>")
                    continue
                print(f"Searching for: {' '.join(args)}...")
                # We will implement the specific search logic in the next step
                
            elif command == "exit":
                print("Exiting search tool.")
                break

            else:
                print(f"Unknown command: {command}")

        except KeyboardInterrupt:
            print("\nUse 'exit' to quit.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()