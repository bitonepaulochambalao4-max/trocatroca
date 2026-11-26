import os, sqlite3
from flask import Flask, render_template_string, request, redirect, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "troca-troca-moz-2026"
ADMIN_SENHA = "1234"
UPLOAD = "static/uploads"
os.makedirs(UPLOAD, exist_ok=True)

def db():
    c = sqlite3.connect("troca.db")
    c.row_factory = sqlite3.Row
    return c

def init():
    con = db()
    con.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, email TEXT UNIQUE, senha TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS produtos(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, tenho TEXT, quero TEXT, desc TEXT, preco TEXT, whatsapp TEXT, fotos TEXT, cidade TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS likes(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, produto_id INTEGER, UNIQUE(user_id, produto_id))")
    con.commit(); con.close()
init()

BASE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial;background:#f0f2f5}
.header{background:#00a651;color:white;text-align:center;padding:16px 10px 14px}
.header h1{margin:0;font-size:22px}
.header p{margin:4px 0 10px;font-size:13px;opacity:0.9}
.btn-add{background:#ffcc00;color:#000;padding:11px 24px;border-radius:25px;font-weight:bold;display:inline-block;text-decoration:none;font-size:15px}
.nav{display:flex;justify-content:space-around;background:white;padding:11px 0;border-bottom:1px solid #ddd;position:sticky;top:0}
.nav a{color:#333;text-decoration:none;font-size:13px;font-weight:bold}
.nav span{color:#00a651}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:10px}
.card{background:white;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.1)}
.card img{width:100%;aspect-ratio:1/1;object-fit:cover;display:block;background:#eee}
.info{padding:9px}
.info small{color:#777;font-size:11px}
.info b{font-size:13px;line-height:1.3;display:block;margin:3px 0}
.like{width:100%;padding:8px;border:1px solid #eee;background:#fafafa;border-radius:8px;margin-top:6px;cursor:pointer}
.like.liked{background:#ffeef2}
.wpp{background:#00c853;color:white;text-align:center;padding:9px;border-radius:8px;display:block;text-decoration:none;margin-top:6px;font-size:13px;font-weight:bold}
input,textarea{width:100%;padding:12px;margin:7px 0;border:1px solid #ddd;border-radius:10px;font-size:14px}
.pub{background:#00a651;color:white;border:none;padding:13px;border-radius:10px;width:100%;font-weight:bold;font-size:15px}
.box{background:white;padding:16px;margin:10px;border-radius:12px}
.galeria img{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:12px;margin-bottom:8px}
</style></head><body>
<div class="header"><h1>🔄 TROCA TROCA MOZ</h1><p>Troca sem dinheiro • Matola - Maputo</p><a class="btn-add" href="/publicar">➕ ADICIONAR TROCA</a></div>
<div class="nav"><a href="/">🏠 Início</a><a href="/publicar">➕ Publicar</a><a href="/login">🔑 Entrar</a><a href="/register">✅ Criar Conta</a></div>
{CONTEUDO}
</body></html>
"""

@app.route("/")
def home():
    con=db()
    prods=con.execute("SELECT p.*, (SELECT COUNT(*) FROM likes WHERE produto_id=p.id) as total FROM produtos p ORDER BY p.id DESC").fetchall()
    liked=set()
    if "user_id" in session:
        liked={r["produto_id"] for r in con.execute("SELECT produto_id FROM likes WHERE user_id=?", (session["user_id"],))}
    con.close()
    cards=""
    for p in prods:
        fotos=(p["fotos"] or "").split(",") if p["fotos"] else []
        capa=fotos[0] if fotos else ""
        cls="liked" if p["id"] in liked else ""
        cor="❤️" if p["id"] in liked else "🤍"
        cards+=f"""<div class="card"><a href="/produto/{p['id']}"><img src="/static/uploads/{capa}"></a>
        <div class="info"><small>{p['cidade'] or 'Maputo'} • {p['tenho'][:25]}</small><b>TENHO: {p['tenho']}</b><small>QUERO: {p['quero']}</small>
        <form action="/like/{p['id']}" method="post"><button class="like {cls}">{cor} Gostei ({p['total']})</button></form>
        <a class="wpp" href="https://wa.me/{p['whatsapp']}">💬 WHATSAPP</a></div></div>"""
    sair='<a href="/logout">🚪 Sair</a>' if "user_id" in session else ''
    ola=f"<p style='padding:0 10px'>Olá, <b>{session.get('nome','')}</b> 👋</p>" if "user_id" in session else ""
    html=f"{ola}<h3 style='padding:0 10px'>🔥 Todas as Trocas</h3><div class='grid'>{cards}</div>"
    if not cards:
        html+="<div class='box'>Ainda não há trocas. Sê o primeiro! 👆</div>"
    return BASE.replace("{CONTEUDO}", html).replace("{SAIR}", sair)

@app.route("/produto/<int:pid>")
def produto(pid):
    con=db(); p=con.execute("SELECT * FROM produtos WHERE id=?", (pid,)).fetchone(); con.close()
    if not p: return redirect("/")
    fotos=(p["fotos"] or "").split(",") if p["fotos"] else []
    imgs="".join([f'<a href="/static/uploads/{f}"><img src="/static/uploads/{f}"></a>' for f in fotos])
    sair='<a href="/logout">🚪 Sair</a>' if "user_id" in session else ''
    html=f"""<div class="box"><div class="galeria">{imgs}</div><h3>{p['tenho']}</h3><p><b>QUERO:</b> {p['quero']}</p><p>{p['desc']}</p><p><b>Preço:</b> {p['preco']} | <b>Cidade:</b> {p['cidade']}</p><a class="wpp" href="https://wa.me/{p['whatsapp']}">💬 FALAR NO WHATSAPP</a><br><br><a href="/">← Voltar</a></div>"""
    return BASE.replace("{CONTEUDO}", html).replace("{SAIR}", sair)

@app.route("/like/<int:pid>", methods=["POST"])
def like(pid):
    if "user_id" not in session: return redirect("/login")
    con=db()
    ex=con.execute("SELECT id FROM likes WHERE user_id=? AND produto_id=?", (session["user_id"], pid)).fetchone()
    if ex: con.execute("DELETE FROM likes WHERE id=?", (ex["id"],))
    else: con.execute("INSERT INTO likes(user_id, produto_id) VALUES(?,?)", (session["user_id"], pid))
    con.commit(); con.close()
    return redirect("/")

@app.route("/publicar", methods=["GET","POST"])
def publicar():
    if "user_id" not in session: return redirect("/login")
    if request.method=="POST":
        nomes=[]
        for f in request.files.getlist("fotos")[:4]:
            if f and f.filename:
                fn=secure_filename(f.filename)
                f.save(os.path.join(UPLOAD, fn)); nomes.append(fn)
        con=db()
        con.execute("INSERT INTO produtos(user_id,tenho,quero,desc,preco,whatsapp,fotos,cidade) VALUES(?,?,?,?,?,?,?,?)",
        (session["user_id"], request.form.get("tenho"), request.form.get("quero"), request.form.get("desc"), request.form.get("preco"), request.form.get("whatsapp"), ",".join(nomes), request.form.get("cidade")))
        con.commit(); con.close()
        return redirect("/")
    sair='<a href="/logout">🚪 Sair</a>'
    html="""<div class="box"><h3>➕ Publicar Troca</h3><form method="post" enctype="multipart/form-data">
    <label><b>Escolhe até 4 fotos:</b></label><input type="file" name="fotos" multiple accept="image/*" required>
    <input name="tenho" placeholder="O que TENS? Ex: Shorts de Senhora" required>
    <input name="quero" placeholder="O que QUERES? Ex: Troca por..." required>
    <textarea name="desc" placeholder="Descreve o produto, cores, tamanhos..."></textarea>
    <input name="preco" placeholder="Preço Ex: 500 MT">
    <input name="whatsapp" placeholder="WhatsApp Ex: 258840000000" required>
    <input name="cidade" placeholder="Cidade Ex: Matola">
    <button class="pub">PUBLICAR AGORA</button></form></div>"""
    return BASE.replace("{%CONTEUDO%}", html).replace("{%SAIR%}", sair)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        con=db()
        try:
            con.execute("INSERT INTO users(nome,email,senha) VALUES(?,?,?)", (request.form.get("nome"), request.form.get("email"), generate_password_hash(request.form.get("senha"))))
            con.commit()
        except: pass
        con.close(); return redirect("/login")
    html="""<div class="box"><h3>✅ Criar Conta</h3><form method="post"><input name="nome" placeholder="Teu Nome" required><input name="email" placeholder="Email" required><input name="senha" type="password" placeholder="Cria uma Senha" required><button class="pub">CRIAR CONTA</button></form><p style="text-align:center">Já tens conta? <a href="/login">Entrar</a></p></div>"""
    return BASE.replace("{%CONTEUDO%}", html).replace("{%SAIR%}", "")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        con=db(); u=con.execute("SELECT * FROM users WHERE email=?", (request.form.get("email"),)).fetchone(); con.close()
        if u and check_password_hash(u["senha"], request.form.get("senha")):
            session["user_id"]=u["id"]; session["nome"]=u["nome"]; return redirect("/")
    html="""<div class="box"><h3>👤 Entrar</h3><form method="post"><input name="email" placeholder="Email" required><input name="senha" type="password" placeholder="Senha" required><button class="pub">ENTRAR</button></form><p style="text-align:center">Não tens conta? <a href="/register">Criar Conta</a></p></div>"""
    return BASE.replace("{%CONTEUDO%}", html).replace("{%SAIR%}", "")

@app.route("/logout")
def logout():
    session.clear(); return redirect("/")
    

def admin_ok():
    return session.get("admin") == True

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("senha") == ADMIN_SENHA:
            session["admin"] = True
            return redirect("/admin")
        return "Senha errada! <a href='/admin'>Voltar</a>"
    if not admin_ok():
        html = """<div class="box"><h3>Admin TrocaTroca</h3>
        <form method="post"><input name="senha" type="password" placeholder="Senha" required>
        <button>ENTRAR</button></form></div>"""
        return BASE.replace("{CONTEUDO}", html).replace("{SAIR}", "")
    con = db()
    users = con.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    prods = con.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    con.close()
    h = "<div class='box'><h3>Painel Admin</h3><p>Users: %s | Produtos: %s</p>" % (len(users), len(prods))
    h += "<h4>Utilizadores</h4>"
    for u in users:
        h += f"<p>{u[0]} - {u[1]} - {u[2]} <a href='/admin/del_user/{u[0]}'>Apagar</a></p>"
    h += "<h4>Produtos</h4>"
    for p in prods:
        h += f"<p>{p[0]} - {p[2]} - {p[4]} MT <a href='/admin/del_prod/{p[0]}'>Apagar</a></p>"
    h += "<br><a href='/logout'>Sair</a></div>"
    return BASE.replace("{CONTEUDO}", h).replace("{SAIR}", "")

@app.route("/admin/del_user/<int:uid>")
def del_user(uid):
    if not admin_ok(): return redirect("/admin")
    con = db(); con.execute("DELETE FROM users WHERE id=?", (uid,)); con.commit(); con.close()
    return redirect("/admin")

@app.route("/admin/del_prod/<int:pid>")
def del_prod(pid):
    if not admin_ok(): return redirect("/admin")
    con = db(); con.execute("DELETE FROM products WHERE id=?", (pid,)); con.commit(); con.close()
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
