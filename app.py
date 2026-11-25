import os, sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "troca-troca-moz-123"
UPLOAD = "static/uploads"
os.makedirs(UPLOAD, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD

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
*{box-sizing:border-box}body{margin:0;font-family:Arial;background:#f2f2f2}
.top{background:#00a651;color:white;text-align:center;padding:12px}
.top a{color:white;text-decoration:none}
.btn{background:white;color:#00a651;padding:8px 16px;border-radius:20px;font-weight:bold;display:inline-block;margin-top:6px}
.menu{display:flex;justify-content:space-around;background:white;padding:10px;font-size:13px}
.menu a{color:#333;text-decoration:none}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:10px}
.card{background:white;border-radius:10px;overflow:hidden}
.card img{width:100%;aspect-ratio:1/1;object-fit:cover;display:block;background:#eee}
.card .info{padding:8px}
.card b{font-size:13px}
.card small{color:#666}
.wpp{background:#00a651;color:white;text-align:center;padding:8px;border-radius:6px;display:block;text-decoration:none;margin-top:6px;font-size:13px}
.like{border:1px solid #ddd;background:white;width:100%;padding:7px;border-radius:6px;margin-top:6px;cursor:pointer}
.like.liked{background:#ffeef2;border-color:#ff4d6d}
.galeria img{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:10px;margin-bottom:8px}
input,textarea,select{width:100%;padding:10px;margin:6px 0;border:1px solid #ddd;border-radius:8px}
button.pub{background:#00a651;color:white;border:none;padding:12px;border-radius:8px;width:100%;font-weight:bold}
.box{background:white;padding:14px;margin:10px;border-radius:10px}
</style></head><body>
<br><a style="background:yellow;color:black;padding:10px 20px;border-radius:20px;font-weight:bold;display:inline-block;margin-top:8px;text-decoration:none" href="/publicar">➕ ADICIONAR TROCA</a>
<a style="background:yellow;color:black;padding:10px 20px;border-radius:20px;font-weight:bold;display:inline-block;margin-top:8px" href="/publicar">➕ ADICIONAR TROCA</a>
{%USER%}
</body></html>
"""

@app.route("/")
def home():
    con=db()
    prods=con.execute("SELECT p.*, (SELECT COUNT(*) FROM likes WHERE produto_id=p.id) as total_likes FROM produtos p ORDER BY p.id DESC").fetchall()
    liked_ids=set()
    if "user_id" in session:
        rows=con.execute("SELECT produto_id FROM likes WHERE user_id=?", (session["user_id"],)).fetchall()
        liked_ids={r["produto_id"] for r in rows}
    con.close()
    cards=""
    for p in prods:
        fotos=(p["fotos"] or "").split(",") if p["fotos"] else []
        capa=fotos[0] if fotos else ""
        liked="liked" if p["id"] in liked_ids else ""
        coracao="❤️" if p["id"] in liked_ids else "🤍"
        cards+=f"""
        <div class="card">
          <a href="/produto/{p['id']}"><img src="/static/uploads/{capa}"></a>
          <div class="info"><small>{p['cidade'] or ''} • {p['tenho']}</small><br><b>TENHO: {p['tenho']}</b><br><small>QUERO: {p['quero']}</small>
          <form action="/like/{p['id']}" method="post"><button class="like {liked}">{coracao} Gostei ({p['total_likes']})</button></form>
          <a class="wpp" href="https://wa.me/{p['whatsapp']}">💬 WHATSAPP</a></div>
        </div>"""
    html=f"<h3 style='padding:0 10px'>🔥 Todas as Trocas</h3><div class='grid'>{cards}</div>"
    return BASE.replace("{%USER%}", html)

@app.route("/produto/<int:pid>")
def produto(pid):
    con=db(); p=con.execute("SELECT * FROM produtos WHERE id=?", (pid,)).fetchone(); con.close()
    if not p: return redirect("/")
    fotos=(p["fotos"] or "").split(",") if p["fotos"] else []
    imgs="".join([f'<a href="/static/uploads/{f}"><img src="/static/uploads/{f}"></a>' for f in fotos])
    html=f"""<div class="box"><div class="galeria">{imgs}</div><h3>{p['tenho']}</h3><p><b>QUERO:</b> {p['quero']}</p><p>{p['desc']}</p><p><b>Preço:</b> {p['preco']} | <b>Cidade:</b> {p['cidade']}</p>
    <a class="wpp" href="https://wa.me/{p['whatsapp']}">💬 FALAR NO WHATSAPP</a><br><br><a href="/">← Voltar</a></div>"""
    return BASE.replace("{%USER%}", html)

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
                f.save(os.path.join(UPLOAD, fn))
                nomes.append(fn)
        con=db()
        con.execute("INSERT INTO produtos(user_id,tenho,quero,desc,preco,whatsapp,fotos,cidade) VALUES(?,?,?,?,?,?,?,?)",
        (session["user_id"], request.form.get("tenho"), request.form.get("quero"), request.form.get("desc"), request.form.get("preco"), request.form.get("whatsapp"), ",".join(nomes), request.form.get("cidade")))
        con.commit(); con.close()
        return redirect("/")
    html="""<div class="box"><h3>Publicar Troca</h3><form method="post" enctype="multipart/form-data">
    <label>Escolhe até 4 fotos (ficam quadradas):</label><input type="file" name="fotos" multiple accept="image/*" required>
    <input name="tenho" placeholder="O que TENS? Ex: iPhone 14 Pro" required>
    <input name="quero" placeholder="O que QUERES? Ex: Samsung S23" required>
    <textarea name="desc" placeholder="Descreve o produto..."></textarea>
    <input name="preco" placeholder="Preço ou Troca">
    <input name="whatsapp" placeholder="WhatsApp Ex: 258840000000" required>
    <input name="cidade" placeholder="Cidade Ex: Matola">
    <button class="pub">PUBLICAR</button></form></div>"""
    return BASE.replace("{%USER%}", html)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        con=db()
        try:
            con.execute("INSERT INTO users(nome,email,senha) VALUES(?,?,?)", (request.form.get("nome"), request.form.get("email"), generate_password_hash(request.form.get("senha"))))
            con.commit()
        except: pass
        con.close(); return redirect("/login")
    return BASE.replace("{%USER%}", """<div class="box"><h3>Criar Conta</h3><form method="post"><input name="nome" placeholder="Nome"><input name="email" placeholder="Email"><input name="senha" type="password" placeholder="Senha"><button class="pub">Criar</button></form></div>""")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        con=db(); u=con.execute("SELECT * FROM users WHERE email=?", (request.form.get("email"),)).fetchone(); con.close()
        if u and check_password_hash(u["senha"], request.form.get("senha")):
            session["user_id"]=u["id"]; session["nome"]=u["nome"]; return redirect("/")
    return BASE.replace("{%USER%}", """<div class="box"><h3>Entrar</h3><form method="post"><input name="email" placeholder="Email"><input name="senha" type="password" placeholder="Senha"><button class="pub">Entrar</button></form></div>""")

@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)
