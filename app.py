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
*{box-sizing:border-box} body{margin:0;font-family:Arial;background:#f5f5f5;color:#222}
.top{background:#00a651;color:white;padding:18px 10px;text-align:center;width:100%}
.top h1{margin:0;font-size:26px}
.top p{margin:6px 0 0;font-size:13px}
.wrap{padding:0;width:100%;margin:0}
.box{background:white;padding:16px;margin:0 0 8px;width:100%}
input,textarea{width:100%;padding:14px;margin:7px 0;border:1px solid #ddd;border-radius:10px;font-size:15px}
textarea{min-height:100px}
label{font-weight:bold;font-size:14px}
.btn{background:#00a651;color:white;border:none;padding:15px;border-radius:10px;width:100%;font-size:17px;font-weight:bold;cursor:pointer}
.btn-yellow{background:#ffcc00;color:#111}
.btn-whats{background:#25D366}
.btn-dark{background:#111}
.grid{display:flex;flex-wrap:wrap;gap:8px;padding:8px;background:#f5f5f5}
.trade{background:white;width:calc(50% - 4px);border-radius:12px;overflow:hidden;padding-bottom:10px}
.trade img.main{width:100%;aspect-ratio:1/1;object-fit:cover;background:#eee;display:block}
.trade .info{padding:8px}
.trade .title{font-size:13px;line-height:1.3;height:34px;overflow:hidden;display:block;color:#333}
.trade .price{font-size:16px;font-weight:bold;color:#111;margin:6px 0 2px}
.trade .mini-btn{background:#00a651;color:white;border:none;padding:9px;border-radius:8px;width:100%;font-size:13px;font-weight:bold;margin-top:6px}
.thumbs{display:flex;gap:4px;padding:6px}
.thumbs img{width:36px;height:36px;border-radius:6px;object-fit:cover;cursor:pointer;border:1px solid #eee}
.stat-big{background:#00a651;color:white;padding:20px;text-align:center;width:100%}
.stat-big b{font-size:36px;display:block}
.stat-row{display:flex;gap:0;width:100%}
.stat-row .box{flex:1;text-align:center}
.stat-row b{font-size:26px;display:block;color:#00a651}
a{color:#00a651;text-decoration:none;font-weight:bold}
small{color:#777}
h3{padding:0 14px}
</style>
"""
HEADER = """<div class="top"><h1>🔄 TROCA TROCA</h1><p>Troque sem gastar dinheiro • Moçambique 🇲🇿</p></div>"""
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
    h += "<h3>🆕 Últimas Trocas</h3><div class='grid'>"
    for t in trades:
        if q and q not in (t.get("title","")+t.get("desc","")).lower(): continue
        photos = t.get("photos", [])
        main = photos[0] if photos else "https://via.placeholder.com/600x600?text=Sem+Foto"
        thumbs = "".join([f'<img src="{p}" onclick="document.getElementById(\'m{t["id"]}\').src=this.src">' for p in photos])
        h += f"""
        <div class="trade">
          <img class="main" id="m{t['id']}" src="{main}">
          <div class="thumbs">{thumbs}</div>
          <div class="info">
            <span class="title">{t.get('title','')}</span>
            <div class="price">MT {t.get('price','')}</div>
            <small>📍 {t.get('location','Matola')} • 👤 {t.get('owner','')}</small><br>
            <small>🔄 {t.get('want','')}</small>
            <a href="https://wa.me/258{t.get('whatsapp','').replace(' ','').replace('+','')}" target="_blank"><button class="mini-btn">💬 WhatsApp</button></a>
            <a href="/p/{t['id']}"><button class="mini-btn" style="background:#111">👁️ Ver detalhes</button></a>
          </div>
        </div>"""
    if not trades:
        h += "<div class='box'><center>Ainda não há trocas.<br>Seja o primeiro a publicar! 👆</center></div>"
    h += "</div></div>"
    return h
@app.route("/p/<int:tid>")
def detail(tid):
    d = load()
    t = next((x for x in d["trades"] if x["id"]==tid), None)
    if not t: return redirect("/")
    photos = t.get("photos", [])
    main = photos[0] if photos else ""
    thumbs = "".join([f'<img src="{p}" onclick="document.getElementById(\'md\').src=this.src" style="width:70px;height:70px;object-fit:cover;border-radius:8px">' for p in photos])
    return CSS + HEADER + f"""<div class="wrap"><div class="box" style="margin:0">
    <img id="md" src="{main}" style="width:100%;height:auto;display:block;border-radius:12px">
    <div style="display:flex;gap:6px;margin-top:8px">{thumbs}</div>
    <h2>{t.get('title','')}</h2>
    <p style="font-size:22px;font-weight:bold">MT {t.get('price','')}</p>
    <p style="white-space:pre-line;line-height:1.6">{t.get('desc','')}</p>
    <p><b>🔄 Quer em troca:</b> {t.get('want','')}</p>
    <p>👤 {t.get('owner','')} • 📍 {t.get('location','')}</p>
    <a href="https://wa.me/258{t.get('whatsapp','').replace(' ','').replace('+','')}" target="_blank"><button class="btn btn-whats">💬 FALAR NO WHATSAPP</button></a><br><br>
    <center><a href="/">← Voltar</a></center></div></div>"""
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
    <textarea name="desc" placeholder="Ex: Novo na caixa, Bluetooth 6.0, ecrã digital..." required></textarea>
    <label>🔄 O que queres em troca?</label><input name="want" placeholder="Ex: Troco por telefone Samsung ou vendo">
    <label>📍 Localização</label><input name="location" value="Matola - Maputo">
    <label>📱 Teu WhatsApp (ex: 840000000)</label><input name="whatsapp" placeholder="840000000">
    <label>📸 Fotos - Escolhe até 4 fotos da tua galeria</label>
    <input type="file" name="photos" accept="image/*" multiple>
    <small>A primeira foto vai ser a principal.</small><br><br>
    <label>Ou cola links de fotos (opcional)</label>
    <input name="link1" placeholder="Link Foto 1"><input name="link2" placeholder="Link Foto 2">
    <input name="link3" placeholder="Link Foto 3"><input name="link4" placeholder="Link Foto 4">
    <button class="btn">✅ PUBLICAR TROCA</button></form></div></div>"""
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
        <div class="box"><b>""" + str(len(d['trades'])) + """</b><span>📦 Produtos</span></div>
        <div class="box"><b>""" + str(len(d['users'])) + """</b><span>👤 Pessoas</span></div>
      </div>
      <div class="box"><h3>👤 Pessoas Registadas</h3>""" + users_list + """</div>
      <div class="box"><h3>📦 Todos os Produtos</h3>""" + trades_list + """</div>
      <div class="box"><center><a href="/">← Voltar para a página principal</a></center></div>
    </div>"""
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
