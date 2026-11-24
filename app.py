import os
from flask import Flask, request, redirect, session, jsonify
import sqlite3
app = Flask(__name__)
app.secret_key = "troca123"
os.makedirs("static/uploads", exist_ok=True)
DB = "trocatroca.db"
def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c
def init():
    c = db()
    c.execute("CREATE TABLE IF NOT EXISTS users (nome TEXT PRIMARY KEY, senha TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, tenho TEXT, quero TEXT, zona TEXT, nome TEXT, foto TEXT, whatsapp TEXT)")
    c.commit(); c.close()
init()

# --- ISTO FAZ O BOTÃO INSTALAR FUNCIONAR ---
@app.route("/manifest.json")
def manifest():
    return jsonify({"name":"Troca Troca Moz","short_name":"TrocaTroca","start_url":"/","display":"standalone","background_color":"#00A651","theme_color":"#00A651","icons":[{"src":"https://cdn-icons-png.flaticon.com/512/3082/3082383.png","sizes":"512x512","type":"image/png"}]})
@app.route("/sw.js")
def sw():
    return "self.addEventListener('fetch',e=>{})", 200, {'Content-Type':'application/javascript'}

CSS = """
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#00A651">
<meta name="mobile-web-app-capable" content="yes">
<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js')}</script>
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:Arial,sans-serif}
body{background:#f0f0f0;width:100%}
.top{background:linear-gradient(135deg,#00A651,#00D465);color:white;padding:20px 10px 25px;text-align:center;width:100%}
.top h1{font-size:24px}
.btn-top{background:white;color:#00A651;padding:9px 18px;border-radius:20px;text-decoration:none;font-weight:bold;font-size:13px;display:inline-block;margin-top:12px}
.bar{display:flex;justify-content:space-between;align-items:center;padding:10px;background:white;width:100%;font-size:13px;gap:5px}
.bar a{color:#00A651;font-weight:bold;text-decoration:none;background:#E8F5E9;padding:7px 10px;border-radius:15px}
.wrap{padding:10px;width:100%}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;width:100%}
.card{background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1)}
.card img{width:100%;height:180px;object-fit:cover}
.card-body{padding:10px}
.wa{display:block;background:#00C853;color:white;text-align:center;padding:10px;border-radius:8px;text-decoration:none;font-weight:bold;margin-top:8px;font-size:13px}
input{width:100%;padding:13px;margin:8px 0;border:1px solid #ddd;border-radius:10px;font-size:16px}
button{width:100%;padding:13px;background:#00A651;color:white;border:none;border-radius:10px;font-size:16px;font-weight:bold}
.box{background:white;margin:15px 10px;padding:20px;border-radius:14px}
</style>
"""
@app.route("/")
def home():
    c = db(); produtos = c.execute("SELECT * FROM produtos ORDER BY id DESC").fetchall(); c.close()
    user = session.get("user","")
    if user:
        bar = f"<div class='bar'><span>👋 <b>{user}</b></span><a href='/login'>🔑 Entrar</a><a href='/register'>📝 Criar Conta</a><a href='/logout'>Sair</a></div>"
    else:
        bar = "<div class='bar'><span>👋 Visitante</span><a href='/login'>🔑 Entrar</a><a href='/register'>📝 Criar Conta</a></div>"
    cards = ""
    for p in produtos:
        img = f"<img src='/{p['foto']}'>" if p['foto'] else "<div style='height:160px;background:#E8F5E9;display:flex;align-items:center;justify-content:center;font-size:50px'>🔄</div>"
        cards += f"<div class='card'>{img}<div class='card-body'><p style='font-size:11px;color:#888'>{p['zona']} - {p['nome']}</p><p style='font-size:13px;margin-top:5px'><b>TENHO:</b> {p['tenho']}</p><p style='font-size:13px;color:#00A651'><b>QUERO:</b> {p['quero']}</p><a class='wa' href='https://wa.me/{p['whatsapp']}'>💬 WHATSAPP</a></div></div>"
    if not produtos:
        cards = "<div style='text-align:center;padding:40px;background:white;border-radius:12px'><h3>Nenhuma troca ainda</h3><p>Seja o primeiro!</p></div>"
    return f"{CSS}<div class='top'><h1>🔄 TROCA TROCA MOZ</h1><p>Troca sem dinheiro - Todos veem tudo</p><br><a class='btn-top' href='/publicar'>+ PUBLICAR COM FOTO</a></div>{bar}<div class='wrap'><h3 style='margin:5px 0 10px'>🔥 Todas as Trocas</h3><div class='grid'>{cards}</div><p style='text-align:center;margin-top:20px'><a href='/admin' style='color:#999;font-size:12px'>Painel Admin</a></p></div>"
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        try:
            c=db(); c.execute("INSERT INTO users VALUES (?,?)",(request.form["nome"],request.form["senha"])); c.commit(); c.close()
        except: pass
        session["user"]=request.form["nome"]; return redirect("/")
    return f"{CSS}<div class='top'><h1>📝 Criar Conta</h1></div><div class='box'><form method='POST'><input name='nome' placeholder='Teu nome' required><input name='senha' type='password' placeholder='Senha' required><button>CRIAR CONTA</button></form><p style='text-align:center;margin-top:10px'><a href='/login'>Já tenho conta</a></p></div>"
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        c=db(); u=c.execute("SELECT * FROM users WHERE nome=? AND senha=?",(request.form["nome"],request.form["senha"])).fetchone(); c.close()
        if u: session["user"]=request.form["nome"]; return redirect("/")
        return "Senha errada! <a href='/login'>Voltar</a>"
    return f"{CSS}<div class='top'><h1>🔑 Entrar</h1></div><div class='box'><form method='POST'><input name='nome' placeholder='Nome' required><input name='senha' type='password' placeholder='Senha' required><button>ENTRAR</button></form><p style='text-align:center;margin-top:10px'><a href='/register'>Criar Conta</a></p></div>"
@app.route("/logout")
def logout():
    session.pop("user",None); return redirect("/")
@app.route("/publicar", methods=["GET","POST"])
def publicar():
    if "user" not in session: return redirect("/login")
    if request.method=="POST":
        filename=""
        if "foto" in request.files:
            f=request.files["foto"]
            if f and f.filename:
                filename="static/uploads/"+f.filename; f.save(filename)
        c=db(); c.execute("INSERT INTO produtos (tenho,quero,zona,nome,foto,whatsapp) VALUES (?,?,?,?,?,?)",(request.form["tenho"],request.form["quero"],request.form["zona"],session["user"],filename,request.form.get("whatsapp",""))); c.commit(); c.close(); return redirect("/")
    return f"{CSS}<div class='top'><h1>📸 Publicar Troca</h1></div><div class='box'><form method='POST' enctype='multipart/form-data'><input name='tenho' placeholder='O que tens?' required><input name='quero' placeholder='O que queres?' required><input name='zona' placeholder='Zona Ex: Matola' required><input name='whatsapp' placeholder='WhatsApp Ex: 258840000000' required><p>Foto:</p><input type='file' name='foto'><button>Publicar</button></form></div>"
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method=="POST":
        if request.form.get("senha")=="Troca2026":
            session["admin"]=True; return redirect("/admin")
        return "Senha errada! <a href='/admin'>Voltar</a>"
    if not session.get("admin"):
        return f"{CSS}<div class='top'><h1>🔐 PAINEL ADMIN</h1></div><div class='box'><form method='POST'><input name='senha' type='password' placeholder='Senha Admin'><button>ENTRAR</button></form></div>"
    c=db(); produtos=c.execute("SELECT * FROM produtos ORDER BY id DESC").fetchall(); total_users=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]; c.close()
    rows=""
    for p in produtos:
        img=f"<img src='/{p['foto']}' style='width:60px;height:60px;object-fit:cover;border-radius:10px'>" if p['foto'] else "🔄"
        rows+=f"<div style='display:flex;gap:10px;background:white;padding:10px;border-radius:12px;margin:8px 0;align-items:center'>{img}<div style='flex:1'><b>{p['tenho']} ➡️ {p['quero']}</b><br>👤 {p['nome']} | 📍 {p['zona']}</div><a href='/admin/apagar/{p['id']}' onclick=\"return confirm('Apagar?')\" style='background:red;color:white;padding:8px 12px;border-radius:8px;text-decoration:none'>Apagar</a></div>"
    if not produtos: rows="<p>Nenhuma troca.</p>"
    return f"{CSS}<div class='top'><h1>📊 Painel Admin</h1></div><div class='wrap'><div style='display:flex;gap:10px'><div style='flex:1;background:white;padding:15px;border-radius:12px;text-align:center'><b style='font-size:22px'>{len(produtos)}</b><br>Trocas</div><div style='flex:1;background:white;padding:15px;border-radius:12px;text-align:center'><b style='font-size:22px'>{total_users}</b><br>Utilizadores</div></div>{rows}<p style='text-align:center;margin-top:15px'><a href='/'>Voltar</a> | <a href='/admin/sair'>Sair</a></p></div>"
@app.route("/admin/apagar/<int:id>")
def admin_apagar(id):
    if not session.get("admin"): return redirect("/admin")
    c=db(); c.execute("DELETE FROM produtos WHERE id=?",(id,)); c.commit(); c.close(); return redirect("/admin")
@app.route("/admin/sair")
def admin_sair():
    session.pop("admin",None); return redirect("/")
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
