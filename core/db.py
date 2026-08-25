import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "strategies.db"
HISTORY_DIR = Path(__file__).resolve().parent.parent / "artifact_history"

JMA_CROSS_DSL = '''strategy "JMA_7_50_Cross" {
    timeframe = "1d"

    close_sma60 = ta.sma(close, 60)
    jma_fast = ta.jma(close, 7, 50, 2)
    jma_slow = ta.jma(close, 50, 50, 4)

    long_entry = close >= close_sma60 and ta.crossover(jma_fast, jma_slow)
    long_exit = ta.crossunder(jma_fast, jma_slow)
    short_entry = false
    short_exit = false

    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''


def _resolve_db_path(db_path=None) -> Path:
    return Path(db_path) if db_path is not None else DB_PATH


def init_db(db_path=None):
    database_path = _resolve_db_path(db_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            dsl_code TEXT NOT NULL,
            source_code TEXT,
            source_type TEXT DEFAULT 'DSL',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        parent_id INTEGER, artifact_type TEXT NOT NULL DEFAULT 'strategy',
        sort_order INTEGER DEFAULT 0, UNIQUE(name, parent_id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS artifact_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, artifact_id INTEGER NOT NULL,
        version INTEGER NOT NULL, user_request TEXT, llm_response TEXT,
        dsl_code TEXT NOT NULL, validation_json TEXT, playbook_version TEXT,
        playbook_hash TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(artifact_id, version)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS validation_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, artifact_id INTEGER,
        artifact_type TEXT, user_request TEXT, llm_response TEXT,
        extracted_dsl TEXT, status TEXT NOT NULL, diagnostic_json TEXT,
        playbook_version TEXT, playbook_hash TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    existing_columns = {
        row[1] for row in cur.execute("PRAGMA table_info(strategies)").fetchall()
    }
    if "source_type" not in existing_columns:
        cur.execute("ALTER TABLE strategies ADD COLUMN source_type TEXT DEFAULT 'DSL'")
    if "source_code" not in existing_columns:
        cur.execute("ALTER TABLE strategies ADD COLUMN source_code TEXT")
        cur.execute("UPDATE strategies SET source_code = dsl_code WHERE source_code IS NULL")
    if "created_at" not in existing_columns:
        cur.execute("ALTER TABLE strategies ADD COLUMN created_at TIMESTAMP")
        cur.execute("UPDATE strategies SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    if "updated_at" not in existing_columns:
        cur.execute("ALTER TABLE strategies ADD COLUMN updated_at TIMESTAMP")
        cur.execute("UPDATE strategies SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
    for name, declaration in {
        "category_id": "INTEGER", "artifact_type": "TEXT DEFAULT 'strategy'",
        "user_request": "TEXT", "llm_response": "TEXT", "validation_status": "TEXT DEFAULT 'validated'",
        "playbook_version": "TEXT", "playbook_hash": "TEXT", "prompt_text": "TEXT"
    }.items():
        if name not in existing_columns:
            cur.execute(f"ALTER TABLE strategies ADD COLUMN {name} {declaration}")
    version_columns={row[1] for row in cur.execute("PRAGMA table_info(artifact_versions)").fetchall()}
    if "prompt_text" not in version_columns:cur.execute("ALTER TABLE artifact_versions ADD COLUMN prompt_text TEXT")
    event_columns={row[1] for row in cur.execute("PRAGMA table_info(validation_events)").fetchall()}
    if "prompt_text" not in event_columns:cur.execute("ALTER TABLE validation_events ADD COLUMN prompt_text TEXT")
    category_names = [("지표", "indicator", 10), ("신호", "signal", 20),
                      ("강세·약세", "strength", 30), ("전략", "strategy", 40),
                      ("사용자형식", "drawing", 50)]
    for category_name, artifact_type, order in category_names:
        rows = cur.execute("""SELECT id FROM categories
                            WHERE parent_id IS NULL AND artifact_type=? AND name=?
                            ORDER BY id""", (artifact_type, category_name)).fetchall()
        if rows:
            canonical = rows[0][0]
        else:
            cur.execute("INSERT INTO categories(name,parent_id,artifact_type,sort_order) VALUES (?,NULL,?,?)",
                        (category_name, artifact_type, order))
            canonical = cur.lastrowid
        for duplicate, in rows[1:]:
            cur.execute("UPDATE strategies SET category_id=? WHERE category_id=?", (canonical, duplicate))
            cur.execute("UPDATE categories SET parent_id=? WHERE parent_id=?", (canonical, duplicate))
            cur.execute("DELETE FROM categories WHERE id=?", (duplicate,))
        cur.execute("UPDATE categories SET sort_order=? WHERE id=?", (order, canonical))
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS categories_root_unique ON categories(name, COALESCE(parent_id,-1))")
    strategy_category = cur.execute("SELECT id FROM categories WHERE artifact_type='strategy' AND parent_id IS NULL ORDER BY id LIMIT 1").fetchone()[0]
    cur.execute("UPDATE strategies SET artifact_type=COALESCE(artifact_type,'strategy'), category_id=COALESCE(category_id,?)",
                (strategy_category,))

    cur.execute("SELECT COUNT(*) FROM strategies")
    if cur.fetchone()[0] == 0:
        sample_dsl = """strategy "Dual_SMA_RSI_Breakout" {\n    timeframe = "1d"\n    \n    ma_fast = ta.sma(close, 5)\n    ma_slow = ta.sma(close, 20)\n    rsi14   = ta.rsi(close, 14)\n    \n    entry_cond = ta.crossover(ma_fast, ma_slow) and (rsi14 < 70) and (close > close[1])\n    exit_cond  = ta.crossunder(ma_fast, ma_slow) or (rsi14 > 80)\n    \n    on(entry_cond) {\n        order.buy(type = "MARKET")\n    }\n    \n    on(exit_cond) {\n        order.close_position()\n    }\n}"""
        cur.execute(
            "INSERT INTO strategies (name, description, dsl_code, source_type) VALUES (?, ?, ?, ?)",
            ("Dual_SMA_RSI_Breakout", "5/20 이평 골든크로스 및 RSI 필터", sample_dsl, "DSL")
        )
    cur.execute(
        "INSERT OR IGNORE INTO strategies (name, description, dsl_code, source_type) VALUES (?, ?, ?, ?)",
        ("JMA_7_50_Cross", "종가≥SMA60 및 JMA(7,50,2)/JMA(50,50,4) 교차 전략", JMA_CROSS_DSL, "DSL")
    )
    cur.execute("UPDATE strategies SET artifact_type=COALESCE(artifact_type,'strategy'), category_id=COALESCE(category_id,?)",
                (strategy_category,))
    conn.commit()
    conn.close()


def get_all_strategies() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""SELECT id,name,description,dsl_code,source_type,updated_at,COALESCE(source_code,dsl_code),
                          category_id,COALESCE(artifact_type,'strategy'),user_request,llm_response,
                          COALESCE(validation_status,'validated'),playbook_version,playbook_hash,prompt_text
                   FROM strategies ORDER BY id DESC""")
    rows = cur.fetchall()
    conn.close()
    keys=("id","name","description","dsl_code","source_type","updated_at","source_code","category_id",
          "artifact_type","user_request","llm_response","validation_status","playbook_version","playbook_hash","prompt_text")
    return [dict(zip(keys,row)) for row in rows]


def insert_strategy(name: str, description: str, dsl_code: str, source_type: str, source_code: str = "") -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO strategies (name, description, dsl_code, source_type, source_code) VALUES (?, ?, ?, ?, ?)",
        (name, description, dsl_code, source_type, source_code or dsl_code)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_strategy(strat_id: int, name: str, description: str, dsl_code: str, source_type: str, source_code: str = ""):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE strategies SET name=?, description=?, dsl_code=?, source_type=?, source_code=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (name, description, dsl_code, source_type, source_code or dsl_code, strat_id)
    )
    conn.commit()
    conn.close()


def delete_strategy(strat_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM strategies WHERE id=?", (strat_id,))
    conn.commit()
    conn.close()


def get_categories(db_path=None):
    conn=sqlite3.connect(_resolve_db_path(db_path)); conn.row_factory=sqlite3.Row
    rows=conn.execute("SELECT id,name,parent_id,artifact_type,sort_order FROM categories ORDER BY sort_order,name").fetchall(); conn.close()
    return [dict(row) for row in rows]


def create_category(name: str, artifact_type: str, parent_id=None):
    conn=sqlite3.connect(DB_PATH); cur=conn.cursor()
    cur.execute("INSERT INTO categories(name,parent_id,artifact_type) VALUES (?,?,?)",(name,parent_id,artifact_type))
    conn.commit(); value=cur.lastrowid; conn.close(); return value


def update_category(category_id: int, name: str, artifact_type: str, parent_id=None):
    conn=sqlite3.connect(DB_PATH); conn.execute("UPDATE categories SET name=?,artifact_type=?,parent_id=? WHERE id=?",(name,artifact_type,parent_id,category_id)); conn.commit(); conn.close()


def delete_category(category_id: int):
    conn=sqlite3.connect(DB_PATH)
    children=conn.execute("SELECT COUNT(*) FROM categories WHERE parent_id=?",(category_id,)).fetchone()[0]
    artifacts=conn.execute("SELECT COUNT(*) FROM strategies WHERE category_id=?",(category_id,)).fetchone()[0]
    if children or artifacts: conn.close(); raise ValueError("하위 카테고리 또는 결과물이 있어 삭제할 수 없습니다.")
    conn.execute("DELETE FROM categories WHERE id=?",(category_id,)); conn.commit(); conn.close()


def commit_artifact(artifact_id: Optional[int], *, name: str, description: str, category_id: int,
                    artifact_type: str, source_type: str, source_code: str, dsl_code: str,
                    user_request: str, prompt_text: str, llm_response: str, validation_json: str,
                    playbook_version: str, playbook_hash: str) -> int:
    conn=sqlite3.connect(DB_PATH); cur=conn.cursor()
    if artifact_id:
        cur.execute("""UPDATE strategies SET name=?,description=?,category_id=?,artifact_type=?,source_type=?,
                    source_code=?,dsl_code=?,user_request=?,prompt_text=?,llm_response=?,validation_status='validated',
                    playbook_version=?,playbook_hash=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                    (name,description,category_id,artifact_type,source_type,source_code,dsl_code,user_request,
                     prompt_text,llm_response,playbook_version,playbook_hash,artifact_id))
    else:
        cur.execute("""INSERT INTO strategies(name,description,category_id,artifact_type,source_type,source_code,
                    dsl_code,user_request,prompt_text,llm_response,validation_status,playbook_version,playbook_hash)
                    VALUES (?,?,?,?,?,?,?,?,?,?,'validated',?,?)""",
                    (name,description,category_id,artifact_type,source_type,source_code,dsl_code,user_request,
                     prompt_text,llm_response,playbook_version,playbook_hash)); artifact_id=cur.lastrowid
    version=cur.execute("SELECT COALESCE(MAX(version),0)+1 FROM artifact_versions WHERE artifact_id=?",(artifact_id,)).fetchone()[0]
    cur.execute("""INSERT INTO artifact_versions(artifact_id,version,user_request,prompt_text,llm_response,dsl_code,
                validation_json,playbook_version,playbook_hash) VALUES (?,?,?,?,?,?,?,?,?)""",
                (artifact_id,version,user_request,prompt_text,llm_response,dsl_code,validation_json,playbook_version,playbook_hash))
    conn.commit(); conn.close()
    folder=HISTORY_DIR/str(artifact_id);folder.mkdir(parents=True,exist_ok=True)
    (folder/f"v{version:04d}.json").write_text(json.dumps({"artifact_id":artifact_id,"version":version,"name":name,
        "artifact_type":artifact_type,"source_type":source_type,"source_code":source_code,"user_request":user_request,
        "prompt_text":prompt_text,"llm_response":llm_response,"dsl_code":dsl_code,"validation":json.loads(validation_json or "{}"),
        "playbook_version":playbook_version,"playbook_hash":playbook_hash},ensure_ascii=False,indent=2),encoding="utf-8")
    return artifact_id


def get_artifact_versions(artifact_id: int):
    conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row
    rows=conn.execute("SELECT * FROM artifact_versions WHERE artifact_id=? ORDER BY version DESC",(artifact_id,)).fetchall(); conn.close()
    return [dict(row) for row in rows]


def record_validation(**values):
    conn=sqlite3.connect(DB_PATH); cur=conn.cursor()
    cur.execute("""INSERT INTO validation_events(artifact_id,artifact_type,user_request,prompt_text,llm_response,extracted_dsl,
                status,diagnostic_json,playbook_version,playbook_hash) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                tuple(values.get(key) for key in ("artifact_id","artifact_type","user_request","prompt_text","llm_response",
                      "extracted_dsl","status","diagnostic_json","playbook_version","playbook_hash")))
    conn.commit(); value=cur.lastrowid; conn.close()
    folder=HISTORY_DIR/(str(values.get("artifact_id")) if values.get("artifact_id") else "drafts")/"validations"
    folder.mkdir(parents=True,exist_ok=True)
    (folder/f"event-{value:06d}.json").write_text(json.dumps({"event_id":value,**values},ensure_ascii=False,indent=2),encoding="utf-8")
    return value
