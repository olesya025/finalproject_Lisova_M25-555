from valutatrade_hub.logging_config import setup_logging

def main():
    """Точка входа в приложение."""
    setup_logging()
    
    from valutatrade_hub.cli.interface import WalletCLI
    cli = WalletCLI()
    cli.run()

if __name__ == "__main__":
    main()