// Preencha com sua chave da YouTube Data API v3 e recarregue a página.
const CHAVE_API = "";
const QUANTIDADE_POR_PAGINA = 12;

const canais = [
    { nome: "Unoesc", handle: "@unoescoficial" },
    { nome: "Google for Developers", handle: "@GoogleDevelopers" },
    { nome: "NASA", handle: "@NASA" }
];

const selectCanal = document.querySelector("#canal");
const campoPesquisa = document.querySelector("#pesquisa");
const areaVideos = document.querySelector("#videos");
const infoCanal = document.querySelector("#infoCanal");
const loading = document.querySelector("#loading");
const mensagem = document.querySelector("#mensagem");
const botaoCarregarMais = document.querySelector("#carregarMais");
const modalVideo = document.querySelector("#modalVideo");
const playerVideo = document.querySelector("#playerVideo");
const fecharModal = document.querySelector("#fecharModal");

let playlistUploads = null;
let proximaPagina = null;
let videosCarregados = [];
let requisicaoAtual = null;

document.addEventListener("DOMContentLoaded", iniciar);

async function iniciar() {
    carregarListaCanais();

    selectCanal.addEventListener("change", carregarCanalSelecionado);
    campoPesquisa.addEventListener("input", filtrarVideos);
    botaoCarregarMais.addEventListener("click", carregarMaisVideos);
    fecharModal.addEventListener("click", fecharVideo);

    modalVideo.addEventListener("click", evento => {
        if (evento.target === modalVideo) fecharVideo();
    });

    modalVideo.addEventListener("close", () => {
        playerVideo.src = "";
    });

    await carregarCanalSelecionado();
}

function carregarListaCanais() {
    canais.forEach((canal, indice) => {
        const option = document.createElement("option");
        option.value = indice;
        option.textContent = canal.nome;
        selectCanal.appendChild(option);
    });
}

async function carregarCanalSelecionado() {
    requisicaoAtual?.abort();
    const requisicao = new AbortController();
    requisicaoAtual = requisicao;
    limparEstado();
    if (!CHAVE_API.trim()) {
        mostrarLoading(false);
        mostrarMensagem('Chave de API pendente. Preencha CHAVE_API em assets/js/script.js e recarregue a página.', 'aviso');
        return;
    }
    mostrarLoading(true);

    try {
        const canal = canais[selectCanal.value];
        const dadosCanal = await buscarCanal(canal.handle, requisicao.signal);

        if (!dadosCanal) {
            mostrarMensagem("Canal não encontrado.", "aviso");
            return;
        }

        infoCanal.innerHTML = `
            <h2>${escaparHTML(dadosCanal.snippet.title)}</h2>
            <p>Últimos vídeos publicados</p>
        `;

        playlistUploads = dadosCanal.contentDetails.relatedPlaylists.uploads;
        await carregarVideos(requisicao.signal);
    } catch (erro) {
        if (erro.name === 'AbortError') return;
        console.error(erro);
        mostrarMensagem("Não foi possível carregar os dados do YouTube.", "erro");
    } finally {
        if (requisicaoAtual === requisicao) mostrarLoading(false);
    }
}

async function buscarCanal(handle, signal) {
    const parametros = new URLSearchParams({
        part: "snippet,contentDetails",
        forHandle: handle,
        key: CHAVE_API
    });

    const url = `https://www.googleapis.com/youtube/v3/channels?${parametros}`;
    const resposta = await fetch(url, { signal });

    if (!resposta.ok)
        throw new Error(`Erro HTTP: ${resposta.status}`);

    const dados = await resposta.json();
    return dados.items?.[0] ?? null;
}

async function carregarVideos(signal) {
    esconderMensagem();

    const parametros = new URLSearchParams({
        part: "snippet",
        playlistId: playlistUploads,
        maxResults: QUANTIDADE_POR_PAGINA,
        key: CHAVE_API
    });

    if (proximaPagina)
        parametros.set("pageToken", proximaPagina);

    const url = `https://www.googleapis.com/youtube/v3/playlistItems?${parametros}`;
    const resposta = await fetch(url, { signal });

    if (!resposta.ok)
        throw new Error(`Erro HTTP: ${resposta.status}`);

    const dados = await resposta.json();

    proximaPagina = dados.nextPageToken ?? null;

    const novosVideos = (dados.items ?? []).filter(
        video => video.snippet?.resourceId?.videoId
    );

    videosCarregados.push(...novosVideos);

    atualizarBotaoCarregarMais();
    filtrarVideos();
}

async function carregarMaisVideos() {
    if (!proximaPagina || botaoCarregarMais.disabled) return;
    const requisicao = requisicaoAtual;

    botaoCarregarMais.disabled = true;
    botaoCarregarMais.textContent = "Carregando...";

    try {
        await carregarVideos(requisicao.signal);
    } catch (erro) {
        if (erro.name === 'AbortError') return;
        console.error(erro);
        mostrarMensagem("Não foi possível carregar mais vídeos.", "erro");
    } finally {
        if (requisicaoAtual === requisicao) {
            botaoCarregarMais.disabled = false;
            botaoCarregarMais.textContent = "Carregar mais";
        }
    }
}

function filtrarVideos() {
    if (!CHAVE_API.trim()) return;
    const termo = campoPesquisa.value.trim().toLowerCase();

    const encontrados = videosCarregados.filter(video => {
        const titulo = video.snippet.title.toLowerCase();
        const descricao = (video.snippet.description ?? "").toLowerCase();

        return titulo.includes(termo) || descricao.includes(termo);
    });

    mostrarVideos(encontrados);
}

function mostrarVideos(videos) {
    areaVideos.innerHTML = "";

    if (!videos.length) {
        mostrarMensagem("Nenhum vídeo encontrado.", "aviso");
        return;
    }

    esconderMensagem();

    videos.forEach(video => {
        const titulo = video.snippet.title;
        const descricao = video.snippet.description ?? "";
        const imagem = obterThumbnail(video);
        const videoId = video.snippet.resourceId.videoId;
        const data = formatarData(video.snippet.publishedAt);

        const artigo = document.createElement("article");
        artigo.className = "video-card";

        artigo.innerHTML = `
            <div class="video-thumb">
                <img src="${escaparHTML(imagem)}"
                    alt="Miniatura do vídeo ${escaparHTML(titulo)}"
                    loading="lazy">

                <div class="video-overlay">
                    <p>${escaparHTML(limitarTexto(descricao, 140))}</p>
                </div>
            </div>

            <div class="video-conteudo">
                <h3>${escaparHTML(titulo)}</h3>
                <span class="video-data">Publicado em ${data}</span>

                <div class="video-acoes">
                    <button class="assistir">Assistir</button>

                    <a class="abrir-youtube"
                    href="https://www.youtube.com/watch?v=${encodeURIComponent(videoId)}"
                    target="_blank"
                    rel="noopener noreferrer">
                        Abrir no YouTube
                    </a>
                </div>
            </div>
        `;

        artigo.querySelector(".assistir").addEventListener("click", () => abrirVideo(videoId));
        artigo.querySelector(".video-thumb").addEventListener("click", () => {
            abrirVideo(videoId);
        });

        areaVideos.appendChild(artigo);
    });
}

function obterThumbnail(video) {
    const thumbnails = video.snippet.thumbnails ?? {};

    return thumbnails.maxres?.url ??
           thumbnails.standard?.url ??
           thumbnails.high?.url ??
           thumbnails.medium?.url ??
           thumbnails.default?.url ??
           "";
}

function formatarData(data) {
    return new Intl.DateTimeFormat("pt-BR", {
        day: "2-digit",
        month: "long",
        year: "numeric"
    }).format(new Date(data));
}

function limitarTexto(texto, limite) {
    return texto.length <= limite ?
        texto :
        texto.substring(0, limite) + "...";
}

function escaparHTML(texto) {
    return String(texto)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function abrirVideo(videoId) {
    playerVideo.src = `https://www.youtube.com/embed/${encodeURIComponent(videoId)}?autoplay=1`;
    modalVideo.showModal();
}

function fecharVideo() {
    modalVideo.close();
}

function mostrarLoading(exibir) {
    loading.classList.toggle("oculto", !exibir);
}

function mostrarMensagem(texto, tipo = "aviso") {
    mensagem.textContent = texto;
    mensagem.className = `mensagem ${tipo}`;
}

function esconderMensagem() {
    mensagem.className = "mensagem oculto";
}

function atualizarBotaoCarregarMais() {
    botaoCarregarMais.classList.toggle("oculto", !proximaPagina);
}

function limparEstado() {
    playlistUploads = null;
    proximaPagina = null;
    videosCarregados = [];
    areaVideos.innerHTML = "";
    infoCanal.innerHTML = "";
    campoPesquisa.value = "";
    botaoCarregarMais.disabled = false;
    botaoCarregarMais.textContent = "Carregar mais";
    esconderMensagem();
    atualizarBotaoCarregarMais();
}
