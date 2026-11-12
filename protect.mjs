// Gera a pasta dist/ que a Vercel publica.
//  - Sem SITE_PASSWORD: copia o site como está (público).
//  - Com SITE_PASSWORD: criptografa a página inteira (AES-256-GCM, chave derivada da senha com PBKDF2).
//    O navegador pede a senha e só então abre o site. As imagens vão dentro da página criptografada.
//
// Uso local:  SITE_PASSWORD="sua senha" node protect.mjs
// Na Vercel:  defina SITE_PASSWORD em Settings > Environment Variables e faça um novo deploy.

import { readFileSync, writeFileSync, mkdirSync, cpSync, rmSync, existsSync } from 'node:fs';
import { pbkdf2Sync, randomBytes, createCipheriv } from 'node:crypto';

const password = process.env.SITE_PASSWORD || process.argv[2] || '';
const ITER = 300000;

rmSync('dist', { recursive: true, force: true });
mkdirSync('dist', { recursive: true });
for (const f of ['index.html', 'favicon.svg', 'assets']) {
  if (existsSync(f)) cpSync(f, 'dist/' + f, { recursive: true });
}

if (!password) {
  console.log('SITE_PASSWORD não definida: o site ficará público.');
  process.exit(0);
}

const mime = { png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', svg: 'image/svg+xml' };
const dataUri = (path) => `data:${mime[path.split('.').pop()]};base64,${readFileSync(path).toString('base64')}`;

// coloca as imagens dentro da página, para não ficarem públicas em /assets
let html = readFileSync('index.html', 'utf8').replace(/assets\/[\w.-]+\.(?:png|jpe?g|svg)/g, (p) => dataUri(p));

const salt = randomBytes(16);
const iv = randomBytes(12);
const key = pbkdf2Sync(password, salt, ITER, 32, 'sha256');
const cipher = createCipheriv('aes-256-gcm', key, iv);
const enc = Buffer.concat([cipher.update(html, 'utf8'), cipher.final()]);
const payload = {
  s: salt.toString('base64'),
  v: iv.toString('base64'),
  i: ITER,
  c: Buffer.concat([enc, cipher.getAuthTag()]).toString('base64'),
};

const logo = existsSync('assets/logo.png') ? dataUri('assets/logo.png') : '';
const gate = `<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Prime Precision</title>
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<style>
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;background:#0E1114;color:#F1F3F4;font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{position:relative;width:100%;max-width:380px;background:#171B1F;border:1px solid #2A3138;border-top:4px solid #D60210;border-radius:14px;padding:28px}
img{display:block;height:40px;width:auto;margin-bottom:22px}
.lang{width:fit-content;margin:0 0 18px auto;display:flex;gap:2px;border:1px solid #2A3138;border-radius:999px;padding:3px;background:#0E1114}
.lang button{width:auto;font:600 .8rem system-ui,sans-serif;color:#A3ADB5;background:transparent;border:0;border-radius:999px;padding:6px 10px;min-width:36px;cursor:pointer}
.lang button[aria-pressed="true"]{background:#D60210;color:#fff}
.lang button:hover{color:#F1F3F4}
h1{margin:0 0 6px;font-size:1.3rem}
p{margin:0 0 18px;color:#A3ADB5;font-size:.95rem}
label{display:block;font-weight:600;font-size:.9rem;margin-bottom:6px}
input[type=password]{width:100%;font:inherit;color:#F1F3F4;background:#0E1114;border:1px solid #2A3138;border-radius:8px;padding:12px 14px}
input:focus-visible,button:focus-visible{outline:3px solid #D60210;outline-offset:2px}
.rem{display:flex;gap:8px;align-items:center;margin:14px 0;color:#A3ADB5;font-size:.9rem}
button{width:100%;font:600 1rem system-ui,sans-serif;color:#fff;background:#D60210;border:0;border-radius:8px;padding:13px;cursor:pointer}
button:disabled{opacity:.6;cursor:wait}
.err{min-height:1.4em;margin-top:12px;color:#FF7A82;font-size:.9rem}
</style>
</head>
<body>
<main>
  <div class="lang" id="lang" role="group" aria-label="Idioma">
    <button type="button" data-l="pt" aria-label="Português" aria-pressed="true">PT</button>
    <button type="button" data-l="en" aria-label="English" aria-pressed="false">EN</button>
    <button type="button" data-l="de" aria-label="Deutsch" aria-pressed="false">DE</button>
  </div>
  ${logo ? `<img src="${logo}" alt="Prime">` : ''}
  <h1 data-i="title">Acesso restrito</h1>
  <p data-i="sub">Digite a senha para ver o site.</p>
  <form id="f" autocomplete="off">
    <label for="pw" data-i="pw">Senha</label>
    <input id="pw" type="password" autocomplete="current-password" required autofocus>
    <label class="rem" for="rem"><input id="rem" type="checkbox" checked> <span data-i="rem">Lembrar neste aparelho</span></label>
    <button id="go" type="submit" data-i="go">Entrar</button>
    <div class="err" id="err" role="alert"></div>
  </form>
</main>
<script>
var P=${JSON.stringify(payload)};
var K="prime-key";
var TX={
  pt:{title:"Acesso restrito",sub:"Digite a senha para ver o site.",pw:"Senha",rem:"Lembrar neste aparelho",go:"Entrar",bad:"Senha incorreta. Tente de novo.",nosub:"Este navegador não consegue abrir a página protegida. Use um navegador atualizado e o endereço https.",grp:"Idioma"},
  en:{title:"Restricted access",sub:"Enter the password to view the site.",pw:"Password",rem:"Remember on this device",go:"Enter",bad:"Incorrect password. Please try again.",nosub:"This browser cannot open the protected page. Use an up-to-date browser and the https address.",grp:"Language"},
  de:{title:"Zugriff beschränkt",sub:"Geben Sie das Passwort ein, um die Website zu sehen.",pw:"Passwort",rem:"Auf diesem Gerät merken",go:"Anmelden",bad:"Falsches Passwort. Bitte versuchen Sie es erneut.",nosub:"Dieser Browser kann die geschützte Seite nicht öffnen. Verwenden Sie einen aktuellen Browser und die https-Adresse.",grp:"Sprache"}
};
var lang="pt";
function setLang(l,save){
  lang=l;var d=TX[l];
  document.documentElement.lang={pt:"pt-BR",en:"en",de:"de"}[l];
  Array.prototype.forEach.call(document.querySelectorAll("[data-i]"),function(e){e.textContent=d[e.getAttribute("data-i")]});
  document.getElementById("lang").setAttribute("aria-label",d.grp);
  Array.prototype.forEach.call(document.querySelectorAll("#lang button"),function(b){b.setAttribute("aria-pressed",b.getAttribute("data-l")===l?"true":"false")});
  var er=document.getElementById("err");if(er&&er.getAttribute("data-k")){er.textContent=d[er.getAttribute("data-k")]}
  if(save){try{localStorage.setItem("prime-lang",l)}catch(e){}}
}
function startLang(){
  var l="pt";
  try{var s=localStorage.getItem("prime-lang");if(s==="pt"||s==="en"||s==="de")l=s;else{var n=(navigator.language||"pt").slice(0,2).toLowerCase();if(n==="en"||n==="de")l=n}}catch(e){}
  setLang(l,false);
}
function showErr(k){var er=document.getElementById("err");er.setAttribute("data-k",k);er.textContent=TX[lang][k]}
function b64(s){return Uint8Array.from(atob(s),function(c){return c.charCodeAt(0)})}
function open_(html){document.open();document.write(html);document.close()}
async function decryptWith(key){
  var buf=await crypto.subtle.decrypt({name:"AES-GCM",iv:b64(P.v)},key,b64(P.c));
  return new TextDecoder().decode(buf);
}
async function derive(pw){
  var km=await crypto.subtle.importKey("raw",new TextEncoder().encode(pw),"PBKDF2",false,["deriveKey"]);
  return crypto.subtle.deriveKey({name:"PBKDF2",salt:b64(P.s),iterations:P.i,hash:"SHA-256"},km,{name:"AES-GCM",length:256},true,["decrypt"]);
}
(async function(){
  startLang();
  Array.prototype.forEach.call(document.querySelectorAll("#lang button"),function(b){b.addEventListener("click",function(){setLang(b.getAttribute("data-l"),true)})});
  if(!window.crypto||!crypto.subtle){showErr("nosub");return}
  try{var saved=localStorage.getItem(K);if(saved){
    var k=await crypto.subtle.importKey("raw",b64(saved),"AES-GCM",false,["decrypt"]);
    open_(await decryptWith(k));return}}catch(e){try{localStorage.removeItem(K)}catch(_){}}
  document.getElementById("f").addEventListener("submit",async function(e){
    e.preventDefault();
    var go=document.getElementById("go"),err=document.getElementById("err");
    go.disabled=true;err.textContent="";err.removeAttribute("data-k");
    try{
      var key=await derive(document.getElementById("pw").value);
      var html=await decryptWith(key);
      if(document.getElementById("rem").checked){
        try{var raw=new Uint8Array(await crypto.subtle.exportKey("raw",key));
          localStorage.setItem(K,btoa(String.fromCharCode.apply(null,raw)))}catch(_){}}
      open_(html);
    }catch(x){showErr("bad");go.disabled=false;document.getElementById("pw").select()}
  });
})();
</script>
</body>
</html>
`;

writeFileSync('dist/index.html', gate);
rmSync('dist/assets', { recursive: true, force: true });
console.log('Site protegido por senha. Arquivos em dist/.');
