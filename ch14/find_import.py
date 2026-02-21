import findlib
def find_module(name):
    try:
        import importlib
        m = importlib.import_module(name)
        print(f"Found {name} at {m.__file__}")
    except Exception as e:
        print(f"Error importing {name}: {e}")

find_module("langchain.storage")
find_module("langchain_core.stores")
find_module("langchain_community.storage")
find_module("langchain_core.storage")
