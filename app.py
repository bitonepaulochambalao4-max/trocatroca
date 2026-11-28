import os, sqlite3
from flask import Flask, request, redirect, session, g
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key = "trocatroca-123"
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
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{titulo}</title><style>*{{box-sizing:border-box}}body{{font-family:Arial,sans-serif;margin:0;background:#f2f2f2}} .header{{background:#00b140;color:#fff;text-align:center;padding:20px 12px}} .header h1{{margin:0;font-size:30px;font-weight:900}} .header p{{margin:8px 0 14px}} .btn-amarelo{{display:inline-block;background:#ffcc00;color:#000;font-weight:900;padding:12px 28px;border-radius:30px;text-decoration:none}} .nav{{background:#fff;display:flex;justify-content:space-around;padding:12px 5px;border-bottom:1px solid #ddd;position:sticky;top:0;z-index:10}} .nav a{{color:#111;text-decoration:none;font-weight:bold;font-size:14px}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:10px}} .card{{background:#fff;border-radius:12px;overflow:hidden;text-decoration:none;color:#111;display:block}} .card img{{width:100%;height:165px;object-fit:cover;display:block}} .card .p{{padding:10px}} .card .p b{{font-size:14px;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .card .p small{{color:#666;font-size:12px}} .preco{{color:#e60023;font-weight:bold;margin-top:4px}} .main-img{{width:100%;height:330px;object-fit:cover;border-radius:10px;display:block}} .thumbs{{display:flex;gap:8px;margin-top:10px}} .thumbs img{{width:60px;height:60px;object-fit:cover;border-radius:8px;border:2px solid #eee}} .thumbs img.active{{border-color:#00b140}} .btn{{background:#00b140;color:#fff;border:0;padding:12px;border-radius:8px;display:block;text-decoration:none;text-align:center;width:100%;font-weight:bold}} input,select,textarea{{width:100%;padding:11px;margin:6px 0;border:1px solid #ccc;border-radius:8px}} .wrap{{max-width:1000px;margin:auto}} .box{{background:#fff;padding:14px;border-radius:10px}} .links{{text-align:center;padding:20px}} .links a{{color:#4a00e0}}</style></head><body><div class="header"><h1>🔄 TROCA TROCA MOZ</h1><p>Troca sem dinheiro • Matola - Maputo</p><a class="btn-amarelo" href="/publicar">+ ADICIONAR TROCA</a></div><div class="nav"><a href="/">🏠 Início</a><a href="/publicar">+ Publicar</a><a href="/login">🔑 Entrar</a><a href="/register">✅ Criar Conta</a></div><div class="wrap">{html}</div><div class="links"><a href="/login">Entrar</a> | <a href="/register">Criar Conta</a> | <a href="/admin">Admin</a></div></body></html>"""
@app.route("/")
def index():
    con = db()
    prods = con.execute("SELECT * FROM produtos ORDER BY id DESC").fetchall()
    cards = ""
    for p in prods:
        fotos = (p["fotos"] or "").split(",")
        foto = fotos[0] if fotos and fotos[0] else ""
        img = f"/static/uploads/{foto}" if foto else "https://via.placeholder.com/300"
        cards += f'<a class="card" href="/produto/{p["id"]}"><img src="{img}"><div class="p"><b>{p["tenho"]}</b><small>Troco por: {p["quero"]}</small><div class="preco">{p["preco"] or ""} MT</div><small>{p["cidade"] or "Matola"}</small></div></a>'
    if not cards:
        cards = "<div style='padding:20px'><h2>Últimas Trocas</h2><p>Ainda não há trocas. Seja o primeiro!</p></div>"
    else:
        cards = f"<h2 style='padding:5px 10px'>Últimas Trocas</h2><div class='grid'>{cards}</div>"
    return BASE(cards)
@app.route("/produto/<int:pid>")
def produto(pid):
    con = db()
    p = con.execute("SELECT * FROM produtos WHERE id=?", (pid,)).fetchone()
    if not p: return redirect("/")
    fotos = [f for f in (p["fotos"] or "").split(",") if f]
    if not fotos: fotos = [""]
    main = f"/static/uploads/{fotos[0]}" if fotos[0] else "https://via.placeholder.com/400"
    thumbs = "".join([f'<img src="/static/uploads/{f}" onclick="trocar(this, \'/static/uploads/{f}\')" class="{"active" if i==0 else ""}">' for i,f in enumerate(fotos)])
    html = f"""<div class="box"><img id="mainImg" class="main-img" src="{main}"><div class="thumbs">{thumbs}</div><h2>{p["tenho"]}</h2><p><b>Quero:</b> {p["quero"]}</p><p>{p["desc"]}</p><h3 style="color:#e60023">{p["preco"] or ""} MT</h3><p>Local: {p["cidade"]}</p><a class="btn" href="https://wa.me/{p["whatsapp"]}">Falar no WhatsApp</a></div><script>function trocar(el,src){{document.getElementById('mainImg').src=src;document.querySelectorAll('.thumbs img').forEach(i=>i.classList.remove('active'));el.classList.add('active')}}</script>"""
    return BASE(html, p["tenho"])
@app.route("/publicar", methods=["GET","POST"])
def publicar():
    if "user_id" not in session: return redirect("/login")
    if request.method == "POST":
        fotos = []
        for f in request.files.getlist("fotos"):
            if f and f.filename:
                nome = secure_filename(f.filename)
                f.save(os.path.join(app.config["UPLOAD_FOLDER"], nome))
                fotos.append(nome)
        con = db()
        con.execute("INSERT INTO produtos(user_id,tenho,quero,desc,preco,whatsapp,fotos,cidade) VALUES(?,?,?,?,?,?,?,?)", (session["user_id"], request.form.get("tenho"), request.form.get("quero"), request.form.get("desc"), request.form.get("preco"), request.form.get("whatsapp"), ",".join(fotos), request.form.get("cidade")))
        con.commit()
        return redirect("/")
    html = """<h2>Publicar Troca</h2><div class="box"><form method="post" enctype="multipart/form-data"><input name="tenho" placeholder="O que tens?" required><input name="quero" placeholder="O que queres?" required><textarea name="desc" placeholder="Descreva..."></textarea><input name="preco" placeholder="Valor MT"><input name="whatsapp" placeholder="WhatsApp 258..."><input name="cidade" placeholder="Cidade"><label>Até 4 fotos:</label><input type="file" name="fotos" multiple accept="image/*"><button class="btn">Publicar</button></form></div>"""
    return BASE(html)
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        try:
            con = db()
            con.execute("INSERT INTO users(nome,email,senha) VALUES(?,?,?)", (request.form.get("nome"), request.form.get("email"), generate_password_hash(request.form.get("senha"))))
            con.commit()
        except: return BASE("<p>Email já existe</p>")
        return redirect("/login")
    return BASE("""<h2>Criar Conta</h2><div class="box"><form method="post"><input name="nome" placeholder="Teu Nome" required><input name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button class="btn">Criar Conta</button></form></div>""")
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        con = db()
        u = con.execute("SELECT * FROM users WHERE email=?", (request.form.get("email"),)).fetchone()
        if u and check_password_hash(u["senha"], request.form.get("senha")):
            session["user_id"] = u["id"]; session["nome"] = u["nome"]
            return redirect("/")
        return BASE("Senha errada")
    return BASE("""<h2>Entrar</h2><div class="box"><form method="post"><input name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button class="btn">Entrar</button></form></div>""")
@app.route("/logout")
def logout():
    session.clear(); return redirect("/")
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form.get("senha") == ADMIN_SENHA: session["admin"] = True; return redirect("/admin")
        return BASE("Senha errada")
    if not session.get("admin"):
        return BASE("<h2>Admin</h2><div class='box'><form method='post'><input type='password' name='senha' placeholder='Senha'><button class='btn'>Entrar</button></form></div>")
    con = db()
    users = con.execute("SELECT * FROM users").fetchall()
    prods = con.execute("SELECT * FROM produtos").fetchall()
    h = "<h2>Admin</h2>"
    for u in users: h += f"<p>{u['nome']} - {u['email']} <a href='/admin/del_user/{u['id']}'>Apagar</a></p>"
    for p in prods: h += f"<p>{p['tenho']} <a href='/admin/del_prod/{p['id']}'>Apagar</a></p>"
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
