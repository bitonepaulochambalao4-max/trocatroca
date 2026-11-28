import os, sqlite3
from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "trocatroca-secreto-123"
ADMIN_PASS = "admin123"
DB = "trocatroca.db"

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    c = db()
    c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, nome TEXT, email TEXT UNIQUE, senha TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS trocas(id INTEGER PRIMARY KEY, titulo TEXT, preco TEXT, desc TEXT, dono TEXT, foto TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS visitas(id INTEGER PRIMARY KEY, total INTEGER)")
    c.execute("INSERT OR IGNORE INTO visitas(id,total) VALUES(1,0)")
    c.commit(); c.close()
init()

CSS = """
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif}
body{background:#f0f7f0}
.top{background:#0a7a2f;color:white;padding:18px 15px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0}
.top b{font-size:22px}
.top b span{color:#ffdd00}
.top a{background:white;color:#0a7a2f;padding:8px 14px;border-radius:20px;text-decoration:none;font-weight:bold;font-size:13px}
.hero{background:linear-gradient(135deg,#0a7a2f,#12b84a);color:white;text-align:center;padding:28px 15px}
.hero h1{font-size:26px;margin-bottom:6px}
.hero p{opacity:.9;font-size:14px}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:15px}
.card{background:white;border-radius:14px;padding:16px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.08);border-top:4px solid #0a7a2f}
.card h2{font-size:28px;color:#0a7a2f}
.card p{font-size:12px;color:#666;margin-top:4px}
.section{padding:0 15px 20px}
.section h3{margin:10px 0}
.item{background:white;border-radius:14px;padding:14px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,.08);display:flex;gap:12px;align-items:center}
.item img{width:70px;height:70px;border-radius:10px;object-fit:cover;background:#e8f5e9}
.btn{background:#0a7a2f;color:white;border:none;padding:12px;width:100%;border-radius:10px;font-weight:bold;font-size:15px}
.btn2{background:#ffdd00;color:#111;padding:10px 18px;border-radius:20px;text-decoration:none;font-weight:bold;display:inline-block;margin-top:10px}
input{width:100%;padding:13px;margin:8px 0;border:1px solid #ddd;border-radius:10px}
.footer{text-align:center;padding:20px;color:#888;font-size:12px}
.footer a{color:#0a7a2f;text-decoration:none;margin:0 8px;font-weight:bold}
</style>
"""

def header():
    u = session.get("nome")
    btn = f"<span>Olá, {u}</span> <a href='/sair'>Sair</a>" if u else "<a href='/entrar'>Entrar</a> <a href='/criar'>Criar Conta</a>"
    return f"<div class='top'><b>TROCA<span>TROCA</span> 🇲🇿</b><div>{btn}</div></div>"

@app.route("/")
def home():
    c = db()
    c.execute("UPDATE visitas SET total=total+1 WHERE id=1"); c.commit()
    total_visitas = c.execute("SELECT total FROM visitas WHERE id=1").fetchone()[0]
    n_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    trocas = c.execute("SELECT * FROM trocas ORDER BY id DESC").fetchall()
    n_trocas = len(trocas)
    c.close()
    items = ""
    for t in trocas:
        items += f"<div class='item'><img src='{t['foto'] or 'https://via.placeholder.com/70'}'><div style='flex:1'><b>{t['titulo']}</b><br><small>{t['desc']}</small><br><b style='color:#0a7a2f'>{t['preco']} MZN</b> • {t['dono']}</div></div>"
    if not items:
        items = "<div style='background:white;padding:20px;border-radius:14px;text-align:center'>Ainda não há trocas.<br>Seja o primeiro a publicar! 👇</div>"
    return render_template_string(CSS + header() + f"""
    <div class='hero'><h1>Troca, Vende & Compra em Moçambique</h1><p>Sem dinheiro? Troca por outra coisa!</p><a class='btn2' href='/adicionar'>+ ADICIONAR TROCA</a></div>
    <div class='stats'>
      <div class='card'><h2>👥 {total_visitas}</h2><p>Pessoas que visitaram o site</p></div>
      <div class='card'><h2>🔄 {n_trocas}</h2><p>Trocas Ativas</p></div>
      <div class='card'><h2>👤 {n_users}</h2><p>Utilizadores Registados</p></div>
      <div class='card'><h2>✅ {n_trocas}</h2><p>Trocas Publicadas</p></div>
    </div>
    <div class='section'><h3>🔥 Últimas Trocas</h3>{items}</div>
    <div class='footer'><a href='/entrar'>Entrar</a> | <a href='/criar'>Criar Conta</a> | <a href='/admin'>Admin</a><br><br>TrocaTroca Moz © 2026</div>
    """)

@app.route("/criar", methods=["GET","POST"])
def criar():
    if request.method=="POST":
        c=db()
        try:
            c.execute("INSERT INTO users(nome,email,senha) VALUES(?,?,?)",(request.form["nome"],request.form["email"],generate_password_hash(request.form["senha"])));c.commit();c.close()
            session["nome"]=request.form["nome"]; return redirect("/")
        except: return "Email já existe. <a href='/criar'>Voltar</a>"
    return render_template_string(CSS+header()+"<div style='padding:20px'><h2>Criar Conta</h2><form method='post'><input name='nome' placeholder='Teu nome' required><input name='email' placeholder='Email' required><input name='senha' type='password' placeholder='Senha' required><button class='btn'>CRIAR CONTA</button></form></div>")

@app.route("/entrar", methods=["GET","POST"])
def entrar():
    if request.method=="POST":
        c=db(); u=c.execute("SELECT * FROM users WHERE email=?",(request.form["email"],)).fetchone();c.close()
        if u and check_password_hash(u["senha"],request.form["senha"]):
            session["nome"]=u["nome"]; return redirect("/")
        return "Senha errada. <a href='/entrar'>Voltar</a>"
    return render_template_string(CSS+header()+"<div style='padding:20px'><h2>Entrar</h2><form method='post'><input name='email' placeholder='Email' required><input name='senha' type='password' placeholder='Senha' required><button class='btn'>ENTRAR</button></form></div>")

@app.route("/sair")
def sair():
    session.clear(); return redirect("/")

@app.route("/adicionar", methods=["GET","POST"])
def adicionar():
    if "nome" not in session: return redirect("/entrar")
    if request.method=="POST":
        c=db(); c.execute("INSERT INTO trocas(titulo,preco,desc,dono,foto) VALUES(?,?,?,?,?)",(request.form["titulo"],request.form["preco"],request.form["desc"],session["nome"],request.form.get("foto","")));c.commit();c.close(); return redirect("/")
    return render_template_string(CSS+header()+"<div style='padding:20px'><h2>+ Adicionar Troca</h2><form method='post'><input name='titulo' placeholder='Ex: iPhone 11' required><input name='preco' placeholder='Preço em MZN' required><input name='desc' placeholder='O que queres em troca? Ex: Troco por Samsung'><input name='foto' placeholder='Link da foto (opcional)'><button class='btn'>PUBLICAR</button></form></div>")

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method=="POST" and request.form.get("senha")==ADMIN_PASS:
        session["admin"]=True
    if not session.get("admin"):
        return render_template_string(CSS+"<div style='padding:20px'><h2>🔐 Admin</h2><form method='post'><input name='senha' type='password' placeholder='Senha Admin' required><button class='btn'>ENTRAR</button></form><p>Senha: admin123</p></div>")
    c=db(); n_users=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]; n_trocas=c.execute("SELECT COUNT(*) FROM trocas").fetchone()[0]; visitas=c.execute("SELECT total FROM visitas WHERE id=1").fetchone()[0]; users=c.execute("SELECT * FROM users").fetchall(); c.close()
    lista="".join([f"<div class='item'><div><b>{u['nome']}</b><br><small>{u['email']}</small></div></div>" for u in users])
    return render_template_string(CSS+header()+f"<div class='hero'><h1>Painel Admin</h1></div><div class='stats'><div class='card'><h2>{visitas}</h2><p>Visitas Totais</p></div><div class='card'><h2>{n_users}</h2><p>Utilizadores</p></div><div class='card'><h2>{n_trocas}</h2><p>Trocas</p></div><div class='card'><h2>🟢 Online</h2><p>Site Ativo</p></div></div><div class='section'><h3>Utilizadores</h3>{lista}</div>")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
