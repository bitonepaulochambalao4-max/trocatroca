import os, sqlite3
from flask import Flask, request, redirect, session, g
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "trocatroca-secreto-123"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ADMIN_SENHA = "admin123"

def db():
    if "db" not in g:
        g.db = sqlite3.connect("troca.db")
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    d = g.pop("db", None)
    if d: d.close()

def init_db():
    con = sqlite3.connect("troca.db")
    con.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, email TEXT UNIQUE, senha TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS produtos(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, tenho TEXT, quero TEXT, desc TEXT, preco TEXT, whatsapp TEXT, fotos TEXT, cidade TEXT)")
    con.commit(); con.close()
init_db()

def BASE(html, titulo="Troca Troca Moz"):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{titulo}</title>
<style>
*{{box-sizing:border-box}} body{{font-family:Arial,sans-serif;margin:0;background:#f2f2f2;color:#111}}
/* TOPO VERDE IGUAL PRINT */
.header{{background:#00b140;color:#fff;text-align:center;padding:20px 12px 18px}}
.header h1{{margin:0;font-size:30px;font-weight:900;letter-spacing:-1px}}
.header p{{margin:8px 0 14px;opacity:.95}}
.btn-amarelo{{display:inline-block;background:#ffcc00;color:#000;font-weight:900;padding:12px 28px;border-radius:30px;text-decoration:none;font-size:16px}}
/* MENU BRANCO */
.nav{{background:#fff;display:flex;justify-content:space-around;padding:12px 5px;border-bottom:1px solid #ddd;position:sticky;top:0;z-index:10}}
.nav a{{color:#111;text-decoration:none;font-weight:bold;font-size:14px}}
/* GRID ALIEXPRESS - 2 POR LINHA */
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:10px}}
.card{{background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 5px rgba(0,0,0,.1);text-decoration:none;color:#111;display:block}}
.card img{{width:100%;height:165px;object-fit:cover;display:block}}
.card .p{{padding:10px}} .card .p b{{font-size:14px;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.card .p small{{color:#666;font-size:12px}} .preco{{color:#e
