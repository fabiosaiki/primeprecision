# Prime Precision

Site estático (HTML, CSS e JS puros) da Prime Precision.

## Estrutura

- `index.html`: página inteira
- `assets/logo.png`: logo com fundo transparente
- `assets/hero.jpg`: foto do topo
- `favicon.svg`

## Senha de acesso

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
