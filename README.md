<div align="center">
  <h1>💰 DescontoMEN-Bot</h1>
  <p><b>Monitor de Ofertas Inteligente para Telegram (Moda & Perfumaria)</b></p>

  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/Status-Produção-green?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/Deploy-Render-black?style=for-the-badge&logo=render" alt="Deploy">
</div>

<hr>

<h2>🚀 Sobre o Projeto</h2>
<p>
  O <b>DescontoMEN-Bot</b> é uma solução de automação de ponta a ponta desenvolvida para capturar, filtrar e publicar as melhores ofertas do Mercado Livre. O foco principal é a <b>Experiência do Usuário (UX)</b> e a <b>Segurança de Dados</b>.
</p>

<h2>✨ Diferenciais de Usabilidade (v32.0)</h2>
<ul>
  <li><b>Imagens em Ultra HD:</b> Algoritmo que converte miniaturas borradas em fotos originais de alta resolução (1000px).</li>
  <li><b>Cálculo Automático de Desconto:</b> Exibe a porcentagem exata de economia e o valor em Reais economizado.</li>
  <li><b>Botões de Compra (Inline Keyboards):</b> Botões interativos diretamente no Telegram para aumentar a taxa de cliques.</li>
  <li><b>Limpeza de Dados Pro:</b> Filtros via Regex que removem ruídos de títulos (ex: "Frete Grátis", "Original", etc).</li>
</ul>

<h2>🛠️ Stack Tecnológica</h2>
<table width="100%">
  <tr>
    <td width="50%"><b>Web Scraping</b></td>
    <td>Cloudscraper, BeautifulSoup4</td>
  </tr>
  <tr>
    <td><b>Backend & API</b></td>
    <td>Python, Flask (Health Check), Telegram API</td>
  </tr>
  <tr>
    <td><b>Segurança</b></td>
    <td>Variáveis de Ambiente (os.getenv)</td>
  </tr>
  <tr>
    <td><b>Infraestrutura</b></td>
    <td>Render Cloud, GitHub Actions</td>
  </tr>
</table>

<h2>🛡️ Segurança e QA</h2>
<p>
  Como um projeto focado em <b>Quality Assurance</b>, a arquitetura foi desenhada para ser resiliente:
</p>
<blockquote>
  <i>"As chaves de acesso e tokens nunca são expostos no código. Utilizamos o padrão de Variáveis de Ambiente para garantir que o projeto possa ser público sem comprometer a segurança da aplicação."</i>
</blockquote>

<h2>⚙️ Como Configurar no Render</h2>
<p>Este bot não utiliza arquivos de configuração físicos no servidor. Para rodar, adicione as seguintes chaves no painel do Render:</p>
<code>TOKEN_TELEGRAM</code> | <code>CHAT_ID</code> | <code>MEU_TAG_AFILIADO</code> | <code>MEU_TOOL_ID</code>

<hr>

<div align="center">
  <p>Desenvolvido com ☕ por <b>Pablo Lima (PabloCoder1)</b></p>
  <a href="https://www.linkedin.com/in/pablo-lima-aaba02269/">
    <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
  </a>
</div>
