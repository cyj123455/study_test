import sys
import os
import traceback

# Ensure backend package is importable
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from app.database import SessionLocal
from app.services.analysis import correlation_price_weather

product = '本地白菜'

def main():
    db = SessionLocal()
    try:
        print(f"Calling correlation_price_weather for product: {product}")
        df = correlation_price_weather(db, product)
        print("Type:", type(df))
        try:
            print("Empty:", df.empty)
            print("Columns:", df.columns.tolist())
            print("Shape:", df.shape)
            # print full DataFrame
            if not df.empty:
                print(df.to_string())
                # Also print JSON-serializable matrix and columns as backend returns
                matrix = df.values.tolist()
                columns = df.columns.tolist()
                print("\n--- Returned JSON shape ---")
                print({"matrix_len": len(matrix), "columns": columns})
                # Print a small sample of matrix
                for i, row in enumerate(matrix):
                    print(i, row)
            else:
                print("DataFrame is empty (no correlation data)")
        except Exception:
            traceback.print_exc()
    except Exception:
        print("Exception while calling service:")
        traceback.print_exc()
    finally:
        try:
            db.close()
        except Exception:
            pass

if __name__ == '__main__':
    main()
