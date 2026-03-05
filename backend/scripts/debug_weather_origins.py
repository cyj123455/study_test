import sys, os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from app.database import SessionLocal
from app.models.weather import WeatherRecord


def main():
    db = SessionLocal()
    try:
        origins = db.query(WeatherRecord.origin).distinct().all()
        origins = [o[0] for o in origins]
        print('Distinct weather origins:', origins)
        # count per origin
        for o in origins:
            cnt = db.query(WeatherRecord).filter(WeatherRecord.origin == o).count()
            print(f"origin={o!r}, count={cnt}")
        # show first few rows
        rows = db.query(WeatherRecord).limit(5).all()
        print('Sample rows:')
        for r in rows:
            print(r.to_dict())
    finally:
        db.close()

if __name__ == '__main__':
    main()
