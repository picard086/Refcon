# __main__.py
import economy

def main():
    print("[econ] Starting Refuge Economy Bot...")

    # If economy.py already has a main() function, call it
    if hasattr(economy, "main"):
        economy.main()
    else:
        raise RuntimeError("economy.py has no main() function. Please define one.")

if __name__ == "__main__":
    main()

