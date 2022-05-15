import sqlite3
import websockets
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path


async def main():
    db = sqlite3.connect(f"{str(Path(__file__).parent / ('mango_level3_' + str(datetime.utcnow().date()) + '.db'))}")

    db.execute('pragma journal_mode=WAL')

    db.execute('pragma synchronous=normal')

    db.execute("""
        create table if not exists entries (
            content text,
            local_timestamp text
        )
    """)

    db.execute('create index if not exists entries_idx_0 on entries (local_timestamp)')

    db.execute("create index if not exists entries_idx_1 on entries (json_extract(json(content), '$.market'), json_extract(json(content), '$.timestamp'))")

    db.execute("create index if not exists entries_idx_2 on entries (json_extract(json(content), '$.market'), json_extract(json(content), '$.slot'))")

    async for connection in websockets.connect('ws://mangolorians.com:8010/v1/ws'):
        try:
            message = {
                'op': 'subscribe',
                'channel': 'level3',
                'markets': [
                    'BTC-PERP',
                    'SOL-PERP',
                    'MNGO-PERP',
                    'ADA-PERP',
                    'AVAX-PERP',
                    'BNB-PERP',
                    'ETH-PERP',
                    'FTT-PERP',
                    'LUNA-PERP',
                    'MNGO-PERP',
                    'RAY-PERP',
                    'SRM-PERP'
                ]
            }

            await connection.send(json.dumps(message))

            async for response in connection:
                content = json.loads(response)

                if content['type'] not in {'l3snapshot', 'open', 'fill', 'change', 'done'}:
                    continue

                db.execute(
                    'insert into entries values (?, ?)',
                    (json.dumps(content), datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'))
                )

                db.commit()
        except websockets.WebSocketException:
            continue

if __name__ == '__main__':
    asyncio.run(main())