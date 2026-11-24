# Prime Precision

Site estático (HTML, CSS e JS puros) da Prime Precision.

## Estrutura

- `index.html`: página inteira
- `assets/logo.png`: logo com fundo transparente (usado só na tela de senha)
- `assets/logo-light.png` e `assets/logo-dark.png`: logo com slogan (preto no tema claro, branco no escuro)
- `assets/hero.jpg`: foto do topo
- `favicon.svg`

## Senha de acesso

**Estado atual: desativada.** Em `protect.mjs`, `GATE_ATIVO = false` deixa o site público, mesmo com SITE_PASSWORD definida na Vercel. Para reativar, troque para `true` e faça um novo deploy.

O site pode abrir só com senha. A página é criptografada no deploy (AES-256), e o navegador a abre quando a senha está certa.

1. Na Vercel, abra o projeto e vá em **Settings > Environment Variables**.
2. Crie a variável **SITE_PASSWORD** com a senha escolhida, nos ambientes Production e Preview.
3. Faça um novo deploy (Deployments > menu do último deploy > Redeploy).

Para trocar a senha, mude o valor da variável e faça um novo deploy. Para deixar o site público, apague a variável e faça um novo deploy. A senha não fica no Git.

Use uma senha longa (12 caracteres ou mais). A página criptografada é pública, então uma senha curta pode ser descoberta por tentativa.

## Publicar

1. Crie um repositório no GitHub e envie esta pasta.
2. Na Vercel, clique em Add New > Project e importe o repositório.
3. Framework Preset: Other. O `vercel.json` já define o build e a pasta de saída.
4. Clique em Deploy. Cada push na branch main publica de novo.

## Domínio

Em Project > Settings > Domains, adicione primeprecision.com.br e aplique no DNS do domínio os registros que a Vercel mostrar.

## Segurança

- `vercel.json` envia cabeçalhos de segurança em todas as páginas (CSP, HSTS, X-Frame-Options, nosniff, Referrer-Policy e Permissions-Policy).
- Se um dia o site carregar algo de outro endereço (novo vídeo, mapa, analytics), inclua esse endereço na `Content-Security-Policy`, senão o navegador bloqueia.
- Não guarde senhas nem chaves no repositório. A senha do site fica só na variável `SITE_PASSWORD` da Vercel.
