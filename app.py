from flask import Flask, request, redirect, session, g
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "troca-troca-moz-2026"
app.config['UPLOAD_FOLDER'] = 'static/fotos'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ADMIN_SENHA = "admin123"

def db():
    if 'db' not in g:
        g.db = sqlite3.connect('troca.db')
        g.db.row_factory = sqlite3.Row
        g.db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, nome TEXT, email TEXT UNIQUE, senha TEXT)")
        g.db.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, user_id INTEGER, tenho TEXT, quero TEXT, desc TEXT, preco TEXT, whatsapp TEXT, fotos TEXT, cidade TEXT)")
        g.db.commit()
    return g.db

@app.teardown_appcontext
def close(e):
    d = g.pop('db', None)
    if d: d.close()

def BASE(conteudo, titulo="Troca Troca Moz"):
    user = session.get('nome', '')
    sair = f'<a href="/logout">Sair ({user})</a>' if user else '<a href="/login">Entrar</a> | <a href="/register">Criar Conta</a>'
    return f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{titulo}</title>
    <style>body{{font-family:Arial;margin:0;background:#f2f2f2}} .top{{background:#00a651;color:white;padding:20px;text-align:center}} .btn{{background:#ffcc00;color:black;padding:12px 20px;border-radius:30px;text-decoration:none;font-weight:bold;display:inline-block}} .menu{{background:white;padding:10px;text-align:center}} .menu a{{margin:0 10px;text-decoration:none;color:#333;font-weight:bold}} .card{{background:white;margin:10px;padding:15px;border-radius:10px}} input,textarea,select{{width:100%;padding:12px;margin:5px 0;border:1px solid #ccc;border-radius:8px;box-sizing:border-box}} button{{background:#00a651;color:white;padding:12px;border:none;width:100%;border-radius:8px;font-weight:bold}} img{{width:100%;border-radius:8px}}</style>
    </head><body>
    <div class="top"><h1>🔄 TROCA TROCA MOZ</h1><p>Troca sem dinheiro • Matola - Maputo</p><a class="btn" href="/publicar">+ ADICIONAR TROCA</a></div>
    <div class="menu"><a href="/">🏠 Início</a><a href="/publicar">+ Publicar</a><a href="/login">🔑 Entrar</a><a href="/register">✅ Criar Conta</a></div>
    <div style="padding:10px">{conteudo}<br><center>{sair} | <a href="/admin">Admin</a></center></div>
    </body></html>
    """

@app.route("/")
def index():
    con = db()
    prods = con.execute("SELECT * FROM produtos ORDER BY id DESC").fetchall()
    h = "<h2>Últimas Trocas</h2>"
    if not prods:
        h += "<p>Ainda não há trocas. Seja o primeiro a publicar!</p>"
    for p in prods:
        foto = ""
        if p['fotos']:
            foto = f'<img src="/{p["fotos"].split(",")[0]}">'
        h += f'<div class="card">{foto}<h3>Tenho: {p["tenho"]} ➡️ Quero: {p["quero"]}</h3><p>{p["desc"]}</p><p><b>{p["preco"]} MT</b> - {p["cidade"]}</p><a class="btn" href="https://wa.me/{p["whatsapp"]}">Falar no WhatsApp</a></div>'
    return BASE(h)

@app.route("/publicar", methods=["GET","POST"])
def publicar():
    if 'user_id' not in session:
        return redirect("/login")
    if request.method == "POST":
        fotos = []
        for f in request.files.getlist("fotos"):
            if f and f.filename:
                nome = secure_filename(f.filename)
                caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome)
                f.save(caminho)
                fotos.append(caminho)
        con = db()
        con.execute("INSERT INTO produtos(user_id,tenho,quero,desc,preco,whatsapp,fotos,cidade) VALUES(?,?,?,?,?,?,?,?)",
        (session['user_id'], request.form.get("tenho"), request.form.get("quero"), request.form.get("desc"), request.form.get("preco"), request.form.get("whatsapp"), ",".join(fotos), request.form.get("cidade")))
        con.commit()
        return redirect("/")
    html = """<h2>Publicar Troca</h2><form method="post" enctype="multipart/form-data">
    <input name="tenho" placeholder="O que tens? Ex: Telefone" required>
    <input name="quero" placeholder="O que queres? Ex: Troca por Bicicleta" required>
    <textarea name="desc" placeholder="Descreve o produto, cores, tamanho..."></textarea>
    <input name="preco" placeholder="Valor em MT Ex: 500">
    <input name="whatsapp" placeholder="WhatsApp Ex: 258840000000" required>
    <input name="cidade" placeholder="Cidade Ex: Matola">
    <label>Escolhe até 4 fotos</label><input type="file" name="fotos" multiple accept="image/*">
    <button>PUBLICAR AGORA</button></form>"""
    return BASE(html)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        try:
            con = db()
            con.execute("INSERT INTO users(nome,email,senha) VALUES(?,?,?)",
            (request.form.get("nome"), request.form.get("email"), generate_password_hash(request.form.get("senha"))))
            con.commit()
            return redirect("/login")
        except:
            return BASE("<p>Email já existe! <a href='/register'>Tentar de novo</a></p>")
    return BASE("""<h2>Criar Conta</h2><form method="post"><input name="nome" placeholder="Teu Nome" required><input name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button>Criar Conta</button></form>""")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        con = db()
        u = con.execute("SELECT * FROM users WHERE email=?", (request.form.get("email"),)).fetchone()
        if u and check_password_hash(u['senha'], request.form.get("senha")):
            session['user_id'] = u['id']
            session['nome'] = u['nome']
            return redirect("/")
        return BASE("<p>Senha errada! <a href='/login'>Tentar de novo</a></p>")
    return BASE("""<h2>Entrar</h2><form method="post"><input name="email" placeholder="Email" required><input type="password" name="senha" placeholder="Senha" required><button>Entrar</button></form>""")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form.get("senha") == ADMIN_SENHA:
            session['admin'] = True
            return redirect("/admin")
        return BASE("<p>Senha errada!</p>")
    if not session.get('admin'):
        return BASE("""<h2>Admin TrocaTroca</h2><form method="post"><input type="password" name="senha" placeholder="Senha admin"><button>ENTRAR</button></form>""")
    con = db()
    users = con.execute("SELECT * FROM users").fetchall()
    prods = con.execute("SELECT * FROM produtos").fetchall()
    h = f"<h2>Painel Admin</h2><p>{len(users)} Users | {len(prods)} Produtos</p>"
    for u in users:
        h += f"<p>{u['nome']} - {u['email']} <a href='/admin/del_user/{u['id']}'>Apagar</a></p>"
    for p in prods:
        h += f"<p>{p['tenho']} ➡️ {p['quero']} - {p['preco']} MT <a href='/admin/del_prod/{p['id']}'>Apagar</a></p>"
    h += "<br><a href='/logout'>Sair</a>"
    return BASE(h)

@app.route("/admin/del_user/<int:uid>")
def del_user(uid):
    if not session.get('admin'): return redirect("/admin")
    con = db(); con.execute("DELETE FROM users WHERE id=?", (uid,)); con.commit(); return redirect("/admin")

@app.route("/admin/del_prod/<int:pid>")
def del_prod(pid):
    if not session.get('admin'): return redirect("/admin")
    con = db(); con.execute("DELETE FROM produtos WHERE id=?", (pid,)); con.commit(); return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)
