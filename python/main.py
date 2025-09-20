import db_manager
import ui_main

def run():
    db_manager.create_tables()
    ui_main.main()

if __name__ == "__main__":
    run()