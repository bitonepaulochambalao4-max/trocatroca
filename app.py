import os
from flask import Flask, request, redirect, session, send_from_directory
import sqlite3

app = Flask(__name__)
app.secret_key = "troca123"
os.makedirs("static/uploads", exist_ok=True)
DB = "trocatroca.db"

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    c = db()
    c.execute("CREATE TABLE IF NOT EXISTS users (nome TEXT PRIMARY KEY, senha TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, tenho TEXT, quero TEXT, zona TEXT, nome TEXT, foto TEXT, whatsapp TEXT)")
    c.commit()
    c.close()
init()

@app.route("/")
def home():
    c = db()
    produtos = c.execute("SELECT * FROM produtos ORDER BY id DESC").fetchall()
    c.close()
    user = session.get("user", "")
    header = f"<div style='text-align:right;padding:10px'>Ola, {user} <a href='/logout'>Sair</a></div>" if user else "<div style='text-align:right;padding:10px'><a href='/login'>Entrar</a> | <a href='/register'>Criar Conta</a></div>"
    cards = ""
    for p in produtos:
        img = f"<img src='/{p['foto']}' style='width:100%;max-height:200px;object-fit:cover;border-radius:10px'>" if p['foto'] else ""
        cards += f"<div style='border:1px solid #ddd;padding:12px;border-radius:12px;margin:10px 0'>{img}<h3>{p['tenho']} ➡️ {p['quero']}</h3><p>📍 {p['zona']} | 👤 {p['nome']}</p><a href='https://wa.me/{p['whatsapp']}' style='background:#25D366;color:white;padding:10px;display:block;text-align:center;border-radius:8px;text-decoration:none'>Falar no WhatsApp</a></div>"
    if not produtos:
        cards = "<p style='text-align:center'>Nenhuma troca ainda. Seja a primeira!</p>"
    return f"<div style='font-family:sans-serif;padding:20px;max-width:480px;margin:auto;background:#f2f2f2;min-height:100vh'><h1 style='text-align:center;color:#e65100'>🔥 TROCA TROCA MOZ 🇲🇿</h1>{header}<a href='/publicar' style='display:block;background:#e65100;color:white;padding:14px;text-align:center;border-radius:10px;text-decoration:none;font-weight:bold'>+ Publicar Troca</a>{cards}<p style='text-align:center'><a href='/admin'>Painel Admin</a></p></div>"

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        try:
            c = db()
            c.execute("INSERT INTO users VALUES (?,?)", (request.form["nome"], request.form["senha"]))
            c.commit(); c.close()
        except: pass
        session["user"] = request.form["nome"]
        return redirect("/")
    return "<div style='font-family:sans-serif;padding:20px;max-width:480px;margin:auto'><h2>Criar Conta</h2><form method='POST'><input name='nome' placeholder='Teu nome' style='width:100%;padding:12px;margin:8px 0' required><input name='senha' type='password' placeholder='Senha' style='width:100%;padding:12px;margin:8px 0' required><button style='width:100%;padding:12px;background:#e65100;color:white;border:none;border-radius:8px'>Criar Conta</button></form></div>"

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        c = db()
        u = c.execute("SELECT * FROM users WHERE nome=? AND senha=?", (request.form["nome"], request.form["senha"])).fetchone()
        c.close()
        if u:
            session["user"] = request.form["nome"]
            return redirect("/")
        return "Senha errada! <a href='/login'>Voltar</a>"
    return "<div style='font-family:sans-serif;padding:20px;max-width:480px;margin:auto'><h2>Entrar</h2><form method='POST'><input name='nome' placeholder='Nome' style='width:100%;padding:12px;margin:8px 0' required><input name='senha' type='password' placeholder='Senha' style='width:100%;padding:12px;margin:8px 0' required><button style='width:100%;padding:12px;background:#e65100;color:white;border:none'>Entrar</button></form></div>"

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/publicar", methods=["GET","POST"])
def publicar():
    if "user" not in session: return redirect("/login")
    if request.method == "POST":
        filename = ""
        if "foto" in request.files:
            f = request.files["foto"]
            if f and f.filename:
                filename = "static/uploads/" + f.filename
                f.save(filename)
        c = db()
        c.execute("INSERT INTO produtos (tenho, quero, zona, nome, foto, whatsapp) VALUES (?,?,?,?,?,?)", (request.form["tenho"], request.form["quero"], request.form["zona"], session["user"], filename, request.form.get("whatsapp","")))
        c.commit(); c.close()
        return redirect("/")
    return "<div style='font-family:sans-serif;padding:20px;max-width:480px;margin:auto'><h2>Publicar com sucesso</h2><form method='POST' enctype='multipart/form-data'><input name='tenho' placeholder='O que tens? Ex: Sapato' style='width:100%;padding:12px;margin:8px 0' required><input name='quero' placeholder='O que queres? Ex: Pasta' style='width:100%;padding:12px;margin:8px 0' required><input name='zona' placeholder='Zona Ex: Matola' style='width:100%;padding:12px;margin:8px 0' required><input name='whatsapp' placeholder='WhatsApp Ex: 258840000000' style='width:100%;padding:12px;margin:8px 0' required><input type='file' name='foto' style='width:100%;padding:12px'><button style='width:100%;padding:12px;background:#e65100;color:white;border:none;border-radius:8px'>Publicar Troca</button></form></div>"

# ===== PAINEL ADMIN NOVO =====
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form.get("senha") == "Troca2026":
            session["admin"] = True
            return redirect("/admin")
        return "Senha errada! <a href='/admin'>Tentar de novo</a>"
    if not session.get("admin"):
        return "<div style='font-family:sans-serif;padding:20px;max-width:480px;margin:auto;text-align:center'><h1>🔐 PAINEL ADMIN</h1><form method='POST'><input name='senha' type='password' placeholder='Senha Admin' style='width:100%;padding:12px;margin:10px 0'><button style='width:100%;padding:12px;background:#e65100;color:white;border:none;border-radius:8px'>ENTRAR</button></form></div>"
    c = db()
    produtos = c.execute("SELECT * FROM produtos ORDER BY id DESC").fetchall()
    total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    c.close()
    rows = ""
    for p in produtos:
        img = f"<img src='/{p['foto']}' style='width:70px;height:70px;object-fit:cover;border-radius:8px'>" if p['foto'] else ""
        rows += f"<div style='display:flex;gap:10px;border:1px solid #ddd;padding:10px;border-radius:10px;margin:8px 0;align-items:center'>{img}<div style='flex:1'><b>{p['tenho']} ➡️ {p['quero']}</b><br>👤 {p['nome']} | 📍 {p['zona']}<br>📱 {p['whatsapp']}</div><a href='/admin/apagar/{p['id']}' onclick=\"return confirm('Apagar?')\" style='background:red;color:white;padding:8px 12px;border-radius:8px;text-decoration:none'>Apagar</a></div>"
    if not produtos: rows = "<p>Nenhuma troca ainda.</p>"
    return f"<div style='font-family:sans-serif;padding:15px;max-width:600px;margin:auto'><h1 style='text-align:center'>📊 Painel Admin</h1><div style='display:flex;gap:10px;text-align:center'><div style='flex:1;background:#fff3e0;padding:15px;border-radius:10px'><b>{len(produtos)}</b><br>Trocas</div><div style='flex:1;background:#e3f2fd;padding:15px;border-radius:10px'><b>{total_users}</b><br>Utilizadores</div></div><h3>Todas as Trocas:</h3>{rows}<a href='/' style='display:block;text-align:center;margin-top:15px'>Voltar ao site</a> | <a href='/admin/sair'>Sair do Painel</a></div>"

@app.route("/admin/apagar/<int:id>")
def admin_apagar(id):
    if not session.get("admin"): return redirect("/admin")
    c = db()
    c.execute("DELETE FROM produtos WHERE id=?", (id,))
    c.commit(); c.close()
    return redirect("/admin")

@app.route("/admin/sair")
def admin_sair():
    session.pop("admin", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
