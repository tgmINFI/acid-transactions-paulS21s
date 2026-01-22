import sqlite3

class ShipmentProcessor:
    def __init__(self, db_path):
        self.db_path = db_path

    def process_shipment(self, item_name, quantity, log_callback):
        """
        Executes the shipment logic atomically.
        :param item_name: Name of the item
        :param quantity: Amount to move
        :param log_callback: A function to print to the GUI console
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        log_callback(f"--- STARTING TRANSACTION: Move {quantity} of {item_name} ---")

        # Start a transaction explicitly
        conn.execute("BEGIN")

        try:
            # STEP 1: Check current stock
            cursor.execute(
                "SELECT stock_qty FROM inventory WHERE item_name = ?",
                (item_name,)
            )
            result = cursor.fetchone()
            if result is None:
                raise ValueError(f"Item '{item_name}' does not exist.")
            current_stock = result[0]

            if current_stock < quantity:
                raise ValueError(
                    f"Insufficient stock for '{item_name}'. Available: {current_stock}, requested: {quantity}"
                )

            # STEP 2: Deduct inventory
            cursor.execute(
                "UPDATE inventory SET stock_qty = stock_qty - ? WHERE item_name = ?",
                (quantity, item_name)
            )
            log_callback(">> STEP 1 SUCCESS: Inventory Deducted.")

            # STEP 3: Log the shipment
            cursor.execute(
                "INSERT INTO shipment_log (item_name, qty_moved) VALUES (?, ?)",
                (item_name, quantity)
            )
            log_callback(">> STEP 2 SUCCESS: Shipment Logged.")

            # Commit transaction
            conn.commit()
            log_callback("--- TRANSACTION COMMITTED ---")

        except Exception as e:
            # Rollback on any error
            conn.rollback()
            log_callback(f">> TRANSACTION FAILED: {e} - No changes were made.")

        finally:
            conn.close()