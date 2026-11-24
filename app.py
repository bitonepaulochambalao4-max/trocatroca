from flask import Flask, request, redirect, session, send_from_directory
import sqlite3, os
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
    c.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, tenho TEXT, quero TEXT, zona TEXT, wa TEXT, foto TEXT, autor TEXT)")
    c.commit()
    c.close()
init()
@app.route('/')
def home():
    c = db()
    produtos = c.execute("SELECT * FROM produtos ORDER BY id DESC").fetchall()
    c.close()
    user = session.get("user","")
    top = f"<div style='text-align:right;padding:10px'>Ola, <b>{user}</b> | <a href='/logout'>Sair</a></div>" if user else "<div style='text-align:right;padding:10px'><a href='/login'>Entrar</a> | <a href='/registar'>Criar Conta</a></div>"
    cards=""
    for p in produtos:
        img = f"<img src='/{p['foto']}' style='width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:10px;display:block'>" if p['foto'] else "<div style='width:100%;aspect-ratio:1/1;background:#eee;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:40px'>📦</div>"
        cards+=f"<div style='background:white;border-radius:15px;padding:10px;box-shadow:0 4px 10px #00000022'>{img}<div style='font-size:11px;color:#888;margin-top:8px'>{p['zona']} • {p['autor']}</div><div style='font-size:14px;font-weight:bold'>TENHO: {p['tenho']}</div><div style='font-size:14px;color:#00A651;font-weight:bold'>QUERO: {p['quero']}</div><a href='https://wa.me/{p['wa']}' style='display:block;background:#25D366;color:white;text-align:center;padding:10px;border-radius:10px;text-decoration:none;font-weight:bold;margin-top:8px;font-size:13px'>💬 WHATSAPP</a></div>"
    if not cards: cards="<p style='text-align:center'>Nenhuma troca ainda. Seja o primeiro!</p>"
    return f"<div style='font-family:sans-serif;background:#F2F2F2;min-height:100vh'>{top}<div style='background:linear-gradient(90deg,#00A651,#00D264);color:white;padding:25px;text-align:center;border-radius:0 0 20px 20px'><h1>🔄 TROCA TROCA MOZ</h1><p>Troca sem dinheiro • Todos veem tudo</p><a href='/publicar' style='display:inline-block;background:white;color:#00A651;padding:12px 20px;border-radius:30px;text-decoration:none;font-weight:bold'>+ PUBLICAR COM FOTO</a></div><h2 style='padding:0 15px'>🔥 Todas as Trocas</h2><div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:0 10px 20px'>{cards}</div></div>"
@app.route('/registar', methods=['GET','POST'])
def reg():
    if request.method=='POST':
        c=db()
        try:
            c.execute("INSERT INTO users VALUES (?,?)",(request.form['nome'],request.form['senha']))
            c.commit()
        except: pass
        c.close()
        session['user']=request.form['nome']
        return redirect('/')
    return "<div style='font-family:sans-serif;padding:20px;max-width:400px;margin:auto'><h2>Criar Conta</h2><form method='POST'><input name='nome' placeholder='Teu nome' required style='width:100%;padding:12px;margin:5px 0;border-radius:10px;border:1px solid #ccc'><input name='senha' type='password' placeholder='Senha' required style='width:100%;padding:12px;margin:5px 0;border-radius:10px;border:1px solid #ccc'><button style='width:100%;padding:14px;background:#00A651;color:white;border:none;border-radius:10px;font-weight:bold'>CRIAR CONTA</button></form></div>"
@app.route('/login', methods=['GET','POST'])
def log():
    if request.method=='POST':
        c=db()
        u=c.execute("SELECT * FROM users WHERE nome=? AND senha=?",(request.form['nome'],request.form['senha'])).fetchone()
        c.close()
        if u:
            session['user']=request.form['nome']
            return redirect('/')
        return "Senha errada! <a href='/login'>Voltar</a>"
    return "<div style='font-family:sans-serif;padding:20px;max-width:400px;margin:auto'><h2>Entrar</h2><form method='POST'><input name='nome' placeholder='Nome' required style='width:100%;padding:12px;margin:5px 0;border-radius:10px;border:1px solid #ccc'><input name='senha' type='password' placeholder='Senha' required style='width:100%;padding:12px;margin:5px 0;border-radius:10px;border:1px solid #ccc'><button style='width:100%;padding:14px;background:#00A651;color:white;border:none;border-radius:10px;font-weight:bold'>ENTRAR</button></form></div>"
@app.route('/logout')
def out():
    session.pop('user',None)
    return redirect('/')
@app.route('/publicar', methods=['GET','POST'])
def pub():
    if 'user' not in session: return redirect('/login')
    if request.method=='POST':
        f=request.files.get('foto')
        caminho=""
        if f and f.filename:
            caminho=f"static/uploads/{f.filename}"
            f.save(caminho)
        c=db()
        c.execute("INSERT INTO produtos (tenho,quero,zona,wa,foto,autor) VALUES (?,?,?,?,?,?)",(request.form['tenho'],request.form['quero'],request.form['zona'],request.form['wa'],caminho,session['user']))
        c.commit(); c.close()
        return redirect('/')
    return "<div style='font-family:sans-serif;padding:20px;max-width:400px;margin:auto'><h2>Publicar com Foto</h2><form method='POST' enctype='multipart/form-data'><input name='tenho' placeholder='O que tens?' required style='width:100%;padding:12px;margin:5px 0;border-radius:10px;border:1px solid #ccc'><input name='quero' placeholder='O que queres?' required style='width:100%;padding:12px;margin:5px 0;border-radius:10px;border:1px solid #ccc'><input name='zona' placeholder='Zona' required style='width:100%;padding:12px;margin:5px 0;border-radius:10px;border:1px solid #ccc'><input name='wa' placeholder='WhatsApp 258...' required style='width:100%;padding:12px;margin:5px 0;border-radius:10px;border:1px solid #ccc'><p>📷 Foto:</p><input type='file' name='foto' accept='image/*' style='width:100%'><button style='width:100%;padding:14px;background:#00A651;color:white;border:none;border-radius:10px;font-weight:bold;margin-top:10px'>PUBLICAR</button></form></div>"
import os; app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))