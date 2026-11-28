import os, sqlite3, secrets
from flask import Flask, request, redirect, url_for, session, g
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
    user = session.get("nome", "")
    topo = f'<a href="/">TROCA TROCA MOZ</a><div><a href="/publicar" style="background:#fff;color:#ff3b30;padding:6px 10px;border-radius:20px">+ ADICIONAR TROCA</a> &nbsp; <a href="/login">{user if user else "Entrar"}</a></div>' if user else f'<a href="/">TROCA TROCA MOZ</a><div><a href="/login">Criar Conta</a> &nbsp; <a href="/login">Entrar</a></div>'
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{titulo}</title>
<style>
body{{font-family:Arial,sans-serif;margin:0;background:#f4f4f4;color:#111}}
.top{{background:#ff3b30;color:#fff;padding:14px 16px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10}}
.top a{{color:#fff;text-decoration:none;font-weight:bold}}
.btn{{background:#ff3b30;color:#fff;border:0;padding:12px 14px;border-radius:8px;display:inline-block;text-decoration:none;text-align:center;width:100%;box-sizing:border-box;font-weight:bold}}
/* ESTILO ALIEXPRESS - 2 POR LINHA */
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:10px}}
.card{{background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 5px rgba(0,0,0,.1);text-decoration:none;color:#111;display:block}}
.card img{{width:100%;height:170px;object-fit:cover;display:block}}
.card .p{{padding:10px}}
.card .p b{{font-size:14px;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.card .p small{{color:#666;font-size:12px}}
.card .preco{{color:#ff3b30;font-weight:bold;font-size:15px;margin-top:4px}}
/* GALERIA PAGINA PRODUTO - ALIEXPRESS */
.main-img{{width:100%;height:330px;object-fit:cover;border-radius:10px;display:block}}
.thumbs{{display:flex;gap:8px;margin-top:10px}}
.thumbs img{{width:60px;height:60px;object-fit:cover;border-radius:8px;border:2px solid #eee;cursor:pointer}}
.thumbs img.active{{border-color:#ff3b30}}
input,select,textarea{{width:100%;padding:11px;margin:6px 0;border:1px solid #ccc;border-radius:8px;box-sizing:border-box}}
.wrap{{max-width:1000px;margin:auto;padding:12px}}
.box{{background:#fff;padding:14px;border-radius:10px}}
</style></head><body><div class="top">{topo}</div><div class="wrap">{html}</div></body></html>"""

@app.route("/")
def index():
    con = db()
    prods = con.execute("SELECT * FROM produtos ORDER BY id DESC").fetchall()
    cards = ""
    for p in prods:
        fotos = (p["fotos"] or "").split(",")
        foto = fotos[0] if fotos and fotos[0] else ""
        img = f"/static/uploads/{foto}" if foto else "https://via.placeholder.com/300"
        cards += f'<a class="card" href="/produto/{p["id"]}"><img src="{img}"><div class="p"><b>{p["tenho"]}</b><small>Troco por: {p["quero"]}</small><div class="preco">{p["preco"] or ""} MT</div><small>{p["cidade"] or "Matola - Maputo"}</small></div></a>'
    if not cards:
        cards = "<div class='box'><h3>Nenhuma troca ainda</h3><p>Seja o primeiro a publicar! Clique em + ADICIONAR TROCA</p></div>"
    html = f"<h2 style='padding:0 10px'>Trocas Recentes - Matola / Maputo</h2><div class='grid'>{cards}</div>"
    return BASE(html)

@app.route("/produto/<int:pid>")
def produto(pid):
    con = db()
    p = con.execute("SELECT * FROM produtos WHERE id=?", (pid,)).fetchone()
    if not p: return redirect("/")
    fotos = [f for f in (p["fotos"] or "").split(",") if f]
    if not fotos: fotos = [""]
    main = f"/static/uploads/{fotos[0]}" if fotos[0] else "https://via.placeholder.com/400"
    thumbs = "".join([f'<img src="/static/uploads/{f}" onclick="trocar(this, \'/static/uploads/{f}\')" class="{"active" if i==0 else ""}">' for i,f in enumerate(fotos)])
    html = f"""<div class="box"><img id="mainImg" class="main-img" src="{main}"><div class="thumbs">{thumbs}</div>
    <h2>{p["tenho"]}</h2><p><b>Quero:</b> {p["quero"]}</p><p>{p["desc"]}</p><h3 style="color:#ff3b30">{p["preco"] or ""} MT</h3><p>Local: {p["cidade"]}</p>
    <a class="btn" href="https://wa.me/{p["whatsapp"]}" target="_blank">Falar no WhatsApp</a></div>
    <script>function trocar(el,src){{document.getElementById('mainImg').src=src;document.querySelectorAll('.thumbs img').forEach(i=>i.classList.remove('active'));el.classList.add('active')}}</script>"""
    return BASE(html, p["tenho"])

@app.route("/publicar", methods=["GET","POST"])
def publicar():
    if "user_id" not in session: return redirect("/login")
    if request.method == "POST":
        fotos = []
        for f in request.files.getlist("fotos"):
            if f and f.filename:
                nome = secure_filename(f.filename)
                caminho = os.path.join(app.config["UPLOAD_FOLDER"], nome)
                f.save(caminho)
                fotos.append(nome)
        con = db()
        con.execute("INSERT INTO produtos(user_id,tenho,quero,desc,preco,whatsapp,fotos,cidade) VALUES(?,?,?,?,?,?,?,?)", (session["user_id"], request.form.get("tenho"), request.form.get("quero"), request.form.get("desc"), request.form.get("preco"), request.form.get("whatsapp"), ",".join(fotos), request.form.get("cidade")))
        con.commit()
        return redirect("/")
    html = """<h2>Publicar Troca</h2><div class="box"><form method="post" enctype="multipart/form-data">
    <input name="tenho" placeholder="O que tens? Ex: Microfone Bluetooth" required>
    <input name="quero" placeholder="O que queres em troca?" required>
    <textarea name="desc" placeholder="Descreva: estado, cores, tamanho..."></textarea>
    <input name="preco" placeholder="Valor em MT Ex: 500">
    <input name="whatsapp" placeholder="WhatsApp Ex: 258840000000">
    <input name="cidade" placeholder="Cidade Ex: Matola">
    <label>Escolha até 4 fotos:</label><input type="file" name="fotos" multiple accept="image/*">
    <button class="btn">Publicar</button></form></div>"""
    return BASE(html)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        try:
            con = db()
            con.execute("INSERT INTO users(nome,email,senha) VALUES(?,?,?)", (request.form.get("nome"), request.form.get("email"), generate_password_hash(request.form.get("senha"))))
            con.commit()
        except: return BASE("<p>Email já existe</p><a href='/register'>Tentar de novo</a>")
        return redirect("/login")
    html = """<h2>Criar Conta</h2><div class="box"><form method="post"><input name="nome" placeholder="Teu Nome" required><input name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button class="btn">Criar Conta</button></form><p><a href="/login">Já tens conta? Entrar</a></p></div>"""
    return BASE(html)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        con = db()
        u = con.execute("SELECT * FROM users WHERE email=?", (request.form.get("email"),)).fetchone()
        if u and check_password_hash(u["senha"], request.form.get("senha")):
            session["user_id"] = u["id"]; session["nome"] = u["nome"]
            return redirect("/")
        return BASE("Senha errada <a href='/login'>Tentar de novo</a>")
    html = """<h2>Entrar</h2><div class="box"><form method="post"><input name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button class="btn">Entrar</button></form><p><a href="/register">Criar conta nova</a></p></div>"""
    return BASE(html)

@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form.get("senha") == ADMIN_SENHA: session["admin"] = True; return redirect("/admin")
        return BASE("Senha errada")
    if not session.get("admin"):
        return BASE("<h2>Admin</h2><form method='post'><input type='password' name='senha' placeholder='Senha'><button class='btn'>Entrar</button></form>")
    con = db()
    users = con.execute("SELECT * FROM users").fetchall()
    prods = con.execute("SELECT * FROM produtos").fetchall()
    h = "<h2>Admin</h2><h3>Users</h3>"
    for u in users: h += f"<p>{u['nome']} - {u['email']} <a href='/admin/del_user/{u['id']}'>Apagar</a></p>"
    h += "<h3>Produtos</h3>"
    for p in prods: h += f"<p>{p['tenho']} | {p['quero']} <a href='/admin/del_prod/{p['id']}'>Apagar</a></p>"
    return BASE(h)

@app.route("/admin/del_user/<int:uid>")
def del_user(uid):
    if not session.get("admin"): return redirect("/admin")
    con = db(); con.execute("DELETE FROM users WHERE id=?", (uid,)); con.commit(); return redirect("/admin")

@app.route("/admin/del_prod/<int:pid>")
def del_prod(pid):
    if not session.get("admin"): return redirect("/admin")
    con = db(); con.execute("DELETE FROM produtos WHERE id=?", (pid,)); con.commit(); return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)
