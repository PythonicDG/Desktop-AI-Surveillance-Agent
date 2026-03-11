from utils.config_loader import load_config

def main():
    config = load_config()
    print(f"Starting {config.get('app', {}).get('name', 'AI Agent')}...")

if __name__ == "__main__":
    main()
