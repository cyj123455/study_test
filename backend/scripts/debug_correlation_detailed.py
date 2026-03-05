import sys
import os
import traceback

# Ensure backend package is importable
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from app.database import SessionLocal
from app.services.analysis import get_price_series, get_weather_series, correlation_price_weather

product = '本地白菜'


def main():
    db = SessionLocal()
    try:
        print(f"=== Debug: product={product} ===")
        price_df = get_price_series(db, product)
        print("price_df type:", type(price_df))
        print("price_df empty:", price_df.empty)
        if not price_df.empty:
            print("price_df shape:", price_df.shape)
            print(price_df.head().to_string())
            print("price_df columns:", price_df.columns.tolist())
            # origin info
            if "origin" in price_df.columns:
                print("origin unique:", price_df["origin"].dropna().unique().tolist())
                print("origin isna all:", price_df["origin"].isna().all())
        else:
            print("price_df is empty - no price data for this product")

        # Try derive origin same as service
        origin = None
        if not price_df.empty and "origin" in price_df.columns:
            non_na = price_df["origin"].dropna()
            if len(non_na) > 0:
                origin = non_na.iloc[0]
        print("derived origin:", origin)

        if origin:
            weather_df = get_weather_series(db, origin)
            print("weather_df empty:", weather_df.empty)
            if not weather_df.empty:
                print("weather_df shape:", weather_df.shape)
                print(weather_df.head().to_string())
                print("weather_df columns:", weather_df.columns.tolist())
        else:
            print("No origin determined; skipping weather fetch")

        # Call correlation function
        print("\nCalling correlation_price_weather()...")
        corr_df = correlation_price_weather(db, product)
        print("corr type:", type(corr_df))
        print("corr empty:", corr_df.empty)
        if not corr_df.empty:
            print("corr shape:", corr_df.shape)
            print(corr_df.to_string())
        else:
            print("corr is empty")

    except Exception:
        traceback.print_exc()
    finally:
        try:
            db.close()
        except Exception:
            pass

if __name__ == '__main__':
    main()
