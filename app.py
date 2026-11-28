import os, json, base64
from flask import Flask, request, redirect, session
app = Flask(__name__)
app.secret_key = "trocatroca-123"
DB = "data.json"

def load():
    if not os.path.exists(DB):
        return {"users": [], "trades": [], "visits": 0}
    try:
        with open(DB, "r", encoding="utf-8") as f:
            d = json.load(f)
            d.setdefault("users", []); d.setdefault("trades", []); d.setdefault("visits", 0)
            return d
    except:
        return {"users": [], "trades": [], "visits": 0}

def save(d):
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)

def get_user():
    if "email" not in session: return None
    d = load()
    for u in d["users"]:
        if u["email"] == session["email"]: return u
    return None

CSS = """
<style>
*{box-sizing:border-box} body{margin:0;font-family:Arial;background:#f0f2f5;color:#222}
.top{background:#00a651;color:white;padding:18px 12px;text-align:center}
.top h1{margin:0;font-size:26px}
.top p{margin:6px 0 0;font-size:13px;opacity:.95}
.wrap{padding:12px;padding-bottom:30px;max-width:600px;margin:0 auto}
.box{background:white;border-radius:14px;padding:16px;margin-bottom:12px;box-shadow:0 2px 10px rgba(0,0,0,.07)}
input,textarea{width:100%;padding:13px;margin:7px 0;border:1px solid #ddd;border-radius:10px;font-size:15px}
textarea{min-height:100px}
label{font-weight:bold;font-size:14px}
.btn{background:#00a651;color:white;border:none;padding:14px;border-radius:10px;width:100%;font-size:16px;font-weight:bold;cursor:pointer}
.btn-yellow{background:#ffcc00;color:#111}
.btn-whats{background:#25D366}
.btn-dark{background:#111}
.trade{border-radius:14px;overflow:hidden;background:white;box-shadow:0 2px 10px rgba(0,0,0,.07);margin-bottom:14px}
.trade img.main{width:100%;height:240px;object-fit:cover;background:#eee}
.thumbs{display:flex;gap:6px;padding:8px}
.thumbs img{width:68px;height:68px;border-radius:8px;object-fit:cover;cursor:pointer;border:2px solid #eee}
.badge{background:#e8f5e9;color:#00a651;padding:5px 10px;border-radius:20px;font-size:12px;font-weight:bold}
.stat-big{background:#00a651;color:white;border-radius:14px;padding:20px;text-align:center;margin-bottom:12px}
.stat-big b{font-size:36px;display:block}
.stat-row{display:flex;gap:10px}
.stat-row .box{flex:1;text-align:center}
.stat-row b{font-size:26px;display:block;color:#00a651}
a{color:#00a651;text-decoration:none;font-weight:bold}
small{color:#777}
</style>
"""

HEADER = """<div class="top"><h1>🔄 TROCA TROCA</h1><p>Troque sem gastar dinheiro • Moçambique 🇲🇿</p></div>"""

# ========== PÁGINA PRINCIPAL - LIMPA, SEM NÚMEROS ==========
@app.route("/")
def home():
    d = load()
    d["visits"] += 1; save(d)
    user = get_user()
    trades = list(reversed(d["trades"]))
    q = (request.args.get("q") or "").lower()
    h = CSS + HEADER + '<div class="wrap">'
    if user:
        h += f"""<div class="box">Olá, <b>{user['name']}</b> 👋<br><br>
        <a href="/add"><button class="btn btn-yellow">+ ADICIONAR TROCA</button></a><br><br>
        <center><a href="/logout">Sair</a></center></div>"""
    else:
        h += """<div class="box"><center><b>Bem-vindo ao Troca Troca</b><br><small>Publica o que tens e troca pelo que precisas</small></center><br>
        <a href="/login"><button class="btn">ENTRAR</button></a><br><br>
        <a href="/register"><button class="btn btn-yellow">CRIAR CONTA GRÁTIS</button></a></div>"""
    h += """<div class="box"><b>🔍 Pesquisar troca</b><form method="get"><input name="q" placeholder="Ex: LCD S26, iPhone, Samsung..."><button class="btn">PESQUISAR</button></form></div>"""
    h += "<h3>🆕 Últimas Trocas</h3>"
    for t in trades:
        if q and q not in (t.get("title","")+t.get("desc","")).lower(): continue
        photos = t.get("photos", [])
        main = photos[0] if photos else "https://via.placeholder.com/600x400?text=Sem+Foto"
        thumbs = "".join([f'<img src="{p}" onclick="document.getElementById(\'m{t["id"]}\').src=this.src">' for p in photos])
        h += f"""
        <div class="trade">
          <img class="main" id="m{t['id']}" src="{main}">
          <div class="thumbs">{thumbs}</div>
          <div style="padding:0 14px 14px">
            <span class="badge">✅ Disponível</span>
            <h3 style="margin:8px 0">{t.get('title','')}</h3>
            <p style="color:#555;white-space:pre-line;line-height:1.5">{t.get('desc','')}</p>
            <p><b style="font-size:18px;color:#00a651">💰 {t.get('price','')} MZN</b></p>
            <p><b>🔄 Quer em troca:</b> {t.get('want','')}</p>
            <p>👤 {t.get('owner','')} • 📍 {t.get('location','Matola')}</p>
            <a href="https://wa.me/258{t.get('whatsapp','').replace(' ','').replace('+','')}" target="_blank"><button class="btn btn-whats">💬 FALAR NO WHATSAPP</button></a>
          </div>
        </div>"""
    if not trades:
        h += "<div class='box'><center>Ainda não há trocas.<br>Seja o primeiro a publicar! 👆</center></div>"
    h += "</div>"
    return h

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        d = load()
        d["users"].append({"name": request.form["name"], "email": request.form["email"], "password": request.form["password"]})
        save(d); session["email"] = request.form["email"]; return redirect("/")
    return CSS + HEADER + """<div class="wrap"><div class="box"><h2>Criar Conta</h2><form method="post">
    <input name="name" placeholder="Teu nome" required><input name="email" placeholder="Email" required>
    <input name="password" type="password" placeholder="Senha" required><button class="btn">CRIAR CONTA</button></form></div></div>"""

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        d = load()
        for u in d["users"]:
            if u["email"] == request.form["email"] and u["password"] == request.form["password"]:
                session["email"] = u["email"]; return redirect("/")
        return "Senha errada! <a href='/login'>Voltar</a>"
    return CSS + HEADER + """<div class="wrap"><div class="box"><h2>Entrar</h2><form method="post">
    <input name="email" placeholder="Email" required><input name="password" type="password" placeholder="Senha" required>
    <button class="btn">ENTRAR</button></form><br><center><a href="/register">Criar conta</a></center></div></div>"""

@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

@app.route("/add", methods=["GET","POST"])
def add():
    user = get_user()
    if not user: return redirect("/login")
    if request.method == "POST":
        d = load()
        photos = []
        for f in request.files.getlist("photos")[:4]:
            if f and f.filename:
                photos.append(f"data:{f.mimetype};base64,{base64.b64encode(f.read()).decode()}")
        for i in range(1,5):
            link = request.form.get(f"link{i}", "").strip()
            if link: photos.append(link)
        d["trades"].append({
            "id": len(d["trades"])+1,
            "title": request.form["title"],
            "price": request.form["price"],
            "want": request.form["want"],
            "desc": request.form["desc"],
            "location": request.form.get("location","Matola"),
            "whatsapp": request.form.get("whatsapp",""),
            "owner": user["name"],
            "photos": photos
        })
        save(d); return redirect("/")
    return CSS + HEADER + """<div class="wrap"><div class="box"><h2>➕ Adicionar Troca</h2>
    <form method="post" enctype="multipart/form-data">
    <label>Título do Produto *</label><input name="title" placeholder="Ex: LCD S26 - Microfone Bluetooth" required>
    <label>Preço (MZN) *</label><input name="price" type="number" placeholder="1500" required>
    <label>📝 Descrição do Produto *</label>
    <textarea name="desc" placeholder="Ex: Novo na caixa, Bluetooth 6.0, ecrã digital, microfone com cancelamento de ruído, bateria longa..." required></textarea>
    <label>🔄 O que queres em troca?</label><input name="want" placeholder="Ex: Troco por telefone Samsung ou vendo">
    <label>📍 Localização</label><input name="location" value="Matola - Maputo">
    <label>📱 Teu WhatsApp (ex: 840000000)</label><input name="whatsapp" placeholder="840000000">
    <label>📸 Fotos - Escolhe até 4 fotos da tua galeria</label>
    <input type="file" name="photos" accept="image/*" multiple>
    <small>A primeira foto vai ser a principal. Clica nas outras para ver maior.</small><br><br>
    <label>Ou cola links de fotos (opcional)</label>
    <input name="link1" placeholder="Link Foto 1"><input name="link2" placeholder="Link Foto 2">
    <input name="link3" placeholder="Link Foto 3"><input name="link4" placeholder="Link Foto 4">
    <button class="btn">✅ PUBLICAR TROCA</button></form></div></div>"""

# ========== PÁGINA ADMIN - DIFERENTE, COM TODOS OS NÚMEROS ==========
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") == "admin123":
            session["is_admin"] = True
        else: return "Senha errada!"
    if not session.get("is_admin"):
        return CSS + """<div class="top" style="background:#111"><h1>🔐 ADMIN</h1><p>Só o dono do site</p></div>
        <div class="wrap"><div class="box"><h2>Entra como Admin</h2><form method="post">
        <input name="password" type="password" placeholder="Senha admin"><button class="btn btn-dark">ENTRAR NO PAINEL</button></form></div></div>"""
    d = load()
    users_list = "".join([f"<p>👤 {u['name']} - {u['email']}</p>" for u in d["users"]]) or "<p>Nenhum utilizador ainda</p>"
    trades_list = "".join([f"<p>📦 {t.get('title','')} - {t.get('price','')} MZN - {t.get('owner','')}</p>" for t in d["trades"]]) or "<p>Nenhuma troca ainda</p>"
    return CSS + """<div class="top" style="background:#111"><h1>📊 PAINEL DO DONO</h1><p>Troca Troca - Estatísticas</p></div>
    <div class="wrap">
      <div class="stat-big"><span>👥 PESSOAS QUE VISITARAM O SITE</span><b>""" + str(d['visits']) + """</b><span>visitas totais</span></div>
      <div class="stat-row">
        <div class="box"><b>""" + str(len(d['trades'])) + """</b><span>📦 Produtos / Trocas</span></div>
        <div class="box"><b>""" + str(len(d['users'])) + """</b><span>👤 Pessoas Registadas</span></div>
      </div>
      <div class="box"><h3>👤 Pessoas Registadas</h3>""" + users_list + """</div>
      <div class="box"><h3>📦 Todos os Produtos</h3>""" + trades_list + """</div>
      <div class="box"><center><a href="/">← Voltar para a página principal</a></center></div>
    </div>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
