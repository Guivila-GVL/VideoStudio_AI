// ========================================================
// VIDEOSTUDIO AI - CLIENT CONTROLLER (V2.5)
// Capa Genérica (Universo & Biblia de Personajes) +
// Capa Específica (Capítulos, Storyboard & Render)
// ========================================================

document.addEventListener("DOMContentLoaded", () => {
  // Estado Global
  const state = {
    projects: [],
    currentProject: null,
    currentChapterId: null,
    currentChapterOriginType: null,
    currentChapterOriginRef: null,
    currentChapterOrden: 1,
    chapters: [],
    manuscriptDoc: null,
    selectedPageNum: 1,
    selectedSectionIdx: 0,
    scenes: [],
    uploadedDoc: null,
    voices: []
  };

  // Metadatos exhaustivos de técnicas de dibujo y estilos visuales
  const STYLE_METADATA = {
    watercolor: {
      name: "Acuarela y Tinta Poética",
      icon: "🖌️",
      tags: ["🖌️ Aguadas traslúcidas", "📜 Textura papel rugoso", "✒️ Tinta sepia / grafito", "📐 4 Vistas obligatorio"],
      desc: "Técnica pictórica tradicional con pigmentos solubles en agua sobre papel de algodón rugoso. Manchas y veladuras orgánicas, bordes suaves difuminados y contornos caligráficos finos de pluma o grafito. Sin brillos sintéticos ni texturas plásticas 3D.",
      defaultDetails: "Acuarela poética con pigmentos transparentes, aguadas luminosas, contornos sutiles de lápiz y luz solar mediterránea que evoca la calidez del campo andaluz.",
      coherenceNote: "Tanto los Personajes (Hojas de Modelo de 4 Vistas estándar Darbón) como los Escenarios Clave se generarán con esta técnica pictórica artesanal para mantener unidad estética en toda la obra."
    },
    ghibli_anime: {
      name: "Studio Ghibli Tradicional",
      icon: "🍃",
      tags: ["🍃 Pintado a mano", "🎨 Fondos témpera / gouache", "⛅ Cielos volumétricos", "📐 4 Vistas obligatorio"],
      desc: "Estilo artesanal inspirado en las obras de Hayao Miyazaki. Personajes con líneas cel limpias y expresivas, colores planos vivos con sombras suaves; escenarios pintados en témpera gouache rica en vegetación, nubes esponjosas y nostalgia.",
      defaultDetails: "Estética Studio Ghibli tradicional, fondos artesanales en témpera gouache, cielos con cúmulos esponjosos, colores cálidos nostálgicos y líneas de animación fluidas.",
      coherenceNote: "Personajes y escenarios comparten la paleta viva y poética de la animación cel clásica japonesa, con fondos pictóricos llenos de vida natural."
    },
    storybook_kids: {
      name: "Cuento Infantil Ilustrado",
      icon: "🧸",
      tags: ["🧸 Formas redondeadas", "🌈 Paleta viva y dulce", "📖 Textura editorial", "📐 4 Vistas obligatorio"],
      desc: "Ilustración editorial infantil entrañable. Proporciones suaves, personajes amables y tiernos, paleta cromática pastel saturada muy atractiva, iluminación difusa y acabados de libro ilustrado de alta gama.",
      defaultDetails: "Ilustración de cuento infantil clásico con líneas tiernas redondeadas, paleta viva y alegre, iluminación difusa sin sombras duras y textura de libro ilustrado.",
      coherenceNote: "Garantiza un tono inocente y cálido tanto en la caracterización de los personajes como en la arquitectura y naturaleza de los escenarios."
    },
    pixar_3d: {
      name: "Animación 3D tipo Pixar / Disney",
      icon: "✨",
      tags: ["✨ Render volumétrico", "💡 Subsurface scattering", "👁️ Ojos hiper-expresivos", "📐 4 Vistas obligatorio"],
      desc: "Modelado CGI volumétrico con sombreado de dispersión bajo la superficie (piel suave, pelaje detallado), iluminación cinemática de tres puntos, texturas ricas estilizadas y expresiones faciales sumamente carismáticas.",
      defaultDetails: "Render CGI 3D estilo Pixar Disney, iluminación volumétrica suave, dispersión bajo la superficie para piel y pelaje, texturas estilizadas 4K.",
      coherenceNote: "Todos los personajes tendrán el volumen y la suavidad de un largometraje animado moderno, integrándose en escenarios con iluminación global 3D."
    },
    cinematic: {
      name: "Cinematográfico 4K (35mm)",
      icon: "🎬",
      tags: ["🎬 Lente 35mm anamórfica", "🌗 Claroscuro dramático", "🎞️ Bokeh de cámara", "📐 4 Vistas obligatorio"],
      desc: "Fotografía de cine de alta gama. Profundidad de campo reducida con fondos desenfocados (bokeh), sombras dramáticas, etalonaje cinematográfico profesional y texturas fotorrealistas de alta definición.",
      defaultDetails: "Fotografía cinematográfica 35mm con iluminación de contraste dramático, profundidad de campo reducida, etalonaje cinematográfico profesional y grano sutil.",
      coherenceNote: "Personajes y escenarios se tratarán como planos de una producción cinematográfica de imagen real con iluminación óptica natural y sombras volumétricas."
    },
    anime: {
      name: "Anime Makoto Shinkai",
      icon: "🎨",
      tags: ["☀️ Luz solar radiante", "☁️ Cielos hiperdetallados", "✨ Destellos de lente", "📐 4 Vistas obligatorio"],
      desc: "Anime cinematográfico con cielos colosales, múltiples capas de nubes crepusculares, destellos prismáticos de lente, reflejos hiperrealistas en superficies y líneas de animación digital impecables.",
      defaultDetails: "Estética anime Makoto Shinkai, cielos crepusculares vibrantes, reflejos de lente fotográficos, contrastes luminosos intensos y detalle minucioso.",
      coherenceNote: "Los personajes adquieren estética de anime moderno con ojos luminosos y cabellos dinámicos, en escenarios con contrastes celestes asombrosos."
    },
    noir_bw: {
      name: "Blanco y Negro Film Noir",
      icon: "🕵️‍♂️",
      tags: ["🖤 Monocromo puro", "🔦 Claroscuro alto contraste", "🌫️ Sombras venecianas", "📐 4 Vistas obligatorio"],
      desc: "Blanco y negro estricto con sombras venecianas profundas, haces de luz puntuales, niebla y atmósfera de suspense de los años 40-50.",
      defaultDetails: "Fotografía film noir monocromática de alto contraste, iluminación claroscuro tipo Rembrandt, sombras alargadas y grano analógico 35mm.",
      coherenceNote: "Toda la serie renuncia al color para apoyarse en el juego magistral de luces directas, siluetas y misterio tanto en personajes como en decorados."
    },
    comic: {
      name: "Cómic / Novela Gráfica",
      icon: "💥",
      tags: ["💥 Entintado a plumilla", "📐 Tramas mecánicas", "🔥 Colores de imprenta", "📐 4 Vistas obligatorio"],
      desc: "Trazos firmes de entintado con pincel y plumilla, tramas mecánicas (halftones), colores planos saturados y sombras en negro pleno.",
      defaultDetails: "Novela gráfica moderna con entintado vigoroso a plumilla, sombras con tramas mecánicas, colores dinámicos saturados y contornos rotundos.",
      coherenceNote: "Las hojas de modelo de personajes y las viñetas escénicas parecerán páginas de una novela gráfica de autor europeo o americano."
    },
    dark_fantasy: {
      name: "Dark Fantasy Épico",
      icon: "🐉",
      tags: ["🐉 Atmósfera grimdark", "🛡️ Texturas desgastadas", "⚡ Niebla y claroscuro", "📐 4 Vistas obligatorio"],
      desc: "Atmósfera medieval oscura y decadente. Iluminación tenue de antorchas y niebla, armaduras y ropajes desgastados, tonos desaturados con toques de fuego o magia.",
      defaultDetails: "Dark fantasy medieval hiperdetallado, atmósfera grimdark con niebla y ceniza, iluminación de antorchas y render Unreal Engine 5.",
      coherenceNote: "Personajes rudos y sombríos en entornos góticos o ruinas antiguas con texturas densas e iluminación lúgubre."
    },
    cyberpunk: {
      name: "Cyberpunk Neón",
      icon: "⚡",
      tags: ["⚡ Neones cian y magenta", "🌧️ Reflejos en suelo mojado", "🏙️ Distopía retrofuturista", "📐 4 Vistas obligatorio"],
      desc: "Escenario nocturno con lluvia incesante, reflejos brillantes de neones en charcos, cables expuestos, tecnología sucia y contrastes extremos.",
      defaultDetails: "Estética cyberpunk con neones cian y magenta, calles lluviosas con reflejos volumétricos, niebla sintética y arquitectura retrofuturista.",
      coherenceNote: "Personajes con indumentaria técnica, implantes o complementos luminosos en escenarios hiperdensos de rascacielos y lluvia ácida."
    },
    vintage: {
      name: "Fotografía Retro Analógica 70s",
      icon: "📷",
      tags: ["📷 Película Kodak Portra", "🎞️ Grano analógico cálido", "🍂 Tonos ámbar y sepia", "📐 4 Vistas obligatorio"],
      desc: "Película química analógica con grano pronunciado, esquinas ligeramente viñeteadas, colores ligeramente desvaídos en tonos sepia/ámbar.",
      defaultDetails: "Fotografía analógica de los años 70 en película Kodak Portra 400, tonos ámbar cálidos, grano orgánico pronunciado y suave viñeteado óptico.",
      coherenceNote: "Toda la producción respirará la autenticidad y nostalgia del celuloide clásico con grano natural y colores templados."
    }
  };

  // Nombres legibles de estilos
  const styleNames = Object.fromEntries(
    Object.entries(STYLE_METADATA).map(([k, v]) => [k, `${v.icon} ${v.name}`])
  );

  // ========================================================
  // ELEMENTOS DOM
  // ========================================================
  const projectSelect = document.getElementById("project-select");
  const btnOpenProjectsHub = document.getElementById("btn-open-projects-hub");
  const btnCreateProjectModal = document.getElementById("btn-create-project-modal");
  const btnOpenSettings = document.getElementById("btn-open-settings");
  const btnOpenHistory = document.getElementById("btn-open-history");

  // Navegación de Capas
  const tabNavGeneric = document.getElementById("tab-nav-generic");
  const tabNavSpecific = document.getElementById("tab-nav-specific");
  const viewGeneric = document.getElementById("view-generic");
  const viewSpecific = document.getElementById("view-specific");
  const btnGoToChapters = document.getElementById("btn-go-to-chapters");
  const btnSwitchToGeneric = document.getElementById("btn-switch-to-generic");

  // Elementos Capa Genérica y Manuscrito
  const savedBookCard = document.getElementById("saved-book-card");
  const savedBookFilename = document.getElementById("saved-book-filename");
  const savedBookPath = document.getElementById("saved-book-path");
  const savedBookMeta = document.getElementById("saved-book-meta");
  const btnLoadChaptersToSpecific = document.getElementById("btn-load-chapters-to-specific");
  const btnToggleReplaceBook = document.getElementById("btn-toggle-replace-book");
  const uploadBookContainer = document.getElementById("upload-book-container");

  const dropZoneBook = document.getElementById("drop-zone-book");
  const fileInputBook = document.getElementById("file-input-book");
  const bookSampleText = document.getElementById("book-sample-text");
  const bookWordsCount = document.getElementById("book-words-count");
  const bookDocInfo = document.getElementById("book-doc-info");
  const bookDocFilename = document.getElementById("book-doc-filename");
  const bookDocStats = document.getElementById("book-doc-stats");
  const btnAiAnalyzeBook = document.getElementById("btn-ai-analyze-book");
  const btnAnalyzeUploadedDoc = document.getElementById("btn-analyze-uploaded-doc");

  const univTitle = document.getElementById("univ-title");
  const univAudience = document.getElementById("univ-audience");
  const univAmbient = document.getElementById("univ-ambient");
  const univVoice = document.getElementById("univ-voice");
  const univStyle = document.getElementById("univ-style");
  const univStyleDetails = document.getElementById("univ-style-details");
  const univImageEngine = document.getElementById("univ-image-engine");
  const univRecurrentChars = document.getElementById("univ-recurrent-chars");

  const styleImplicationsBanner = document.getElementById("style-implications-banner");
  const styleImplicationsIcon = document.getElementById("style-implications-icon");
  const styleImplicationsTitle = document.getElementById("style-implications-title");
  const styleImplicationsTags = document.getElementById("style-implications-tags");
  const styleImplicationsDesc = document.getElementById("style-implications-desc");
  const btnSyncStyleToAll = document.getElementById("btn-sync-style-to-all");

  const charactersCardsGrid = document.getElementById("characters-cards-grid");
  const btnAddCharacterCard = document.getElementById("btn-add-character-card");
  const environmentsCardsGrid = document.getElementById("environments-cards-grid");
  const btnAddEnvironmentCard = document.getElementById("btn-add-environment-card");
  const btnSaveUniverse = document.getElementById("btn-save-universe");

  // Elementos Sección 5: Dirección de Narración y Casting de Voz
  const narratorName = document.getElementById("narrator-name");
  const narratorGender = document.getElementById("narrator-gender");
  const narratorAge = document.getElementById("narrator-age");
  const narratorAgeBracket = document.getElementById("narrator-age-bracket");
  const narratorTone = document.getElementById("narrator-tone");
  const narratorJustification = document.getElementById("narrator-justification");
  const narratorVoiceSelect = document.getElementById("narrator-voice-select");
  const selectedVoiceIcon = document.getElementById("selected-voice-icon");
  const selectedVoiceName = document.getElementById("selected-voice-name");
  const selectedVoiceTags = document.getElementById("selected-voice-tags");
  const selectedVoiceDesc = document.getElementById("selected-voice-desc");
  const narratorSampleText = document.getElementById("narrator-sample-text");
  const btnResetSampleText = document.getElementById("btn-reset-sample-text");
  const btnTestNarratorVoice = document.getElementById("btn-test-narrator-voice");
  const voiceTestStatus = document.getElementById("voice-test-status");
  const audioAuditionPlayerCard = document.getElementById("audio-audition-player-card");
  const playerVoiceTitle = document.getElementById("player-voice-title");
  const playerDurationBadge = document.getElementById("player-duration-badge");
  const narratorAudioElement = document.getElementById("narrator-audio-element");
  const btnAiRecommendNarrator = document.getElementById("btn-ai-recommend-narrator");

  // Elementos Capa Específica: Árbol de Capítulos
  const chaptersTreeSidebar = document.getElementById("chapters-tree-sidebar");
  const chaptersTreeList = document.getElementById("chapters-tree-list");
  const treeChaptersCounter = document.getElementById("tree-chapters-counter");
  const btnTreeNewChapter = document.getElementById("btn-tree-new-chapter");
  const btnTreeImportDoc = document.getElementById("btn-tree-import-doc");
  const treeSearchInput = document.getElementById("tree-search-input");
  const btnTreeRefresh = document.getElementById("btn-tree-refresh");

  // Elementos Capa Específica: Workspace y Selector del Manuscrito
  const miniBannerTitle = document.getElementById("mini-banner-title");
  const miniBannerAudience = document.getElementById("mini-banner-audience");
  const miniBannerStyle = document.getElementById("mini-banner-style");
  const miniBannerCharsCount = document.getElementById("mini-banner-chars-count");
  const miniBannerEnvsCount = document.getElementById("mini-banner-envs-count");

  const currentChapterHeading = document.getElementById("current-chapter-heading");
  const currentChapterOriginPill = document.getElementById("current-chapter-origin-pill");

  const tabSrcPage = document.getElementById("tab-src-page");
  const tabSrcChapter = document.getElementById("tab-src-chapter");
  const tabSrcManual = document.getElementById("tab-src-manual");
  const sourcePagesCount = document.getElementById("source-pages-count");
  const sourceChaptersCount = document.getElementById("source-chapters-count");

  const panelSourcePage = document.getElementById("panel-source-page");
  const selectManuscriptPage = document.getElementById("select-manuscript-page");
  const btnPrevPage = document.getElementById("btn-prev-page");
  const btnNextPage = document.getElementById("btn-next-page");
  const btnAssignPageToChapter = document.getElementById("btn-assign-page-to-chapter");
  const btnCreateChapterFromPage = document.getElementById("btn-create-chapter-from-page");
  const pagePreviewBadge = document.getElementById("page-preview-badge");
  const pagePreviewStats = document.getElementById("page-preview-stats");
  const pagePreviewText = document.getElementById("page-preview-text");

  const panelSourceChapter = document.getElementById("panel-source-chapter");
  const selectManuscriptSection = document.getElementById("select-manuscript-section");
  const btnAssignSectionToChapter = document.getElementById("btn-assign-section-to-chapter");
  const btnCreateChapterFromSection = document.getElementById("btn-create-chapter-from-section");
  const sectionPreviewBadge = document.getElementById("section-preview-badge");
  const sectionPreviewStats = document.getElementById("section-preview-stats");
  const sectionPreviewText = document.getElementById("section-preview-text");

  const rawChapterText = document.getElementById("raw-chapter-text");
  const chapterWordsCounter = document.getElementById("chapter-words-counter");
  const chapterTitleInput = document.getElementById("chapter-title-input");
  const scenesCountSelect = document.getElementById("scenes-count");
  const btnGenerateStoryboard = document.getElementById("btn-generate-storyboard");
  const btnQuickSaveChapter = document.getElementById("btn-quick-save-chapter");
  const btnDeleteActiveChapter = document.getElementById("btn-delete-active-chapter");

  // Storyboard y Render
  const storyboardContainer = document.getElementById("storyboard-container");
  const storyboardTitle = document.getElementById("storyboard-title");
  const scenesGrid = document.getElementById("scenes-grid");
  const btnGenerateAllAudio = document.getElementById("btn-generate-all-audio");
  const btnGenerateAllImages = document.getElementById("btn-generate-all-images");
  const btnAnimateAllScenes = document.getElementById("btn-animate-all-scenes");
  const btnAddScene = document.getElementById("btn-add-scene");
  const btnSaveChapterDraft = document.getElementById("btn-save-chapter-draft");
  const btnRenderVideo = document.getElementById("btn-render-video");

  const chkKenBurns = document.getElementById("chk-kenburns");
  const chkSubtitles = document.getElementById("chk-subtitles");
  const renderProgress = document.getElementById("render-progress");
  const progressText = document.getElementById("progress-text");

  // Phone Mockup
  const phoneEmpty = document.getElementById("phone-empty");
  const phoneVideoContainer = document.getElementById("phone-video-container");
  const finalVideoPlayer = document.getElementById("final-video-player");
  const phoneProjectTag = document.getElementById("phone-project-tag");
  const phoneCaption = document.getElementById("phone-caption");
  const videoMetaCard = document.getElementById("video-meta-card");
  const metaDuration = document.getElementById("meta-duration");
  const metaSize = document.getElementById("meta-size");
  const metaScenes = document.getElementById("meta-scenes");
  const btnDownloadVideo = document.getElementById("btn-download-video");

  // Modal Importación en Lote
  const modalBatchImport = document.getElementById("modal-batch-import");
  const optImportPages = document.getElementById("opt-import-pages");
  const optImportChapters = document.getElementById("opt-import-chapters");
  const badgeImportPagesCount = document.getElementById("badge-import-pages-count");
  const badgeImportChaptersCount = document.getElementById("badge-import-chapters-count");
  const btnConfirmBatchImport = document.getElementById("btn-confirm-batch-import");
  let selectedBatchImportMode = "pages";

  // Modales
  const modalProjectsHub = document.getElementById("modal-projects-hub");
  const projectsHubGrid = document.getElementById("projects-hub-grid");
  const hubProjectsCount = document.getElementById("hub-projects-count");
  const btnHubNewProject = document.getElementById("btn-hub-new-project");

  const modalProjectCreate = document.getElementById("modal-project-create");
  const newProjTitle = document.getElementById("new-proj-title");
  const newProjDesc = document.getElementById("new-proj-desc");
  const btnConfirmCreateProject = document.getElementById("btn-confirm-create-project");

  const modalSettings = document.getElementById("modal-settings");
  const settingOpenai = document.getElementById("setting-openai");
  const settingFal = document.getElementById("setting-fal");
  const settingEleven = document.getElementById("setting-eleven");
  const settingPollinations = document.getElementById("setting-pollinations");
  const settingGemini = document.getElementById("setting-gemini");
  const btnSaveSettings = document.getElementById("btn-save-settings");

  const modalHistory = document.getElementById("modal-history");
  const historyGrid = document.getElementById("history-grid");

  // Notificaciones Toast
  function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon = type === "success" ? "✅" : type === "error" ? "❌" : "ℹ️";
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // ========================================================
  // CONTROL DE LA CASILLA GLOBAL DE ESTADO DEL SISTEMA
  // ========================================================
  let _statusTimeout = null;
  function setSystemStatus(stateType, title, message) {
    const card = document.getElementById("system-status-card");
    const badge = document.getElementById("status-indicator-badge");
    const tag = document.getElementById("status-tag");
    const primaryText = document.getElementById("status-primary-text");
    const secondaryText = document.getElementById("status-secondary-text");
    const timeText = document.getElementById("status-time");
    const spinner = document.getElementById("status-spinner-box");

    if (!badge) return;

    if (_statusTimeout) {
      clearTimeout(_statusTimeout);
      _statusTimeout = null;
    }

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    // Resetear clases
    if (card) card.className = "system-status-card";
    badge.className = "status-indicator-badge header-status-pill";

    if (stateType === "busy") {
      if (card) card.classList.add("status-busy");
      badge.classList.add("busy");
      badge.title = title || "Procesando...";
      if (tag) tag.textContent = "PROCESANDO";
      if (spinner) spinner.style.display = "flex";
      if (primaryText) primaryText.textContent = title || "Procesando...";
      if (secondaryText) secondaryText.textContent = message || "La Inteligencia Artificial está generando los contenidos...";
      if (timeText) timeText.textContent = timeStr;
    } else if (stateType === "healing") {
      if (card) card.classList.add("status-healing");
      badge.classList.add("healing");
      badge.title = title || "Corrigiendo...";
      if (tag) tag.textContent = "CORRIGIENDO";
      if (spinner) spinner.style.display = "flex";
      if (primaryText) primaryText.textContent = title || "Corrigiendo incoherencias...";
      if (secondaryText) secondaryText.textContent = message || "Regenerando elementos con IA para garantizar el estándar...";
      if (timeText) timeText.textContent = timeStr;
    } else if (stateType === "success") {
      if (card) card.classList.add("status-success");
      badge.classList.add("success");
      badge.title = title || "Completado";
      if (tag) tag.textContent = "LISTO";
      if (spinner) spinner.style.display = "none";
      if (primaryText) primaryText.textContent = title || "Operación finalizada";
      if (secondaryText) secondaryText.textContent = message || "Listo.";
      if (timeText) timeText.textContent = timeStr;

      _statusTimeout = setTimeout(() => {
        setSystemStatus("idle");
      }, 7000);
    } else if (stateType === "error") {
      if (card) card.classList.add("status-error");
      badge.classList.add("error");
      badge.title = title || "Error";
      if (tag) tag.textContent = "ERROR";
      if (spinner) spinner.style.display = "none";
      if (primaryText) primaryText.textContent = title || "Error en la operación";
      if (secondaryText) secondaryText.textContent = message || "Ha ocurrido un error al procesar la solicitud.";
      if (timeText) timeText.textContent = timeStr;
    } else {
      // idle
      badge.title = "En espera";
      if (tag) tag.textContent = "EN ESPERA";
      if (spinner) spinner.style.display = "none";
      if (primaryText) primaryText.textContent = title || "Listo para recibir órdenes";
      if (secondaryText) secondaryText.textContent = message || "En espera.";
      if (timeText) timeText.textContent = "";
    }
  }
  window.setSystemStatus = setSystemStatus;

  // ========================================================
  // 1. INICIALIZACIÓN
  // ========================================================
  async function init() {
    try {
      // Estado de APIs
      await refreshApiStatus();

      // Cargar lista de voces
      const vRes = await fetch("/api/voices");
      state.voices = await vRes.json();
      populateVoices(state.voices);

      // Cargar proyectos existentes
      await loadProjects();

      // Configurar eventos modales
      setupModalClosers();

    } catch (e) {
      console.error("Error inicializando VideoStudio AI:", e);
    }
  }

  function populateVoices(voices) {
    state.voicesCatalog = voices;

    // 1. Dropdown Punto 2
    if (univVoice) {
      univVoice.innerHTML = "";
      voices.forEach(v => {
        const opt = document.createElement("option");
        opt.value = v.id;
        opt.textContent = v.name;
        univVoice.appendChild(opt);
      });
    }

    // 2. Dropdown Categorizado Punto 5
    if (narratorVoiceSelect) {
      narratorVoiceSelect.innerHTML = "";

      const groups = [
        { label: "🇪🇸 Voces Nativas en Español (España Peninsular - Sin Acento Inglés)", filter: v => v.category === "espanol_nativo" || (v.tags && v.tags.some(t => t.includes("España") || t.includes("Español"))) },
        { label: "🌟 Narradores Juveniles & Adolescentes Multilingües", filter: v => v.category === "juvenil" || v.age_group === "joven" },
        { label: "📖 Cuentacuentos & Narradores Clásicos", filter: v => v.category === "cuentacuentos" },
        { label: "🎭 Voces Dramáticas & Solemnes", filter: v => v.category === "dramatico" },
        { label: "🌸 Voces Femeninas & Cuentos", filter: v => v.category === "femenino" || v.gender === "femenino" },
        { label: "⚡ Voces Neutras, Fallback & Otras", filter: v => v.category === "neutro" || v.category === "gratuito" || v.category === "elevenlabs_custom" }
      ];

      const addedIds = new Set();
      groups.forEach(g => {
        const matching = voices.filter(v => g.filter(v) && !addedIds.has(v.id));
        if (matching.length > 0) {
          const optGroup = document.createElement("optgroup");
          optGroup.label = g.label;
          matching.forEach(v => {
            addedIds.add(v.id);
            const opt = document.createElement("option");
            opt.value = v.id;
            opt.textContent = `${v.name} • ${v.tags ? v.tags.join(" | ") : ""}`;
            optGroup.appendChild(opt);
          });
          narratorVoiceSelect.appendChild(optGroup);
        }
      });

      const remaining = voices.filter(v => !addedIds.has(v.id));
      if (remaining.length > 0) {
        const optGroup = document.createElement("optgroup");
        optGroup.label = "Otras Voces";
        remaining.forEach(v => {
          const opt = document.createElement("option");
          opt.value = v.id;
          opt.textContent = v.name;
          optGroup.appendChild(opt);
        });
        narratorVoiceSelect.appendChild(optGroup);
      }
    }
  }

  function updateSelectedVoiceCard(voiceId) {
    if (!voiceId || !state.voicesCatalog) return;
    const v = state.voicesCatalog.find(x => x.id === voiceId || x.voice_id === voiceId);
    if (!v) return;

    if (selectedVoiceName) selectedVoiceName.textContent = v.name;
    if (selectedVoiceDesc) selectedVoiceDesc.textContent = v.description || "Voz seleccionada para la narración.";
    if (selectedVoiceTags) {
      selectedVoiceTags.innerHTML = (v.tags || [v.gender || "Voz", v.provider || "TTS"]).map(t => {
        const isHighlight = t.toLowerCase().includes("joven") || t.toLowerCase().includes("lírico") || t.toLowerCase().includes("12-16") || t.toLowerCase().includes("españa") || t.toLowerCase().includes("sin acento");
        return `<span class="voice-pill ${isHighlight ? 'highlight' : ''}">${t}</span>`;
      }).join("");
    }

    // Actualizar botones de audición rápida
    document.querySelectorAll(".btn-quick-voice").forEach(btn => {
      if (btn.dataset.voice === voiceId) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    // Sincronizar univVoice si difiere
    if (univVoice && univVoice.value !== voiceId) {
      univVoice.value = voiceId;
    }
    if (narratorVoiceSelect && narratorVoiceSelect.value !== voiceId) {
      narratorVoiceSelect.value = voiceId;
    }
  }

  function populateNarratorFields(narrator, voiceId) {
    if (!narrator) {
      narrator = {
        nombre: "El Poeta / Muchacho de Moguer (Narrador Lírico)",
        genero: "masculino",
        edad_aprox: "12-14 años (Joven / Adolescente)",
        rango_edad: "joven",
        tono: "Lírico, contemplativo, tierno, pausado y reflexivo en español nativo",
        justificacion: "En Platero y yo el narrador es una voz lírica joven (12-14 años) en español peninsular nativo, sin acento foráneo.",
        voz_recomendada: "edge_alvaro_joven",
        texto_muestra: "Platero es pequeño, peludo, suave; tan blando por fuera, que se diría todo de algodón, que no lleva huesos. Sólo los espejos de azabache de sus ojos son duros cual dos escarabajos de cristal negro."
      };
    }

    if (narratorName) narratorName.value = narrator.nombre || "";
    if (narratorGender) narratorGender.value = narrator.genero || "masculino";
    if (narratorAge) narratorAge.value = narrator.edad_aprox || "";
    if (narratorAgeBracket) narratorAgeBracket.value = narrator.rango_edad || "joven";
    if (narratorTone) narratorTone.value = narrator.tono || "";
    if (narratorJustification) narratorJustification.value = narrator.justificacion || "";
    if (narratorSampleText) {
      narratorSampleText.value = narrator.texto_muestra || "Platero es pequeño, peludo, suave; tan blando por fuera, que se diría todo de algodón, que no lleva huesos. Sólo los espejos de azabache de sus ojos son duros cual dos escarabajos de cristal negro.";
    }

    const chosenVoice = voiceId || narrator.voz_recomendada || "edge_alvaro_joven";
    updateSelectedVoiceCard(chosenVoice);
  }

  function setupModalClosers() {
    document.querySelectorAll("[data-close]").forEach(el => {
      el.addEventListener("click", () => {
        const modalId = el.getAttribute("data-close");
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.remove("open");
      });
    });

    const lightboxModal = document.getElementById("modal-image-lightbox");
    const lightboxImg = document.getElementById("lightbox-image-el");
    const lightboxTitle = document.getElementById("lightbox-image-title");

    document.addEventListener("click", (e) => {
      const img = e.target.closest(".char-portrait-frame img, .char-4views-grid img, .env-portrait-frame img, .scene-image-box img");
      if (img && lightboxModal && lightboxImg) {
        lightboxImg.src = img.src;
        if (lightboxTitle) lightboxTitle.textContent = img.alt || "Vista ampliada";
        lightboxModal.classList.add("open");
        return;
      }
      if (lightboxModal && e.target === lightboxModal) {
        lightboxModal.classList.remove("open");
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && lightboxModal?.classList.contains("open")) {
        lightboxModal.classList.remove("open");
      }
    });
  }

  // ========================================================
  // 2. NAVEGACIÓN ENTRE CAPAS
  // ========================================================
  function switchLayer(layer) {
    if (layer === "generic") {
      tabNavGeneric.classList.add("active");
      tabNavSpecific.classList.remove("active");
      viewGeneric.style.display = "block";
      viewSpecific.style.display = "none";
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      tabNavSpecific.classList.add("active");
      tabNavGeneric.classList.remove("active");
      viewSpecific.style.display = "block";
      viewGeneric.style.display = "none";
      window.scrollTo({ top: 0, behavior: "smooth" });
      updateMiniBanner();
      if (typeof updateSubtitlePreview === "function") updateSubtitlePreview();
    }
  }

  tabNavGeneric.addEventListener("click", () => switchLayer("generic"));
  tabNavSpecific.addEventListener("click", () => switchLayer("specific"));
  btnGoToChapters.addEventListener("click", async () => {
    await saveUniverse(false);
    switchLayer("specific");
  });
  btnSwitchToGeneric.addEventListener("click", () => switchLayer("generic"));

  function updateMiniBanner() {
    if (!state.currentProject) return;
    const p = state.currentProject;
    miniBannerTitle.textContent = p.titulo;
    miniBannerAudience.textContent = `🎯 ${p.audiencia || "Todos los públicos"}`;
    miniBannerStyle.textContent = styleNames[p.estilo_visual] || p.estilo_visual;
    miniBannerCharsCount.textContent = `👥 ${(p.personajes || []).length} personajes`;
    if (miniBannerEnvsCount) miniBannerEnvsCount.textContent = `🏛️ ${(p.escenarios || []).length} escenarios`;
  }

  // ========================================================
  // 3. GESTIÓN DE PROYECTOS / LIBROS
  // ========================================================
  async function loadProjects(selectProjectId = null) {
    try {
      const res = await fetch("/api/projects");
      const list = await res.json();
      state.projects = list;

      projectSelect.innerHTML = "";

      if (list.length === 0) {
        await createDefaultSeedProject();
        return;
      }

      list.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.titulo} (${p.capitulos_count || 0} caps)`;
        projectSelect.appendChild(opt);
      });

      // Restaurar el proyecto guardado previamente en el navegador
      const savedProjectId = localStorage.getItem("active_project_id");
      let targetId = selectProjectId;
      if (!targetId && savedProjectId && list.some(p => p.id === savedProjectId)) {
        targetId = savedProjectId;
      }

      // Si no hay proyecto guardado previo o targetId no existe, abrimos el Hub de Proyectos
      if (!targetId) {
        targetId = list[0].id;
        openProjectsHub();
      }

      projectSelect.value = targetId;
      await selectProject(targetId);

    } catch (e) {
      console.error("Error cargando proyectos:", e);
    }
  }

  async function createDefaultSeedProject() {
    const seed = {
      titulo: "El Guardián del Faro",
      descripcion: "Saga de misterio y arqueología marina en una costa solitaria.",
      audiencia: "Adultos (Thriller / Misterio)",
      ambiente: "Costa atlántica lluviosa de los años 50 con niebla marina constante y faro de piedra antiguo.",
      estilo_visual: "noir_bw",
      estilo_detalles: "Fotografía blanco y negro de alto contraste, sombras duras y claroscuro",
      voz_defecto: "eleven_george",
      personajes: [
        {
          id: "mateo",
          nombre: "Mateo",
          rol: "Arqueólogo detective",
          descripcion_visual: "Hombre de 32 años, gabardina desgastada, pelo castaño alborotado, ojos grises inquisitivos, bufanda azul oscura",
          prompt_retrato: "Character concept art portrait of Mateo, 32 years old man, worn brown trenchcoat, messy brown hair, 9:16 vertical"
        },
        {
          id: "elena",
          nombre: "Elena",
          rol: "Científica marina",
          descripcion_visual: "Mujer de 30 años, pelo negro recogido en coleta, gafas de pasta, chubasquero técnico amarillo, mirada analítica",
          prompt_retrato: "Character concept art portrait of Elena, 30 years old woman, yellow technical raincoat, round glasses, ponytail, 9:16 vertical"
        }
      ]
    };

    const res = await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(seed)
    });
    const data = await res.json();
    if (data.success) {
      await loadProjects(data.project.id);
    }
  }

  async function selectProject(projectId) {
    state.universeRenderedOk = false;
    try {
      const res = await fetch(`/api/projects/${projectId}`);
      const project = await res.json();
      state.currentProject = project;
      localStorage.setItem("active_project_id", project.id);

      // Sincronizar dropdown superior
      projectSelect.value = project.id;

      // Actualizar formulario de Capa Genérica
      univTitle.value = project.titulo || "";
      univAudience.value = project.audiencia || "Todos los públicos";
      univAmbient.value = project.ambiente || "";
      univStyle.value = project.estilo_visual || "cinematic";
      if (univStyleDetails) univStyleDetails.value = project.estilo_detalles || "";
      if (univImageEngine) univImageEngine.value = project.motor_imagenes || "flux";
      applyGenerationRulesToUI(project.reglas_generacion);
      updateStyleImplications(univStyle.value, false);
      if (univVoice && project.voz_defecto) univVoice.value = project.voz_defecto;
      if (univRecurrentChars) univRecurrentChars.value = project.personajes_recurrentes_texto || "";
      renderRecurrentCharsGrid(project.personajes_recurrentes_texto || "", project.personajes || [], project.referencia_personaje_id || null);
      renderRecurrentEnvsGrid(project.escenarios || [], project.referencia_escenario_id || null);

      // Cargar y sincronizar perfil del narrador (Punto 5)
      populateNarratorFields(project.perfil_narrador, project.voz_defecto);

      phoneProjectTag.textContent = `@${project.titulo.replace(/\s+/g, '')} • Capítulos`;

      // Renderizar tarjetas de personajes y escenarios guardados
      renderCharacterCards(project.personajes || []);
      renderEnvironmentCards(project.escenarios || []);
      state.universeRenderedOk = true;

      // Actualizar mini banner
      updateMiniBanner();

      // Cargar lista de capítulos y árbol de navegación
      await loadProjectChapters(project.id);

      // Tarjeta de libro guardado vs Subida
      if (project.documento_activo) {
        if (savedBookCard) savedBookCard.style.display = "block";
        if (uploadBookContainer) uploadBookContainer.style.display = "none";
        if (savedBookFilename) savedBookFilename.textContent = project.documento_activo.nombre;
        if (savedBookPath) savedBookPath.textContent = `proyectos/${project.id}/documentos/`;
        if (savedBookMeta) {
          const docsCount = project.documentos_detalle ? project.documentos_detalle.length : 1;
          savedBookMeta.textContent = `${project.documento_activo.tamano_formateado || project.documento_activo.tamano || ''} · ${docsCount} archivo(s)`.replace(/^\s*·\s*/, '');
        }
        // Cargar estructura completa del manuscrito (páginas y capítulos detectados)
        await loadManuscriptStructure(project.id);
      } else {
        state.manuscriptDoc = null;
        if (savedBookCard) savedBookCard.style.display = "none";
        if (uploadBookContainer) uploadBookContainer.style.display = "block";
        if (sourcePagesCount) sourcePagesCount.textContent = "0 págs";
        if (sourceChaptersCount) sourceChaptersCount.textContent = "0 secciones";
        if (selectManuscriptPage) selectManuscriptPage.innerHTML = "<option value=''>Sin manuscrito en disco</option>";
        if (selectManuscriptSection) selectManuscriptSection.innerHTML = "<option value=''>Sin secciones</option>";
        if (pagePreviewText) pagePreviewText.textContent = "(No hay manuscrito guardado en documentos/ de este libro)";
        if (sectionPreviewText) sectionPreviewText.textContent = "(No hay secciones disponibles)";
      }

    } catch (e) {
      console.error("Error seleccionando proyecto:", e);
      showToast("Error seleccionando proyecto", "error");
    }
  }

  projectSelect.addEventListener("change", async e => {
    if (e.target.value) {
      await selectProject(e.target.value);
      showToast(`Libro activo: '${state.currentProject.titulo}'`, "info");
    }
  });

  // Eventos de la tarjeta de Manuscrito Guardado
  if (btnToggleReplaceBook) {
    btnToggleReplaceBook.addEventListener("click", () => {
      if (uploadBookContainer.style.display === "none") {
        uploadBookContainer.style.display = "block";
        btnToggleReplaceBook.textContent = "✖️ Ocultar Subida";
      } else {
        uploadBookContainer.style.display = "none";
        btnToggleReplaceBook.textContent = "🔄 Reemplazar Archivo";
      }
    });
  }

  if (btnLoadChaptersToSpecific) {
    btnLoadChaptersToSpecific.addEventListener("click", () => {
      switchLayer("specific");
    });
  }

  // ========================================================
  // CENTRO DE PROYECTOS & LIBROS (PROJECTS HUB)
  // ========================================================
  function openProjectsHub() {
    if (!modalProjectsHub) return;
    renderProjectsHub();
    modalProjectsHub.classList.add("open");
  }

  if (btnOpenProjectsHub) {
    btnOpenProjectsHub.addEventListener("click", () => openProjectsHub());
  }

  if (btnHubNewProject) {
    btnHubNewProject.addEventListener("click", () => {
      if (modalProjectsHub) modalProjectsHub.classList.remove("open");
      newProjTitle.value = "";
      newProjDesc.value = "";
      modalProjectCreate.classList.add("open");
    });
  }

  function renderProjectsHub() {
    if (!projectsHubGrid) return;
    const list = state.projects || [];
    if (hubProjectsCount) {
      hubProjectsCount.textContent = `${list.length} proyectos guardados en disco`;
    }

    if (list.length === 0) {
      projectsHubGrid.innerHTML = `
        <div class="empty-state-card text-center p-4">
          <p class="text-muted">No hay proyectos creados aún en la carpeta <code>proyectos/</code>.</p>
        </div>
      `;
      return;
    }

    projectsHubGrid.innerHTML = "";
    list.forEach(p => {
      const isCurrent = state.currentProject && state.currentProject.id === p.id;
      const card = document.createElement("div");
      card.className = `project-hub-card ${isCurrent ? 'active-project' : ''}`;

      // Miniaturas de personajes
      let charThumbsHtml = "";
      if (p.personajes_thumbnails && p.personajes_thumbnails.length > 0) {
        charThumbsHtml = `
          <div class="hub-thumbnails-strip" style="display: flex; gap: 6px; align-items: center; margin-top: 4px; flex-wrap: wrap;">
            ${p.personajes_thumbnails.map(thumb => `<img src="${thumb}" alt="Personaje" class="hub-thumb-avatar" style="width: 42px; height: 52px; object-fit: cover; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2);" onerror="this.style.display='none'">`).join("")}
          </div>
        `;
      }

      // Miniaturas de escenarios
      let escThumbsHtml = "";
      if (p.escenarios_thumbnails && p.escenarios_thumbnails.length > 0) {
        escThumbsHtml = `
          <div class="hub-thumbnails-strip mt-1" style="display: flex; gap: 6px; align-items: center; margin-top: 4px; flex-wrap: wrap;">
            ${p.escenarios_thumbnails.map(thumb => `<img src="${thumb}" alt="Escenario" class="hub-thumb-scene" style="width: 72px; height: 44px; object-fit: cover; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2);" onerror="this.style.display='none'">`).join("")}
          </div>
        `;
      }

      // Detalle de documento guardado
      const docLabel = p.documento_activo 
        ? `📄 ${p.documento_activo.nombre} (${p.documento_activo.tamano})` 
        : `⚠️ Sin manuscrito guardado`;

      card.innerHTML = `
        <div class="hub-card-header">
          <div class="hub-card-title-group">
            <h3 class="hub-card-title">${p.titulo}</h3>
            ${isCurrent ? '<span class="badge badge-accent">Activo</span>' : ''}
          </div>
          <span class="hub-folder-name">📁 proyectos/${p.id}/</span>
        </div>

        <p class="hub-card-desc">${p.descripcion || 'Sin descripción'}</p>

        <div class="hub-card-meta-pills">
          <span class="hub-meta-pill">🎯 ${p.audiencia || 'Todos'}</span>
          <span class="hub-meta-pill">🎨 ${styleNames[p.estilo_visual] || p.estilo_visual}</span>
        </div>

        <div class="hub-folder-breakdown">
          <div class="hub-folder-row">
            <span class="folder-icon">📄</span>
            <span class="folder-name">documentos/:</span>
            <span class="folder-info">${docLabel}</span>
          </div>
          <div class="hub-folder-row">
            <span class="folder-icon">👥</span>
            <span class="folder-name">personajes/:</span>
            <span class="folder-info">${p.personajes_count || 0} registrados</span>
          </div>
          ${charThumbsHtml}
          <div class="hub-folder-row mt-2">
            <span class="folder-icon">🏛️</span>
            <span class="folder-name">escenarios/:</span>
            <span class="folder-info">${p.escenarios_count || 0} entornos</span>
          </div>
          ${escThumbsHtml}
          <div class="hub-folder-row mt-2">
            <span class="folder-icon">🎬</span>
            <span class="folder-name">capitulos/:</span>
            <span class="folder-info">${p.capitulos_count || 0} episodios producidos</span>
          </div>
        </div>

        <div class="hub-card-footer">
          <button class="btn ${isCurrent ? 'btn-secondary' : 'btn-accent'} btn-sm btn-load-proj" data-proj-id="${p.id}">
            ${isCurrent ? '✅ Proyecto Actual' : '▶️ Continuar Producción'}
          </button>
          <button class="btn btn-danger-ghost btn-xs btn-delete-proj" data-proj-id="${p.id}" data-proj-title="${p.titulo}" title="Eliminar proyecto de disco">
            🗑️
          </button>
        </div>
      `;

      projectsHubGrid.appendChild(card);
    });

    // Eventos de botones en tarjetas
    projectsHubGrid.querySelectorAll(".btn-load-proj").forEach(btn => {
      btn.addEventListener("click", async () => {
        const pId = btn.getAttribute("data-proj-id");
        await selectProject(pId);
        if (modalProjectsHub) modalProjectsHub.classList.remove("open");
        showToast(`Proyecto '${state.currentProject.titulo}' cargado con éxito`, "success");
      });
    });

    projectsHubGrid.querySelectorAll(".btn-delete-proj").forEach(btn => {
      btn.addEventListener("click", async () => {
        const pId = btn.getAttribute("data-proj-id");
        const pTitle = btn.getAttribute("data-proj-title");
        if (confirm(`¿Estás seguro de que deseas eliminar permanentemente el proyecto '${pTitle}' y toda su carpeta en disco (documentos, personajes y capítulos)?`)) {
          await deleteProject(pId);
        }
      });
    });
  }

  async function deleteProject(projectId) {
    try {
      const res = await fetch(`/api/projects/${projectId}`, { method: "DELETE" });
      const data = await res.json();
      if (data.success) {
        showToast(`Proyecto eliminado de disco`, "info");
        if (localStorage.getItem("active_project_id") === projectId) {
          localStorage.removeItem("active_project_id");
        }
        await loadProjects();
        renderProjectsHub();
      } else {
        showToast(data.error || "No se pudo eliminar el proyecto", "error");
      }
    } catch (e) {
      showToast("Error eliminando proyecto", "error");
    }
  }

  // Modal Crear Proyecto
  btnCreateProjectModal?.addEventListener("click", () => {
    newProjTitle.value = "";
    newProjDesc.value = "";
    modalProjectCreate.classList.add("open");
  });

  btnConfirmCreateProject.addEventListener("click", async () => {
    const title = newProjTitle.value.trim();
    if (!title) {
      showToast("El título del libro es obligatorio", "error");
      return;
    }

    try {
      const res = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          titulo: title,
          descripcion: newProjDesc.value.trim(),
          audiencia: "Todos los públicos",
          ambiente: "",
          estilo_visual: "cinematic",
          personajes: []
        })
      });
      const data = await res.json();
      if (data.success) {
        modalProjectCreate.classList.remove("open");
        showToast(`Proyecto '${title}' creado con éxito`, "success");
        await loadProjects(data.project.id);
        switchLayer("generic");
      }
    } catch (e) {
      showToast("Error creando proyecto", "error");
    }
  });

  // Contador de palabras en texto de muestra
  bookSampleText.addEventListener("input", () => {
    const words = bookSampleText.value.trim().split(/\s+/).filter(w => w.length > 0).length;
    bookWordsCount.textContent = `${words} palabras`;
  });

  // ========================================================
  // 4. SUBIDA DE MANUSCRITO Y ANÁLISIS DE LIBRO CON IA
  // ========================================================
  dropZoneBook.addEventListener("click", () => fileInputBook.click());
  dropZoneBook.addEventListener("dragover", e => {
    e.preventDefault();
    dropZoneBook.classList.add("dragover");
  });
  dropZoneBook.addEventListener("dragleave", () => dropZoneBook.classList.remove("dragover"));
  dropZoneBook.addEventListener("drop", async e => {
    e.preventDefault();
    dropZoneBook.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      await handleBookUpload(e.dataTransfer.files[0]);
    }
  });

  fileInputBook.addEventListener("change", async e => {
    if (e.target.files.length > 0) {
      await handleBookUpload(e.target.files[0]);
    }
  });

  async function handleBookUpload(file) {
    if (!state.currentProject) {
      showToast("Selecciona un proyecto primero", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    showToast(`Analizando '${file.name}'...`, "info");

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/documents/upload`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (data.success && data.document) {
        state.uploadedDoc = data.document;
        bookDocInfo.style.display = "flex";
        bookDocFilename.textContent = file.name;
        bookDocStats.textContent = `${data.document.total_words} palabras • ${data.document.chapters_count} capítulos detectados`;

        // Llenar selector de capítulos para la Capa Específica
        populateChapterPicker(data.document.chapters);

        // Prellenar textarea de muestra
        if (!bookSampleText.value.trim()) {
          bookSampleText.value = data.document.full_text.slice(0, 4000);
          bookSampleText.dispatchEvent(new Event("input"));
        }

        showToast(`Documento subido a la carpeta del proyecto (${data.document.total_words} palabras)`, "success");
      }
    } catch (e) {
      showToast("Error subiendo libro", "error");
    }
  }

  // Modal y Confirmación de Análisis con IA
  const modalAiAnalyzeConfirm = document.getElementById("modal-ai-analyze-confirm");
  const modalAnalyzeDocName = document.getElementById("modal-analyze-doc-name");
  const modalAnalyzeDocHint = document.getElementById("modal-analyze-doc-hint");
  const btnConfirmAiAnalyze = document.getElementById("btn-confirm-ai-analyze");

  function openAiAnalyzeConfirmation() {
    if (!state.currentProject) {
      showToast("Selecciona o crea un proyecto primero", "error");
      return;
    }

    const docName = (state.currentProject.documento_activo ? state.currentProject.documento_activo.nombre : "")
      || (state.uploadedDoc ? state.uploadedDoc.filename : "")
      || (bookSampleText.value.trim() ? "Texto manual pegado en el formulario" : "");

    if (!docName && !state.currentProject.documento_activo) {
      showToast("Sube un archivo de libro o pega texto en el formulario antes de analizar", "error");
      return;
    }

    if (modalAnalyzeDocName) {
      modalAnalyzeDocName.textContent = docName || "Manuscrito del proyecto";
    }
    if (modalAnalyzeDocHint) {
      if (state.currentProject.documento_activo) {
        modalAnalyzeDocHint.textContent = `Manuscrito guardado en proyectos/${state.currentProject.id}/documentos/`;
      } else if (state.uploadedDoc) {
        modalAnalyzeDocHint.textContent = "Documento recién subido listo para procesamiento";
      } else {
        modalAnalyzeDocHint.textContent = "Fragmento o sinopsis extensa introducida manualmente";
      }
    }

    if (modalAiAnalyzeConfirm) {
      modalAiAnalyzeConfirm.classList.add("open");
    } else {
      triggerAiBookAnalysis();
    }
  }

  // Botón Analizar con IA
  if (btnAiAnalyzeBook) {
    btnAiAnalyzeBook.addEventListener("click", () => openAiAnalyzeConfirmation());
  }
  if (btnAnalyzeUploadedDoc) {
    btnAnalyzeUploadedDoc.addEventListener("click", () => openAiAnalyzeConfirmation());
  }
  if (btnConfirmAiAnalyze) {
    btnConfirmAiAnalyze.addEventListener("click", () => {
      if (modalAiAnalyzeConfirm) modalAiAnalyzeConfirm.classList.remove("open");
      triggerAiBookAnalysis();
    });
  }

  async function triggerAiBookAnalysis() {
    const textToAnalyze = (state.uploadedDoc ? state.uploadedDoc.full_text : "")
      || (state.manuscriptDoc ? state.manuscriptDoc.full_text : "")
      || bookSampleText.value.trim();

    if (!textToAnalyze && !state.currentProject?.documento_activo) {
      showToast("Sube un archivo de libro o pega texto en el área antes de analizar", "error");
      return;
    }

    btnAiAnalyzeBook.disabled = true;
    btnAiAnalyzeBook.innerHTML = '<span class="btn-icon-symbol">⏳</span> Analizando libro con IA...';
    setSystemStatus("busy", "Analizando libro con IA...", "Extrayendo ambiente, personajes, escenarios y perfil del narrador (sin alterar tu estilo visual)...");

    try {
      const hint = univRecurrentChars ? univRecurrentChars.value.trim() : "";
      const res = await fetch(`/api/projects/${state.currentProject.id}/analyze-book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: textToAnalyze || "",
          recurrent_chars_hint: hint
        })
      });
      const data = await res.json();
      if (data.success && data.analysis) {
        await processAiBookAnalysisResult(data.analysis);
      } else {
        showToast(data.detail || "Error analizando libro con IA", "error");
        setSystemStatus("error", "Error en análisis de libro", data.detail || "Fallo al procesar el texto con IA.");
      }
    } catch (e) {
      showToast("Error analizando libro con IA", "error");
      setSystemStatus("error", "Error de conexión en análisis", e.message);
    } finally {
      btnAiAnalyzeBook.disabled = false;
      btnAiAnalyzeBook.innerHTML = '<span class="btn-icon-symbol">🔮</span> Analizar IA';
    }
  }

  function applySingleAiField(key, a) {
    if (key === "titulo" && a.titulo_sugerido && univTitle) {
      univTitle.value = a.titulo_sugerido;
    } else if (key === "audiencia" && a.audiencia && univAudience) {
      univAudience.value = a.audiencia;
    } else if (key === "ambiente" && a.ambiente && univAmbient) {
      univAmbient.value = a.ambiente;
    } else if (key === "personajes" && Array.isArray(a.personajes) && a.personajes.length > 0) {
      if (a.personajes_recurrentes_texto && univRecurrentChars) {
        univRecurrentChars.value = a.personajes_recurrentes_texto;
      }
      renderCharacterCards(a.personajes);
    } else if (key === "escenarios" && Array.isArray(a.escenarios) && a.escenarios.length > 0) {
      renderEnvironmentCards(a.escenarios);
    } else if (key === "narrador") {
      if (univVoice && a.voz_defecto) univVoice.value = a.voz_defecto;
      if (a.perfil_narrador) {
        populateNarratorFields(a.perfil_narrador, a.voz_defecto || a.perfil_narrador.voz_recomendada);
      }
    }
  }

  function shortenPreview(text, maxLen = 130) {
    const clean = String(text || "").replace(/\s+/g, " ").trim();
    if (!clean) return "(vacío)";
    return clean.length > maxLen ? clean.slice(0, maxLen) + "…" : clean;
  }

  async function processAiBookAnalysisResult(a) {
    const existingChars = collectCharactersFromUI();
    const existingEnvs = collectEnvironmentsFromUI();
    const savedAudience = (state.currentProject?.universo?.audiencia || "").trim();

    const fieldSpecs = [
      {
        key: "titulo",
        label: "1. Título del proyecto",
        hasAiValue: Boolean(a.titulo_sugerido && a.titulo_sugerido.trim()),
        isEmpty: !univTitle?.value.trim() || univTitle.value.trim().startsWith("Nuevo"),
        isSame: univTitle?.value.trim() === (a.titulo_sugerido || "").trim(),
        currentPreview: univTitle?.value.trim() || "",
        aiPreview: a.titulo_sugerido || ""
      },
      {
        key: "audiencia",
        label: "1. Público objetivo",
        hasAiValue: Boolean(a.audiencia && a.audiencia.trim()),
        isEmpty: !savedAudience && !univAmbient?.value.trim() && existingChars.length === 0,
        isSame: univAudience?.value === a.audiencia,
        currentPreview: univAudience?.value || "",
        aiPreview: a.audiencia || ""
      },
      {
        key: "ambiente",
        label: "2. Ambiente (no toca tu estilo visual)",
        hasAiValue: Boolean(a.ambiente && a.ambiente.trim()),
        isEmpty: !univAmbient?.value.trim(),
        isSame: univAmbient?.value.trim() === (a.ambiente || "").trim(),
        currentPreview: shortenPreview(univAmbient?.value, 140),
        aiPreview: shortenPreview(a.ambiente, 140)
      },
      {
        key: "personajes",
        label: "3. Personajes",
        hasAiValue: Array.isArray(a.personajes) && a.personajes.length > 0,
        isEmpty: existingChars.length === 0,
        isSame: false,
        warning: existingChars.some(c => c.imagen_url)
          ? `⚠️ Tienes ${existingChars.filter(c => c.imagen_url).length} personaje(s) con imagen generada. Si sobrescribes, se reemplazarán las tarjetas actuales.`
          : "",
        currentPreview: `${existingChars.length} personaje(s): ${existingChars.map(c => c.nombre).slice(0, 4).join(", ")}${existingChars.length > 4 ? "…" : ""}`,
        aiPreview: `${(a.personajes || []).length} personaje(s): ${(a.personajes || []).map(c => c.nombre).slice(0, 4).join(", ")}${(a.personajes || []).length > 4 ? "…" : ""}`
      },
      {
        key: "escenarios",
        label: "4. Escenarios",
        hasAiValue: Array.isArray(a.escenarios) && a.escenarios.length > 0,
        isEmpty: existingEnvs.length === 0,
        isSame: false,
        warning: existingEnvs.some(e => e.imagen_url)
          ? `⚠️ Tienes ${existingEnvs.filter(e => e.imagen_url).length} escenario(s) con imagen generada. Si sobrescribes, se reemplazarán las tarjetas actuales.`
          : "",
        currentPreview: `${existingEnvs.length} escenario(s): ${existingEnvs.map(e => e.nombre).slice(0, 4).join(", ")}${existingEnvs.length > 4 ? "…" : ""}`,
        aiPreview: `${(a.escenarios || []).length} escenario(s): ${(a.escenarios || []).map(e => e.nombre).slice(0, 4).join(", ")}${(a.escenarios || []).length > 4 ? "…" : ""}`
      },
      {
        key: "narrador",
        label: "5. Narración (perfil y voz)",
        hasAiValue: Boolean(a.perfil_narrador || a.voz_defecto),
        isEmpty: !narratorName?.value.trim() && !narratorTone?.value.trim() && !narratorJustification?.value.trim(),
        isSame: false,
        currentPreview: `${narratorName?.value.trim() || "Sin nombre"} · ${shortenPreview(narratorTone?.value, 70)}`,
        aiPreview: `${a.perfil_narrador?.nombre || "Narrador IA"} · ${shortenPreview(a.perfil_narrador?.tono, 70)}`
      }
    ];

    const emptyAppliedLabels = [];
    const conflicts = [];

    fieldSpecs.forEach(spec => {
      if (!spec.hasAiValue) return;
      if (spec.isEmpty) {
        applySingleAiField(spec.key, a);
        emptyAppliedLabels.push(spec.label);
      } else if (!spec.isSame) {
        conflicts.push(spec);
      }
    });

    if (emptyAppliedLabels.length > 0) {
      await saveUniverse(false);
    }

    if (conflicts.length === 0) {
      showToast("¡Análisis completado! Campos vacíos rellenados sin alterar tu estilo visual.", "success");
      setSystemStatus("success", "¡Análisis completado!", "Se han rellenado los campos correspondientes respetando tu estilo visual.");
      return;
    }

    openAiOverwriteModal(a, emptyAppliedLabels, conflicts);
  }

  function openAiOverwriteModal(analysis, emptyAppliedLabels, conflicts) {
    const modal = document.getElementById("modal-ai-overwrite-confirm");
    const emptyInfo = document.getElementById("ai-overwrite-empty-info");
    const listEl = document.getElementById("ai-overwrite-list");
    const btnAllYes = document.getElementById("btn-ai-overwrite-all-yes");
    const btnAllNo = document.getElementById("btn-ai-overwrite-all-no");
    const btnApply = document.getElementById("btn-ai-overwrite-apply");
    if (!modal || !listEl || !btnApply) return;

    if (emptyInfo) {
      if (emptyAppliedLabels.length > 0) {
        emptyInfo.style.display = "block";
        emptyInfo.textContent = `✅ Ya se han rellenado automáticamente los campos que estaban vacíos: ${emptyAppliedLabels.join(", ")}.`;
      } else {
        emptyInfo.style.display = "none";
      }
    }

    listEl.innerHTML = conflicts.map(item => `
      <div class="ai-overwrite-row" data-key="${item.key}" style="padding:0.75rem 0.9rem; border-radius:8px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.09);">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.45rem;">
          <strong style="font-size:0.9rem; color:#e2e8f0;">${escapeHtml(item.label)}</strong>
          <div style="display:flex; gap:0.5rem; align-items:center; font-size:0.82rem;">
            <label style="display:inline-flex; align-items:center; gap:4px; cursor:pointer; padding:3px 9px; border-radius:6px; background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.3);">
              <input type="radio" name="ai-ow-${item.key}" value="yes"> Sí, sobrescribir
            </label>
            <label style="display:inline-flex; align-items:center; gap:4px; cursor:pointer; padding:3px 9px; border-radius:6px; background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3);">
              <input type="radio" name="ai-ow-${item.key}" value="no" checked> No, mantener actual
            </label>
          </div>
        </div>
        ${item.warning ? `<div style="font-size:0.78rem; color:#fbbf24; margin-bottom:0.4rem;">${escapeHtml(item.warning)}</div>` : ""}
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.6rem; font-size:0.78rem;">
          <div style="padding:0.45rem 0.6rem; border-radius:6px; background:rgba(15,23,42,0.55); border:1px solid rgba(255,255,255,0.06);">
            <div style="color:#94a3b8; font-weight:600; margin-bottom:2px;">Actual</div>
            <div style="color:#cbd5e1;">${escapeHtml(item.currentPreview)}</div>
          </div>
          <div style="padding:0.45rem 0.6rem; border-radius:6px; background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.22);">
            <div style="color:#a5b4fc; font-weight:600; margin-bottom:2px;">Propuesta IA</div>
            <div style="color:#e2e8f0;">${escapeHtml(item.aiPreview)}</div>
          </div>
        </div>
      </div>
    `).join("");

    const setAllChoices = (val) => {
      listEl.querySelectorAll(`input[type="radio"][value="${val}"]`).forEach(r => { r.checked = true; });
    };
    if (btnAllYes) btnAllYes.onclick = () => setAllChoices("yes");
    if (btnAllNo) btnAllNo.onclick = () => setAllChoices("no");

    btnApply.onclick = async () => {
      let overwritten = 0;
      let kept = 0;
      conflicts.forEach(item => {
        const yesRadio = listEl.querySelector(`input[name="ai-ow-${item.key}"][value="yes"]`);
        if (yesRadio && yesRadio.checked) {
          applySingleAiField(item.key, analysis);
          overwritten++;
        } else {
          kept++;
        }
      });

      if (overwritten > 0) {
        await saveUniverse(false);
        showToast(`Actualizado(s) ${overwritten} campo(s) y mantenido(s) ${kept}.`, "success");
        setSystemStatus("success", "Selección aplicada", `Sobrescritos ${overwritten} campo(s); ${kept} mantenido(s) intactos.`);
      } else {
        showToast("Se han mantenido todos los campos actuales sin cambios.", "info");
        setSystemStatus("success", "Campos mantenidos", "No se ha sobrescrito ningún dato existente.");
      }
      modal.classList.remove("open");
    };

    setSystemStatus("success", "Esperando confirmación", "Elige Sí o No en cada campo que ya tenía datos.");
    modal.classList.add("open");
  }

  // ========================================================
  // 5. GESTIÓN DE LA BIBLIA DE PERSONAJES & RETRATOS
  // ========================================================
  function buildAssetHistoryHtml(category, itemId, historial, frameId, activeVersion = null) {
    if (!Array.isArray(historial) || historial.length === 0) return "";
    const sorted = [...historial].sort((a, b) => (b.version || 0) - (a.version || 0));
    const targetVer = activeVersion !== null && activeVersion !== undefined
      ? Number(activeVersion)
      : (sorted[0]?.version ?? 0);
    const options = sorted.map(h => {
      const label = `v${String(h.version ?? 0).padStart(3, "0")} · ${h.provider || "ia"} (${(h.fecha || "").slice(5, 16)})`;
      const sel = Number(h.version) === targetVer ? "selected" : "";
      return `<option value="${h.version}" ${sel}>${label}</option>`;
    }).join("");
    return `
      <div class="asset-history-bar" data-category="${category}" data-item-id="${itemId}" data-frame-id="${frameId}" style="display:flex; gap:4px; margin-top:6px; align-items:center; width:100%;">
        <select class="form-select-xs asset-history-select" style="flex:1; min-width:0; font-size:0.72rem;" title="Selecciona una versión para activarla al instante sin gastar créditos (${historial.length})">
          ${options}
        </select>
      </div>
    `;
  }

  async function handleRestoreAssetVersion(barEl) {
    if (!state.currentProject || !barEl) return;
    const category = barEl.dataset.category;
    const itemId = barEl.dataset.itemId;
    const frameId = barEl.dataset.frameId;
    const selectEl = barEl.querySelector(".asset-history-select");
    if (!selectEl) return;
    const version = parseInt(selectEl.value, 10);
    if (Number.isNaN(version)) return;

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/${category}/${itemId}/restore-version`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ version })
      });
      const data = await res.json();
      if (data.success && data.imagen_url) {
        const frame = document.getElementById(frameId);
        if (frame) {
          const isPng = data.imagen_url.includes(".png");
          if (isPng) frame.classList.add("transparent-bg");
          else frame.classList.remove("transparent-bg");
          const freshUrl = `${data.imagen_url.split("?")[0]}?t=${Date.now()}`;
          frame.innerHTML = `<img src="${freshUrl}" alt="Versión v${version}">`;
        }
        const card = barEl.closest(".char-card");
        if (card && data.prompt) {
          const promptInput = card.querySelector(".char-input-prompt");
          if (promptInput) promptInput.value = data.prompt;
        }
        showToast(`✅ Versión v${String(version).padStart(3, "0")} restaurada como activa`, "success");
      } else {
        showToast(data.detail || "No se pudo restaurar la versión", "error");
      }
    } catch (e) {
      showToast(`Error restaurando versión: ${e.message}`, "error");
    }
  }

  function renderCharacterCards(characters) {
    charactersCardsGrid.innerHTML = "";

    if (characters.length === 0) {
      charactersCardsGrid.innerHTML = `
        <div class="card" style="grid-column: 1 / -1; text-align: center; padding: 2rem;">
          <p class="text-muted">No hay personajes en la biblia aún.</p>
          <button class="btn btn-primary btn-sm mt-2" id="btn-add-first-char">➕ Añadir Primer Personaje</button>
        </div>
      `;
      document.getElementById("btn-add-first-char")?.addEventListener("click", () => addCharacterCard());
      return;
    }

    characters.forEach((char, index) => {
      const card = createCharacterCardElement(char, index);
      charactersCardsGrid.appendChild(card);
    });
  }

  function getApprovalBadgeHtml(status, reason = "", btnClass = "btn-toggle-char-approval") {
    if (status === "aprobado") {
      return `<button type="button" class="badge ${btnClass}" style="background: rgba(34, 197, 94, 0.22); color: #4ade80; border: 1px solid #22c55e; font-size: 0.72rem; padding: 3px 10px; border-radius: 4px; cursor: pointer;" title="Pulsa para volver a Pendiente. Estando Aprobado, esta imagen y su semilla quedan fijadas como referencia para las escenas.">✅ Aprobado</button>`;
    }
    if (status === "en_revision") {
      return `<button type="button" class="badge ${btnClass}" style="background: rgba(245, 158, 11, 0.22); color: #fbbf24; border: 1px solid #f59e0b; font-size: 0.72rem; padding: 3px 10px; border-radius: 4px; cursor: pointer;" title="En revisión: ${escapeHtml(reason || 'Revisar cambios de coherencia')}. Pulsa para aprobar cuando esté corregido.">⚠️ En revisión</button>`;
    }
    if (status === "rechazado") {
      return `<button type="button" class="badge ${btnClass}" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; font-size: 0.72rem; padding: 3px 10px; border-radius: 4px; cursor: pointer;" title="Rechazado: ${escapeHtml(reason || 'No cuadra')}. Pulsa para aprobar esta imagen.">❌ Rechazado</button>`;
    }
    return `<button type="button" class="badge ${btnClass}" style="background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid #eab308; font-size: 0.72rem; padding: 3px 10px; border-radius: 4px; cursor: pointer;" title="Pulsa para aprobar esta imagen y fijar su semilla como referencia oficial para escenas.">⏳ Pendiente</button>`;
  }

  function render4ViewsGridHtml(vistas4, charName = "Personaje") {
    const v = vistas4 || {};
    const ts = Date.now();
    const tiles = [
      { key: "detalle", label: "Detalle" },
      { key: "frontal", label: "Frontal" },
      { key: "trasera", label: "Trasera" },
      { key: "perfil", label: "Perfil" }
    ];
    return tiles.map(t => {
      const rawUrl = v[t.key] || "";
      const imgHtml = rawUrl
        ? `<img src="${rawUrl.split('?')[0]}?t=${ts}" alt="${escapeHtml(charName)} - ${t.label}">`
        : `<span>—</span>`;
      return `
        <div class="char-4view-tile">
          <div class="char-4view-thumb">${imgHtml}</div>
          <span class="char-4view-label">${t.label}</span>
        </div>`;
    }).join("");
  }

  function createCharacterCardElement(char, index) {
    const card = document.createElement("div");
    card.className = "char-card";
    card.dataset.index = index;
    card.dataset.id = char.id || `char_${index+1}`;
    card.dataset.estadoAprobacion = char.estado_aprobacion || (char.imagen_url ? "aprobado" : "pendiente");
    card.dataset.motivoRechazo = char.motivo_rechazo || "";
    card.dataset.telegramMessageId = char.telegram_message_id || "";

    let charImgUrl = char.imagen_url;
    if (charImgUrl) {
      const baseUrl = charImgUrl.split("?")[0];
      charImgUrl = `${baseUrl}?t=${Date.now()}`;
    }

    const portraitHtml = charImgUrl
      ? `<img src="${charImgUrl}" alt="${char.nombre}">`
      : `<div class="char-placeholder">
           <span class="char-placeholder-icon">👤</span>
           <small>Sin foto 9:16</small>
         </div>`;

    const vistas4Obj = char.vistas_4 || {};
    const views4Html = render4ViewsGridHtml(vistas4Obj, char.nombre || "Personaje");

    const charTipo = char.tipo || ((char.nombre && char.nombre.toLowerCase().includes("platero")) || (char.descripcion_visual && char.descripcion_visual.toLowerCase().includes("burro")) ? "animal" : "humano");
    card.dataset.rol = char.rol || "";
    card.dataset.tipo = charTipo;
    card.dataset.crefWeight = char.cref_weight !== undefined ? String(char.cref_weight) : "100";
    card.dataset.loraModel = char.lora_model || "";
    card.dataset.loraTrigger = char.lora_trigger || "";
    card.dataset.seedConsistencia = char.seed_consistencia ? String(char.seed_consistencia) : "";
    card.dataset.hoja4VistasUrl = char.hoja_4_vistas_url || "";
    card.dataset.vistas4Json = JSON.stringify(vistas4Obj || {});
    const isPng = char.imagen_url && (char.imagen_url.includes(".png") || char.imagen_url.includes("nobg"));
    const isSinFondo = char.sin_fondo !== false;
    const formatoVista = char.formato_vista === "retrato" ? "retrato" : "cuerpo_entero";

    const projRules = (typeof getGenerationRulesFromUI === "function" ? getGenerationRulesFromUI() : null) || state.currentProject?.reglas_generacion || {};
    const charRules = char.reglas_personaje || {};
    const rFullBody = charRules.cuerpo_entero !== undefined ? Boolean(charRules.cuerpo_entero) : (char.formato_vista ? formatoVista !== "retrato" : projRules.cuerpo_entero !== false);
    const rWhiteBg = charRules.fondo_blanco !== undefined ? Boolean(charRules.fondo_blanco) : (char.sin_fondo !== undefined ? isSinFondo : projRules.fondo_blanco !== false);
    const rNoText = charRules.sin_texto !== undefined ? Boolean(charRules.sin_texto) : (projRules.sin_texto !== false);
    const rVertical = charRules.formato_vertical !== undefined ? Boolean(charRules.formato_vertical) : (projRules.formato_vertical !== false);
    const rDetail = charRules.nivel_detalle !== undefined ? Number(charRules.nivel_detalle) : (projRules.nivel_detalle !== undefined ? Number(projRules.nivel_detalle) : 75);
    const rRealism = charRules.nivel_realismo !== undefined ? Number(charRules.nivel_realismo) : (projRules.nivel_realismo !== undefined ? Number(projRules.nivel_realismo) : 75);

    const approvalStatus = card.dataset.estadoAprobacion;
    const statusBadge = getApprovalBadgeHtml(approvalStatus, char.motivo_rechazo);

    card.innerHTML = `
      <div class="char-card-main-row">
        <!-- Columna Retrato -->
        <div class="char-portrait-box">
          <div class="char-portrait-frame ${isPng ? 'transparent-bg' : ''}" id="char-frame-${index}">
            ${portraitHtml}
          </div>
          <div style="display:flex; flex-direction:column; align-items:center; gap:4px; margin-top:6px;">
            <div class="char-approval-slot">${statusBadge}</div>
            <div style="font-size:0.71rem; color:#94a3b8; text-align:center; line-height:1.3;">
              Ref: <code>${escapeHtml(card.dataset.id)}</code> · Seed: <code class="char-seed-code">${char.seed_consistencia || 'auto'}</code>
            </div>
          </div>
          <div class="char-portrait-actions">
            <button class="btn btn-secondary btn-xs btn-gen-portrait" data-index="${index}" title="Generar diseño inicial en tres cuartos (3/4) y formato vertical 9:16">
              🎨 ${char.imagen_url ? 'Regenerar 3/4' : 'Generar 3/4'}
            </button>
            <label class="btn btn-ghost btn-xs">
              📁 Subir
              <input type="file" class="input-upload-portrait" data-index="${index}" accept="image/*" style="display:none;">
            </label>
          </div>
          <div class="char-history-slot">
            ${buildAssetHistoryHtml("personajes", card.dataset.id, char.historial_imagenes || [], `char-frame-${index}`, char.active_version)}
          </div>
        </div>

        <!-- Columna Detalles -->
        <div class="char-details-box">
        <div class="char-details-header" style="display: flex; gap: 0.5rem; align-items: center;">
          <input type="text" class="char-input-name" placeholder="Nombre (ej: Platero)" value="${char.nombre || ''}" style="flex: 1;">
          <button class="btn-remove-char-card" data-index="${index}" title="Eliminar personaje">&times;</button>
        </div>

        <label class="char-desc-label mt-2" style="display:block; font-size:0.71rem; font-weight:600; color:#94a3b8; margin-bottom:2px;">Descripción del personaje</label>
        <textarea class="char-input-desc" rows="3" placeholder="Descripción visual del personaje tomada del documento (edad, pelaje/ropa, rasgos)...">${char.descripcion_visual || ''}</textarea>

        <!-- Opciones específicas rápidas para este personaje (heredan de 2. Estilo visual) -->
        <div class="char-rules-bar mt-2" style="display:flex; flex-wrap:wrap; gap:0.55rem; align-items:center; padding:5px 8px; border-radius:6px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); font-size:0.75rem;">
          <span style="color:#94a3b8; font-weight:600;">Opciones:</span>
          <label style="display:inline-flex; align-items:center; gap:3px; cursor:pointer;" title="Mostrar cuerpo entero de pies a cabeza">
            <input type="checkbox" class="char-rule-fullbody" ${rFullBody ? 'checked' : ''}> Cuerpo entero
          </label>
          <label style="display:inline-flex; align-items:center; gap:3px; cursor:pointer;" title="Fondo blanco puro aislado (#FFFFFF)">
            <input type="checkbox" class="char-rule-whitebg" ${rWhiteBg ? 'checked' : ''}> Fondo blanco
          </label>
          <label style="display:inline-flex; align-items:center; gap:3px; cursor:pointer;" title="Prohibir textos, etiquetas o flechas en la imagen">
            <input type="checkbox" class="char-rule-notext" ${rNoText ? 'checked' : ''}> Sin texto
          </label>
          <label style="display:inline-flex; align-items:center; gap:3px; cursor:pointer;" title="Formato vertical 9:16 para personajes">
            <input type="checkbox" class="char-rule-vertical" ${rVertical ? 'checked' : ''}> Vertical 9:16
          </label>
        </div>
        <div class="char-sliders-bar">
          <div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;">
              <span>Detalle</span>
              <strong class="char-slider-detail-val" style="color:#a5b4fc;">${rDetail}%</strong>
            </div>
            <input type="range" class="char-slider-detail" min="0" max="100" step="5" value="${rDetail}">
            <div class="slider-effect-hint char-slider-detail-hint">${getDetailEffectHtml(rDetail)}</div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;">
              <span>Realismo</span>
              <strong class="char-slider-realism-val" style="color:#a5b4fc;">${rRealism}%</strong>
            </div>
            <input type="range" class="char-slider-realism" min="0" max="100" step="5" value="${rRealism}">
            <div class="slider-effect-hint char-slider-realism-hint">${getRealismEffectHtml(rRealism)}</div>
          </div>
        </div>

        <!-- Prompt en inglés para IA gráfica -->
        <div class="char-prompt-section mt-2">
          <div class="char-prompt-header">
            <button type="button" class="btn btn-secondary btn-xs btn-optimize-prompt" data-index="${index}" title="Genera el prompt en inglés combinando descripción, opciones, detalle/realismo y estilo del proyecto">Generar prompt con IA</button>
          </div>
          <span class="char-prompt-desc">Traduce y combina descripción, opciones, detalle/realismo y estilo del proyecto.</span>
          <textarea class="char-input-prompt" rows="3" placeholder="Pulsa 'Generar prompt con IA' para crear el prompt en inglés con el estilo del proyecto...">${char.prompt_retrato || ''}</textarea>
        </div>
      </div>
      </div>

      <!-- Fila inferior completa: 4 vistas (Detalle, Frontal, Trasera, Perfil) -->
      <div class="char-4views-box">
        <div class="char-4views-header">
          <button type="button" class="btn btn-primary btn-xs btn-gen-4views" data-index="${index}" ${charImgUrl ? '' : 'disabled'} title="Genera las 4 vistas nuevas (Detalle facial, Frontal, Trasera y Perfil) a partir del diseño 3/4">
            🔄 Generar vistas
          </button>
        </div>
        <div class="char-4views-grid" id="char-4views-grid-${index}">
          ${views4Html}
        </div>
      </div>
    `;

    // Eventos de la tarjeta
    const descArea = card.querySelector(".char-input-desc");
    if (descArea) {
      descArea.addEventListener("input", () => {
        card.dataset.descDirty = "true";
      });
    }

    card.querySelectorAll(".char-rule-fullbody, .char-rule-whitebg, .char-rule-notext, .char-rule-vertical").forEach(chk => {
      chk.addEventListener("change", () => {
        card.dataset.descDirty = "true";
      });
    });

    card.querySelector(".char-slider-detail")?.addEventListener("input", (ev) => {
      const valEl = card.querySelector(".char-slider-detail-val");
      if (valEl) valEl.textContent = `${ev.target.value}%`;
      const hintEl = card.querySelector(".char-slider-detail-hint");
      if (hintEl) hintEl.innerHTML = getDetailEffectHtml(ev.target.value);
      card.dataset.descDirty = "true";
    });
    card.querySelector(".char-slider-realism")?.addEventListener("input", (ev) => {
      const valEl = card.querySelector(".char-slider-realism-val");
      if (valEl) valEl.textContent = `${ev.target.value}%`;
      const hintEl = card.querySelector(".char-slider-realism-hint");
      if (hintEl) hintEl.innerHTML = getRealismEffectHtml(ev.target.value);
      card.dataset.descDirty = "true";
    });

    card.querySelector(".btn-remove-char-card").addEventListener("click", async () => {
      await removeCharacterCard(index, char.id);
    });

    card.querySelector(".asset-history-select")?.addEventListener("change", (ev) => {
      handleRestoreAssetVersion(ev.currentTarget.closest(".asset-history-bar"));
    });
    card.querySelector(".char-approval-slot")?.addEventListener("click", async (ev) => {
      const btnToggle = ev.target.closest(".btn-toggle-char-approval");
      if (!btnToggle || !state.currentProject) return;
      const isApproved = card.dataset.estadoAprobacion === "aprobado";
      const nextAction = isApproved ? "pending" : "approve";
      btnToggle.disabled = true;
      try {
        const res = await fetch(`/api/projects/${state.currentProject.id}/characters/${card.dataset.id}/decision`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: nextAction, feedback: "", notify_telegram: false })
        });
        const data = await res.json();
        if (res.ok && data.ok) {
          const newStatus = data.status || (isApproved ? "pendiente" : "aprobado");
          card.dataset.estadoAprobacion = newStatus;
          if (data.seed_consistencia) {
            card.dataset.seedConsistencia = String(data.seed_consistencia);
            const seedEl = card.querySelector(".char-seed-code");
            if (seedEl) seedEl.textContent = String(data.seed_consistencia);
          }
          const slot = card.querySelector(".char-approval-slot");
          if (slot) slot.innerHTML = getApprovalBadgeHtml(newStatus, "");
          syncCharacterApprovalLock(card);
          showToast(
            newStatus === "aprobado"
              ? `✅ ${char.nombre || card.dataset.id} aprobado (Seed ${data.seed_consistencia || card.dataset.seedConsistencia || 'auto'} fijada como referencia)`
              : `⏳ ${char.nombre || card.dataset.id} marcado como pendiente`,
            newStatus === "aprobado" ? "success" : "info"
          );
        } else {
          showToast(data.detail || "No se pudo cambiar el estado", "error");
        }
      } catch (err) {
        showToast(`Error cambiando estado: ${err.message}`, "error");
      } finally {
        btnToggle.disabled = false;
      }
    });
    card.querySelector(".btn-gen-portrait").addEventListener("click", async () => {
      await generateCharacterPortrait(card, char.id, index);
    });
    card.querySelector(".btn-gen-4views")?.addEventListener("click", async () => {
      await generateCharacter4Views(card, char.id, index);
    });

    const btnRemoveBg = card.querySelector(".btn-remove-bg");
    if (btnRemoveBg) {
      btnRemoveBg.addEventListener("click", async () => {
        await removeCharacterBackground(index);
      });
    }

    card.querySelector(".btn-optimize-prompt").addEventListener("click", async () => {
      await optimizeCharacterPrompt(card, char.id);
    });

    card.querySelector(".btn-send-telegram-char")?.addEventListener("click", async () => {
      await sendCharacterToTelegram(char.id, index);
    });

    card.querySelector(".btn-approve-char")?.addEventListener("click", async () => {
      await applyApprovalDecision("character", char.id, "approve");
    });

    card.querySelector(".btn-reject-char")?.addEventListener("click", async () => {
      const feedback = prompt("Indica el motivo del rechazo o qué revisar porque no cuadra:", "No cuadra con la visión del personaje.");
      if (feedback !== null) {
        await applyApprovalDecision("character", char.id, "reject", feedback);
      }
    });

    card.querySelector(".btn-redo-char")?.addEventListener("click", async () => {
      if (confirm(`¿Rehacer y regenerar la propuesta para '${char.nombre || char.id}'?`)) {
        await applyApprovalDecision("character", char.id, "redo", "Rehacer porque no cuadra");
      }
    });

    card.querySelector(".input-upload-portrait").addEventListener("change", async e => {
      if (e.target.files.length > 0) {
        await uploadCharacterPortrait(index, e.target.files[0]);
      }
    });

    syncCharacterApprovalLock(card);

    return card;
  }

  function syncCharacterApprovalLock(card) {
    if (!card) return;
    const isApproved = card.dataset.estadoAprobacion === "aprobado";
    const lockMsg = "Personaje aprobado y bloqueado. Pulsa '✅ Aprobado' para volver a 'Pendiente' si quieres cambiar o regenerar.";

    const btnGen = card.querySelector(".btn-gen-portrait");
    if (btnGen) {
      btnGen.disabled = isApproved;
      btnGen.title = isApproved ? lockMsg : "Generar diseño inicial en tres cuartos (3/4) y formato vertical 9:16";
    }

    const uploadInput = card.querySelector(".input-upload-portrait");
    if (uploadInput) {
      uploadInput.disabled = isApproved;
      const lbl = uploadInput.closest("label");
      if (lbl) {
        lbl.classList.toggle("is-locked", isApproved);
        lbl.title = isApproved ? lockMsg : "Subir imagen manualmente";
      }
    }

    const histSelect = card.querySelector(".asset-history-select");
    if (histSelect) {
      histSelect.disabled = isApproved;
      histSelect.title = isApproved ? lockMsg : "Cambiar a una versión anterior";
    }
  }

  function addCharacterCard(name = "", role = "", desc = "", tipo = "humano", prompt = "") {
    const chars = collectCharactersFromUI();
    const newId = `char_${Date.now().toString().slice(-6)}`;
    chars.push({
      id: newId,
      nombre: name || `Personaje ${chars.length + 1}`,
      rol: role || "Rol",
      tipo: tipo,
      descripcion_visual: desc || "Rasgos físicos inmutables (ropa, pelo, cara)...",
      imagen_url: null,
      prompt_retrato: prompt
    });
    renderCharacterCards(chars);
  }

  btnAddCharacterCard.addEventListener("click", () => {
    addCharacterCard("", "", "");
  });

  async function removeCharacterCard(index, charId) {
    if (state.currentProject && charId) {
      try {
        await fetch(`/api/projects/${state.currentProject.id}/characters/${charId}`, {
          method: "DELETE"
        });
      } catch (e) {}
    }
    const chars = collectCharactersFromUI();
    chars.splice(index, 1);
    renderCharacterCards(chars);
    showToast("Personaje eliminado", "info");
  }

  function collectCharactersFromUI() {
    const cards = document.querySelectorAll(".char-card");
    const characters = [];
    cards.forEach((card, idx) => {
      const charId = card.dataset.id || `char_${idx+1}`;
      const name = card.querySelector(".char-input-name").value.trim();
      const role = card.querySelector(".char-input-role")?.value.trim() ?? (card.dataset.rol || "");
      const tipo = card.querySelector(".char-select-type")?.value ?? (card.dataset.tipo || "humano");
      const desc = card.querySelector(".char-input-desc").value.trim();
      const prompt = card.querySelector(".char-input-prompt")?.value.trim() || "";
      const img = card.querySelector(".char-portrait-frame img");
      const imgUrl = img ? img.getAttribute("src") : null;
      const rFull = card.querySelector(".char-rule-fullbody")?.checked ?? true;
      const rWhite = card.querySelector(".char-rule-whitebg")?.checked ?? true;
      const rNoText = card.querySelector(".char-rule-notext")?.checked ?? true;
      const rVertical = card.querySelector(".char-rule-vertical")?.checked ?? true;
      const rDetail = parseInt(card.querySelector(".char-slider-detail")?.value || "75", 10);
      const rRealism = parseInt(card.querySelector(".char-slider-realism")?.value || "75", 10);
      const formatoVista = rFull ? "cuerpo_entero" : "retrato";
      const sinFondo = rWhite;
      const reglasPersonaje = {
        hoja_4_vistas: false,
        cuerpo_entero: rFull,
        fondo_blanco: rWhite,
        sin_texto: rNoText,
        formato_vertical: rVertical,
        nivel_detalle: isNaN(rDetail) ? 75 : rDetail,
        nivel_realismo: isNaN(rRealism) ? 75 : rRealism
      };
      let vistas4Parsed = null;
      try {
        if (card.dataset.vistas4Json) vistas4Parsed = JSON.parse(card.dataset.vistas4Json);
      } catch (e) { vistas4Parsed = null; }
      const crefWeight = parseInt(card.querySelector(".char-input-cref-weight")?.value || card.dataset.crefWeight || "100", 10);
      const loraModel = card.querySelector(".char-input-lora-model")?.value.trim() ?? (card.dataset.loraModel || "");
      const loraTrigger = card.querySelector(".char-input-lora-trigger")?.value.trim() ?? (card.dataset.loraTrigger || "");

      characters.push({
        id: charId,
        nombre: name || `Personaje ${idx+1}`,
        rol: role,
        tipo: tipo,
        descripcion_visual: desc,
        imagen_url: imgUrl,
        hoja_4_vistas_url: card.dataset.hoja4VistasUrl || null,
        vistas_4: vistas4Parsed,
        prompt_retrato: prompt,
        sin_fondo: sinFondo,
        formato_vista: formatoVista,
        reglas_personaje: reglasPersonaje,
        cref_weight: isNaN(crefWeight) ? 100 : crefWeight,
        lora_model: loraModel || null,
        lora_trigger: loraTrigger || null,
        estado_aprobacion: card.dataset.estadoAprobacion || "pendiente",
        motivo_rechazo: card.dataset.motivoRechazo || "",
        telegram_message_id: card.dataset.telegramMessageId || null
      });
    });
    return characters;
  }

  // Optimizar Prompt en inglés de un personaje con IA
  async function optimizeCharacterPrompt(card, charId) {
    if (!state.currentProject) return;
    if (!card) card = document.querySelector(`.char-card[data-id="${charId}"]`);
    if (!card) return;

    const actualId = charId || card.dataset.id;
    const desc = card.querySelector(".char-input-desc")?.value.trim() || "";
    const name = card.querySelector(".char-input-name")?.value.trim() || "Personaje";
    const role = card.querySelector(".char-input-role")?.value.trim() ?? (card.dataset.rol || "");
    const tipo = card.querySelector(".char-select-type")?.value ?? (card.dataset.tipo || "humano");
    const rFull = card.querySelector(".char-rule-fullbody")?.checked ?? true;
    const rWhite = card.querySelector(".char-rule-whitebg")?.checked ?? true;
    const rNoText = card.querySelector(".char-rule-notext")?.checked ?? true;
    const rVertical = card.querySelector(".char-rule-vertical")?.checked ?? true;
    const rDetail = parseInt(card.querySelector(".char-slider-detail")?.value || "75", 10);
    const rRealism = parseInt(card.querySelector(".char-slider-realism")?.value || "75", 10);
    const formatoVista = rFull ? "cuerpo_entero" : "retrato";
    const sinFondo = rWhite;
    const reglasPersonaje = {
      hoja_4_vistas: false,
      cuerpo_entero: rFull,
      fondo_blanco: rWhite,
      sin_texto: rNoText,
      formato_vertical: rVertical,
      nivel_detalle: isNaN(rDetail) ? 75 : rDetail,
      nivel_realismo: isNaN(rRealism) ? 75 : rRealism
    };
    const stylePromptEl = document.getElementById("univ-style-prompt-en");
    const stylePromptEn = stylePromptEl ? (stylePromptEl.value || stylePromptEl.textContent || "").trim() : "";

    const btn = card.querySelector(".btn-optimize-prompt");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "⚡ Optimizando...";
    }

    setSystemStatus(
      "busy",
      `Optimizando prompt de ${name}...`,
      "Traduciendo descripción al inglés, aplicando opciones del personaje y estilo del proyecto..."
    );

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/characters/${actualId}/optimize-prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          descripcion_visual: desc,
          nombre: name,
          rol: role,
          tipo: tipo,
          formato_vista: formatoVista,
          sin_fondo: sinFondo,
          estilo_visual: univStyle ? univStyle.value : undefined,
          estilo_detalles: univStyleDetails ? univStyleDetails.value.trim() : undefined,
          estilo_prompt_en: stylePromptEn || undefined,
          reglas_personaje: reglasPersonaje
        })
      });
      const data = await res.json();
      if (data.success && data.prompt_retrato) {
        const promptInput = card.querySelector(".char-input-prompt");
        if (promptInput) promptInput.value = data.prompt_retrato;
        card.dataset.descDirty = "false";
        showToast(`¡Prompt de ${name} optimizado con IA!`, "success");
        setSystemStatus("success", `¡Prompt de ${name} optimizado!`, "Descripción actualizada en el prompt en inglés con cuerpo completo y fondo blanco puro.");
      } else {
        showToast(data.detail || "Error optimizando prompt", "error");
        setSystemStatus("error", `Error optimizando prompt de ${name}`, data.detail || "Fallo en motor de optimización.");
      }
    } catch (e) {
      showToast("Error optimizando prompt", "error");
      setSystemStatus("error", `Error optimizando prompt`, e.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "Generar prompt con IA";
      }
    }
  }

  let activeProposalContext = null;

  function applySelectedPortraitToCard(card, actualId, charName, index, data) {
    const frame = (index !== undefined ? document.getElementById(`char-frame-${index}`) : null) || card.querySelector(".char-portrait-frame");
    if (frame) {
      if (data.sin_fondo) frame.classList.add("transparent-bg");
      else frame.classList.remove("transparent-bg");
      const freshUrl = `${data.imagen_url.split('?')[0]}?t=${Date.now()}`;
      frame.innerHTML = `<img src="${freshUrl}" alt="${escapeHtml(charName)}">`;
    }
    const btn = card.querySelector(".btn-gen-portrait");
    if (btn) btn.textContent = "🎨 Regenerar 3/4";
    const btn4v = card.querySelector(".btn-gen-4views");
    if (btn4v) btn4v.disabled = false;

    if (data.seed_consistencia) {
      card.dataset.seedConsistencia = String(data.seed_consistencia);
      const seedEl = card.querySelector(".char-seed-code");
      if (seedEl) seedEl.textContent = String(data.seed_consistencia);
    }
    if (data.prompt_used) {
      const promptInput = card.querySelector(".char-input-prompt");
      if (promptInput) promptInput.value = data.prompt_used;
    }
    if (Array.isArray(data.historial_imagenes)) {
      const histSlot = card.querySelector(".char-history-slot");
      const frameIdAttr = frame ? frame.id : `char-frame-${index}`;
      if (histSlot) {
        histSlot.innerHTML = buildAssetHistoryHtml("personajes", actualId, data.historial_imagenes, frameIdAttr, data.active_version);
        histSlot.querySelector(".asset-history-select")?.addEventListener("change", (ev) => {
          handleRestoreAssetVersion(ev.currentTarget.closest(".asset-history-bar"));
        });
      }
    }
    card.dataset.estadoAprobacion = "pendiente";
    const appSlot = card.querySelector(".char-approval-slot");
    if (appSlot) {
      appSlot.innerHTML = getApprovalBadgeHtml("pendiente", "");
    }
    syncCharacterApprovalLock(card);
  }

  function applySelectedEnvironmentToCard(card, actualId, envName, index, data) {
    const frame = (index !== undefined ? document.getElementById(`env-frame-${index}`) : null) || card.querySelector(".env-preview-frame");
    if (frame) {
      const freshUrl = `${data.imagen_url.split('?')[0]}?t=${Date.now()}`;
      frame.innerHTML = `<img src="${freshUrl}" alt="${escapeHtml(envName)}">`;
    }
    const btn = card.querySelector(".btn-gen-env");
    if (btn) btn.textContent = "🎨 Regenerar";
    if (data.seed_consistencia) {
      card.dataset.seedConsistencia = String(data.seed_consistencia);
      const seedEl = card.querySelector(".env-seed-code");
      if (seedEl) seedEl.textContent = String(data.seed_consistencia);
    }
    if (data.prompt_used) {
      const promptInput = card.querySelector(".env-input-prompt");
      if (promptInput) promptInput.value = data.prompt_used;
    }
    if (Array.isArray(data.historial_imagenes)) {
      const histSlot = card.querySelector(".env-history-slot");
      const frameIdAttr = frame ? frame.id : `env-frame-${index}`;
      if (histSlot) {
        histSlot.innerHTML = buildAssetHistoryHtml("escenarios", actualId, data.historial_imagenes, frameIdAttr, data.active_version);
        histSlot.querySelector(".asset-history-select")?.addEventListener("change", (ev) => {
          handleRestoreAssetVersion(ev.currentTarget.closest(".asset-history-bar"));
        });
      }
    }
    card.dataset.estadoAprobacion = "pendiente";
    const appSlot = card.querySelector(".env-approval-slot");
    if (appSlot) {
      appSlot.innerHTML = getApprovalBadgeHtml("pendiente", "", "btn-toggle-env-approval");
    }
    syncEnvironmentApprovalLock(card);
  }

  async function loadCharacterPortraitProposals(ctx) {
    const modal = document.getElementById("modal-portrait-proposals");
    const grid = document.getElementById("proposals-grid");
    const titleEl = document.getElementById("proposals-modal-title");
    const subEl = document.getElementById("proposals-modal-subtitle");
    const btnRegen6 = document.getElementById("btn-regenerate-6-proposals");
    if (!modal || !grid) return;

    const isEnv = ctx.kind === "environment";
    const itemName = ctx.charName || ctx.envName || "Elemento";
    if (titleEl) titleEl.textContent = isEnv ? `🎨 6 propuestas de escenario para ${itemName}` : `🎨 6 propuestas 3/4 para ${itemName}`;
    if (subEl) subEl.textContent = "Generando 6 variaciones con distintas semillas para que elijas la que mejor encaja...";
    grid.innerHTML = Array.from({ length: 6 }, (_, i) => `
      <div class="proposal-card">
        <div class="proposal-skeleton">Generando #${i + 1}...</div>
      </div>
    `).join("");
    if (btnRegen6) btnRegen6.disabled = true;
    modal.classList.add("open");

    setSystemStatus(
      "busy",
      `Generando 6 propuestas de ${itemName}...`,
      `Pintando 6 variaciones en formato vertical 9:16 y técnica ${state.currentProject?.estilo_visual || 'acuarela'}...`
    );

    try {
      const genUrl = isEnv
        ? `/api/projects/${state.currentProject.id}/environments/generate-proposals`
        : `/api/projects/${state.currentProject.id}/characters/generate-portrait-proposals`;
      const genBody = isEnv
        ? {
            environment_id: ctx.actualId,
            prompt_override: ctx.promptOverride,
            provider: univImageEngine ? univImageEngine.value : "basic"
          }
        : {
            character_id: ctx.actualId,
            prompt_override: ctx.promptOverride,
            sin_fondo: ctx.sinFondo,
            formato_vista: ctx.formatoVista,
            descripcion_visual: ctx.desc,
            provider: univImageEngine ? univImageEngine.value : "basic"
          };

      const res = await fetch(genUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(genBody)
      });
      const data = await res.json();
      if (!res.ok || !data.success || !Array.isArray(data.proposals)) {
        throw new Error(data.detail || "No se pudieron generar las 6 propuestas.");
      }

      if (subEl) subEl.textContent = `Elige una de las ${data.proposals.length} propuestas para fijarla en ${itemName}.`;
      grid.innerHTML = data.proposals.map((p, idx) => `
        <div class="proposal-card">
          <div class="proposal-img-wrap">
            <img src="${p.url}" alt="Propuesta ${idx + 1}">
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.72rem; color:#94a3b8;">
            <span>Opción #${idx + 1}</span>
            <code>Seed: ${p.seed || 'auto'}</code>
          </div>
          <button type="button" class="btn btn-primary btn-xs btn-choose-proposal" data-pidx="${idx}">
            ✅ Elegir esta
          </button>
        </div>
      `).join("");

      grid.querySelectorAll(".btn-choose-proposal").forEach(choiceBtn => {
        choiceBtn.addEventListener("click", async () => {
          const p = data.proposals[Number(choiceBtn.dataset.pidx)];
          if (!p) return;
          choiceBtn.disabled = true;
          choiceBtn.textContent = "⏳ Guardando...";
          try {
            const selUrl = isEnv
              ? `/api/projects/${state.currentProject.id}/environments/select-proposal`
              : `/api/projects/${state.currentProject.id}/characters/select-portrait-proposal`;
            const selBody = isEnv
              ? {
                  environment_id: ctx.actualId,
                  file_path: p.file_path,
                  seed: p.seed,
                  provider: p.provider,
                  prompt_used: data.prompt_used
                }
              : {
                  character_id: ctx.actualId,
                  file_path: p.file_path,
                  seed: p.seed,
                  provider: p.provider,
                  prompt_used: data.prompt_used,
                  sin_fondo: ctx.sinFondo,
                  formato_vista: ctx.formatoVista
                };

            const selRes = await fetch(selUrl, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(selBody)
            });
            const selData = await selRes.json();
            if (!selRes.ok || !selData.success) {
              throw new Error(selData.detail || "Error guardando la propuesta elegida.");
            }
            modal.classList.remove("open");
            try {
              if (isEnv) applySelectedEnvironmentToCard(ctx.card, ctx.actualId, itemName, ctx.index, selData);
              else applySelectedPortraitToCard(ctx.card, ctx.actualId, itemName, ctx.index, selData);
            } catch (uiErr) {
              console.error("[applySelectedProposal]", uiErr);
            }
            showToast(`¡Propuesta #${Number(choiceBtn.dataset.pidx) + 1} aplicada a ${itemName} (Seed ${p.seed})!`, "success");
            setSystemStatus("success", `¡Diseño de ${itemName} actualizado!`, `Propuesta guardada con semilla ${p.seed}. Ya puedes aprobarlo.`);
          } catch (err) {
            showToast(err.message || "Error al seleccionar propuesta", "error");
            choiceBtn.disabled = false;
            choiceBtn.textContent = "✅ Elegir esta";
          }
        });
      });

      setSystemStatus("success", `6 propuestas listas para ${itemName}`, "Selecciona una opción en la ventana emergente.");
    } catch (err) {
      grid.innerHTML = `<div style="grid-column: 1 / -1; padding: 1rem; color: #f87171;">❌ ${escapeHtml(err.message || "Error generando propuestas")}</div>`;
      showToast(err.message || "Error generando propuestas", "error");
      setSystemStatus("error", `Error generando propuestas de ${itemName}`, err.message || "Fallo en motor de imagen.");
    } finally {
      if (btnRegen6) btnRegen6.disabled = false;
    }
  }

  document.getElementById("btn-regenerate-6-proposals")?.addEventListener("click", async () => {
    if (activeProposalContext) {
      await loadCharacterPortraitProposals(activeProposalContext);
    }
  });

  // Generar Retrato 3/4 de Personaje con IA (abre selector de 6 propuestas)
  async function generateCharacterPortrait(card, charId, index) {
    if (!state.currentProject) return;
    if (!card) card = document.querySelector(`.char-card[data-id="${charId}"]`) || document.querySelector(`.char-card[data-index="${index}"]`);
    if (!card) return;

    if (card.dataset.estadoAprobacion === "aprobado") {
      showToast("Este personaje está aprobado y bloqueado. Pulsa '✅ Aprobado' para pasarlo a Pendiente si quieres regenerarlo.", "warning");
      return;
    }

    const actualId = charId || card.dataset.id;
    const charName = card.querySelector(".char-input-name")?.value.trim() || "Personaje";

    if (card.dataset.descDirty === "true") {
      await optimizeCharacterPrompt(card, actualId);
      card.dataset.descDirty = "false";
    }

    await saveUniverse(false);

    const promptOverride = card.querySelector(".char-input-prompt")?.value.trim() || "";
    const desc = card.querySelector(".char-input-desc")?.value.trim() || "";
    const rFull = card.querySelector(".char-rule-fullbody")?.checked ?? true;
    const sinFondo = card.querySelector(".char-rule-whitebg")?.checked ?? true;
    const formatoVista = rFull ? "cuerpo_entero" : "retrato";

    activeProposalContext = {
      card,
      actualId,
      charName,
      index,
      promptOverride,
      desc,
      sinFondo,
      formatoVista
    };
    await loadCharacterPortraitProposals(activeProposalContext);
  }

  async function generateCharacter4Views(card, charId, index) {
    if (!state.currentProject) return;
    if (!card) card = document.querySelector(`.char-card[data-id="${charId}"]`);
    if (!card) return;

    const actualId = charId || card.dataset.id;
    const charName = card.querySelector(".char-input-name")?.value.trim() || actualId;
    const btn4v = card.querySelector(".btn-gen-4views");
    if (btn4v) {
      btn4v.disabled = true;
      btn4v.textContent = "🔄 Generando 4 vistas...";
    }

    setSystemStatus(
      "busy",
      `Generando 4 vistas de ${charName}...`,
      "Usando FLUX Kontext con el diseño 3/4 como referencia para crear vista frontal, trasera y perfil..."
    );

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/characters/${actualId}/generate-4-views`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: univImageEngine ? univImageEngine.value : "fal_flux_dev"
        })
      });
      const data = await res.json();
      if (data.success && (data.vistas_4 || data.hoja_4_vistas_url)) {
        if (data.hoja_4_vistas_url) card.dataset.hoja4VistasUrl = data.hoja_4_vistas_url;
        if (data.vistas_4) card.dataset.vistas4Json = JSON.stringify(data.vistas_4);
        const grid4v = (index !== undefined ? document.getElementById(`char-4views-grid-${index}`) : null) || card.querySelector(".char-4views-grid");
        if (grid4v && data.vistas_4) {
          grid4v.innerHTML = render4ViewsGridHtml(data.vistas_4, charName);
        }
        showToast(`¡4 vistas de ${charName} generadas! Pulsa cualquier cuadradito para ampliarlo.`, "success");
        setSystemStatus("success", `¡4 vistas de ${charName} listas!`, "Pulsa sobre cualquier cuadradito para verlo en grande.");
      } else {
        showToast(data.detail || "Error generando las 4 vistas", "error");
        setSystemStatus("error", `Error en 4 vistas de ${charName}`, data.detail || "No se pudo generar la hoja de 4 vistas.");
      }
    } catch (e) {
      showToast("Error conectando para generar las 4 vistas", "error");
      setSystemStatus("error", `Error en 4 vistas de ${charName}`, "Fallo de conexión con el motor gráfico.");
    } finally {
      if (btn4v) {
        btn4v.disabled = false;
        btn4v.textContent = "🔄 Generar vistas";
      }
    }
  }

  // Quitar Fondo a personaje existente con rembg
  async function removeCharacterBackground(index) {
    if (!state.currentProject) return;
    const card = document.querySelector(`.char-card[data-index="${index}"]`);
    if (!card) return;
    const charId = card.dataset.id;
    const charName = card.querySelector(".char-input-name")?.value || "Personaje";
    const btn = card.querySelector(".btn-remove-bg");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "✂️ Recortando...";
    }
    setSystemStatus("busy", `Recortando fondo de ${charName}...`, "Eliminando fondo con rembg para generar PNG transparente...");
    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/characters/${charId}/remove-bg`, {
        method: "POST"
      });
      const data = await res.json();
      if (data.success && data.imagen_url) {
        const frame = document.getElementById(`char-frame-${index}`);
        frame.classList.add("transparent-bg");
        const freshUrl = `${data.imagen_url.split('?')[0]}?t=${Date.now()}`;
        frame.innerHTML = `<img src="${freshUrl}" alt="${charName}">`;
        showToast("¡Fondo eliminado con éxito (PNG transparente guardado)!", "success");
        setSystemStatus("success", `¡Fondo de ${charName} eliminado!`, "Recorte transparente PNG generado con éxito.");
      } else {
        showToast(data.detail || "Error eliminando fondo", "error");
        setSystemStatus("error", `Error recortando fondo de ${charName}`, data.detail || "Error en rembg.");
      }
    } catch (e) {
      showToast("Error procesando eliminación de fondo", "error");
      setSystemStatus("error", `Error recortando fondo`, "Error de conexión con el servicio de rembg.");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "✂️ Sin Fondo";
      }
    }
  }

  // Subir Foto Propia para un personaje
  async function uploadCharacterPortrait(index, file) {
    if (!state.currentProject) return;

    const card = document.querySelector(`.char-card[data-index="${index}"]`);
    if (!card) return;
    const charId = card.dataset.id;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/characters/${charId}/upload-portrait`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (data.success && data.imagen_url) {
        const frame = document.getElementById(`char-frame-${index}`);
        frame.innerHTML = `<img src="${data.imagen_url}" alt="Personaje">`;
        showToast("Foto de referencia subida y adaptada", "success");
      }
    } catch (e) {
      showToast("Error subiendo foto del personaje", "error");
    }
  }

  // ========================================================
  // 5.B GESTIÓN DE LA BIBLIA DE ESCENARIOS DEL ENTORNO
  // ========================================================
  function renderEnvironmentCards(environments) {
    if (!environmentsCardsGrid) return;
    environmentsCardsGrid.innerHTML = "";

    if (!environments || environments.length === 0) {
      environmentsCardsGrid.innerHTML = `
        <div class="card" style="grid-column: 1 / -1; text-align: center; padding: 2rem;">
          <p class="text-muted">No hay escenarios registrados aún en el universo.</p>
          <button class="btn btn-primary btn-sm mt-2" id="btn-add-first-env">➕ Añadir Primer Escenario</button>
        </div>
      `;
      document.getElementById("btn-add-first-env")?.addEventListener("click", () => addEnvironmentCard());
      return;
    }

    environments.forEach((env, index) => {
      const card = createEnvironmentCardElement(env, index);
      environmentsCardsGrid.appendChild(card);
    });
    renderRecurrentEnvsGrid(environments, state.currentProject?.referencia_escenario_id || null);
  }

  function createEnvironmentCardElement(env, index) {
    const card = document.createElement("div");
    card.className = "env-card";
    card.dataset.index = index;
    card.dataset.id = env.id || `esc_${index+1}`;
    card.dataset.tipo = env.tipo || "exterior_urbano";
    card.dataset.estadoAprobacion = env.estado_aprobacion || (env.imagen_url ? "aprobado" : "pendiente");
    card.dataset.motivoRechazo = env.motivo_rechazo || "";
    card.dataset.seedConsistencia = env.seed_consistencia || "";

    let envImgUrl = env.imagen_url;
    if (envImgUrl) {
      const baseUrl = envImgUrl.split("?")[0];
      envImgUrl = `${baseUrl}?t=${Date.now()}`;
    }

    const previewHtml = envImgUrl
      ? `<img src="${envImgUrl}" alt="${env.nombre}">`
      : `<div class="env-placeholder">
           <span class="env-placeholder-icon">🏛️</span>
           <small>Sin arte 9:16</small>
         </div>`;

    const projRules = (typeof getGenerationRulesFromUI === "function") ? getGenerationRulesFromUI() : {};
    const envRules = env.reglas_escenario || {};
    const rNoPeople = envRules.escenarios_sin_personas ?? envRules.sin_personas ?? projRules.escenarios_sin_personas ?? true;
    const rNoText = envRules.sin_texto ?? projRules.sin_texto ?? true;
    const rVertical = envRules.formato_vertical ?? projRules.formato_vertical ?? true;
    const rDetail = Number.isFinite(Number(envRules.nivel_detalle)) ? Number(envRules.nivel_detalle) : 75;
    const rRealism = Number.isFinite(Number(envRules.nivel_realismo)) ? Number(envRules.nivel_realismo) : 75;

    const approvalStatus = card.dataset.estadoAprobacion;
    const statusBadge = getApprovalBadgeHtml(approvalStatus, card.dataset.motivoRechazo, "btn-toggle-env-approval");

    card.innerHTML = `
      <!-- Columna Visual del Escenario -->
      <div class="env-preview-box">
        <div class="env-preview-frame" id="env-frame-${index}">
          ${previewHtml}
        </div>
        <div style="display:flex; flex-direction:column; align-items:center; gap:4px; margin-top:6px;">
          <div class="env-approval-slot">${statusBadge}</div>
          <div style="font-size:0.71rem; color:#94a3b8; text-align:center; line-height:1.3;">
            Ref: <code>${escapeHtml(card.dataset.id)}</code> · Seed: <code class="env-seed-code">${env.seed_consistencia || 'auto'}</code>
          </div>
        </div>
        <div class="env-preview-actions">
          <button class="btn btn-secondary btn-xs btn-gen-env" data-index="${index}" title="Generar 6 propuestas de escenario en formato vertical 9:16">
            🎨 ${env.imagen_url ? 'Regenerar' : 'Generar'}
          </button>
          <label class="btn btn-ghost btn-xs">
            📁 Subir
            <input type="file" class="input-upload-env" data-index="${index}" accept="image/*" style="display:none;">
          </label>
        </div>
        <div class="env-history-slot">
          ${buildAssetHistoryHtml("escenarios", card.dataset.id, env.historial_imagenes || [], `env-frame-${index}`, env.active_version)}
        </div>
      </div>

      <!-- Columna Detalles del Escenario -->
      <div class="env-details-box">
        <div class="env-details-header" style="display: flex; gap: 0.5rem; align-items: center;">
          <input type="text" class="env-input-name" placeholder="Nombre del Escenario (ej: Calles de Moguer)" value="${env.nombre || ''}" style="flex: 1;">
          <button class="btn-remove-env-card" data-index="${index}" title="Eliminar escenario">&times;</button>
        </div>
        <label class="char-desc-label mt-2" style="display:block; font-size:0.71rem; font-weight:600; color:#94a3b8; margin-bottom:2px;">Descripción del escenario</label>
        <textarea class="env-input-desc" rows="3" placeholder="Descripción visual detallada (arquitectura, colores, iluminación, clima)...">${env.descripcion_visual || ''}</textarea>

        <!-- Opciones generales del escenario (heredan de 2. Estilo visual) -->
        <div class="char-rules-bar mt-2" style="display:flex; flex-wrap:wrap; gap:0.55rem; align-items:center; padding:5px 8px; border-radius:6px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); font-size:0.75rem;">
          <span style="color:#94a3b8; font-weight:600;">Opciones:</span>
          <label style="display:inline-flex; align-items:center; gap:3px; cursor:pointer;" title="Escenario limpio sin personas ni personajes">
            <input type="checkbox" class="env-rule-nopeople" ${rNoPeople ? 'checked' : ''}> Sin personas
          </label>
          <label style="display:inline-flex; align-items:center; gap:3px; cursor:pointer;" title="Prohibir textos, etiquetas o carteles en la imagen">
            <input type="checkbox" class="env-rule-notext" ${rNoText ? 'checked' : ''}> Sin texto
          </label>
          <label style="display:inline-flex; align-items:center; gap:3px; cursor:pointer;" title="Formato vertical 9:16 para escenarios">
            <input type="checkbox" class="env-rule-vertical" ${rVertical ? 'checked' : ''}> Vertical 9:16
          </label>
        </div>
        <div class="char-sliders-bar">
          <div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;">
              <span>Detalle</span>
              <strong class="env-slider-detail-val" style="color:#a5b4fc;">${rDetail}%</strong>
            </div>
            <input type="range" class="env-slider-detail" min="0" max="100" step="5" value="${rDetail}">
            <div class="slider-effect-hint env-slider-detail-hint">${getDetailEffectHtml(rDetail)}</div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;">
              <span>Realismo</span>
              <strong class="env-slider-realism-val" style="color:#a5b4fc;">${rRealism}%</strong>
            </div>
            <input type="range" class="env-slider-realism" min="0" max="100" step="5" value="${rRealism}">
            <div class="slider-effect-hint env-slider-realism-hint">${getRealismEffectHtml(rRealism)}</div>
          </div>
        </div>

        <!-- Prompt en inglés para IA gráfica -->
        <div class="char-prompt-section mt-2">
          <div class="char-prompt-header">
            <button type="button" class="btn btn-secondary btn-xs btn-optimize-env-prompt" data-index="${index}" title="Genera el prompt en inglés combinando descripción, opciones, detalle/realismo y estilo del proyecto">Generar prompt con IA</button>
          </div>
          <span class="char-prompt-desc">Traduce y combina descripción, opciones, detalle/realismo y estilo del proyecto.</span>
          <textarea class="env-input-prompt" rows="3" placeholder="Pulsa 'Generar prompt con IA' para crear el prompt en inglés con el estilo del proyecto...">${env.prompt_escenario || ''}</textarea>
        </div>
      </div>
    `;

    // Eventos
    card.querySelector(".btn-remove-env-card").addEventListener("click", async () => {
      await removeEnvironmentCard(index, env.id);
    });

    card.querySelector(".asset-history-select")?.addEventListener("change", (ev) => {
      handleRestoreAssetVersion(ev.currentTarget.closest(".asset-history-bar"));
    });
    card.querySelector(".env-approval-slot")?.addEventListener("click", async (ev) => {
      const btnToggle = ev.target.closest(".btn-toggle-env-approval");
      if (!btnToggle || !state.currentProject) return;
      const isApproved = card.dataset.estadoAprobacion === "aprobado";
      const nextAction = isApproved ? "pending" : "approve";
      btnToggle.disabled = true;
      try {
        const res = await fetch(`/api/projects/${state.currentProject.id}/environments/${card.dataset.id}/decision`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: nextAction, feedback: "", notify_telegram: false })
        });
        const data = await res.json();
        if (res.ok && data.ok) {
          const newStatus = data.status || (isApproved ? "pendiente" : "aprobado");
          card.dataset.estadoAprobacion = newStatus;
          if (data.seed_consistencia) {
            card.dataset.seedConsistencia = String(data.seed_consistencia);
            const seedEl = card.querySelector(".env-seed-code");
            if (seedEl) seedEl.textContent = String(data.seed_consistencia);
          }
          const slot = card.querySelector(".env-approval-slot");
          if (slot) slot.innerHTML = getApprovalBadgeHtml(newStatus, "", "btn-toggle-env-approval");
          syncEnvironmentApprovalLock(card);
          showToast(
            newStatus === "aprobado"
              ? `✅ ${env.nombre || card.dataset.id} aprobado (Seed ${data.seed_consistencia || card.dataset.seedConsistencia || 'auto'} fijada como referencia)`
              : `⏳ ${env.nombre || card.dataset.id} marcado como pendiente`,
            newStatus === "aprobado" ? "success" : "info"
          );
        } else {
          showToast(data.detail || "No se pudo cambiar el estado", "error");
        }
      } catch (err) {
        showToast(`Error cambiando estado: ${err.message}`, "error");
      } finally {
        btnToggle.disabled = false;
      }
    });
    card.querySelector(".btn-gen-env").addEventListener("click", async () => {
      await generateEnvironmentImage(index);
    });

    card.querySelector(".env-slider-detail")?.addEventListener("input", (ev) => {
      const v = Number(ev.target.value);
      const valEl = card.querySelector(".env-slider-detail-val");
      if (valEl) valEl.textContent = `${v}%`;
      const hintEl = card.querySelector(".env-slider-detail-hint");
      if (hintEl) hintEl.innerHTML = getDetailEffectHtml(v);
    });
    card.querySelector(".env-slider-realism")?.addEventListener("input", (ev) => {
      const v = Number(ev.target.value);
      const valEl = card.querySelector(".env-slider-realism-val");
      if (valEl) valEl.textContent = `${v}%`;
      const hintEl = card.querySelector(".env-slider-realism-hint");
      if (hintEl) hintEl.innerHTML = getRealismEffectHtml(v);
    });

    card.querySelector(".btn-optimize-env-prompt").addEventListener("click", async () => {
      await optimizeEnvironmentPrompt(card, card.dataset.id);
    });

    card.querySelector(".input-upload-env").addEventListener("change", async e => {
      if (e.target.files.length > 0) {
        await uploadEnvironmentImage(index, e.target.files[0]);
      }
    });

    syncEnvironmentApprovalLock(card);

    return card;
  }

  function syncEnvironmentApprovalLock(card) {
    if (!card) return;
    const isApproved = card.dataset.estadoAprobacion === "aprobado";
    const lockMsg = "Escenario aprobado y bloqueado. Pulsa '✅ Aprobado' para volver a 'Pendiente' si quieres cambiar o regenerar.";

    const btnGen = card.querySelector(".btn-gen-env");
    if (btnGen) {
      btnGen.disabled = isApproved;
      btnGen.title = isApproved ? lockMsg : "Generar 6 propuestas de escenario en formato vertical 9:16";
    }

    const uploadInput = card.querySelector(".input-upload-env");
    if (uploadInput) {
      uploadInput.disabled = isApproved;
      const lbl = uploadInput.closest("label");
      if (lbl) {
        lbl.classList.toggle("is-locked", isApproved);
        lbl.title = isApproved ? lockMsg : "Subir imagen manualmente";
      }
    }

    const histSelect = card.querySelector(".asset-history-select");
    if (histSelect) {
      histSelect.disabled = isApproved;
      histSelect.title = isApproved ? lockMsg : "Cambiar a una versión anterior";
    }
  }

  function addEnvironmentCard(name = "", tipo = "exterior_urbano", desc = "", prompt = "") {
    const envs = collectEnvironmentsFromUI();
    const newId = `esc_${Date.now().toString().slice(-6)}`;
    envs.push({
      id: newId,
      nombre: name || `Escenario ${envs.length + 1}`,
      tipo: tipo,
      descripcion_visual: desc || "Descripción del entorno (fachadas, luz, paisaje)...",
      imagen_url: null,
      prompt_escenario: prompt || ""
    });
    renderEnvironmentCards(envs);
  }

  async function removeEnvironmentCard(index, envId) {
    if (confirm("¿Eliminar este escenario del proyecto?")) {
      if (state.currentProject && envId) {
        try {
          await fetch(`/api/projects/${state.currentProject.id}/environments/${envId}`, { method: "DELETE" });
        } catch (e) {}
      }
      const envs = collectEnvironmentsFromUI();
      envs.splice(index, 1);
      renderEnvironmentCards(envs);
      await saveUniverse(false);
      showToast("Escenario eliminado", "info");
    }
  }

  function collectEnvironmentsFromUI() {
    if (!environmentsCardsGrid) return [];
    const cards = environmentsCardsGrid.querySelectorAll(".env-card");
    const environments = [];
    cards.forEach((card, idx) => {
      const imgEl = card.querySelector(".env-preview-frame img");
      const rNoPeople = card.querySelector(".env-rule-nopeople")?.checked ?? true;
      const rNoText = card.querySelector(".env-rule-notext")?.checked ?? true;
      const rVertical = card.querySelector(".env-rule-vertical")?.checked ?? true;
      const rDetail = parseInt(card.querySelector(".env-slider-detail")?.value || "75", 10);
      const rRealism = parseInt(card.querySelector(".env-slider-realism")?.value || "75", 10);
      environments.push({
        id: card.dataset.id || `esc_${idx+1}`,
        nombre: card.querySelector(".env-input-name")?.value.trim() || `Escenario ${idx+1}`,
        tipo: card.dataset.tipo || "exterior_urbano",
        descripcion_visual: card.querySelector(".env-input-desc")?.value.trim() || "",
        imagen_url: imgEl ? imgEl.getAttribute("src") : null,
        prompt_escenario: card.querySelector(".env-input-prompt")?.value.trim() || "",
        reglas_escenario: {
          escenarios_sin_personas: rNoPeople,
          sin_texto: rNoText,
          formato_vertical: rVertical,
          nivel_detalle: isNaN(rDetail) ? 75 : rDetail,
          nivel_realismo: isNaN(rRealism) ? 75 : rRealism
        },
        estado_aprobacion: card.dataset.estadoAprobacion || "pendiente",
        motivo_rechazo: card.dataset.motivoRechazo || "",
        seed_consistencia: card.dataset.seedConsistencia ? Number(card.dataset.seedConsistencia) : null
      });
    });
    return environments;
  }

  async function optimizeEnvironmentPrompt(card, envId) {
    if (!state.currentProject) return;
    if (!card) card = document.querySelector(`.env-card[data-id="${envId}"]`);
    if (!card) return;

    const actualId = envId || card.dataset.id;
    const name = card.querySelector(".env-input-name")?.value.trim() || "Escenario";
    const desc = card.querySelector(".env-input-desc")?.value.trim() || "";
    const tipo = card.dataset.tipo || "exterior_urbano";
    const rNoPeople = card.querySelector(".env-rule-nopeople")?.checked ?? true;
    const rNoText = card.querySelector(".env-rule-notext")?.checked ?? true;
    const rVertical = card.querySelector(".env-rule-vertical")?.checked ?? true;
    const rDetail = parseInt(card.querySelector(".env-slider-detail")?.value || "75", 10);
    const rRealism = parseInt(card.querySelector(".env-slider-realism")?.value || "75", 10);
    const reglasEscenario = {
      escenarios_sin_personas: rNoPeople,
      sin_texto: rNoText,
      formato_vertical: rVertical,
      nivel_detalle: isNaN(rDetail) ? 75 : rDetail,
      nivel_realismo: isNaN(rRealism) ? 75 : rRealism
    };
    const stylePromptEl = document.getElementById("univ-style-prompt-en");
    const stylePromptEn = stylePromptEl ? (stylePromptEl.value || stylePromptEl.textContent || "").trim() : "";

    const btn = card.querySelector(".btn-optimize-env-prompt");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "⏳ Optimizando...";
    }

    setSystemStatus(
      "busy",
      `Optimizando prompt de ${name}...`,
      "Traduciendo descripción al inglés, aplicando opciones del escenario y estilo del proyecto..."
    );

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/environments/${actualId}/optimize-prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre: name,
          descripcion_visual: desc,
          tipo: tipo,
          estilo_visual: univStyle ? univStyle.value : undefined,
          estilo_detalles: univStyleDetails ? univStyleDetails.value.trim() : undefined,
          estilo_prompt_en: stylePromptEn || undefined,
          reglas_escenario: reglasEscenario
        })
      });
      const data = await res.json();
      if (res.ok && data.success && data.prompt_escenario) {
        const promptInput = card.querySelector(".env-input-prompt");
        if (promptInput) promptInput.value = data.prompt_escenario;
        setSystemStatus("success", `Prompt de ${name} optimizado`, "Incluye estilo del proyecto, descripción y opciones del escenario.");
        showToast("¡Prompt de escenario optimizado con estilo, descripción y opciones!", "success");
      } else {
        setSystemStatus("error", "Error optimizando prompt de escenario", data.detail || "No se pudo optimizar");
        showToast(data.detail || "Error optimizando prompt de escenario", "error");
      }
    } catch (e) {
      setSystemStatus("error", "Error optimizando prompt de escenario", e.message);
      showToast("Error optimizando prompt de escenario", "error");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "Generar prompt con IA";
      }
    }
  }

  async function generateEnvironmentImage(index) {
    if (!state.currentProject) return;
    const card = document.querySelector(`.env-card[data-index="${index}"]`);
    if (!card) return;
    if (card.dataset.estadoAprobacion === "aprobado") {
      showToast("Este escenario está aprobado y bloqueado. Pulsa '✅ Aprobado' para pasarlo a Pendiente si quieres regenerarlo.", "warning");
      return;
    }
    await saveUniverse(false);
    const envId = card.dataset.id;
    const envName = card.querySelector(".env-input-name")?.value.trim() || "Escenario";
    const promptOverride = card.querySelector(".env-input-prompt")?.value.trim() || "";

    activeProposalContext = {
      kind: "environment",
      card,
      actualId: envId,
      envName,
      index,
      promptOverride
    };
    await loadCharacterPortraitProposals(activeProposalContext);
  }

  async function uploadEnvironmentImage(index, file) {
    if (!state.currentProject) return;
    const card = document.querySelector(`.env-card[data-index="${index}"]`);
    if (!card) return;
    const envId = card.dataset.id;
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/environments/${envId}/upload`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (data.success && data.imagen_url) {
        const frame = document.getElementById(`env-frame-${index}`);
        frame.innerHTML = `<img src="${data.imagen_url}" alt="Escenario">`;
        showToast("Imagen de escenario guardada", "success");
      }
    } catch (e) {
      showToast("Error subiendo imagen de escenario", "error");
    }
  }

  btnAddEnvironmentCard?.addEventListener("click", () => addEnvironmentCard());

  // ========================================================
  // FUNCIONES DE APROBACIÓN HUMAN-IN-THE-LOOP (TELEGRAM)
  // ========================================================
  async function sendCharacterToTelegram(charId, index) {
    if (!state.currentProject) return;
    showToast(`Enviando propuesta de personaje a Telegram...`, "info");
    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/characters/${charId}/send-telegram-approval`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ auto_generate: true })
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        showToast("✅ Propuesta de personaje enviada a Telegram con éxito", "success");
        await loadProjectDetails(state.currentProject.id);
      } else {
        showToast(`Error al enviar a Telegram: ${data.detail || data.error || "Fallo"}`, "error");
      }
    } catch (e) {
      showToast(`Error de red: ${e.message}`, "error");
    }
  }

  async function sendEnvironmentToTelegram(envId, index) {
    if (!state.currentProject) return;
    showToast(`Enviando propuesta de escenario a Telegram...`, "info");
    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/environments/${envId}/send-telegram-approval`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ auto_generate: true })
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        showToast("✅ Propuesta de escenario enviada a Telegram con éxito", "success");
        await loadProjectDetails(state.currentProject.id);
      } else {
        showToast(`Error al enviar a Telegram: ${data.detail || data.error || "Fallo"}`, "error");
      }
    } catch (e) {
      showToast(`Error de red: ${e.message}`, "error");
    }
  }

  async function applyApprovalDecision(itemType, itemId, action, feedback = "") {
    if (!state.currentProject) return;
    const endpoint = itemType === "character"
      ? `/api/projects/${state.currentProject.id}/characters/${itemId}/decision`
      : `/api/projects/${state.currentProject.id}/environments/${itemId}/decision`;

    showToast(`Procesando decisión (${action})...`, "info");
    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, feedback, notify_telegram: true })
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        showToast(`✅ Decisión aplicada: ${action.toUpperCase()}`, "success");
        await loadProjectDetails(state.currentProject.id);
      } else {
        showToast(`Error: ${data.detail || data.error || "Error al aplicar"}`, "error");
      }
    } catch (e) {
      showToast(`Error: ${e.message}`, "error");
    }
  }

  async function sendAllInitialProposalsToTelegram() {
    if (!state.currentProject) {
      showToast("Selecciona primero un proyecto", "warning");
      return;
    }
    if (!confirm(`¿Enviar todas las propuestas iniciales de personajes y escenarios de '${state.currentProject.titulo}' a Telegram?`)) {
      return;
    }
    showToast("Enviando propuestas iniciales a Telegram...", "info");
    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/send-initial-proposals`, { method: "POST" });
      const data = await res.json();
      if (res.ok && data.ok) {
        showToast(`✅ Enviadas ${data.sent_characters.length} personajes y ${data.sent_environments.length} escenarios a Telegram`, "success");
        await loadProjectDetails(state.currentProject.id);
      } else {
        showToast(`Error: ${data.detail || "Fallo al enviar"}`, "error");
      }
    } catch (e) {
      showToast(`Error de red: ${e.message}`, "error");
    }
  }

  async function syncTelegramUpdates() {
    showToast("Consultando respuestas en Telegram...", "info");
    try {
      const res = await fetch("/api/telegram/poll-now", { method: "POST" });
      const data = await res.json();
      if (res.ok && data.ok) {
        if (data.processed_count > 0) {
          showToast(`✅ Se procesaron ${data.processed_count} respuesta(s) de Telegram`, "success");
          if (state.currentProject) {
            await loadProjectDetails(state.currentProject.id);
          }
        } else {
          showToast("No hay respuestas nuevas pendientes en Telegram", "info");
        }
      } else {
        showToast(`Error: ${data.detail || data.error || "Fallo"}`, "error");
      }
    } catch (e) {
      showToast(`Error: ${e.message}`, "error");
    }
  }

  async function syncCharacterBank() {
    if (!state.currentProject) {
      showToast("Selecciona un proyecto primero", "warning");
      return;
    }
    await saveUniverse(false);
    const btn = document.getElementById("btn-sync-character-bank");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "⏳ Catalogando...";
    }
    setSystemStatus("busy", "Sincronizando Banco de Consistencia (--cref / LoRA)...", "Catalogando hojas de referencia de personajes principales y directivas para el generador de prompts...");
    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/character-bank/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ auto_generate_missing: false })
      });
      const data = await res.json();
      if (data.success) {
        await selectProject(state.currentProject.id);
        showToast(`✅ Banco de Consistencia catalogado: ${data.referencias_listas}/${data.total_personajes} hojas de referencia listas (--cref / LoRA)`, "success");
        setSystemStatus("success", "Banco de Consistencia sincronizado", `${data.referencias_listas} de ${data.total_personajes} personajes con hoja de referencia lista.`);
      } else {
        showToast(data.detail || "Error sincronizando banco", "error");
        setSystemStatus("error", "Error en Banco de Consistencia", data.detail || "");
      }
    } catch (e) {
      showToast(`Error: ${e.message}`, "error");
      setSystemStatus("error", "Error de red", e.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "🗂️ Catalogar Banco (--cref / LoRA)";
      }
    }
  }

  document.getElementById("btn-sync-character-bank")?.addEventListener("click", syncCharacterBank);
  document.getElementById("btn-telegram-proposals-all")?.addEventListener("click", sendAllInitialProposalsToTelegram);
  document.getElementById("btn-telegram-poll")?.addEventListener("click", syncTelegramUpdates);

  // Guardar Universo del Proyecto
  async function saveUniverse(showFeedback = true) {
    if (!state.currentProject || state.universeRenderedOk === false) return;

    const title = univTitle.value.trim() || state.currentProject.titulo;
    const chars = collectCharactersFromUI();
    const envs = collectEnvironmentsFromUI();

    const activeVoice = (narratorVoiceSelect ? narratorVoiceSelect.value : null) || (univVoice ? univVoice.value : null) || "openai_fable";
    const narratorProfile = {
      nombre: narratorName ? narratorName.value.trim() : "El Poeta / Muchacho de Moguer (Narrador Lírico)",
      genero: narratorGender ? narratorGender.value : "masculino",
      edad_aprox: narratorAge ? narratorAge.value.trim() : "12-14 años (Joven / Adolescente)",
      rango_edad: narratorAgeBracket ? narratorAgeBracket.value : "joven",
      tono: narratorTone ? narratorTone.value.trim() : "Lírico, contemplativo, tierno, pausado y reflexivo",
      justificacion: narratorJustification ? narratorJustification.value.trim() : "",
      voz_recomendada: activeVoice,
      texto_muestra: narratorSampleText ? narratorSampleText.value.trim() : ""
    };

    const payload = {
      id: state.currentProject.id,
      titulo: title,
      descripcion: state.currentProject.descripcion || "",
      audiencia: univAudience.value,
      ambiente: univAmbient.value.trim(),
      estilo_visual: univStyle.value,
      estilo_detalles: univStyleDetails ? univStyleDetails.value.trim() : "",
      reglas_generacion: getGenerationRulesFromUI(),
      motor_imagenes: univImageEngine ? univImageEngine.value : "flux",
      voz_defecto: activeVoice,
      perfil_narrador: narratorProfile,
      personajes_recurrentes_texto: univRecurrentChars ? univRecurrentChars.value.trim() : "",
      referencia_personaje_id: state.currentProject?.referencia_personaje_id || null,
      referencia_escenario_id: state.currentProject?.referencia_escenario_id || null,
      personajes: chars,
      escenarios: envs
    };

    try {
      const res = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        state.currentProject = data.project;
        updateMiniBanner();
        if (showFeedback) {
          showToast("¡Universo, personajes, escenarios y narrador guardados correctamente!", "success");
        }
      }
    } catch (e) {
      if (showFeedback) showToast("Error guardando universo", "error");
    }
  }

  btnSaveUniverse.addEventListener("click", () => saveUniverse(true));

  // ========================================================
  // SECCIÓN 5: CONTROLADORES DE NARRADOR & ESTUDIO DE VOZ
  // ========================================================
  if (univVoice) {
    univVoice.addEventListener("change", () => {
      updateSelectedVoiceCard(univVoice.value);
    });
  }

  if (narratorVoiceSelect) {
    narratorVoiceSelect.addEventListener("change", () => {
      updateSelectedVoiceCard(narratorVoiceSelect.value);
    });
  }

  // Audición rápida al hacer clic en las pastillas de voz
  document.addEventListener("click", e => {
    const quickBtn = e.target.closest(".btn-quick-voice");
    if (quickBtn) {
      const voice = quickBtn.dataset.voice;
      if (voice) {
        updateSelectedVoiceCard(voice);
        testNarratorVoice(voice);
      }
    }
  });

  // Restaurar fragmento de prueba original
  if (btnResetSampleText) {
    btnResetSampleText.addEventListener("click", () => {
      if (narratorSampleText) {
        narratorSampleText.value = "Platero es pequeño, peludo, suave; tan blando por fuera, que se diría todo de algodón, que no lleva huesos. Sólo los espejos de azabache de sus ojos son duros cual dos escarabajos de cristal negro.";
        showToast("Fragmento de prueba restaurado al texto de Platero", "info");
      }
    });
  }

  // Generador de prueba de voz interactivo en tiempo real
  async function testNarratorVoice(voiceIdOverride = null) {
    if (!state.currentProject) {
      showToast("Selecciona un proyecto primero", "warning");
      return;
    }

    const voiceId = voiceIdOverride || (narratorVoiceSelect ? narratorVoiceSelect.value : (univVoice ? univVoice.value : null)) || "openai_fable";
    const sample = (narratorSampleText ? narratorSampleText.value.trim() : "") || "Platero es pequeño, peludo, suave; tan blando por fuera, que se diría todo de algodón, que no lleva huesos.";

    if (btnTestNarratorVoice) {
      btnTestNarratorVoice.disabled = true;
      btnTestNarratorVoice.innerHTML = '<span class="btn-icon-symbol">⏳</span> Sintetizando Audio...';
    }
    if (voiceTestStatus) {
      voiceTestStatus.textContent = "Generando audio en tiempo real con IA...";
    }

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/narrator/test-voice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          voice_id: voiceId,
          sample_text: sample
        })
      });
      const data = await res.json();
      if (data.success && data.url) {
        if (audioAuditionPlayerCard) audioAuditionPlayerCard.style.display = "block";
        const v = state.voicesCatalog?.find(x => x.id === voiceId || x.voice_id === voiceId);
        if (playerVoiceTitle) {
          playerVoiceTitle.textContent = `Audición: ${v ? v.name : voiceId}`;
        }
        if (playerDurationBadge) {
          playerDurationBadge.textContent = `${data.duration}s`;
        }
        if (narratorAudioElement) {
          narratorAudioElement.src = data.url;
          narratorAudioElement.play().catch(() => {});
        }
        if (voiceTestStatus) {
          voiceTestStatus.textContent = `✅ Sintetizado con ${data.provider.toUpperCase()} (${data.duration}s)`;
        }
        showToast(`Muestra generada con éxito (${data.duration}s)`, "success");
      } else {
        showToast(data.detail || "Error sintetizando muestra de voz", "error");
        if (voiceTestStatus) voiceTestStatus.textContent = "Fallo en la síntesis";
      }
    } catch (e) {
      showToast("Error de conexión al sintetizar voz", "error");
      if (voiceTestStatus) voiceTestStatus.textContent = "Error de conexión";
    } finally {
      if (btnTestNarratorVoice) {
        btnTestNarratorVoice.disabled = false;
        btnTestNarratorVoice.innerHTML = '<span class="btn-icon-symbol">▶</span> Probar Voz Seleccionada';
      }
    }
  }

  if (btnTestNarratorVoice) {
    btnTestNarratorVoice.addEventListener("click", () => testNarratorVoice());
  }

  // Proponer narrador según la especificación del perfil superior
  if (btnAiRecommendNarrator) {
    btnAiRecommendNarrator.addEventListener("click", async () => {
      if (!state.currentProject) {
        showToast("Selecciona un proyecto primero", "warning");
        return;
      }

      btnAiRecommendNarrator.disabled = true;
      btnAiRecommendNarrator.innerHTML = '<span class="btn-icon-symbol">⏳</span> Buscando narrador acorde...';
      setSystemStatus("busy", "Proponiendo narrador...", "Evaluando la especificación narrativa de arriba para elegir la voz más adecuada...");

      const specPayload = {
        nombre: narratorNameInput ? narratorNameInput.value.trim() : "",
        genero: narratorGenderSelect ? narratorGenderSelect.value : "masculino",
        edad_aprox: narratorAgeInput ? narratorAgeInput.value.trim() : "",
        rango_edad: narratorAgeBracket ? narratorAgeBracket.value : "joven",
        tono: narratorToneInput ? narratorToneInput.value.trim() : "",
        justificacion: narratorJustification ? narratorJustification.value.trim() : ""
      };

      try {
        const res = await fetch(`/api/projects/${state.currentProject.id}/narrator/recommend-ai`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(specPayload)
        });
        const data = await res.json();
        if (data.success && data.perfil_narrador) {
          const proposedVoice = data.perfil_narrador.voz_recomendada;
          if (proposedVoice && narratorVoiceSelect) {
            narratorVoiceSelect.value = proposedVoice;
            updateSelectedVoiceCard(proposedVoice);
            document.querySelectorAll(".btn-quick-voice").forEach(b => {
              b.classList.toggle("active", b.dataset.voice === proposedVoice);
            });
          }
          const motivo = data.perfil_narrador.motivo_propuesta || `Voz propuesta: ${proposedVoice}`;
          showToast(`🔮 ${motivo}`, "success");
          setSystemStatus("success", "Narrador propuesto según especificación", motivo);
        } else {
          showToast(data.detail || "Error proponiendo narrador", "error");
          setSystemStatus("error", "Error proponiendo narrador", data.detail || "");
        }
      } catch (e) {
        showToast("Error al proponer narrador", "error");
        setSystemStatus("error", "Error de red proponiendo narrador", e.message);
      } finally {
        btnAiRecommendNarrator.disabled = false;
        btnAiRecommendNarrator.innerHTML = '🔮 Proponer Narrador según la Especificación de Arriba';
      }
    });
  }

  // Animación de la onda de audio al reproducir
  if (narratorAudioElement) {
    const waveAnim = document.getElementById("audio-wave-anim");
    narratorAudioElement.addEventListener("play", () => {
      if (waveAnim) waveAnim.style.opacity = "1";
    });
    narratorAudioElement.addEventListener("pause", () => {
      if (waveAnim) waveAnim.style.opacity = "0.3";
    });
    narratorAudioElement.addEventListener("ended", () => {
      if (waveAnim) waveAnim.style.opacity = "0.3";
    });
  }

  // Actualizar tarjeta de implicaciones técnicas del estilo visual seleccionado
  const STYLE_NEGATIVES = {
    watercolor: "Sin 3D CGI, sin fotorrealismo, sin bordes duros digitales ni texto en imagen.",
    ghibli_anime: "Sin render 3D plástico, sin sombreado fotográfico ni estética cyberpunk.",
    storybook_kids: "Sin realismo fotográfico, sin sombras duras ni proporciones adultas rígidas.",
    pixar_3d: "Sin dibujo plano 2D, sin trazos de tinta ni estética low-poly.",
    cinematic: "Sin estética cartoon, sin trazos de cómic ni colores planos sin volumen.",
    anime: "Sin 3D CGI rígido, sin grano analógico sucio ni estilo acuarela difusa.",
    noir_bw: "Sin color (ni acentos cromáticos), sin iluminación plana de día.",
    comic: "Sin fotorrealismo ni difuminados acuarela; mantener entintado limpio.",
    dark_fantasy: "Sin colores pastel alegres ni estética infantil cartoon.",
    cyberpunk: "Sin iluminación natural diurna rural ni acabados vintage analógicos.",
    vintage: "Sin neones digitales modernos ni render 3D sintético."
  };

  function renderRecurrentCharsGrid(rawText, personajesList = [], refCharId = null) {
    const gridEl = document.getElementById("univ-recurrent-chars-grid");
    if (!gridEl) return;
    const text = (rawText || "").trim();
    let items = [];
    if (text) {
      items = text.split(/,(?![^()]*\))/).map(s => s.trim()).filter(Boolean).map((entry, idx) => {
        const m = entry.match(/^([^(]+)\(([^)]+)\)$/);
        const nombre = m ? m[1].trim() : entry;
        const detalle = m ? m[2].trim() : "";
        const matched = (personajesList || []).find(c =>
          (c.nombre || "").toLowerCase().includes(nombre.toLowerCase()) ||
          nombre.toLowerCase().includes((c.nombre || "").toLowerCase())
        );
        return { id: matched?.id || `char_${idx + 1}`, nombre, detalle };
      });
    } else if (Array.isArray(personajesList) && personajesList.length > 0) {
      items = personajesList.map(c => ({ id: c.id, nombre: c.nombre || c.id, detalle: c.rol || "" }));
    }

    if (items.length === 0) {
      gridEl.innerHTML = `<div class="text-muted" style="font-size:0.8rem;">Sin personajes recurrentes definidos aún.</div>`;
      return;
    }

    const activeRefId = refCharId || state.currentProject?.referencia_personaje_id || items[0]?.id;
    if (state.currentProject && !state.currentProject.referencia_personaje_id && activeRefId) {
      state.currentProject.referencia_personaje_id = activeRefId;
    }

    gridEl.innerHTML = items.map(it => {
      const isRef = it.id === activeRefId;
      return `
        <div class="recurrent-char-chip ${isRef ? 'is-reference' : ''}" data-char-id="${escapeHtml(it.id)}" title="Pulsa para marcar a ${escapeHtml(it.nombre)} como personaje de referencia principal">
          <strong>${isRef ? '★ ' : ''}${escapeHtml(it.nombre)}</strong>
          ${it.detalle ? `<span>${escapeHtml(it.detalle)}</span>` : ""}
        </div>
      `;
    }).join("");

    gridEl.querySelectorAll(".recurrent-char-chip").forEach(chip => {
      chip.addEventListener("click", async () => {
        const chosenId = chip.dataset.charId;
        if (!chosenId) return;
        if (state.currentProject) state.currentProject.referencia_personaje_id = chosenId;
        renderRecurrentCharsGrid(rawText, personajesList, chosenId);
        await saveUniverse(false);
        showToast(`★ Personaje de referencia fijado: ${chip.querySelector("strong")?.textContent.replace("★ ", "")}`, "info");
      });
    });
  }

  function renderRecurrentEnvsGrid(escenariosList = [], refEnvId = null) {
    const gridEl = document.getElementById("univ-recurrent-envs-grid");
    if (!gridEl) return;
    const list = Array.isArray(escenariosList) ? escenariosList : [];
    if (list.length === 0) {
      gridEl.innerHTML = `<div class="text-muted" style="font-size:0.8rem;">Sin escenarios recurrentes definidos aún.</div>`;
      return;
    }

    const activeRefId = refEnvId || state.currentProject?.referencia_escenario_id || list[0]?.id;
    if (state.currentProject && !state.currentProject.referencia_escenario_id && activeRefId) {
      state.currentProject.referencia_escenario_id = activeRefId;
    }

    gridEl.innerHTML = list.map((e, idx) => {
      const eid = e.id || `esc_${idx + 1}`;
      const ename = e.nombre || eid;
      const isRef = eid === activeRefId;
      const descShort = (e.descripcion_visual || "").trim();
      const snippet = descShort.length > 65 ? `${descShort.slice(0, 62)}...` : descShort;
      return `
        <div class="recurrent-char-chip ${isRef ? 'is-reference' : ''}" data-env-id="${escapeHtml(eid)}" title="Pulsa para marcar ${escapeHtml(ename)} como escenario de referencia principal">
          <strong>${isRef ? '★ ' : ''}${escapeHtml(ename)}</strong>
          ${snippet ? `<span>${escapeHtml(snippet)}</span>` : ""}
        </div>
      `;
    }).join("");

    gridEl.querySelectorAll(".recurrent-char-chip").forEach(chip => {
      chip.addEventListener("click", async () => {
        const chosenId = chip.dataset.envId;
        if (!chosenId) return;
        if (state.currentProject) state.currentProject.referencia_escenario_id = chosenId;
        renderRecurrentEnvsGrid(list, chosenId);
        await saveUniverse(false);
        showToast(`★ Escenario de referencia fijado: ${chip.querySelector("strong")?.textContent.replace("★ ", "")}`, "info");
      });
    });
  }

  document.getElementById("btn-toggle-recurrent-raw")?.addEventListener("click", () => {
    if (!univRecurrentChars) return;
    const isHidden = univRecurrentChars.style.display === "none" || !univRecurrentChars.style.display;
    univRecurrentChars.style.display = isHidden ? "block" : "none";
  });

  univRecurrentChars?.addEventListener("input", () => {
    renderRecurrentCharsGrid(univRecurrentChars.value, state.currentProject?.personajes || []);
  });

  const RULE_CHECKBOX_MAP = {
    fondo_blanco: "rule-fondo-blanco",
    cuerpo_entero: "rule-cuerpo-entero",
    sin_texto: "rule-sin-texto",
    escenarios_sin_personas: "rule-escenarios-sin-personas",
    formato_vertical: "rule-formato-vertical"
  };

  const RULE_PROMPTS_EN = {
    fondo_blanco: "isolated on solid plain pure white background (#FFFFFF)",
    cuerpo_entero: "full body standing head to toe, wide safety margins, no cropped feet",
    sin_texto: "no text, no words, no labels, no watermarks, no arrows",
    escenarios_sin_personas: "empty scene, no people, no characters, pure background art",
    formato_vertical: "vertical 9:16 portrait composition"
  };

  let customRulesList = [];

  function renderCustomRulesInGrid() {
    const grid = document.getElementById("gen-rules-grid");
    if (!grid) return;
    grid.querySelectorAll(".custom-rule-item").forEach(el => el.remove());
    customRulesList.forEach((rule, idx) => {
      const label = document.createElement("label");
      label.className = "gen-rule-check custom-rule-item";
      label.innerHTML = `
        <input type="checkbox" class="custom-rule-checkbox" data-idx="${idx}" ${rule.checked ? "checked" : ""}>
        <span style="flex:1;">📌 ${rule.label}</span>
        <button type="button" class="btn btn-ghost btn-xxs btn-del-custom-rule" data-idx="${idx}" title="Quitar regla" style="padding:0 4px;">&times;</button>
      `;
      label.querySelector(".custom-rule-checkbox").addEventListener("change", (e) => {
        customRulesList[idx].checked = e.target.checked;
        updateFinalStylePromptEN();
      });
      label.querySelector(".btn-del-custom-rule").addEventListener("click", (e) => {
        e.preventDefault();
        customRulesList.splice(idx, 1);
        renderCustomRulesInGrid();
        updateFinalStylePromptEN();
      });
      grid.appendChild(label);
    });
  }

  document.getElementById("btn-add-custom-rule")?.addEventListener("click", () => {
    const inp = document.getElementById("new-custom-rule-input");
    const val = inp ? inp.value.trim() : "";
    if (!val) return;
    customRulesList.push({ label: val, checked: true });
    if (inp) inp.value = "";
    renderCustomRulesInGrid();
    updateFinalStylePromptEN();
  });

  function getDetailEffectHtml(detailVal) {
    const d = Number(detailVal);
    if (d <= 20) return "<strong>0–20% Minimalista:</strong> Formas simples, muy poco detalle, aguadas planas.";
    if (d <= 40) return "<strong>21–40% Sencillo:</strong> Trazo limpio y sombreado mínimo de cuento.";
    if (d <= 60) return "<strong>41–60% Equilibrado:</strong> Detalle medio de álbum ilustrado y aguadas suaves.";
    if (d <= 80) return "<strong>61–80% Delicado:</strong> Tinta fina sepia, detalle cuidado y veladuras suaves.";
    return "<strong>81–100% Muy detallado:</strong> Tinta muy fina, trazo intrincado y capas ricas.";
  }

  function getRealismEffectHtml(realismVal) {
    const r = Number(realismVal);
    if (r <= 20) return "<strong>0–20% Cartoon 2D:</strong> Dibujo animado muy estilizado y proporciones juguetonas.";
    if (r <= 40) return "<strong>21–40% Cuento animado:</strong> Semi-estilizado suave tipo animación clásica.";
    if (r <= 60) return "<strong>41–60% Cuento clásico:</strong> Ilustración tradicional a mano con proporciones poéticas.";
    if (r <= 80) return "<strong>61–80% Ilustración estilizada:</strong> Álbum ilustrado con rasgos simplificados (sin anatomía realista).";
    return "<strong>81–100% Ilustración naturalista:</strong> Proporciones más fieles de libro clásico (sin fotorrealismo).";
  }

  function getSliderPromptEn(detailVal, realismVal) {
    const d = Number(detailVal);
    const r = Number(realismVal);
    const parts = [];
    if (d <= 20) parts.push("minimalist simplified shapes, very low detail, clean uncluttered lines, simple flat washes");
    else if (d <= 40) parts.push("simple charming storybook detail, clean uncluttered ink lines, soft minimal shading");
    else if (d <= 60) parts.push("balanced medium storybook detail, clear expressive features, gentle watercolor washes");
    else if (d <= 80) parts.push("delicate storybook detail, fine sepia ink linework and soft artistic translucent washes");
    else parts.push("intricate fine ink linework, rich delicate storybook detail and layered translucent washes");

    if (r <= 20) parts.push("stylized 2D cartoon character design, exaggerated playful proportions, expressive animated look");
    else if (r <= 40) parts.push("semi-stylized animated storybook character, gentle charming stylized proportions");
    else if (r <= 60) parts.push("classic hand-drawn storybook illustration proportions, gentle stylized poetic character design");
    else if (r <= 80) parts.push("gentle stylized classic storybook illustration proportions, expressive hand-drawn picture-book character design, soft simplified features");
    else parts.push("refined classic picture-book illustration proportions, expressive hand-drawn storybook style");
    return parts.join(", ");
  }

  function getGenerationRulesFromUI() {
    const out = {};
    for (const [k, elId] of Object.entries(RULE_CHECKBOX_MAP)) {
      const el = document.getElementById(elId);
      out[k] = el ? el.checked : true;
    }
    const detailEl = document.getElementById("slider-nivel-detalle");
    const realismEl = document.getElementById("slider-nivel-realismo");
    out.nivel_detalle = detailEl ? parseInt(detailEl.value, 10) : 75;
    out.nivel_realismo = realismEl ? parseInt(realismEl.value, 10) : 75;
    if (customRulesList.length > 0) {
      out._custom = customRulesList;
    }
    return out;
  }

  function applyGenerationRulesToUI(reglas) {
    const r = reglas || {};
    for (const [k, elId] of Object.entries(RULE_CHECKBOX_MAP)) {
      const el = document.getElementById(elId);
      if (el) el.checked = r[k] !== undefined ? Boolean(r[k]) : true;
    }
    const detailEl = document.getElementById("slider-nivel-detalle");
    const detailValEl = document.getElementById("slider-nivel-detalle-val");
    const detailHintEl = document.getElementById("slider-nivel-detalle-hint");
    const dVal = r.nivel_detalle !== undefined ? Number(r.nivel_detalle) : 75;
    if (detailEl) detailEl.value = String(dVal);
    if (detailValEl) detailValEl.textContent = `${dVal}%`;
    if (detailHintEl) detailHintEl.innerHTML = getDetailEffectHtml(dVal);

    const realismEl = document.getElementById("slider-nivel-realismo");
    const realismValEl = document.getElementById("slider-nivel-realismo-val");
    const realismHintEl = document.getElementById("slider-nivel-realismo-hint");
    const rVal = r.nivel_realismo !== undefined ? Number(r.nivel_realismo) : 75;
    if (realismEl) realismEl.value = String(rVal);
    if (realismValEl) realismValEl.textContent = `${rVal}%`;
    if (realismHintEl) realismHintEl.innerHTML = getRealismEffectHtml(rVal);

    customRulesList = Array.isArray(r._custom) ? r._custom.map(x => ({ ...x })) : [];
    renderCustomRulesInGrid();
    updateFinalStylePromptEN();
  }

  function updateFinalStylePromptEN() {
    const outEl = document.getElementById("univ-final-prompt-en");
    if (!outEl) return;
    const styleKey = univStyle ? univStyle.value : "watercolor";
    const parts = [];
    parts.push(STYLE_PROMPTS_EN[styleKey] || STYLE_PROMPTS_EN["cinematic"]);

    for (const [k, elId] of Object.entries(RULE_CHECKBOX_MAP)) {
      const el = document.getElementById(elId);
      if (el && el.checked && RULE_PROMPTS_EN[k]) {
        parts.push(RULE_PROMPTS_EN[k]);
      }
    }
    const detailEl = document.getElementById("slider-nivel-detalle");
    const realismEl = document.getElementById("slider-nivel-realismo");
    parts.push(getSliderPromptEn(detailEl ? detailEl.value : 75, realismEl ? realismEl.value : 75));

    customRulesList.forEach(r => {
      if (r.checked && r.label) parts.push(r.label);
    });

    const manualNotes = univStyleDetails ? univStyleDetails.value.trim() : "";
    if (manualNotes) parts.push(manualNotes);

    outEl.value = parts.join(", ");
  }

  Object.values(RULE_CHECKBOX_MAP).forEach(elId => {
    document.getElementById(elId)?.addEventListener("change", updateFinalStylePromptEN);
  });
  document.getElementById("slider-nivel-detalle")?.addEventListener("input", (ev) => {
    const vEl = document.getElementById("slider-nivel-detalle-val");
    if (vEl) vEl.textContent = `${ev.target.value}%`;
    const hEl = document.getElementById("slider-nivel-detalle-hint");
    if (hEl) hEl.innerHTML = getDetailEffectHtml(ev.target.value);
    updateFinalStylePromptEN();
  });
  document.getElementById("slider-nivel-realismo")?.addEventListener("input", (ev) => {
    const vEl = document.getElementById("slider-nivel-realismo-val");
    if (vEl) vEl.textContent = `${ev.target.value}%`;
    const hEl = document.getElementById("slider-nivel-realismo-hint");
    if (hEl) hEl.innerHTML = getRealismEffectHtml(ev.target.value);
    updateFinalStylePromptEN();
  });
  univStyleDetails?.addEventListener("input", updateFinalStylePromptEN);

  const STYLE_PROMPTS_EN = {
    cinematic: "cinematic lighting, photorealistic 8k, shot on 35mm lens, atmospheric depth of field, dramatic shadows, no cartoon, no comic outlines, no flat colors",
    noir_bw: "black and white film noir photography, dramatic high contrast monochrome, sharp shadows, moody lighting, classic monochrome 35mm film, strictly monochrome, no color, no flat daylight",
    anime: "anime aesthetic, Makoto Shinkai style, vibrant colors, beautiful sky, high quality anime screencap, trending on Pixiv, no 3D CGI, no analog grain, no blurry watercolor",
    ghibli_anime: "Studio Ghibli aesthetic, Hayao Miyazaki hand-drawn anime, painterly backgrounds, warm nostalgic feel, whimsical art, no plastic 3D render, no photorealism, no cyberpunk",
    watercolor: "delicate poetic watercolor and ink storybook illustration, soft artistic translucent color washes, subtle sepia pencil and ink outlines, no 3D CGI, no photorealism",
    storybook_kids: "whimsical children's book illustration, vibrant friendly colors, charming storybook character art, soft lighting, family friendly, highly detailed, no photorealism, no harsh shadows",
    pixar_3d: "3D animated movie render, Pixar Disney style, soft volumetric subsurface scattering, expressive character facial features, 4k 8k, no flat 2D drawing, no ink outlines, no low-poly",
    dark_fantasy: "dark fantasy, hyperdetailed, grimdark aesthetic, ominous lighting, mystical atmosphere, concept art, Unreal Engine 5 render, no bright pastel colors, no cartoon",
    cyberpunk: "cyberpunk style, neon lights, rainy reflection, high tech dystopian, blade runner aesthetic, volumetric glow, no rural daylight, no vintage analog",
    vintage: "vintage 1970s film grain, warm Kodak Portra color tones, nostalgic, retro photography, authentic cinematic texture, no modern neon, no synthetic 3D render",
    comic: "graphic novel comic illustration, bold ink lines, dynamic comic book shading, expressive colors, Frank Miller style, no photorealism, no soft watercolor wash"
  };

  function updateStyleImplications(styleKey, _unused = false) {
    const meta = STYLE_METADATA[styleKey] || STYLE_METADATA["watercolor"];
    if (styleImplicationsIcon) styleImplicationsIcon.textContent = meta.icon;
    if (styleImplicationsTitle) styleImplicationsTitle.textContent = `Estilo: ${meta.name}`;
    if (styleImplicationsTags) {
      const cleanTags = (meta.tags || []).filter(t => !t.includes("4 Vistas"));
      styleImplicationsTags.innerHTML = cleanTags.map(t => `<span class="style-badge-tag">${t}</span>`).join("");
    }
    if (styleImplicationsDesc) {
      const negRule = STYLE_NEGATIVES[styleKey] || "";
      styleImplicationsDesc.textContent = negRule ? `${meta.desc} (${negRule})` : meta.desc;
    }
    const promptEnEl = document.getElementById("style-implications-prompt-en");
    if (promptEnEl) {
      promptEnEl.textContent = STYLE_PROMPTS_EN[styleKey] || STYLE_PROMPTS_EN["cinematic"];
    }
    updateFinalStylePromptEN();
  }

  // Sincronizar y propagar técnica visual a todos los personajes y escenarios
  function openSyncStyleConfirmation() {
    if (!state.currentProject) {
      showToast("Selecciona un proyecto primero", "warning");
      return;
    }
    const modal = document.getElementById("modal-sync-style-confirm");
    if (!modal) {
      syncStyleToAllEntities(true, true);
      return;
    }

    const chars = collectCharactersFromUI();
    const envs = collectEnvironmentsFromUI();
    const styleLabel = univStyle?.options[univStyle.selectedIndex]?.text || univStyle?.value || "—";

    const nameEl = document.getElementById("sync-style-modal-name");
    const charsInfoEl = document.getElementById("sync-style-chars-info");
    const envsInfoEl = document.getElementById("sync-style-envs-info");
    if (nameEl) nameEl.textContent = styleLabel;
    if (charsInfoEl) {
      const withPrompt = chars.filter(c => (c.prompt_retrato || "").trim()).length;
      charsInfoEl.textContent = chars.length > 0
        ? `${chars.length} personaje(s) (${withPrompt} con prompt actual que se actualizará).`
        : "No hay personajes todavía.";
    }
    if (envsInfoEl) {
      const withPrompt = envs.filter(e => (e.prompt_escenario || "").trim()).length;
      envsInfoEl.textContent = envs.length > 0
        ? `${envs.length} escenario(s) (${withPrompt} con prompt actual que se actualizará).`
        : "No hay escenarios todavía.";
    }

    const btnConfirm = document.getElementById("btn-confirm-sync-style");
    if (btnConfirm) {
      btnConfirm.onclick = async () => {
        const syncChars = modal.querySelector('input[name="sync-opt-chars"][value="yes"]')?.checked !== false;
        const syncEnvs = modal.querySelector('input[name="sync-opt-envs"][value="yes"]')?.checked !== false;
        modal.classList.remove("open");
        if (!syncChars && !syncEnvs) {
          showToast("No se ha modificado ningún prompt.", "info");
          return;
        }
        await syncStyleToAllEntities(syncChars, syncEnvs);
      };
    }

    modal.classList.add("open");
  }

  async function syncStyleToAllEntities(syncCharacters = true, syncEnvironments = true) {
    if (!state.currentProject) {
      showToast("Selecciona un proyecto primero", "warning");
      return;
    }

    await saveUniverse(false);
    const currentStyle = univStyle.value;
    const currentDetails = univStyleDetails ? univStyleDetails.value.trim() : "";

    if (btnSyncStyleToAll) {
      btnSyncStyleToAll.disabled = true;
      btnSyncStyleToAll.textContent = "⏳ Sincronizando...";
    }

    setSystemStatus(
      "busy",
      "Sincronizando Estilo del Universo...",
      `Actualizando prompts seleccionados a la técnica '${currentStyle}'...`
    );

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/sync-style`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          estilo_visual: currentStyle,
          estilo_detalles: currentDetails,
          sync_characters: syncCharacters,
          sync_environments: syncEnvironments
        })
      });
      const data = await res.json();
      if (data.success) {
        state.currentProject.estilo_visual = data.estilo_visual;
        state.currentProject.estilo_detalles = data.estilo_detalles;
        state.currentProject.personajes = data.personajes;
        state.currentProject.escenarios = data.escenarios;

        renderCharacterCards(data.personajes || []);
        renderEnvironmentCards(data.escenarios || []);
        updateMiniBanner();

        showToast(`✅ ¡Estilo sincronizado! ${data.characters_synced} personaje(s) y ${data.environments_synced} escenario(s) actualizados.`, "success");
        setSystemStatus(
          "success",
          "Estilo sincronizado",
          `${data.characters_synced} personaje(s) y ${data.environments_synced} escenario(s) adaptados a '${currentStyle}' (imágenes intactas).`
        );
      } else {
        showToast("Error al sincronizar estilo", "error");
        setSystemStatus("error", "Error al sincronizar estilo", data.detail || "Fallo en sincronización.");
      }
    } catch (err) {
      showToast("Error de conexión al sincronizar estilo", "error");
      setSystemStatus("error", "Error de conexión", err.message);
    } finally {
      if (btnSyncStyleToAll) {
        btnSyncStyleToAll.disabled = false;
        btnSyncStyleToAll.textContent = "⚡ Sincronizar estilo";
      }
    }
  }

  if (univStyle) {
    univStyle.addEventListener("change", () => updateStyleImplications(univStyle.value, true));
  }
  if (btnSyncStyleToAll) {
    btnSyncStyleToAll.addEventListener("click", openSyncStyleConfirmation);
  }

  // ========================================================
  // 5.B AUDITORÍA Y REVISIÓN DE COHERENCIA VISUAL CON IA
  // ========================================================
  const btnAuditCharacters = document.getElementById("btn-audit-characters");
  const btnAuditEnvironments = document.getElementById("btn-audit-environments");
  const modalAuditResults = document.getElementById("modal-audit-results");

  function openAuditModal(title, subtitle) {
    if (!modalAuditResults) return;
    const titleEl = document.getElementById("audit-modal-title");
    const subEl = document.getElementById("audit-modal-subtitle");
    if (titleEl) titleEl.textContent = title;
    if (subEl) subEl.textContent = subtitle;
    modalAuditResults.classList.add("open");
  }

  function renderAuditResults(data, entityType) {
    const statTotal = document.getElementById("audit-stat-total");
    const statApproved = document.getElementById("audit-stat-approved");
    const statHealed = document.getElementById("audit-stat-healed");
    const statRejected = document.getElementById("audit-stat-rejected");
    const listEl = document.getElementById("audit-results-list");

    if (statTotal) statTotal.textContent = `📊 Total: ${data.total}`;
    if (statApproved) statApproved.textContent = `✅ Coherentes: ${data.approved}`;
    if (statHealed) statHealed.textContent = `🔄 Corregidos: ${data.healed}`;
    if (statRejected) statRejected.textContent = `❌ Fallidos: ${data.rejected}`;

    if (!listEl) return;
    listEl.innerHTML = "";

    if (!data.results || data.results.length === 0) {
      listEl.innerHTML = `<p class="text-muted">No se encontraron elementos para auditar.</p>`;
      return;
    }

    data.results.forEach(item => {
      const card = document.createElement("div");
      card.className = "audit-item-row";
      card.style.cssText = `
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 12px 16px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        transition: background 0.2s;
      `;

      let badgeHtml = "";
      if (item.status === "APPROVED") {
        badgeHtml = `<span style="background: rgba(34,197,94,0.2); color: #4ade80; border: 1px solid rgba(34,197,94,0.4); padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">✅ Coherente</span>`;
      } else if (item.status === "HEALED") {
        badgeHtml = `<span style="background: rgba(245,158,11,0.2); color: #fbbf24; border: 1px solid rgba(245,158,11,0.4); padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">🔄 Corregido con IA</span>`;
      } else {
        badgeHtml = `<span style="background: rgba(239,68,68,0.2); color: #f87171; border: 1px solid rgba(239,68,68,0.4); padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">❌ Incoherente</span>`;
      }

      const imgHtml = item.imagen_url
        ? `<img src="${item.imagen_url}?t=${Date.now()}" alt="${item.nombre}" style="width: 56px; height: 80px; object-fit: cover; border-radius: 8px; border: 1px solid rgba(255,255,255,0.15); flex-shrink: 0;" />`
        : `<div style="width: 56px; height: 80px; background: rgba(255,255,255,0.05); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; flex-shrink: 0;">🎨</div>`;

      card.innerHTML = `
        ${imgHtml}
        <div style="flex: 1; min-width: 0;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <strong style="font-size: 0.95rem; color: #fff;">${item.nombre}</strong>
            ${badgeHtml}
          </div>
          <p style="margin: 0; font-size: 0.82rem; color: rgba(255,255,255,0.7); line-height: 1.35;">
            ${item.reason || "Sin observaciones."}
          </p>
          ${item.detected_style ? `<small style="display: block; margin-top: 4px; font-size: 0.75rem; color: rgba(255,255,255,0.45);">🎨 Estilo detectado: <em>${item.detected_style}</em></small>` : ""}
        </div>
      `;

      listEl.appendChild(card);
    });
  }

  async function handleAuditCharacters() {
    if (!state.currentProject) {
      showToast("Selecciona o abre un proyecto primero", "warning");
      return;
    }

    if (btnAuditCharacters) {
      btnAuditCharacters.disabled = true;
      btnAuditCharacters.innerHTML = `⏳ Revisando prompts y estilo...`;
    }

    // Guardar cambios actuales antes de auditar
    await saveUniverse(false);
    const refCharId = state.currentProject?.referencia_personaje_id || null;

    setSystemStatus(
      "busy",
      "Revisando Coherencia de Personajes...",
      "Comprobando que todos los prompts cuadren con el estilo del libro, opciones particulares y personaje de referencia..."
    );

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/audit-characters-coherence`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reference_char_id: refCharId })
      });
      const data = await res.json();
      if (data.success) {
        // Actualizar las tarjetas en pantalla para reflejar los que pasaron a "En revisión"
        (data.results || []).forEach(r => {
          const cardEl = document.querySelector(`.char-card[data-id="${r.id}"]`);
          if (cardEl && r.estado_aprobacion) {
            cardEl.dataset.estadoAprobacion = r.estado_aprobacion;
            cardEl.dataset.motivoRechazo = r.status !== "APPROVED" ? (r.reason || "") : "";
            const slot = cardEl.querySelector(".char-approval-slot");
            if (slot) {
              if (r.estado_aprobacion === "en_revision") {
                slot.innerHTML = `<button type="button" class="badge btn-toggle-char-approval" style="background: rgba(245, 158, 11, 0.22); color: #fbbf24; border: 1px solid #f59e0b; font-size: 0.72rem; padding: 3px 10px; border-radius: 4px; cursor: pointer;" title="${escapeHtml(r.reason || 'En revisión')}">⚠️ En revisión</button>`;
              }
            }
          }
        });

        const toastMsg = data.rejected === 0
          ? `✅ Todos los personajes (${data.approved}) son coherentes con ${data.reference_char_name || 'la referencia'}`
          : `⚠️ ${data.rejected} personaje(s) pasaron a "En revisión" por diferencias con ${data.reference_char_name || 'la referencia'}`;
        showToast(toastMsg, data.rejected > 0 ? "warning" : "success");
        setSystemStatus(
          data.rejected > 0 ? "warning" : "success",
          data.rejected > 0 ? `${data.rejected} personaje(s) en revisión` : "Coherencia de personajes al 100%",
          `Referencia principal: ${data.reference_char_name || 'N/A'} · Estilo: ${data.style}`
        );

        openAuditModal(
          "🔍 Revisión de Coherencia de Personajes",
          data.rejected > 0
            ? `Estos son los cambios necesarios respecto a ${data.reference_char_name || 'la referencia'} (${data.style}). Se les ha quitado el Aprobado y han pasado a "En revisión".`
            : `Todos los personajes cumplen con el estilo (${data.style}) y con el prompt de ${data.reference_char_name || 'la referencia'}.`
        );
        renderAuditResults(data, "characters");

        if (data.rejected > 0) {
          const listEl = document.getElementById("audit-results-list");
          if (listEl) {
            const actionWrap = document.createElement("div");
            actionWrap.style.cssText = "display:flex; justify-content:flex-end; margin-top:12px;";
            actionWrap.innerHTML = `<button type="button" class="btn btn-primary btn-sm" id="btn-sync-incoherent-prompts">⚡ Actualizar solo los ${data.rejected} prompts desalineados (sin tocar imágenes)</button>`;
            listEl.appendChild(actionWrap);
            document.getElementById("btn-sync-incoherent-prompts")?.addEventListener("click", async (ev) => {
              const b = ev.currentTarget;
              b.disabled = true;
              b.textContent = "⏳ Sincronizando prompts...";
              try {
                const sRes = await fetch(`/api/projects/${state.currentProject.id}/sync-incoherent-prompts`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ reference_char_id: refCharId })
                });
                const sData = await sRes.json();
                if (sData.success) {
                  await selectProject(state.currentProject.id);
                  renderAuditResults(sData.audit, "characters");
                  showToast(`✅ ${sData.updated_count} prompts actualizados y alineados sin tocar imágenes`, "success");
                }
              } finally {
                b.disabled = false;
              }
            });
          }
        }
      } else {
        showToast("Error en auditoría: " + (data.detail || "desconocido"), "error");
        setSystemStatus("error", "Error en auditoría de personajes", data.detail || "Desconocido");
      }
    } catch (err) {
      showToast("Error de conexión durante la auditoría de personajes", "error");
      setSystemStatus("error", "Error de conexión en auditoría", err.message);
    } finally {
      if (btnAuditCharacters) {
        btnAuditCharacters.disabled = false;
        btnAuditCharacters.innerHTML = `🔍 Revisar Coherencia de Personajes`;
      }
    }
  }

  async function handleAuditEnvironments() {
    if (!state.currentProject) {
      showToast("Selecciona o abre un proyecto primero", "warning");
      return;
    }

    if (btnAuditEnvironments) {
      btnAuditEnvironments.disabled = true;
      btnAuditEnvironments.innerHTML = `⏳ Revisando prompts y estilo...`;
    }

    await saveUniverse(false);
    const refEnvId = state.currentProject?.referencia_escenario_id || null;

    setSystemStatus(
      "busy",
      "Revisando Coherencia de Escenarios...",
      "Comprobando que todos los prompts cuadren con el estilo del libro, opciones particulares y escenario de referencia..."
    );

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/audit-environments-coherence`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reference_env_id: refEnvId })
      });
      const data = await res.json();
      if (data.success) {
        (data.results || []).forEach(r => {
          const cardEl = document.querySelector(`.env-card[data-id="${r.id}"]`);
          if (cardEl && r.estado_aprobacion) {
            cardEl.dataset.estadoAprobacion = r.estado_aprobacion;
            cardEl.dataset.motivoRechazo = r.status !== "APPROVED" ? (r.reason || "") : "";
            const slot = cardEl.querySelector(".env-approval-slot");
            if (slot) {
              slot.innerHTML = getApprovalBadgeHtml(r.estado_aprobacion, cardEl.dataset.motivoRechazo, "btn-toggle-env-approval");
            }
          }
        });

        const toastMsg = data.rejected === 0
          ? `✅ Todos los escenarios (${data.approved}) son coherentes con ${data.reference_env_name || 'la referencia'}`
          : `⚠️ ${data.rejected} escenario(s) pasaron a "En revisión" por diferencias con ${data.reference_env_name || 'la referencia'}`;
        showToast(toastMsg, data.rejected > 0 ? "warning" : "success");
        setSystemStatus(
          data.rejected > 0 ? "warning" : "success",
          data.rejected > 0 ? `${data.rejected} escenario(s) en revisión` : "Coherencia de escenarios al 100%",
          `Referencia principal: ${data.reference_env_name || 'N/A'} · Estilo: ${data.style}`
        );

        openAuditModal(
          "🔍 Revisión de Coherencia de Escenarios",
          data.rejected > 0
            ? `Estos son los cambios necesarios respecto a ${data.reference_env_name || 'la referencia'} (${data.style}). Se les ha quitado el Aprobado y han pasado a "En revisión".`
            : `Todos los escenarios cumplen con el estilo (${data.style}) y con el prompt de ${data.reference_env_name || 'la referencia'}.`
        );
        renderAuditResults(data, "environments");

        if (data.rejected > 0) {
          const listEl = document.getElementById("audit-results-list");
          if (listEl) {
            const actionWrap = document.createElement("div");
            actionWrap.style.cssText = "display:flex; justify-content:flex-end; margin-top:12px;";
            actionWrap.innerHTML = `<button type="button" class="btn btn-primary btn-sm" id="btn-sync-incoherent-env-prompts">⚡ Actualizar solo los ${data.rejected} prompts desalineados (sin tocar imágenes)</button>`;
            listEl.appendChild(actionWrap);
            document.getElementById("btn-sync-incoherent-env-prompts")?.addEventListener("click", async (ev) => {
              const b = ev.currentTarget;
              b.disabled = true;
              b.textContent = "⏳ Sincronizando prompts...";
              try {
                const sRes = await fetch(`/api/projects/${state.currentProject.id}/sync-environments-prompts`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ reference_env_id: refEnvId })
                });
                const sData = await sRes.json();
                if (sData.success) {
                  await selectProject(state.currentProject.id);
                  renderAuditResults(sData.audit, "environments");
                  showToast(`✅ ${sData.updated_count} prompts de escenarios actualizados sin tocar imágenes`, "success");
                }
              } finally {
                b.disabled = false;
              }
            });
          }
        }
      } else {
        showToast("Error en auditoría: " + (data.detail || "desconocido"), "error");
        setSystemStatus("error", "Error en auditoría de escenarios", data.detail || "Desconocido");
      }
    } catch (err) {
      showToast("Error de conexión durante la auditoría de escenarios", "error");
      setSystemStatus("error", "Error de conexión en auditoría", err.message);
    } finally {
      if (btnAuditEnvironments) {
        btnAuditEnvironments.disabled = false;
        btnAuditEnvironments.innerHTML = `🔍 Revisar Coherencia de Escenarios`;
      }
    }
  }

  if (btnAuditCharacters) {
    btnAuditCharacters.addEventListener("click", handleAuditCharacters);
  }
  if (btnAuditEnvironments) {
    btnAuditEnvironments.addEventListener("click", handleAuditEnvironments);
  }

  // ========================================================
  // 6. CAPA ESPECÍFICA: GENERACIÓN DE STORYBOARD Y VÍDEOS
  // ========================================================
  // PROPUESTA PREVIA (PASO 1) Y GENERACIÓN DE ESCENAS (PASO 2)
  // ========================================================
  function renderChapterProposal(proposal) {
    const panel = document.getElementById("chapter-proposal-panel");
    const enfoqueEl = document.getElementById("proposal-enfoque-input");
    const blocksEl = document.getElementById("proposal-blocks-list");
    const totalEl = document.getElementById("proposal-total-duration");
    if (!panel || !enfoqueEl || !blocksEl) return;

    if (!proposal || !Array.isArray(proposal.bloques) || proposal.bloques.length === 0) {
      state.currentProposal = null;
      panel.style.display = "none";
      blocksEl.innerHTML = "";
      return;
    }

    state.currentProposal = proposal;
    panel.style.display = "block";
    enfoqueEl.value = proposal.enfoque_general || "";
    blocksEl.innerHTML = "";

    const recalcTotal = () => {
      let sum = 0;
      blocksEl.querySelectorAll(".proposal-block-dur").forEach(inp => {
        sum += Math.max(1, parseInt(inp.value) || 5);
      });
      if (totalEl) totalEl.textContent = sum;
    };

    proposal.bloques.forEach((b, idx) => {
      const row = document.createElement("div");
      row.className = "proposal-block-row";
      row.style.cssText = "padding:0.65rem 0.75rem; background:rgba(15,23,42,0.55); border:1px solid rgba(148,163,184,0.2); border-radius:8px; display:flex; flex-direction:column; gap:0.4rem;";
      const transHtml = idx > 0 ? `
        <div style="display:flex; align-items:center; gap:0.45rem; padding:0.35rem 0.5rem; background:rgba(59,130,246,0.08); border-left:3px solid #60a5fa; border-radius:4px;">
          <span style="font-size:0.76rem; color:#93c5fd; white-space:nowrap; font-weight:600;">↪️ Paso desde Escena ${idx}:</span>
          <input type="text" class="form-input proposal-block-trans" value="${escapeHtml(b.transicion_desde_anterior || "")}" placeholder="Cómo se pasa desde la escena anterior..." style="font-size:0.8rem; padding:0.25rem 0.45rem; flex:1;" />
        </div>
      ` : "";
      row.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; gap:0.5rem;">
          <input type="text" class="form-input proposal-block-title" value="${escapeHtml(b.titulo || `Escena ${idx + 1}`)}" style="font-weight:600; font-size:0.86rem; padding:0.3rem 0.5rem; flex:1;" />
          <label style="display:flex; align-items:center; gap:0.3rem; font-size:0.8rem; color:#cbd5e1; white-space:nowrap;">
            ⏱️ <input type="number" min="2" max="30" class="form-input proposal-block-dur" value="${parseInt(b.duracion_seg) || 5}" style="width:62px; padding:0.25rem 0.4rem; text-align:center;" /> s
          </label>
          <button type="button" class="btn btn-ghost btn-xxs btn-del-proposal-block" title="Quitar esta escena de la propuesta" style="color:#f87171;">🗑️</button>
        </div>
        ${transHtml}
        <div style="margin-top:0.25rem;">
          <label style="display:block; font-size:0.78rem; color:#94a3b8; margin-bottom:0.25rem; font-weight:600;">
            🎬 Qué ocurre visualmente en esta escena:
          </label>
          <textarea class="form-textarea proposal-block-desc" rows="3" style="width:100%; box-sizing:border-box; font-size:0.86rem; padding:0.5rem 0.65rem;">${escapeHtml(b.que_ocurre || "")}</textarea>
        </div>
        <div style="margin-top:0.25rem;">
          <label style="display:block; font-size:0.78rem; color:#94a3b8; margin-bottom:0.25rem; font-weight:600;">
            🎙️ En esta escena el narrador leerá:
          </label>
          <textarea class="form-textarea proposal-block-narr" rows="3" style="width:100%; box-sizing:border-box; font-size:0.86rem; padding:0.5rem 0.65rem; color:#e2e8f0; background:rgba(30,41,59,0.55);" placeholder="Fragmento de texto que leerá el narrador en esta escena...">${escapeHtml(b.texto_narrado || "")}</textarea>
        </div>
      `;
      row.querySelector(".proposal-block-dur")?.addEventListener("input", recalcTotal);
      row.querySelector(".btn-del-proposal-block")?.addEventListener("click", () => {
        if (blocksEl.querySelectorAll(".proposal-block-row").length <= 1) {
          showToast("Debe quedar al menos 1 escena en la propuesta", "info");
          return;
        }
        row.remove();
        recalcTotal();
      });
      blocksEl.appendChild(row);
    });
    recalcTotal();
  }

  function collectEditedProposal() {
    const panel = document.getElementById("chapter-proposal-panel");
    if (!panel || panel.style.display === "none") return null;
    const enfoqueEl = document.getElementById("proposal-enfoque-input");
    const blocksEl = document.getElementById("proposal-blocks-list");
    if (!enfoqueEl || !blocksEl) return null;

    const bloques = [];
    let total = 0;
    blocksEl.querySelectorAll(".proposal-block-row").forEach((row, idx) => {
      const titulo = row.querySelector(".proposal-block-title")?.value.trim() || `Escena ${idx + 1}`;
      const transicion_desde_anterior = row.querySelector(".proposal-block-trans")?.value.trim() || "";
      const que_ocurre = row.querySelector(".proposal-block-desc")?.value.trim() || "";
      const texto_narrado = row.querySelector(".proposal-block-narr")?.value.trim() || "";
      const duracion_seg = Math.max(2, parseInt(row.querySelector(".proposal-block-dur")?.value) || 5);
      total += duracion_seg;
      bloques.push({ id: idx + 1, titulo, transicion_desde_anterior, que_ocurre, texto_narrado, duracion_seg });
    });

    if (bloques.length === 0) return null;
    return {
      enfoque_general: enfoqueEl.value.trim(),
      bloques,
      duracion_total_seg: total
    };
  }

  const btnGenerateProposal = document.getElementById("btn-generate-proposal");
  if (btnGenerateProposal) {
    btnGenerateProposal.addEventListener("click", async () => {
      const text = rawChapterText.value.trim();
      if (!text) {
        showToast("Escribe o selecciona el texto del capítulo antes de continuar", "error");
        return;
      }
      if (!state.currentProject) {
        showToast("Selecciona un proyecto primero", "error");
        return;
      }
      btnGenerateProposal.disabled = true;
      btnGenerateProposal.innerHTML = '<span class="btn-icon-symbol">⏳</span> Elaborando propuesta...';
      const title = chapterTitleInput.value.trim() || "Capítulo";
      try {
        const res = await fetch("/api/storyboard/propose", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_id: state.currentProject.id,
            chapter_title: title,
            text,
            characters: state.currentProject.personajes,
            escenarios: state.currentProject.escenarios || [],
            style_key: state.currentProject.estilo_visual,
            style_details: state.currentProject.estilo_detalles || "",
            audiencia: state.currentProject.audiencia || "",
            ambiente: state.currentProject.ambiente || "",
            target_scenes: parseInt(scenesCountSelect.value)
          })
        });
        const data = await res.json();
        if (data.success && data.proposal) {
          renderChapterProposal(data.proposal);
          await saveCurrentChapter(true);
          document.getElementById("chapter-proposal-panel")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
          showToast("Propuesta generada y guardada. Puedes ajustarla antes de generar las escenas.", "success");
        } else {
          showToast(data.detail || "Error generando propuesta", "error");
        }
      } catch (e) {
        showToast(`Error generando propuesta: ${e.message}`, "error");
      } finally {
        btnGenerateProposal.disabled = false;
        btnGenerateProposal.innerHTML = '<span class="btn-icon-symbol">💡</span> Proponer Historia y Duración';
      }
    });
  }

  btnGenerateStoryboard.addEventListener("click", async () => {
    const text = rawChapterText.value.trim();
    if (!text) {
      showToast("Escribe o selecciona el texto del capítulo antes de continuar", "error");
      return;
    }

    if (!state.currentProject) {
      showToast("Selecciona un proyecto primero", "error");
      return;
    }

    const editedProposal = collectEditedProposal();

    btnGenerateStoryboard.disabled = true;
    btnGenerateStoryboard.innerHTML = '<span class="btn-icon-symbol">⏳</span> Generando escenas desde la propuesta...';

    const title = chapterTitleInput.value.trim() || "Capítulo";
    setSystemStatus(
      "busy",
      `Generando escenas: ${title}...`,
      "Creando locuciones y prompts visuales coherentes con tu propuesta y la biblia..."
    );

    try {
      const res = await fetch("/api/storyboard/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: state.currentProject.id,
          chapter_title: title,
          text: text,
          characters: state.currentProject.personajes,
          escenarios: state.currentProject.escenarios || [],
          style_key: state.currentProject.estilo_visual,
          style_details: state.currentProject.estilo_detalles || "",
          audiencia: state.currentProject.audiencia || "",
          ambiente: state.currentProject.ambiente || "",
          target_scenes: editedProposal?.bloques?.length || parseInt(scenesCountSelect.value),
          propuesta: editedProposal
        })
      });

      const data = await res.json();
      if (data.success && data.scenes) {
        state.scenes = data.scenes;
        storyboardTitle.textContent = "Escenas";
        renderStoryboard();
        storyboardContainer.style.display = "block";
        await saveCurrentChapter(true);
        storyboardContainer.scrollIntoView({ behavior: "smooth" });
        showToast(`Capítulo adaptado en ${state.scenes.length} escenas consistentes`, "success");
        setSystemStatus("success", `¡Storyboard generado!`, `${state.scenes.length} escenas generadas según tu propuesta.`);
      } else {
        showToast(data.detail || "Error generando storyboard", "error");
        setSystemStatus("error", "Error generando storyboard", data.detail || "No se pudo generar el guión.");
      }
    } catch (e) {
      showToast(`Error generando storyboard: ${e.message}`, "error");
      setSystemStatus("error", "Error de conexión en storyboard", e.message);
    } finally {
      btnGenerateStoryboard.disabled = false;
      btnGenerateStoryboard.innerHTML = '<span class="btn-icon-symbol">✨</span> Generar Escenas desde la Propuesta';
    }
  });

  // Helper para generar los badges del header de la escena
  function buildSceneBadgesHtml(sc, index) {
    const charsInScene = (sc.personajes_en_escena && sc.personajes_en_escena.length > 0)
      ? sc.personajes_en_escena.map(n => {
          const pMatch = state.currentProject?.personajes?.find(p => 
            p.nombre.toLowerCase() === n.toLowerCase() || (p.id && p.id.toLowerCase() === n.toLowerCase())
          );
          if (pMatch && pMatch.imagen_url) {
            return `<span class="char-reference-pill" title="Rasgos canónicos vinculados de ${pMatch.nombre}"><img src="${pMatch.imagen_url}" class="char-pill-avatar" alt="${pMatch.nombre}"> ${pMatch.nombre}</span>`;
          }
          return `<span class="meta-pill" style="font-size:0.7rem; padding:0.15rem 0.45rem;">👤 ${n}</span>`;
        }).join(" ")
      : "";

    const envInScene = (sc.escenario_clave && sc.escenario_clave !== "General" && sc.escenario_clave !== "Escenario específico")
      ? `<span class="env-reference-pill" title="Escenario recurrente: ${sc.escenario_clave}">🏛️ ${sc.escenario_clave}</span>`
      : "";

    let sceneApprBadge = "";
    if (sc.estado_aprobacion === "aprobado") {
      sceneApprBadge = `<span class="badge" style="background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #22c55e; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px;">✅ Aprobada</span>`;
    } else if (sc.estado_aprobacion === "regenerar_solicitado" || sc.estado_aprobacion === "regenerando" || sc.estado_aprobacion === "rechazado") {
      sceneApprBadge = `<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px;" title="${sc.motivo_rechazo || ''}">🔄 Regenerar escena</span>`;
    } else if (sc.estado_aprobacion === "pendiente" && sc.telegram_message_id) {
      sceneApprBadge = `<span class="badge" style="background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid #eab308; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px;">⏳ En Telegram</span>`;
    }

    return `
      Escena ${index + 1}
      <span class="scene-badge-pill" id="dur-badge-${index}">
        ${sc.duracion_real ? sc.duracion_real + 's' : '~' + sc.duracion_estimada + 's'}
      </span>
    `;
  }

  function updateSceneHeaderBadges(idx) {
    const badgeEl = document.querySelector(`#scene-card-${idx} .scene-badge`);
    if (badgeEl && state.scenes[idx]) {
      badgeEl.innerHTML = buildSceneBadgesHtml(state.scenes[idx], idx);
    }
  }

  function renderSceneCharacterChips(sc, index) {
    const allChars = state.currentProject?.personajes || [];
    if (allChars.length === 0) {
      return `<small class="text-muted" style="font-size:0.75rem;">No hay personajes en la biblia genérica</small>`;
    }
    return allChars.map(p => {
      const isSelected = (sc.personajes_en_escena || []).some(n => 
        n.toLowerCase() === p.nombre.toLowerCase() || (p.id && n.toLowerCase() === p.id.toLowerCase())
      );
      return `
        <label class="scene-char-chip ${isSelected ? 'selected' : ''}" data-idx="${index}" data-name="${p.nombre}" title="${p.descripcion_visual || p.nombre}">
          <input type="checkbox" class="chk-scene-char" data-idx="${index}" data-name="${p.nombre}" ${isSelected ? 'checked' : ''} style="display:none;">
          ${p.imagen_url ? `<img src="${p.imagen_url}" class="scene-char-chip-img" alt="${p.nombre}">` : `<span>👤</span>`}
          <span>${p.nombre}</span>
        </label>
      `;
    }).join("");
  }

  function renderSceneEnvSelect(sc, index) {
    const allEnvs = state.currentProject?.escenarios || [];
    const currentEnv = allEnvs.find(e => 
      sc.escenario_clave && (e.nombre.toLowerCase() === sc.escenario_clave.toLowerCase() || (e.id && e.id.toLowerCase() === sc.escenario_clave.toLowerCase()))
    );
    const thumbHtml = (currentEnv && currentEnv.imagen_url)
      ? `<img src="${currentEnv.imagen_url}" class="scene-env-thumb-mini" alt="${currentEnv.nombre}" title="${currentEnv.nombre}">`
      : "";

    return `
      <div style="display: flex; align-items: center; gap: 8px;">
        <div style="flex: 1;">
          <select class="form-select select-scene-env" data-idx="${index}">
            <option value="">🏛️ Escenario general / No fijado</option>
            ${allEnvs.map(e => `
              <option value="${e.nombre}" ${sc.escenario_clave === e.nombre ? 'selected' : ''}>${e.nombre}</option>
            `).join("")}
          </select>
        </div>
        <div id="env-thumb-container-${index}">
          ${thumbHtml}
        </div>
      </div>
    `;
  }

  function buildSceneAudioBlockHtml(sc, index) {
    const hasAudio = Boolean(sc.audio_url);
    const durTxt = sc.duracion_real ? ` (${sc.duracion_real}s)` : "";
    const statusBadge = hasAudio
      ? `<span class="badge" style="background: rgba(34, 197, 94, 0.16); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); font-size: 0.75rem; padding: 0.2rem 0.55rem; border-radius: 6px;">✅ Voz generada${durTxt}</span>`
      : `<span class="badge" style="background: rgba(148, 163, 184, 0.12); color: var(--text-muted); border: 1px solid rgba(148, 163, 184, 0.25); font-size: 0.75rem; padding: 0.2rem 0.55rem; border-radius: 6px;">⚪ Voz no generada</span>`;

    const playerRow = hasAudio
      ? `<div style="margin-top: 0.5rem; width: 100%;">
           <audio controls class="audio-player-mini" style="width: 100%; height: 36px;" src="${sc.audio_url}"></audio>
         </div>`
      : "";

    return `
      <div style="display: flex; align-items: center; justify-content: flex-start; gap: 0.6rem; flex-wrap: wrap;">
        <button type="button" class="btn btn-secondary btn-xs btn-gen-audio" data-idx="${index}">
          🔊 ${hasAudio ? 'Regenerar voz' : 'Generar voz'}
        </button>
        ${statusBadge}
      </div>
      ${playerRow}
    `;
  }

  // Renderizar Storyboard Escena por Escena
  function renderStoryboard() {
    scenesGrid.innerHTML = "";

    state.scenes.forEach((sc, index) => {
      const card = document.createElement("div");
      card.className = "scene-card";
      card.id = `scene-card-${index}`;

      const imgPreviewHtml = sc.image_url 
        ? `<img src="${sc.image_url}" alt="Escena ${index+1}">`
        : `<div class="scene-image-placeholder">
             <span class="placeholder-icon">🖼️</span>
             <small>9:16 Vertical</small>
           </div>`;

      card.innerHTML = `
        <!-- Panel Visual (Izquierda) -->
        <div class="scene-visual-pane">
          <div class="scene-image-preview" id="img-preview-${index}">
            ${imgPreviewHtml}
          </div>
          <div class="scene-image-actions">
            <button class="btn btn-secondary btn-xs btn-gen-img" data-idx="${index}" title="Genera la ilustración 9:16 usando el motor configurado en General (${state.currentProject?.motor_imagenes || 'flux'}) y las referencias de personaje/escenario">
              🎨 ${sc.image_url ? 'Regenerar Foto' : 'Generar Foto'}
            </button>
            <label class="btn btn-ghost btn-xs btn-upload-label">
              📁 Subir Foto
              <input type="file" class="input-upload-img" data-idx="${index}" accept="image/*" style="display:none;">
            </label>
          </div>
          <div style="margin-top:6px; display:flex; flex-direction:column; gap:4px;">
            <button class="btn btn-primary btn-xs btn-animate-scene" data-idx="${index}" ${sc.image_url ? '' : 'disabled'} title="Convierte la imagen en un vídeo con movimiento real del personaje mediante Fal.ai (Image-to-Video)">
              🎥 ${sc.video_clip_url ? 'Re-animar escena' : 'Animar escena (I2V)'}
            </button>
            ${index < state.scenes.length - 1 ? `
              <label style="font-size:0.72rem; display:flex; align-items:center; gap:4px; opacity:0.85; cursor:pointer;">
                <input type="checkbox" class="chk-link-next-scene" data-idx="${index}" ${state.scenes[index + 1]?.image_url ? 'checked' : ''}>
                🔗 Enlazar con escena ${index + 2}
              </label>
            ` : ''}
            <div id="anim-preview-${index}" style="margin-top:4px;">
              ${sc.video_clip_url ? `<video src="${sc.video_clip_url}" controls loop muted playsinline style="width:100%; border-radius:8px; border:1px solid rgba(56,189,248,0.4);"></video>` : ''}
            </div>
          </div>
        </div>

        <!-- Panel Editorial (Derecha) -->
        <div class="scene-editorial-pane">
          <div>
            <div class="scene-header-bar">
              <span class="scene-badge">
                ${buildSceneBadgesHtml(sc, index)}
              </span>
              <div class="scene-tools">
                <button class="btn btn-ghost btn-xs btn-delete-scene" data-idx="${index}" title="Eliminar escena">
                  🗑️
                </button>
              </div>
            </div>

            <!-- 1. Selección de Personajes y Escenario -->
            <div class="scene-canon-binding-box mt-3" style="margin-top: 0.75rem;">
              <div style="margin-bottom: 6px;">
                <span style="font-size: 0.72rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">
                  👥 Personajes en esta escena
                </span>
              </div>
              <div class="scene-char-selector-row">
                ${renderSceneCharacterChips(sc, index)}
              </div>

              <div style="margin-top: 8px; margin-bottom: 4px;">
                <span style="font-size: 0.72rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">
                  🏛️ Escenario
                </span>
              </div>
              ${renderSceneEnvSelect(sc, index)}
            </div>

            <!-- 2. Descripción de la Escena (Amplia, todo el ancho) + Botón debajo a la izquierda -->
            <div class="mt-3">
              <label class="field-label" style="display:block; margin-bottom:0.35rem; font-weight: 600; font-size: 0.85rem;">📝 Descripción de la escena</label>
              <div style="display:flex; justify-content:flex-start; margin-bottom:0.45rem;">
                <button type="button" class="btn btn-secondary btn-xs btn-gen-desc-from-proposal" data-idx="${index}" title="Genera con detalle la descripción de esta escena a partir de la propuesta general de arriba, los personajes y el escenario seleccionados">
                  ✨ Generar la descripción de la escena
                </button>
              </div>
              <textarea class="form-textarea input-scene-desc" data-idx="${index}" rows="6" style="width: 100%; box-sizing: border-box; font-size: 0.88rem; line-height: 1.45; padding: 0.65rem 0.75rem; min-height: 120px;" placeholder="Describe detalladamente qué ocurre y qué aparece en esta escena (acciones de personajes, entorno, transición)...">${sc.descripcion_escena || sc.descripcion || ""}</textarea>
            </div>

            <!-- 3. Prompt Visual + Botón Generar prompt debajo a la izquierda -->
            <div class="mt-3">
              <label class="field-label" style="display:block; margin-bottom:0.35rem; font-weight: 600; font-size: 0.85rem;">🎨 Prompt Visual (Inglés con estilo global, semillas y transición)</label>
              <div style="display:flex; justify-content:flex-start; margin-bottom:0.45rem;">
                <button type="button" class="btn btn-secondary btn-xs btn-gen-prompt-from-desc" data-idx="${index}" title="Genera el prompt visual en inglés usando la descripción de la escena, semillas de personajes y escenario, transición y estilo global">
                  🪄 Generar prompt
                </button>
              </div>
              <textarea class="form-textarea input-prompt" data-idx="${index}" rows="5" style="width: 100%; box-sizing: border-box; font-family: var(--font-mono); font-size: 0.82rem; line-height: 1.4; padding: 0.65rem 0.75rem; min-height: 100px;">${sc.prompt_imagen || ""}</textarea>
            </div>

            <!-- 4. Locución del Narrador + Botón Generar voz debajo + Reproductor debajo -->
            <div class="mt-3">
              <label class="field-label" style="display:block; margin-bottom:0.35rem; font-weight: 600; font-size: 0.85rem;">🎙️ Locución del Narrador</label>
              <textarea class="form-textarea input-narrador" data-idx="${index}" rows="4" style="width: 100%; box-sizing: border-box; font-size: 0.88rem; padding: 0.65rem 0.75rem;">${sc.narrador || ""}</textarea>
              <div id="audio-row-${index}" style="margin-top: 0.5rem; display: flex; flex-direction: column; align-items: flex-start; width: 100%;">
                ${buildSceneAudioBlockHtml(sc, index)}
              </div>
            </div>
          </div>
        </div>
      `;

      scenesGrid.appendChild(card);
    });

    attachSceneEventListeners();
  }

  function attachSceneEventListeners() {
    document.querySelectorAll(".input-scene-desc").forEach(el => {
      el.addEventListener("input", e => {
        const idx = parseInt(e.target.dataset.idx);
        state.scenes[idx].descripcion_escena = e.target.value;
      });
    });

    document.querySelectorAll(".btn-gen-desc-from-proposal").forEach(el => {
      el.addEventListener("click", async e => {
        const idx = parseInt(e.currentTarget.dataset.idx);
        await generateDescriptionFromProposalForScene(idx);
      });
    });

    document.querySelectorAll(".btn-gen-prompt-from-desc").forEach(el => {
      el.addEventListener("click", async e => {
        const idx = parseInt(e.currentTarget.dataset.idx);
        await generatePromptFromDescriptionForScene(idx);
      });
    });

    document.querySelectorAll(".input-narrador").forEach(el => {
      el.addEventListener("input", e => {
        const idx = parseInt(e.target.dataset.idx);
        state.scenes[idx].narrador = e.target.value;
      });
    });

    document.querySelectorAll(".input-prompt").forEach(el => {
      el.addEventListener("input", e => {
        const idx = parseInt(e.target.dataset.idx);
        state.scenes[idx].prompt_imagen = e.target.value;
      });
    });

    // Checkboxes / Chips de Personajes interactivos
    document.querySelectorAll(".chk-scene-char").forEach(el => {
      el.addEventListener("change", async e => {
        const idx = parseInt(e.target.dataset.idx);
        const charName = e.target.dataset.name;
        const checked = e.target.checked;
        const sc = state.scenes[idx];
        if (!sc.personajes_en_escena) sc.personajes_en_escena = [];

        if (checked) {
          if (!sc.personajes_en_escena.some(n => n.toLowerCase() === charName.toLowerCase())) {
            sc.personajes_en_escena.push(charName);
          }
        } else {
          sc.personajes_en_escena = sc.personajes_en_escena.filter(n => n.toLowerCase() !== charName.toLowerCase());
        }

        const parentChip = e.target.closest(".scene-char-chip");
        if (parentChip) {
          if (checked) parentChip.classList.add("selected");
          else parentChip.classList.remove("selected");
        }

        updateSceneHeaderBadges(idx);
        await reinforceSceneConsistency(idx, false);
      });
    });

    // Selector de Escenario interactivo
    document.querySelectorAll(".select-scene-env").forEach(el => {
      el.addEventListener("change", async e => {
        const idx = parseInt(e.target.dataset.idx);
        const val = e.target.value;
        const sc = state.scenes[idx];
        sc.escenario_clave = val;

        const thumbCont = document.getElementById(`env-thumb-container-${idx}`);
        if (thumbCont) {
          const eMatch = state.currentProject?.escenarios?.find(esc => esc.nombre === val);
          if (eMatch && eMatch.imagen_url) {
            thumbCont.innerHTML = `<img src="${eMatch.imagen_url}" class="scene-env-thumb-mini" alt="${eMatch.nombre}" title="${eMatch.nombre}">`;
          } else {
            thumbCont.innerHTML = "";
          }
        }

        updateSceneHeaderBadges(idx);
        await reinforceSceneConsistency(idx, false);
      });
    });

    document.querySelectorAll(".btn-gen-audio").forEach(el => {
      el.addEventListener("click", async e => {
        const idx = parseInt(e.target.dataset.idx);
        await generateAudioForScene(idx);
      });
    });

    document.querySelectorAll(".btn-gen-img").forEach(el => {
      el.addEventListener("click", async e => {
        const idx = parseInt(e.target.dataset.idx);
        await generateImageForScene(idx);
      });
    });

    document.querySelectorAll(".btn-animate-scene").forEach(el => {
      el.addEventListener("click", async e => {
        const idx = parseInt(e.target.dataset.idx);
        await animateSceneForScene(idx);
      });
    });

    document.querySelectorAll(".input-upload-img").forEach(el => {
      el.addEventListener("change", async e => {
        const idx = parseInt(e.target.dataset.idx);
        const file = e.target.files[0];
        if (file) {
          await uploadImageForScene(idx, file);
        }
      });
    });

    document.querySelectorAll(".btn-inject-anchors").forEach(el => {
      el.addEventListener("click", async e => {
        const idx = parseInt(e.target.dataset.idx);
        await reinforceSceneConsistency(idx, true);
      });
    });

    document.querySelectorAll(".btn-rewrite-scene").forEach(el => {
      el.addEventListener("click", async e => {
        const idx = parseInt(e.target.dataset.idx);
        const feedback = prompt("¿Qué cambios deseas en esta escena? (Ej: 'Que aparezca Mateo en primer plano', 'Más oscuro'):", "");
        if (feedback && feedback.trim()) {
          await rewriteSceneWithAI(idx, feedback.trim());
        }
      });
    });

    document.querySelectorAll(".btn-delete-scene").forEach(el => {
      el.addEventListener("click", e => {
        const idx = parseInt(e.target.dataset.idx);
        if (state.scenes.length <= 1) {
          showToast("El capítulo debe tener al menos 1 escena", "error");
          return;
        }
        state.scenes.splice(idx, 1);
        renderStoryboard();
      });
    });

    document.querySelectorAll(".btn-send-scene-telegram").forEach(el => {
      el.addEventListener("click", async e => {
        const idx = parseInt(e.target.dataset.idx);
        await sendSingleSceneClipToTelegram(idx);
      });
    });

    document.querySelectorAll(".btn-approve-scene-clip").forEach(el => {
      el.addEventListener("click", async e => {
        const idx = parseInt(e.target.dataset.idx);
        await applySceneClipDecisionUI(idx, "approve");
      });
    });

    document.querySelectorAll(".btn-redo-scene-clip").forEach(el => {
      el.addEventListener("click", async e => {
        const idx = parseInt(e.target.dataset.idx);
        await applySceneClipDecisionUI(idx, "redo", "Regenerar escena solicitado");
      });
    });
  }

  async function sendSingleSceneClipToTelegram(idx) {
    if (!state.currentProject) return;
    if (!state.currentChapterId) {
      await saveCurrentChapter(true);
    }
    const sc = state.scenes[idx];
    const sceneId = sc.id || (idx + 1);
    showToast(`Enviando clip de Escena #${idx + 1} a Telegram / n8n...`, "info");
    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/chapters/${state.currentChapterId}/scenes/${sceneId}/send-telegram-approval`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ render_clip_if_missing: true, enable_ken_burns: false, trigger_n8n: true })
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        sc.estado_aprobacion = "pendiente";
        sc.telegram_message_id = data.message_id;
        if (data.clip_url) sc.clip_url = data.clip_url;
        updateSceneHeaderBadges(idx);
        showToast(`✅ Clip de Escena #${idx + 1} enviado a Telegram con botones 'Aprobar' y 'Regenerar escena'`, "success");
      } else {
        showToast(data.detail || data.error || "Error enviando clip a Telegram", "error");
      }
    } catch (e) {
      showToast(`Error: ${e.message}`, "error");
    }
  }

  async function applySceneClipDecisionUI(idx, action, feedback = "") {
    if (!state.currentProject) return;
    if (!state.currentChapterId) {
      await saveCurrentChapter(true);
    }
    const sc = state.scenes[idx];
    const sceneId = sc.id || (idx + 1);
    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/chapters/${state.currentChapterId}/scenes/${sceneId}/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, feedback, notify_telegram: true, auto_regenerate_media: false })
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        sc.estado_aprobacion = data.status === "aprobado" ? "aprobado" : "regenerar_solicitado";
        updateSceneHeaderBadges(idx);
        showToast(`✅ Escena #${idx + 1}: ${data.status === "aprobado" ? "Aprobada" : "Marcada para regenerar"}`, "success");
      }
    } catch (e) {
      showToast(`Error: ${e.message}`, "error");
    }
  }

  // Generar Descripción Detallada de la Escena desde la Propuesta
  async function generateDescriptionFromProposalForScene(idx) {
    const sc = state.scenes[idx];
    if (!state.currentProject || !sc) return;

    const btn = document.querySelector(`.btn-gen-desc-from-proposal[data-idx="${idx}"]`);
    if (btn) {
      btn.disabled = true;
      btn.textContent = "⏳ Detallando escena...";
    }

    try {
      const editedProposal = collectEditedProposal() || state.currentProposal || null;
      const res = await fetch("/api/storyboard/generate-description", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: state.currentProject.id,
          scene_index: idx,
          propuesta: editedProposal,
          personajes_en_escena: sc.personajes_en_escena || [],
          escenario_clave: sc.escenario_clave || "",
          characters: state.currentProject.personajes || [],
          escenarios: state.currentProject.escenarios || [],
          narrador: sc.narrador || "",
          chapter_text: rawChapterText ? rawChapterText.value.trim() : "",
          audiencia: state.currentProject.audiencia || "",
          ambiente: state.currentProject.ambiente || ""
        })
      });
      const data = await res.json();
      if (data.success && data.descripcion_escena) {
        sc.descripcion_escena = data.descripcion_escena;
        const descInput = document.querySelector(`.input-scene-desc[data-idx="${idx}"]`);
        if (descInput) {
          descInput.value = data.descripcion_escena;
        }
        await saveCurrentChapter(true);
        showToast(`Descripción detallada generada para Escena ${idx + 1}`, "success");
      } else {
        showToast(data.detail || "No se pudo generar la descripción de la escena", "error");
      }
    } catch (e) {
      showToast(`Error generando descripción: ${e.message}`, "error");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "✨ Generar la descripción de la escena";
      }
    }
  }

  // Generar Prompt Visual desde la Descripción de la Escena
  async function generatePromptFromDescriptionForScene(idx) {
    const sc = state.scenes[idx];
    if (!state.currentProject || !sc) return;

    const desc = (sc.descripcion_escena || sc.descripcion || "").trim();
    if (!desc) {
      showToast("Escribe primero la descripción de la escena", "error");
      return;
    }

    const btn = document.querySelector(`.btn-gen-prompt-from-desc[data-idx="${idx}"]`);
    if (btn) {
      btn.disabled = true;
      btn.textContent = "⏳ Generando prompt...";
    }

    try {
      const editedProposal = collectEditedProposal() || state.currentProposal || null;
      const res = await fetch("/api/storyboard/generate-prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: state.currentProject.id,
          scene_index: idx,
          propuesta: editedProposal,
          descripcion_escena: desc,
          personajes_en_escena: sc.personajes_en_escena || [],
          escenario_clave: sc.escenario_clave || "",
          characters: state.currentProject.personajes || [],
          escenarios: state.currentProject.escenarios || [],
          style_key: state.currentProject.estilo_visual || "cinematic",
          style_details: state.currentProject.estilo_detalles || "",
          audiencia: state.currentProject.audiencia || "",
          ambiente: state.currentProject.ambiente || ""
        })
      });
      const data = await res.json();
      if (data.success && data.prompt_imagen) {
        sc.prompt_imagen = data.prompt_imagen;
        const promptInput = document.querySelector(`.input-prompt[data-idx="${idx}"]`);
        if (promptInput) {
          promptInput.value = data.prompt_imagen;
        }
        await saveCurrentChapter(true);
        showToast(`Prompt visual actualizado para Escena ${idx + 1}`, "success");
      } else {
        showToast(data.detail || "No se pudo generar el prompt", "error");
      }
    } catch (e) {
      showToast(`Error generando prompt: ${e.message}`, "error");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "🪄 Generar prompt";
      }
    }
  }

  // Reforzar e Inyectar Rasgos Canónicos en Escena
  async function reinforceSceneConsistency(idx, showToastNotification = true) {
    const sc = state.scenes[idx];
    if (!state.currentProject) return;

    const btn = document.querySelector(`.btn-inject-anchors[data-idx="${idx}"]`);
    if (btn && showToastNotification) {
      btn.disabled = true;
      btn.textContent = "🛡️ Reforzando...";
    }

    try {
      const res = await fetch("/api/storyboard/inject-anchors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: state.currentProject.id,
          scene: sc,
          characters: state.currentProject.personajes,
          escenarios: state.currentProject.escenarios || [],
          style_key: state.currentProject.estilo_visual,
          style_details: state.currentProject.estilo_detalles || ""
        })
      });
      const data = await res.json();
      if (data.success && data.scene) {
        state.scenes[idx] = data.scene;
        const promptInput = document.querySelector(`.input-prompt[data-idx="${idx}"]`);
        if (promptInput) {
          promptInput.value = data.scene.prompt_imagen;
        }
        if (showToastNotification) {
          showToast(`Rasgos canónicos reforzados en la Escena #${idx+1}`, "success");
        }
      }
    } catch (e) {
      if (showToastNotification) {
        showToast("Error inyectando consistencia", "error");
      }
    } finally {
      if (btn && showToastNotification) {
        btn.disabled = false;
        btn.textContent = "🛡️ Consistencia";
      }
    }
  }

  // Generación de Audio Escena
  async function generateAudioForScene(idx) {
    const sc = state.scenes[idx];
    const btn = document.querySelector(`.btn-gen-audio[data-idx="${idx}"]`);
    btn.disabled = true;
    btn.textContent = "⏳ Generando...";
    setSystemStatus("busy", `Locución Escena #${idx + 1}...`, "Sintetizando voz natural sincronizada...");

    const voiceKey = (univVoiceSelect && univVoiceSelect.value)
      || (state.currentProject && state.currentProject.voz_defecto)
      || "edge_alvaro";

    try {
      const res = await fetch("/api/tts/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: sc.narrador,
          voice_key: voiceKey
        })
      });
      const data = await res.json();
      if (data.success) {
        sc.audio_url = data.url;
        sc.duracion_real = data.duration;

        const audioRow = document.getElementById(`audio-row-${idx}`);
        if (audioRow) {
          audioRow.innerHTML = buildSceneAudioBlockHtml(sc, idx);
          audioRow.querySelector(".btn-gen-audio")?.addEventListener("click", () => generateAudioForScene(idx));
        }
        const durBadge = document.getElementById(`dur-badge-${idx}`);
        if (durBadge) durBadge.textContent = `${data.duration}s`;
        await saveCurrentChapter(true);
        showToast(`Audio escena ${idx+1} listo (${data.duration}s)`, "success");
        setSystemStatus("success", `Locución Escena #${idx + 1} lista (${data.duration}s)`, "Audio sincronizado con el narrador.");
      } else {
        showToast(data.detail || `Error en audio escena ${idx+1}`, "error");
        setSystemStatus("error", `Error de voz en Escena #${idx + 1}`, data.detail || "Fallo en motor de voz.");
      }
    } catch (err) {
      showToast(`Error en audio escena ${idx+1}`, "error");
      setSystemStatus("error", `Error en audio Escena #${idx + 1}`, err.message);
    } finally {
      btn.disabled = false;
    }
  }

  // Animación Image-to-Video (Fal.ai) con enlace opcional a la escena siguiente
  async function animateSceneForScene(idx) {
    const sc = state.scenes[idx];
    if (!sc || !sc.image_url) {
      showToast("Primero genera o sube una imagen para esta escena", "error");
      return;
    }
    const btn = document.querySelector(`.btn-animate-scene[data-idx="${idx}"]`);
    const linkChk = document.querySelector(`.chk-link-next-scene[data-idx="${idx}"]`);
    const nextSc = (linkChk && linkChk.checked && state.scenes[idx + 1] && state.scenes[idx + 1].image_url)
      ? state.scenes[idx + 1]
      : null;

    if (btn) {
      btn.disabled = true;
      btn.textContent = "⏳ Animando (30-90s)...";
    }
    setSystemStatus(
      "busy",
      `Animando Escena #${idx + 1} (I2V)...`,
      nextSc ? `Generando movimiento y transición continua hacia Escena #${idx + 2}...` : "Generando movimiento del personaje en su entorno..."
    );

    const rCfg = typeof getRenderConfig === "function" ? getRenderConfig() : { aspect_ratio: "9:16" };
    try {
      const res = await fetch("/api/scene/animate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: sc.descripcion_escena || sc.prompt_imagen || sc.narrador || "",
          image_url: sc.image_url,
          next_image_url: nextSc ? nextSc.image_url : null,
          transition_text: nextSc ? (nextSc.descripcion_escena || "").slice(0, 220) : "",
          duration: (sc.duracion_real && sc.duracion_real > 6.5) ? "10" : "5",
          target_duration_sec: sc.duracion_real || sc.duracion_estimada || 10,
          aspect_ratio: rCfg.aspect_ratio || "9:16",
          model: "kling_v16"
        })
      });
      const data = await res.json();
      if (data.success && data.video_clip_url) {
        sc.video_clip_url = data.video_clip_url;
        const preview = document.getElementById(`anim-preview-${idx}`);
        if (preview) {
          preview.innerHTML = `<video src="${sc.video_clip_url}?t=${Date.now()}" controls loop muted playsinline style="width:100%; border-radius:8px; border:1px solid rgba(56,189,248,0.4);"></video>`;
        }
        await saveCurrentChapter(true);
        showToast(`Escena #${idx + 1} animada (${data.size_mb} MB)${data.linked_next ? ' 🔗 enlazada' : ''}`, "success");
        setSystemStatus("success", `Escena #${idx + 1} animada`, "Clip de movimiento guardado y listo para el montaje final.");
      } else {
        showToast(data.detail || `Error animando escena ${idx + 1}`, "error");
        setSystemStatus("error", `Error animando Escena #${idx + 1}`, data.detail || "Fallo en I2V");
      }
    } catch (err) {
      showToast(`Error animando escena ${idx + 1}`, "error");
      setSystemStatus("error", `Error animando Escena #${idx + 1}`, err.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = sc.video_clip_url ? "🎥 Re-animar escena" : "🎥 Animar escena (I2V)";
      }
    }
  }

  // Generación de Imagen Escena con Inyección de Referencia
  async function generateImageForScene(idx) {
    const sc = state.scenes[idx];
    const btn = document.querySelector(`.btn-gen-img[data-idx="${idx}"]`);
    btn.disabled = true;
    btn.textContent = "🎨 Dibujando...";
    setSystemStatus("busy", `Pintando Escena #${idx + 1}...`, "Dibujando fotograma 9:16 con estilo consistente y referencias...");

    // Resolver imágenes de referencia y semillas de consistencia de personajes y escenario
    let refImageUrl = null;
    let charSeed = null;
    let envSeed = null;
    if (state.currentProject?.personajes && sc.personajes_en_escena && sc.personajes_en_escena.length > 0) {
      for (const charName of sc.personajes_en_escena) {
        const pMatch = state.currentProject.personajes.find(p => 
          p.nombre.toLowerCase() === charName.toLowerCase() ||
          (p.id && p.id.toLowerCase() === charName.toLowerCase())
        );
        if (pMatch) {
          if (!refImageUrl && pMatch.imagen_url) refImageUrl = pMatch.imagen_url;
          if (!charSeed && pMatch.seed_consistencia) charSeed = parseInt(pMatch.seed_consistencia);
        }
      }
    }
    if (state.currentProject?.escenarios && sc.escenario_clave) {
      const eMatch = state.currentProject.escenarios.find(e =>
        e.nombre.toLowerCase() === sc.escenario_clave.toLowerCase() ||
        (e.id && e.id.toLowerCase() === sc.escenario_clave.toLowerCase())
      );
      if (eMatch) {
        if (!refImageUrl && eMatch.imagen_url) refImageUrl = eMatch.imagen_url;
        if (eMatch.seed_consistencia) envSeed = parseInt(eMatch.seed_consistencia);
      }
    }
    const baseSeed = (charSeed && envSeed)
      ? (((charSeed + envSeed) % 900000) + 100000)
      : (charSeed || envSeed || sc.seed_consistencia || null);

    // Si la escena ya tiene imagen y el usuario pulsa "Regenerar Foto", variar el seed para obtener una composición distinta.
    // Además, desplazar por índice de escena (idx) para que Escena 1 y Escena 2 nunca compartan la misma semilla.
    let effectiveSeed = null;
    if (sc.image_url) {
      effectiveSeed = Math.floor(100000 + Math.random() * 899999);
    } else if (baseSeed !== null) {
      effectiveSeed = (((parseInt(baseSeed, 10) + (idx + 1) * 7919) % 900000) + 100000);
    }
    if (effectiveSeed !== null) {
      sc.seed_consistencia = effectiveSeed;
    }

    try {
      const res = await fetch("/api/image/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: sc.prompt_imagen,
          provider: state.currentProject?.motor_imagenes || "flux",
          seed: effectiveSeed,
          reference_image: refImageUrl
        })
      });
      const data = await res.json();
      if (data.success) {
        sc.image_url = data.url;
        const preview = document.getElementById(`img-preview-${idx}`);
        const freshUrl = data.url.includes("?") ? `${data.url}&t=${Date.now()}` : `${data.url}?t=${Date.now()}`;
        preview.innerHTML = `<img src="${freshUrl}" alt="Escena ${idx+1}">`;
        btn.textContent = "🎨 Regenerar Foto";
        await saveCurrentChapter(true);
        showToast(`Imagen escena ${idx+1} generada en 9:16`, "success");
        setSystemStatus("success", `Fotograma Escena #${idx + 1} listo`, "Arte vertical 9:16 generado con éxito.");
      } else {
        showToast(data.detail || `Error en imagen escena ${idx+1}`, "error");
        setSystemStatus("error", `Error en imagen Escena #${idx + 1}`, data.detail || "Fallo en motor de imagen.");
      }
    } catch (err) {
      showToast(`Error en imagen escena ${idx+1}`, "error");
      setSystemStatus("error", `Error generando imagen Escena #${idx + 1}`, err.message);
    } finally {
      btn.disabled = false;
    }
  }

  async function uploadImageForScene(idx, file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/image/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (data.success) {
        state.scenes[idx].image_url = data.url;
        const preview = document.getElementById(`img-preview-${idx}`);
        preview.innerHTML = `<img src="${data.url}" alt="Escena ${idx+1}">`;
        showToast(`Imagen subida y recortada a 9:16`, "success");
      }
    } catch (e) {
      showToast("Error subiendo foto", "error");
    }
  }

  async function rewriteSceneWithAI(idx, feedback) {
    const sc = state.scenes[idx];
    showToast("Reescribiendo escena...", "info");

    try {
      const res = await fetch("/api/storyboard/rewrite-scene", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scene: sc,
          feedback: feedback,
          characters: state.currentProject.personajes,
          style_key: state.currentProject.estilo_visual,
          style_details: state.currentProject.estilo_detalles || ""
        })
      });
      const data = await res.json();
      if (data.success) {
        state.scenes[idx] = data.scene;
        renderStoryboard();
        showToast("Escena actualizada con tus indicaciones", "success");
      }
    } catch (e) {
      showToast("Error reescribiendo escena", "error");
    }
  }

  // Acciones en Lote
  btnGenerateAllAudio.addEventListener("click", async () => {
    btnGenerateAllAudio.disabled = true;
    showToast("Generando audios para todas las escenas...", "info");
    setSystemStatus("busy", "Generando todas las locuciones...", `Sintetizando ${state.scenes.length} escenas con IA de voz...`);
    for (let i = 0; i < state.scenes.length; i++) {
      if (!state.scenes[i].audio_url) {
        await generateAudioForScene(i);
      }
    }
    btnGenerateAllAudio.disabled = false;
    showToast("Todos los audios están listos", "success");
    setSystemStatus("success", "¡Todas las locuciones completadas!", "Audios de narración listos para el montaje.");
  });

  btnGenerateAllImages.addEventListener("click", async () => {
    btnGenerateAllImages.disabled = true;
    showToast("Generando imágenes para todas las escenas...", "info");
    setSystemStatus("busy", "Generando todos los fotogramas...", `Pintando ${state.scenes.length} imágenes con consistencia visual...`);
    for (let i = 0; i < state.scenes.length; i++) {
      if (!state.scenes[i].image_url) {
        await generateImageForScene(i);
      }
    }
    btnGenerateAllImages.disabled = false;
    showToast("Todas las imágenes están listas", "success");
    setSystemStatus("success", "¡Todos los fotogramas completados!", "Imágenes 9:16 listas para el montaje.");
  });

  btnAddScene.addEventListener("click", () => {
    const newId = state.scenes.length + 1;
    state.scenes.push({
      id: newId,
      narrador: "Nueva escena de la historia.",
      prompt_imagen: `Vertical 9:16 portrait composition, ${state.currentProject ? state.currentProject.estilo_visual : 'cinematic'}, high detail`,
      personajes_en_escena: [],
      duracion_estimada: 5,
      audio_url: null,
      image_url: null,
      duracion_real: null
    });
    renderStoryboard();
    showToast("Escena añadida al storyboard", "info");
  });

  // Guardar Capítulo como borrador
  if (btnSaveChapterDraft) {
    btnSaveChapterDraft.addEventListener("click", () => saveCurrentChapter(false));
  }

  document.getElementById("btn-send-clips-telegram")?.addEventListener("click", async () => {
    if (!state.currentProject) {
      showToast("Selecciona un proyecto primero", "warning");
      return;
    }
    if (!state.currentChapterId) {
      await saveCurrentChapter(true);
    }
    const btn = document.getElementById("btn-send-clips-telegram");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "⏳ Enviando Clips a Telegram...";
    }
    setSystemStatus("busy", "Enviando clips a Telegram / n8n...", "Generando clips previos y enviando a Telegram con botones 'Aprobar' y 'Regenerar escena'...");
    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/chapters/${state.currentChapterId}/send-clips-approval`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ render_clip_if_missing: true, enable_ken_burns: false, trigger_n8n: true })
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        await loadSavedChapter(state.currentChapterId);
        showToast(`✅ ${data.sent_scenes_count} clips enviados a Telegram para aprobación pre-ensamblado`, "success");
        setSystemStatus("success", "Clips enviados a Telegram", `${data.sent_scenes_count} escenas listas con botones 'Aprobar' y 'Regenerar escena'.`);
      } else {
        showToast(data.detail || "Error enviando clips a Telegram", "error");
      }
    } catch (e) {
      showToast(`Error: ${e.message}`, "error");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "📱 Enviar Clips a Telegram (Pre-Ensamblado)";
      }
    }
  });

  document.getElementById("btn-poll-clips-telegram")?.addEventListener("click", async () => {
    await syncTelegramUpdates();
    if (state.currentChapterId) {
      await loadSavedChapter(state.currentChapterId);
    }
  });

  if (btnAnimateAllScenes) {
    btnAnimateAllScenes.addEventListener("click", async () => {
      if (!state.scenes || state.scenes.length === 0) return;
      btnAnimateAllScenes.disabled = true;
      btnAnimateAllScenes.textContent = "⏳ Animando todas...";
      for (let i = 0; i < state.scenes.length; i++) {
        if (state.scenes[i].image_url) {
          await animateSceneForScene(i);
        }
      }
      btnAnimateAllScenes.disabled = false;
      btnAnimateAllScenes.textContent = "🎥 Animar Todas las Escenas";
      showToast("Todas las escenas han sido animadas y enlazadas", "success");
    });
  }

  // Renderizar Vídeo Final con FFmpeg
  btnRenderVideo.addEventListener("click", async () => {
    if (!state.scenes || state.scenes.length === 0) {
      showToast("No hay escenas para renderizar", "error");
      return;
    }

    setSystemStatus(
      "busy",
      "Montando vídeo final con FFmpeg...",
      "Verificando elementos y ensamblando vídeo vertical con efectos cinemáticos y subtítulos..."
    );

    // Auto-generar audios e imágenes pendientes
    renderProgress.style.display = "block";
    progressText.textContent = "Verificando audios e imágenes de cada escena...";

    for (let i = 0; i < state.scenes.length; i++) {
      if (!state.scenes[i].audio_url) {
        progressText.textContent = `Generando locución escena ${i+1}...`;
        await generateAudioForScene(i);
      }
      if (!state.scenes[i].image_url) {
        progressText.textContent = `Dibujando fotograma escena ${i+1}...`;
        await generateImageForScene(i);
      }
    }

    progressText.textContent = "Ensamblando vídeo vertical con FFmpeg (Efecto Ken Burns + Subtítulos)...";
    setSystemStatus(
      "busy",
      "Renderizando vídeo vertical 1080x1920...",
      "FFmpeg está combinando pistas de audio, aplicando Ken Burns y quemando subtítulos automáticos..."
    );
    btnRenderVideo.disabled = true;

    try {
      const res = await fetch("/api/video/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: chapterTitleInput.value.trim() || "Capítulo",
          project_id: state.currentProject ? state.currentProject.id : null,
          chapter_id: state.currentChapterId,
          scenes: state.scenes,
          enable_subtitles: subEnabledEl ? subEnabledEl.checked : true,
          enable_ken_burns: renderKbStyleEl ? renderKbStyleEl.value !== "fijo" : true,
          subtitle_config: typeof getSubtitleConfig === "function" ? getSubtitleConfig() : undefined,
          render_config: typeof getRenderConfig === "function" ? getRenderConfig() : undefined
        })
      });

      const data = await res.json();
      if (data.success && data.video_url) {
        // Mostrar vídeo en mockup de smartphone
        phoneEmpty.style.display = "none";
        phoneVideoContainer.style.display = "block";
        finalVideoPlayer.src = data.video_url;
        finalVideoPlayer.play().catch(() => {});

        phoneCaption.textContent = `${chapterTitleInput.value} • Creado con VideoStudio AI 🚀`;

        // Datos meta
        videoMetaCard.style.display = "block";
        metaDuration.textContent = `${data.duration}s`;
        metaSize.textContent = `${data.size_mb} MB`;
        metaScenes.textContent = data.scenes_count;
        btnDownloadVideo.href = data.video_url;

        showToast("¡Vídeo renderizado con éxito a 1080x1920!", "success");
        setSystemStatus(
          "success",
          "¡Vídeo renderizado con éxito!",
          `Capítulo montado a 1080x1920 (${data.duration}s, ${data.size_mb} MB). Listo para descargar o previsualizar.`
        );

        // Actualizar lista de capítulos
        if (state.currentProject) {
          await loadProjectChapters(state.currentProject.id, state.currentChapterId);
        }
      } else {
        showToast(data.detail || "Error renderizando vídeo", "error");
        setSystemStatus("error", "Error en renderizado de vídeo", data.detail || "Fallo en motor de render.");
      }
    } catch (e) {
      showToast(`Error renderizando vídeo: ${e.message}`, "error");
      setSystemStatus("error", "Error de conexión en render", e.message);
    } finally {
      renderProgress.style.display = "none";
      btnRenderVideo.disabled = false;
    }
  });

  // ========================================================
  // 6.1 ÁRBOL DE CAPÍTULOS Y FUENTE DEL MANUSCRITO (CAPA ESPECÍFICA)
  // ========================================================

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function updateChapterWordsCounter() {
    if (!chapterWordsCounter || !rawChapterText) return;
    const words = rawChapterText.value.trim().split(/\s+/).filter(Boolean).length;
    chapterWordsCounter.textContent = `${words} palabras`;
    if (words > 400) {
      chapterWordsCounter.style.background = "rgba(239, 68, 68, 0.2)";
      chapterWordsCounter.style.color = "#f87171";
      chapterWordsCounter.title = "Texto extenso para un solo vídeo vertical de 60s. Te recomendamos dividirlo.";
    } else {
      chapterWordsCounter.style.background = "rgba(99, 102, 241, 0.15)";
      chapterWordsCounter.style.color = "var(--primary-glow)";
      chapterWordsCounter.title = "";
    }
  }

  async function loadProjectChapters(projectId, selectChapterId = null) {
    if (!projectId) return;
    try {
      const res = await fetch(`/api/projects/${projectId}/chapters`);
      const chapters = await res.json();
      state.chapters = Array.isArray(chapters) ? chapters : [];
      if (treeChaptersCounter) {
        treeChaptersCounter.textContent = `${state.chapters.length} caps`;
      }

      renderChaptersTree(treeSearchInput ? treeSearchInput.value : "");
      populateManuscriptSections();
      if (state.manuscriptDoc?.chapters?.length) updateSectionPreview(state.selectedSectionIdx || 0);

      if (state.chapters.length > 0) {
        let targetId = selectChapterId;
        if (!targetId || !state.chapters.some(c => c.id === targetId)) {
          targetId = state.currentChapterId && state.chapters.some(c => c.id === state.currentChapterId)
            ? state.currentChapterId
            : state.chapters[0].id;
        }
        await loadSavedChapter(targetId);
      } else {
        createNewChapterDraft();
      }
    } catch (err) {
      console.error("Error cargando capítulos:", err);
      showToast("Error cargando lista de capítulos", "error");
    }
  }

  function highlightActiveTreeChapter(targetId) {
    if (!chaptersTreeList) return;
    chaptersTreeList.querySelectorAll(".tree-chapter-node").forEach(node => {
      if (node.getAttribute("data-id") === targetId) {
        node.classList.add("active");
      } else {
        node.classList.remove("active");
      }
    });
  }

  function renderChaptersTree(filterQuery = "") {
    if (!chaptersTreeList) return;
    chaptersTreeList.innerHTML = "";

    const query = (filterQuery || "").toLowerCase().trim();
    const filtered = state.chapters
      .filter(c => {
        if (!query) return true;
        const titleMatch = (c.titulo || "").toLowerCase().includes(query);
        const originMatch = (c.origen_ref || "").toString().toLowerCase().includes(query);
        return titleMatch || originMatch;
      })
      .sort((a, b) => {
        const ca = (a.creado_en || "").toString();
        const cb = (b.creado_en || "").toString();
        if (ca && cb && ca !== cb) return ca.localeCompare(cb);
        return (a.titulo || "").localeCompare(b.titulo || "", "es", { numeric: true, sensitivity: "base" });
      });

    if (filtered.length === 0) {
      if (state.chapters.length === 0) {
        chaptersTreeList.innerHTML = `
          <div class="tree-empty-state">
            <p class="text-muted" style="font-size:0.82rem; margin-bottom:0.5rem;">
              No hay capítulos creados en este libro.
            </p>
            <div style="font-size:0.75rem; color:var(--text-secondary); line-height:1.4;">
              Usa <strong>⚡ Importar</strong> para convertir el manuscrito en capítulos o pulsa <strong>➕ Nuevo capítulo</strong>.
            </div>
          </div>
        `;
      } else {
        chaptersTreeList.innerHTML = `
          <div class="tree-empty-state">
            <p class="text-muted" style="font-size:0.82rem;">
              No hay capítulos que coincidan con "<em>${escapeHtml(filterQuery)}</em>".
            </p>
          </div>
        `;
      }
    }

    filtered.forEach(cap => {
      const isActive = cap.id === state.currentChapterId;
      const node = document.createElement("div");
      node.className = `tree-chapter-node ${isActive ? "active" : ""}`;
      node.setAttribute("data-id", cap.id);

      // Status pill
      let statusPill = "";
      if (cap.video_url) {
        statusPill = `<span class="status-pill status-rendered">🎬 Render</span>`;
      } else if (cap.scenes && cap.scenes.length > 0) {
        statusPill = `<span class="status-pill status-storyboard">📋 ${cap.scenes.length} esc</span>`;
      } else {
        statusPill = `<span class="status-pill status-draft">✏️ Borrador</span>`;
      }

      // Origin badge
      let originBadge = "";
      if (cap.origen_tipo === "page" && cap.origen_ref) {
        originBadge = `<span class="tree-node-meta-badge">Pág. ${cap.origen_ref}</span>`;
      } else if (cap.origen_tipo === "section" && cap.origen_ref) {
        originBadge = `<span class="tree-node-meta-badge">Sec.</span>`;
      }

      // Duration badge
      const durationBadge = cap.duracion ? `<span class="tree-node-meta-badge">⏱️ ${cap.duracion}s</span>` : "";

      node.innerHTML = `
        <div class="tree-node-main">
          <div class="tree-node-title-row">
            <span class="tree-node-title" title="${escapeHtml(cap.titulo)}">${escapeHtml(cap.titulo)}</span>
            <button class="tree-node-del-btn" data-id="${cap.id}" data-title="${escapeHtml(cap.titulo)}" title="Eliminar capítulo">🗑️</button>
          </div>
          <div class="tree-node-meta-row">
            ${statusPill}
            ${originBadge}
            ${durationBadge}
          </div>
        </div>
      `;

      node.addEventListener("click", e => {
        if (e.target.closest(".tree-node-del-btn")) return;
        loadSavedChapter(cap.id);
      });

      const delBtn = node.querySelector(".tree-node-del-btn");
      if (delBtn) {
        delBtn.addEventListener("click", e => {
          e.stopPropagation();
          deleteChapter(cap.id, cap.titulo);
        });
      }

      chaptersTreeList.appendChild(node);
    });

    // Nodo final con el mismo tamaño para crear un nuevo capítulo
    const newNode = document.createElement("div");
    newNode.className = "tree-chapter-node";
    newNode.style.borderStyle = "dashed";
    newNode.style.opacity = "0.9";
    newNode.innerHTML = `
      <div class="tree-node-main">
        <div class="tree-node-title-row">
          <span class="tree-node-title">➕ Nuevo capítulo</span>
        </div>
        <div class="tree-node-meta-row">
          <span class="tree-node-meta-badge">Crear borrador</span>
        </div>
      </div>
    `;
    newNode.addEventListener("click", () => {
      createNewChapterDraft();
      showToast("Nuevo borrador de capítulo listo", "info");
    });
    chaptersTreeList.appendChild(newNode);
  }

  async function loadSavedChapter(chapterId) {
    if (!state.currentProject) return;
    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/chapters/${chapterId}`);
      if (!res.ok) throw new Error("Capítulo no encontrado");
      const cap = await res.json();

      state.currentChapterId = cap.id;
      state.currentChapterOriginType = cap.origen_tipo || null;
      state.currentChapterOriginRef = cap.origen_ref || null;
      state.currentChapterOrden = cap.orden || 1;

      chapterTitleInput.value = cap.titulo || "";
      rawChapterText.value = cap.texto_original || "";
      if (!rawChapterText.value && cap.scenes && cap.scenes.length > 0) {
        rawChapterText.value = cap.scenes.map(s => s.narrador).filter(Boolean).join("\n\n");
      }
      updateChapterWordsCounter();

      if (currentChapterHeading) {
        currentChapterHeading.textContent = cap.titulo || "Capítulo";
      }

      if (currentChapterOriginPill) {
        if (cap.origen_tipo === "page" && cap.origen_ref) {
          currentChapterOriginPill.textContent = `📄 Pág. ${cap.origen_ref}`;
          currentChapterOriginPill.style.display = "inline-flex";
        } else if (cap.origen_tipo === "section" && cap.origen_ref) {
          currentChapterOriginPill.textContent = `📑 ${cap.origen_ref}`;
          currentChapterOriginPill.style.display = "inline-flex";
        } else {
          currentChapterOriginPill.textContent = "✍️ Manual";
          currentChapterOriginPill.style.display = "inline-flex";
        }
      }

      state.scenes = cap.scenes || [];
      renderChapterProposal(cap.propuesta || null);
      storyboardTitle.textContent = "Escenas";

      if (state.scenes && state.scenes.length > 0) {
        renderStoryboard();
        storyboardContainer.style.display = "block";
      } else {
        storyboardContainer.style.display = "none";
      }

      if (cap.video_url) {
        phoneEmpty.style.display = "none";
        phoneVideoContainer.style.display = "block";
        finalVideoPlayer.src = cap.video_url;
        finalVideoPlayer.muted = false;
        finalVideoPlayer.volume = 1.0;
        btnDownloadVideo.href = cap.video_url;
        videoMetaCard.style.display = "block";
        metaDuration.textContent = `${cap.duracion || 0}s`;
        if (metaSize) metaSize.textContent = cap.peso_mb ? `${cap.peso_mb} MB` : (cap.video_url ? "~3.3 MB" : "0 MB");
        if (metaScenes) metaScenes.textContent = cap.scenes ? cap.scenes.length : 0;
        phoneCaption.textContent = `${cap.titulo} • VideoStudio AI 🚀`;
      } else {
        phoneEmpty.style.display = "flex";
        phoneVideoContainer.style.display = "none";
        videoMetaCard.style.display = "none";
      }

      highlightActiveTreeChapter(cap.id);
    } catch (e) {
      console.error("Error cargando capítulo:", e);
      showToast("Error cargando capítulo", "error");
    }
  }

  function createNewChapterDraft(initialData = {}) {
    state.currentChapterId = null;
    state.currentChapterOriginType = initialData.origen_tipo || null;
    state.currentChapterOriginRef = initialData.origen_ref || null;
    state.currentChapterOrden = initialData.orden || (state.chapters.length + 1);
    renderChapterProposal(null);

    const defaultTitle = initialData.titulo || `Capítulo ${state.chapters.length + 1}`;
    chapterTitleInput.value = defaultTitle;
    rawChapterText.value = initialData.texto || "";
    updateChapterWordsCounter();

    if (currentChapterHeading) {
      currentChapterHeading.textContent = defaultTitle;
    }
    if (currentChapterOriginPill) {
      if (initialData.origen_tipo === "page") {
        currentChapterOriginPill.textContent = `📄 Pág. ${initialData.origen_ref}`;
        currentChapterOriginPill.style.display = "inline-flex";
      } else if (initialData.origen_tipo === "section") {
        currentChapterOriginPill.textContent = `📑 ${initialData.origen_ref}`;
        currentChapterOriginPill.style.display = "inline-flex";
      } else {
        currentChapterOriginPill.textContent = "✏️ Borrador Nuevo";
        currentChapterOriginPill.style.display = "inline-flex";
      }
    }

    state.scenes = [];
    storyboardContainer.style.display = "none";
    phoneEmpty.style.display = "flex";
    phoneVideoContainer.style.display = "none";
    videoMetaCard.style.display = "none";

    highlightActiveTreeChapter(null);
    chapterTitleInput.focus();
  }

  async function saveCurrentChapter(silent = false) {
    if (!state.currentProject) {
      showToast("Selecciona un proyecto primero", "error");
      return;
    }
    const title = chapterTitleInput.value.trim() || `Capítulo ${state.chapters.length + 1}`;
    const text = rawChapterText.value.trim();

    const payload = {
      project_id: state.currentProject.id,
      chapter_id: state.currentChapterId,
      titulo: title,
      texto_original: text,
      scenes: state.scenes || [],
      origen_tipo: state.currentChapterOriginType || "manual",
      origen_ref: state.currentChapterOriginRef ? String(state.currentChapterOriginRef) : "",
      orden: state.currentChapterOrden || (state.chapters.length + 1),
      propuesta: collectEditedProposal()
    };

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/chapters`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success && data.chapter) {
        state.currentChapterId = data.chapter.id;
        if (!silent) {
          showToast(`Capítulo '${title}' guardado correctamente`, "success");
        }
        await loadProjectChapters(state.currentProject.id, state.currentChapterId);
      } else {
        throw new Error(data.detail || "Error guardando capítulo");
      }
    } catch (e) {
      console.error("Error guardando capítulo:", e);
      showToast("Error guardando capítulo: " + e.message, "error");
    }
  }

  async function deleteChapter(chapterId, title) {
    if (!state.currentProject || !chapterId) return;
    const ok = confirm(`¿Estás seguro de eliminar el capítulo "${title}"? Se borrarán sus escenas y configuraciones.`);
    if (!ok) return;

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/chapters/${chapterId}`, {
        method: "DELETE"
      });
      const data = await res.json();
      if (data.success) {
        showToast(`Capítulo "${title}" eliminado`, "info");
        if (state.currentChapterId === chapterId) {
          state.currentChapterId = null;
          createNewChapterDraft();
        }
        await loadProjectChapters(state.currentProject.id);
      } else {
        showToast("Error eliminando capítulo: " + (data.detail || "Error"), "error");
      }
    } catch (err) {
      console.error("Error eliminando capítulo:", err);
      showToast("Error eliminando capítulo", "error");
    }
  }

  async function loadManuscriptStructure(projectId) {
    if (!projectId) return;
    try {
      const res = await fetch(`/api/projects/${projectId}/documents/content`);
      const data = await res.json();
      if (data.success && data.document) {
        const doc = data.document;
        state.manuscriptDoc = doc;

        const totalPages = doc.total_pages || (doc.pages ? doc.pages.length : 0);
        const totalChapters = doc.chapters ? doc.chapters.length : 0;

        if (sourcePagesCount) sourcePagesCount.textContent = `${totalPages} págs`;
        if (sourceChaptersCount) sourceChaptersCount.textContent = `${totalChapters} secciones`;
        if (badgeImportPagesCount) badgeImportPagesCount.textContent = `${totalPages} páginas disponibles`;
        if (badgeImportChaptersCount) badgeImportChaptersCount.textContent = `${totalChapters} secciones disponibles`;
        const analysisStatusEl = document.getElementById("book-chapters-analysis-status");
        if (analysisStatusEl) {
          analysisStatusEl.textContent = `✓ Detectados ${totalChapters} capítulos/secciones en "${doc.filename || "libro"}" (${totalPages} págs).`;
        }

        // Poblar selector de páginas
        if (selectManuscriptPage && doc.pages && doc.pages.length > 0) {
          selectManuscriptPage.innerHTML = "";
          doc.pages.forEach(p => {
            const opt = document.createElement("option");
            opt.value = p.page_number;
            opt.textContent = `Pág. ${p.page_number}: ${p.short_title || p.title} (${p.word_count} palabras)`;
            selectManuscriptPage.appendChild(opt);
          });

          state.selectedPageNum = doc.pages[0].page_number;
          selectManuscriptPage.value = state.selectedPageNum;
          updatePagePreview(state.selectedPageNum);
        }

        // Poblar selector de secciones / capítulos detectados
        if (selectManuscriptSection && doc.chapters && doc.chapters.length > 0) {
          populateManuscriptSections();

          state.selectedSectionIdx = 0;
          selectManuscriptSection.value = 0;
          updateSectionPreview(0);

          if (tabSrcChapter && tabSrcPage) {
            tabSrcChapter.classList.add("active");
            tabSrcPage.classList.remove("active");
            if (panelSourceChapter) panelSourceChapter.style.display = "block";
            if (panelSourcePage) panelSourcePage.style.display = "none";
          }
        }
      }
    } catch (err) {
      console.warn("No se pudo cargar estructura del manuscrito:", err);
    }
  }

  function updatePagePreview(pageNum) {
    if (!state.manuscriptDoc || !state.manuscriptDoc.pages) return;
    const pNum = parseInt(pageNum);
    state.selectedPageNum = pNum;

    const page = state.manuscriptDoc.pages.find(p => p.page_number === pNum);
    if (!page) return;

    if (pagePreviewBadge) {
      pagePreviewBadge.textContent = page.title || `Página ${page.page_number}`;
    }
    if (pagePreviewStats) {
      const total = state.manuscriptDoc.total_pages || state.manuscriptDoc.pages.length;
      pagePreviewStats.textContent = `Página ${page.page_number} de ${total} • ${page.word_count} palabras • Ideal para 1 vídeo vertical`;
    }
    if (pagePreviewText) {
      pagePreviewText.textContent = page.text || "(Esta página no contiene texto extraíble)";
    }

    if (btnPrevPage) {
      btnPrevPage.disabled = pNum <= 1;
    }
    if (btnNextPage) {
      const total = state.manuscriptDoc.total_pages || state.manuscriptDoc.pages.length;
      btnNextPage.disabled = pNum >= total;
    }
  }

  function shortSectionTitle(title) {
    const raw = (title || "").trim();
    if (!raw) return "Sección";
    const firstSentence = raw.split(/\.\s+/)[0].trim();
    const base = firstSentence.length >= 4 && firstSentence.length <= 55 ? firstSentence : raw;
    return base.length > 55 ? base.slice(0, 52) + "..." : base;
  }

  function isSectionAssigned(secTitle) {
    if (!secTitle) return false;
    if (state.currentChapterOriginType === "section" && state.currentChapterOriginRef === secTitle) {
      return true;
    }
    return (state.chapters || []).some(c => c.origen_tipo === "section" && c.origen_ref === secTitle);
  }

  function populateManuscriptSections() {
    if (!selectManuscriptSection || !state.manuscriptDoc || !state.manuscriptDoc.chapters) return;
    const prevVal = selectManuscriptSection.value;
    selectManuscriptSection.innerHTML = "";
    state.manuscriptDoc.chapters.forEach((sec, idx) => {
      const opt = document.createElement("option");
      opt.value = idx;
      const assigned = isSectionAssigned(sec.title);
      const label = shortSectionTitle(sec.title);
      opt.textContent = `${assigned ? "✓ [Asignado] " : ""}${label} (~${sec.word_count || 0} palabras)`;
      if (assigned) {
        opt.style.color = "#4ade80";
        opt.style.fontWeight = "600";
      }
      selectManuscriptSection.appendChild(opt);
    });
    if (prevVal !== "" && state.manuscriptDoc.chapters[parseInt(prevVal)]) {
      selectManuscriptSection.value = prevVal;
    }
  }

  function updateSectionPreview(secIdx) {
    if (!state.manuscriptDoc || !state.manuscriptDoc.chapters) return;
    const idx = parseInt(secIdx);
    state.selectedSectionIdx = idx;

    const sec = state.manuscriptDoc.chapters[idx];
    if (!sec) return;

    const assigned = isSectionAssigned(sec.title);
    if (sectionPreviewBadge) {
      sectionPreviewBadge.textContent = shortSectionTitle(sec.title) || `Sección ${idx + 1}`;
      sectionPreviewBadge.style.color = assigned ? "#4ade80" : "";
      sectionPreviewBadge.style.borderColor = assigned ? "rgba(34,197,94,0.45)" : "";
    }
    const assignedBadgeEl = document.getElementById("section-assigned-badge");
    if (assignedBadgeEl) {
      assignedBadgeEl.style.display = assigned ? "inline-flex" : "none";
    }
    if (sectionPreviewStats) {
      const total = state.manuscriptDoc.chapters.length;
      sectionPreviewStats.textContent = `Sección ${idx + 1} de ${total} • ~${sec.word_count || 0} palabras`;
    }
    if (sectionPreviewText) {
      sectionPreviewText.textContent = sec.text || "(Esta sección no contiene texto)";
    }
  }

  // Event Listeners: Árbol de Capítulos
  if (treeSearchInput) {
    treeSearchInput.addEventListener("input", e => {
      renderChaptersTree(e.target.value);
    });
  }

  if (btnTreeNewChapter) {
    btnTreeNewChapter.addEventListener("click", () => {
      createNewChapterDraft();
      showToast("Nuevo borrador de capítulo listo", "info");
    });
  }

  if (btnTreeRefresh) {
    btnTreeRefresh.addEventListener("click", async () => {
      if (state.currentProject) {
        await loadProjectChapters(state.currentProject.id, state.currentChapterId);
        showToast("Árbol de capítulos actualizado", "info");
      }
    });
  }

  if (btnTreeImportDoc) {
    btnTreeImportDoc.addEventListener("click", () => {
      if (!state.currentProject) {
        showToast("Selecciona un proyecto primero", "error");
        return;
      }
      if (!state.manuscriptDoc) {
        showToast("Este proyecto no tiene un manuscrito guardado en documentos/", "error");
        return;
      }
      modalBatchImport.classList.add("open");
    });
  }

  const btnAnalyzeBookChapters = document.getElementById("btn-analyze-book-chapters");
  if (btnAnalyzeBookChapters) {
    btnAnalyzeBookChapters.addEventListener("click", async () => {
      if (!state.currentProject) {
        showToast("Selecciona un proyecto primero", "error");
        return;
      }
      btnAnalyzeBookChapters.disabled = true;
      const prevText = btnAnalyzeBookChapters.textContent;
      btnAnalyzeBookChapters.textContent = "⏳ Analizando libro...";
      try {
        await loadManuscriptStructure(state.currentProject.id);
        const total = state.manuscriptDoc?.chapters?.length || 0;
        showToast(`Análisis completado: ${total} capítulos/secciones detectados`, "success");
      } catch (err) {
        showToast("Error analizando capítulos del libro", "error");
      } finally {
        btnAnalyzeBookChapters.disabled = false;
        btnAnalyzeBookChapters.textContent = prevText;
      }
    });
  }

  // Event Listeners: Pestañas de Fuente del Manuscrito
  if (tabSrcPage && tabSrcChapter && tabSrcManual) {
    tabSrcPage.addEventListener("click", () => {
      tabSrcPage.classList.add("active");
      tabSrcChapter.classList.remove("active");
      tabSrcManual.classList.remove("active");
      if (panelSourcePage) panelSourcePage.style.display = "block";
      if (panelSourceChapter) panelSourceChapter.style.display = "none";
    });
    tabSrcChapter.addEventListener("click", () => {
      tabSrcChapter.classList.add("active");
      tabSrcPage.classList.remove("active");
      tabSrcManual.classList.remove("active");
      if (panelSourceChapter) panelSourceChapter.style.display = "block";
      if (panelSourcePage) panelSourcePage.style.display = "none";
    });
    tabSrcManual.addEventListener("click", () => {
      tabSrcManual.classList.add("active");
      tabSrcPage.classList.remove("active");
      tabSrcChapter.classList.remove("active");
      if (panelSourcePage) panelSourcePage.style.display = "none";
      if (panelSourceChapter) panelSourceChapter.style.display = "none";
      if (rawChapterText) rawChapterText.focus();
    });
  }

  // Event Listeners: Navegación de Páginas
  if (selectManuscriptPage) {
    selectManuscriptPage.addEventListener("change", e => {
      updatePagePreview(e.target.value);
    });
  }

  if (btnPrevPage) {
    btnPrevPage.addEventListener("click", () => {
      if (state.selectedPageNum > 1) {
        state.selectedPageNum--;
        if (selectManuscriptPage) selectManuscriptPage.value = state.selectedPageNum;
        updatePagePreview(state.selectedPageNum);
      }
    });
  }

  if (btnNextPage) {
    btnNextPage.addEventListener("click", () => {
      const total = state.manuscriptDoc ? (state.manuscriptDoc.total_pages || state.manuscriptDoc.pages.length) : 1;
      if (state.selectedPageNum < total) {
        state.selectedPageNum++;
        if (selectManuscriptPage) selectManuscriptPage.value = state.selectedPageNum;
        updatePagePreview(state.selectedPageNum);
      }
    });
  }

  if (btnAssignPageToChapter) {
    btnAssignPageToChapter.addEventListener("click", () => {
      if (!state.manuscriptDoc || !state.manuscriptDoc.pages) return;
      const page = state.manuscriptDoc.pages.find(p => p.page_number === state.selectedPageNum);
      if (!page) return;

      chapterTitleInput.value = page.title;
      rawChapterText.value = page.text;
      state.currentChapterOriginType = "page";
      state.currentChapterOriginRef = page.page_number;
      updateChapterWordsCounter();

      if (currentChapterHeading) currentChapterHeading.textContent = page.title;
      if (currentChapterOriginPill) {
        currentChapterOriginPill.textContent = `📄 Pág. ${page.page_number}`;
        currentChapterOriginPill.style.display = "inline-flex";
      }
      showToast(`Texto de Página ${page.page_number} asignado al capítulo`, "info");
    });
  }

  if (btnCreateChapterFromPage) {
    btnCreateChapterFromPage.addEventListener("click", async () => {
      if (!state.manuscriptDoc || !state.manuscriptDoc.pages) return;
      const page = state.manuscriptDoc.pages.find(p => p.page_number === state.selectedPageNum);
      if (!page) return;

      createNewChapterDraft({
        titulo: page.title,
        texto: page.text,
        origen_tipo: "page",
        origen_ref: page.page_number,
        orden: page.page_number
      });
      await saveCurrentChapter(true);
      showToast(`Capítulo creado para Página ${page.page_number}`, "success");
    });
  }

  // Event Listeners: Navegación de Secciones / Capítulos
  if (selectManuscriptSection) {
    selectManuscriptSection.addEventListener("change", e => {
      updateSectionPreview(e.target.value);
    });
  }

  if (btnAssignSectionToChapter) {
    btnAssignSectionToChapter.addEventListener("click", () => {
      if (!state.manuscriptDoc || !state.manuscriptDoc.chapters) return;
      const sec = state.manuscriptDoc.chapters[state.selectedSectionIdx];
      if (!sec) return;

      const currentTitle = (chapterTitleInput.value || "").trim();
      const isGenericTitle = !currentTitle || /^nuevo cap[íi]tulo$/i.test(currentTitle);
      if (isGenericTitle) {
        chapterTitleInput.value = shortSectionTitle(sec.title);
      }
      rawChapterText.value = sec.text;
      state.currentChapterOriginType = "section";
      state.currentChapterOriginRef = sec.title;
      updateChapterWordsCounter();

      if (currentChapterHeading) {
        currentChapterHeading.textContent = (chapterTitleInput.value || "").trim() || "Capítulo";
      }
      populateManuscriptSections();
      updateSectionPreview(state.selectedSectionIdx);
      showToast(`Sección "${shortSectionTitle(sec.title)}" asignada al capítulo`, "info");
    });
  }

  if (btnCreateChapterFromSection) {
    btnCreateChapterFromSection.addEventListener("click", async () => {
      if (!state.manuscriptDoc || !state.manuscriptDoc.chapters) return;
      const sec = state.manuscriptDoc.chapters[state.selectedSectionIdx];
      if (!sec) return;

      createNewChapterDraft({
        titulo: sec.title,
        texto: sec.text,
        origen_tipo: "section",
        origen_ref: sec.title,
        orden: state.selectedSectionIdx + 1
      });
      await saveCurrentChapter(true);
      showToast(`Capítulo creado para sección "${sec.title}"`, "success");
    });
  }

  // Event Listeners: Guardado Rápido y Eliminación
  if (rawChapterText) {
    rawChapterText.addEventListener("input", updateChapterWordsCounter);
  }

  if (chapterTitleInput) {
    chapterTitleInput.addEventListener("input", () => {
      const val = chapterTitleInput.value.trim() || "Capítulo";
      if (currentChapterHeading) {
        currentChapterHeading.textContent = val;
      }
      if (state.currentChapterId) {
        const treeTitleEl = document.querySelector(`.chapter-tree-item[data-id="${state.currentChapterId}"] .chapter-tree-title`);
        if (treeTitleEl) {
          treeTitleEl.textContent = val;
        }
      }
    });
  }

  if (btnQuickSaveChapter) {
    btnQuickSaveChapter.addEventListener("click", () => saveCurrentChapter(false));
  }

  if (btnDeleteActiveChapter) {
    btnDeleteActiveChapter.addEventListener("click", () => {
      if (state.currentChapterId) {
        const cap = state.chapters.find(c => c.id === state.currentChapterId);
        const title = cap ? cap.titulo : chapterTitleInput.value;
        deleteChapter(state.currentChapterId, title);
      } else {
        showToast("El borrador actual no está guardado aún", "info");
      }
    });
  }

  // Event Listeners: Modal de Importación en Lote
  if (optImportPages && optImportChapters) {
    optImportPages.addEventListener("click", () => {
      optImportPages.classList.add("active");
      optImportChapters.classList.remove("active");
      selectedBatchImportMode = "pages";
    });
    optImportChapters.addEventListener("click", () => {
      optImportChapters.classList.add("active");
      optImportPages.classList.remove("active");
      selectedBatchImportMode = "chapters";
    });
  }

  if (btnConfirmBatchImport) {
    btnConfirmBatchImport.addEventListener("click", async () => {
      if (!state.currentProject) return;
      btnConfirmBatchImport.disabled = true;
      btnConfirmBatchImport.textContent = "⏳ Importando...";

      try {
        const res = await fetch(`/api/projects/${state.currentProject.id}/chapters/batch-import`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source: selectedBatchImportMode,
            max_items: 60
          })
        });
        const data = await res.json();
        if (data.success) {
          showToast(`¡Se han importado ${data.count} capítulos al árbol!`, "success");
          modalBatchImport.classList.remove("open");
          await loadProjectChapters(state.currentProject.id);
        } else {
          throw new Error(data.detail || "Error en importación");
        }
      } catch (e) {
        console.error("Error importando capítulos en lote:", e);
        showToast("Error en importación: " + e.message, "error");
      } finally {
        btnConfirmBatchImport.disabled = false;
        btnConfirmBatchImport.textContent = "⚡ Iniciar Importación al Árbol";
      }
    });
  }

  if (btnLoadChaptersToSpecific) {
    btnLoadChaptersToSpecific.addEventListener("click", () => {
      switchLayer("specific");
    });
  }

  // ========================================================
  // 7. HISTORIAL Y BIBLIOTECA DE VÍDEOS POR PROYECTO
  // ========================================================
  let currentHistoryFilterMode = "project";

  const historyFilterProjectBtn = document.getElementById("history-filter-project");
  const historyFilterAllBtn = document.getElementById("history-filter-all");
  const historyFolderCode = document.getElementById("history-folder-code");

  async function loadVideosHistory(filterMode = "project") {
    currentHistoryFilterMode = filterMode;
    const projId = (state.currentProject && filterMode === "project") ? state.currentProject.id : "";

    if (historyFilterProjectBtn && historyFilterAllBtn) {
      if (filterMode === "project") {
        historyFilterProjectBtn.className = "btn btn-xs btn-primary";
        historyFilterAllBtn.className = "btn btn-xs btn-secondary";
      } else {
        historyFilterProjectBtn.className = "btn btn-xs btn-secondary";
        historyFilterAllBtn.className = "btn btn-xs btn-primary";
      }
    }

    if (historyFolderCode) {
      if (state.currentProject && filterMode === "project") {
        historyFolderCode.textContent = `proyectos/${state.currentProject.id}/videos/`;
      } else {
        historyFolderCode.textContent = "proyectos/*/videos/";
      }
    }

    historyGrid.innerHTML = "<p class='text-muted'>Cargando biblioteca de vídeos...</p>";
    try {
      const url = projId ? `/api/videos/history?project_id=${encodeURIComponent(projId)}` : "/api/videos/history";
      const res = await fetch(url);
      const list = await res.json();
      if (!list || list.length === 0) {
        const folderName = (state.currentProject && filterMode === "project") ? `proyectos/${state.currentProject.id}/videos/` : "proyectos/";
        historyGrid.innerHTML = `
          <div class="p-4 text-center text-muted" style="grid-column: 1 / -1; width:100%;">
            <p style="font-size:1.05rem; margin-bottom:0.4rem;">📂 No hay vídeos en <code>${folderName}</code> todavía.</p>
            <small>Genera un capítulo y pulsa en <b>"Renderizar Vídeo Final"</b> para compilar el archivo vertical MP4.</small>
          </div>
        `;
        return;
      }

      historyGrid.innerHTML = "";
      list.forEach(v => {
        const item = document.createElement("div");
        item.className = "history-item";
        item.style.position = "relative";
        item.innerHTML = `
          <div style="aspect-ratio: 9/16; background:#000; border-radius:8px; overflow:hidden; position:relative;">
            <video src="${v.video_url}" style="width:100%; height:100%; object-fit:cover;" controls playsinline preload="metadata"></video>
            <button class="btn-play-sound" title="Reproducir con sonido a volumen completo" style="position:absolute; top:8px; right:8px; background:rgba(0,0,0,0.75); border:1px solid rgba(255,255,255,0.4); color:#fff; border-radius:16px; padding:3px 8px; font-size:0.75rem; cursor:pointer; z-index:2; backdrop-filter:blur(4px);">
              🔊 Sonido ON
            </button>
          </div>
          <div class="mt-2" style="font-size:0.8rem;">
            <strong style="color:var(--text-highlight); display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${v.chapter_title || v.filename}">
              ${v.chapter_title || v.filename}
            </strong>
            <div class="text-muted" style="font-size:0.72rem; word-break:break-all; margin-top:2px;">
              📁 <code>${v.folder_path || v.filename}</code>
            </div>
            <div class="text-muted mt-1" style="font-size:0.75rem;">${v.size_mb} MB • ${v.created_at}</div>
            <div class="d-flex gap-1 mt-2">
              <a href="${v.video_url}" download class="btn btn-primary btn-xs" style="flex:1; text-align:center;">⬇️ Descargar MP4</a>
              ${v.project_id ? `<button class="btn btn-secondary btn-xs btn-del-video" data-project="${v.project_id}" data-filename="${v.filename}" title="Eliminar de la carpeta de vídeos">🗑️</button>` : ''}
            </div>
          </div>
        `;

        const vid = item.querySelector("video");
        const btnSound = item.querySelector(".btn-play-sound");
        if (vid && btnSound) {
          btnSound.addEventListener("click", () => {
            vid.muted = false;
            vid.volume = 1.0;
            vid.play();
          });
          vid.addEventListener("play", () => {
            vid.muted = false;
            vid.volume = 1.0;
          });
        }

        const btnDel = item.querySelector(".btn-del-video");
        if (btnDel) {
          btnDel.addEventListener("click", async () => {
            const pid = btnDel.dataset.project;
            const fname = btnDel.dataset.filename;
            if (confirm(`¿Eliminar definitivamente el vídeo '${fname}'?`)) {
              try {
                const dRes = await fetch(`/api/projects/${pid}/videos/${fname}`, { method: "DELETE" });
                if (dRes.ok) {
                  showToast("Vídeo eliminado de la carpeta", "info");
                  loadVideosHistory(currentHistoryFilterMode);
                } else {
                  showToast("Error eliminando vídeo", "error");
                }
              } catch (e) {
                showToast("Error de conexión al eliminar", "error");
              }
            }
          });
        }

        historyGrid.appendChild(item);
      });
    } catch (e) {
      console.error("Error cargando historial de vídeos:", e);
      historyGrid.innerHTML = "<p class='text-muted'>Error cargando historial de vídeos.</p>";
    }
  }

  btnOpenHistory.addEventListener("click", () => {
    modalHistory.classList.add("open");
    loadVideosHistory("project");
  });

  if (historyFilterProjectBtn) {
    historyFilterProjectBtn.addEventListener("click", () => loadVideosHistory("project"));
  }
  if (historyFilterAllBtn) {
    historyFilterAllBtn.addEventListener("click", () => loadVideosHistory("all"));
  }

  // Refrescar píldoras de estado en el header
  async function refreshApiStatus() {
    try {
      const sRes = await fetch("/api/status");
      const status = await sRes.json();
      const elOpenai = document.getElementById("status-openai");
      const elEleven = document.getElementById("status-eleven");
      const elFfmpeg = document.getElementById("status-ffmpeg");

      if (elOpenai) {
        if (status.openai_configured) {
          elOpenai.classList.add("active");
          elOpenai.innerHTML = '<span class="dot"></span> OpenAI Activo';
          elOpenai.title = "OpenAI conectado (GPT-4o-mini listo para análisis y desglose)";
        } else {
          elOpenai.classList.remove("active");
          elOpenai.innerHTML = '<span class="dot"></span> OpenAI Inactivo';
          elOpenai.title = "Falta clave OpenAI en .env (se usarán plantillas heurísticas)";
        }
      }

      if (elEleven) {
        if (status.elevenlabs_configured) {
          elEleven.classList.add("active");
          elEleven.innerHTML = '<span class="dot"></span> ElevenLabs Activo';
          elEleven.title = "ElevenLabs conectado para voces neurales de alta definición";
        } else {
          elEleven.classList.remove("active");
          elEleven.innerHTML = '<span class="dot"></span> Voz Gratuita (EdgeTTS)';
          elEleven.title = "Sin clave ElevenLabs: usando motor gratuito EdgeTTS en español";
        }
      }

      if (elFfmpeg) {
        elFfmpeg.classList.add("active");
        elFfmpeg.innerHTML = '<span class="dot"></span> FFmpeg Activo';
        elFfmpeg.title = "Motor local FFmpeg instalado y listo para ensamblar vídeo vertical 9:16";
      }
    } catch (e) {
      console.warn("Error leyendo estado del sistema:", e);
    }
  }

  // Cargar estado de credenciales en el modal de Ajustes
  async function loadSettingsModal() {
    try {
      const res = await fetch("/api/settings");
      const data = await res.json();

      function renderSettingItem(keyName, badgeId, maskedId, inputEl) {
        const item = data[keyName];
        const badge = document.getElementById(badgeId);
        const masked = document.getElementById(maskedId);
        if (!item || !badge) return;

        if (item.configured) {
          badge.className = "badge badge-success";
          badge.textContent = "✅ Activa en .env";
          if (masked) masked.innerHTML = `Clave actual: <code>${item.masked}</code>`;
        } else {
          badge.className = "badge badge-subtle";
          badge.textContent = keyName === "OPENAI_API_KEY" ? "⚠️ No configurada" : "ℹ️ Opcional";
          if (masked) masked.innerHTML = `<em>${item.fallback}</em>`;
        }
        if (inputEl) inputEl.value = "";
      }

      renderSettingItem("OPENAI_API_KEY", "badge-status-openai", "masked-openai", settingOpenai);
      renderSettingItem("ELEVENLABS_API_KEY", "badge-status-eleven", "masked-eleven", settingEleven);
      renderSettingItem("POLLINATIONS_API_KEY", "badge-status-pollinations", "masked-pollinations", settingPollinations);
      renderSettingItem("FAL_KEY", "badge-status-fal", "masked-fal", settingFal);
      renderSettingItem("GEMINI_API_KEY", "badge-status-gemini", "masked-gemini", settingGemini);

      loadProvidersBilling();
    } catch (err) {
      console.error("Error cargando ajustes:", err);
    }
  }

  async function loadProvidersBilling() {
    const map = [
      ["OPENAI_API_KEY", "billing-openai"],
      ["ELEVENLABS_API_KEY", "billing-eleven"],
      ["POLLINATIONS_API_KEY", "billing-pollinations"],
      ["FAL_KEY", "billing-fal"],
      ["GEMINI_API_KEY", "billing-gemini"],
    ];
    map.forEach(([, elId]) => {
      const span = document.querySelector(`#${elId} > span:first-child`);
      if (span) {
        span.className = "text-muted";
        span.textContent = "⏳ Comprobando saldo / estado...";
      }
    });

    try {
      const res = await fetch("/api/settings/billing");
      const billing = await res.json();

      const statusStyle = {
        ok: { icon: "✅", color: "#4ade80" },
        free: { icon: "🆓", color: "#60a5fa" },
        warning: { icon: "⚠️", color: "#fbbf24" },
        error: { icon: "❌", color: "#f87171" },
        unconfigured: { icon: "ℹ️", color: "#94a3b8" },
      };

      map.forEach(([keyName, elId]) => {
        const info = billing[keyName];
        const span = document.querySelector(`#${elId} > span:first-child`);
        if (!info || !span) return;
        const st = statusStyle[info.status] || statusStyle.unconfigured;
        span.style.color = st.color;
        span.textContent = `${st.icon} ${info.label}`;
      });

      const ffmpegSpan = document.getElementById("billing-ffmpeg");
      if (ffmpegSpan && billing.FFMPEG) {
        const st = statusStyle[billing.FFMPEG.status] || statusStyle.ok;
        ffmpegSpan.textContent = `${st.icon} ${billing.FFMPEG.label}`;
      }
      const edgeSpan = document.getElementById("billing-edgetts");
      if (edgeSpan && billing.EDGE_TTS) {
        edgeSpan.textContent = `🆓 ${billing.EDGE_TTS.label}`;
      }
    } catch (err) {
      console.error("Error consultando billing:", err);
    }
  }

  const btnRefreshBilling = document.getElementById("btn-refresh-billing");
  if (btnRefreshBilling) {
    btnRefreshBilling.addEventListener("click", () => {
      loadProvidersBilling();
    });
  }

  btnOpenSettings.addEventListener("click", () => {
    modalSettings.classList.add("open");
    loadSettingsModal();
  });

  btnSaveSettings.addEventListener("click", async () => {
    const syncCentralEl = document.getElementById("setting-sync-central");
    const payload = {
      SYNC_CENTRAL: syncCentralEl ? syncCentralEl.checked : true
    };
    if (settingOpenai && settingOpenai.value) payload.OPENAI_API_KEY = settingOpenai.value.trim();
    if (settingEleven && settingEleven.value) payload.ELEVENLABS_API_KEY = settingEleven.value.trim();
    if (settingPollinations && settingPollinations.value) payload.POLLINATIONS_API_KEY = settingPollinations.value.trim();
    if (settingFal && settingFal.value) payload.FAL_KEY = settingFal.value.trim();
    if (settingGemini && settingGemini.value) payload.GEMINI_API_KEY = settingGemini.value.trim();

    try {
      const res = await fetch("/api/settings/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        modalSettings.classList.remove("open");
        showToast("Claves guardadas localmente en .env", "success");
        await refreshApiStatus();
      }
    } catch (e) {
      showToast("Error guardando ajustes", "error");
    }
  });

  // ========================================================
  // ESTUDIO DE SUBTÍTULOS Y VISTA PREVIA EN VIVO
  // ========================================================
  const SUB_STORAGE_KEY = "videostudio_subtitle_config";
  const DEFAULT_SUB_CFG = {
    mode: "scrolling_sentence",
    bg_mode: "transparent",
    font_family: "sans",
    font_size: 52,
    text_color: "#FFFFFF",
    highlight_color: "#FBBF24",
    position: "bottom",
    fade: "fade",
  };

  const subEnabledEl = document.getElementById("sub-enabled");
  const subModeEl = document.getElementById("sub-mode");
  const subFadeEl = document.getElementById("sub-fade");
  const subBgModeEl = document.getElementById("sub-bg-mode");
  const subFontFamilyEl = document.getElementById("sub-font-family");
  const subFontSizeEl = document.getElementById("sub-font-size");
  const subPositionEl = document.getElementById("sub-position");
  const subTextColorEl = document.getElementById("sub-text-color");
  const subHighlightColorEl = document.getElementById("sub-highlight-color");
  const subPreviewFrame = document.getElementById("sub-preview-frame");
  const subPreviewBox = document.getElementById("sub-preview-box");
  const btnSubReset = document.getElementById("btn-subtitles-reset");
  const btnSubGotoRender = document.getElementById("btn-subtitles-goto-render");
  const btnSubPreviewAnim = document.getElementById("btn-sub-preview-animate");
  let subAnimTimer = null;

  function getSubtitleConfig() {
    return {
      mode: subModeEl ? subModeEl.value : DEFAULT_SUB_CFG.mode,
      bg_mode: subBgModeEl ? subBgModeEl.value : DEFAULT_SUB_CFG.bg_mode,
      font_family: subFontFamilyEl ? subFontFamilyEl.value : DEFAULT_SUB_CFG.font_family,
      font_size: subFontSizeEl ? parseInt(subFontSizeEl.value, 10) : DEFAULT_SUB_CFG.font_size,
      text_color: subTextColorEl ? subTextColorEl.value : DEFAULT_SUB_CFG.text_color,
      highlight_color: subHighlightColorEl ? subHighlightColorEl.value : DEFAULT_SUB_CFG.highlight_color,
      position: subPositionEl ? subPositionEl.value : DEFAULT_SUB_CFG.position,
      fade: subFadeEl ? subFadeEl.value : DEFAULT_SUB_CFG.fade,
    };
  }

  function applySubtitleConfig(cfg) {
    const c = { ...DEFAULT_SUB_CFG, ...(cfg || {}) };
    if (subModeEl) subModeEl.value = c.mode;
    if (subFadeEl) subFadeEl.value = c.fade;
    if (subBgModeEl) subBgModeEl.value = c.bg_mode;
    if (subFontFamilyEl) subFontFamilyEl.value = c.font_family;
    if (subFontSizeEl) subFontSizeEl.value = String(c.font_size);
    if (subPositionEl) subPositionEl.value = c.position;
    if (subTextColorEl) subTextColorEl.value = c.text_color;
    if (subHighlightColorEl) subHighlightColorEl.value = c.highlight_color;
    updateSubtitlePreview();
  }

  function saveSubtitleConfigLocal() {
    try {
      localStorage.setItem(SUB_STORAGE_KEY, JSON.stringify(getSubtitleConfig()));
    } catch (_) {}
  }

  function updateSubtitlePreview(wordLimit = null) {
    if (!subPreviewBox || !subPreviewFrame) return;
    const cfg = getSubtitleConfig();
    const enabled = subEnabledEl ? subEnabledEl.checked : true;
    subPreviewBox.style.opacity = enabled ? "1" : "0.25";

    const fontCss = cfg.font_family === "serif" ? "Georgia, serif" : cfg.font_family === "mono" ? "Consolas, monospace" : "Arial, 'Segoe UI', sans-serif";
    subPreviewBox.style.fontFamily = fontCss;
    subPreviewBox.style.fontSize = `${Math.round(cfg.font_size * 0.26)}px`;

    let textCol = cfg.text_color;
    if (cfg.bg_mode === "white" && textCol.toUpperCase() === "#FFFFFF") {
      textCol = "#111827";
    }
    subPreviewBox.style.color = textCol;

    if (cfg.bg_mode === "white") {
      subPreviewBox.style.background = "rgba(255, 255, 255, 0.94)";
      subPreviewBox.style.padding = "8px 14px";
      subPreviewBox.style.borderRadius = "10px";
      subPreviewBox.style.textShadow = "none";
    } else if (cfg.bg_mode === "dark") {
      subPreviewBox.style.background = "rgba(12, 16, 24, 0.82)";
      subPreviewBox.style.padding = "8px 14px";
      subPreviewBox.style.borderRadius = "10px";
      subPreviewBox.style.textShadow = "0 1px 3px rgba(0,0,0,0.8)";
    } else {
      subPreviewBox.style.background = "transparent";
      subPreviewBox.style.padding = "4px 6px";
      subPreviewBox.style.borderRadius = "0";
      subPreviewBox.style.textShadow = "0 2px 4px rgba(0,0,0,0.95), 0 0 2px #000";
    }

    if (cfg.position === "top") {
      subPreviewFrame.style.alignItems = "flex-start";
      subPreviewBox.style.marginTop = "30px";
      subPreviewBox.style.marginBottom = "0";
    } else if (cfg.position === "center") {
      subPreviewFrame.style.alignItems = "center";
      subPreviewBox.style.marginTop = "0";
      subPreviewBox.style.marginBottom = "0";
    } else {
      subPreviewFrame.style.alignItems = "flex-end";
      subPreviewBox.style.marginTop = "0";
      subPreviewBox.style.marginBottom = "48px";
    }

    if (cfg.mode === "paragraph_preview") {
      const p1 = ["Platero", "es", "pequeño,", "peludo,", "suave;", "tan", "blando", "por", "fuera", "que", "se", "diría", "todo", "de", "algodón,", "que", "no", "lleva", "huesos."];
      const p2 = "Sólo los espejos de azabache de sus ojos son duros cual dos escarabajos de cristal negro.";
      const aIdx = wordLimit !== null ? Math.min(wordLimit, p1.length - 1) : 4;
      const p1Html = p1.map((w, idx) => {
        if (idx === aIdx) return `<span style="color:${cfg.highlight_color}">${w}</span>`;
        if (idx < aIdx) return `<span style="opacity:0.72">${w}</span>`;
        return w;
      }).join(" ");
      subPreviewBox.innerHTML = `${p1Html}<div style="margin-top:8px;font-size:0.84em;opacity:0.42;filter:blur(0.6px);">${p2}</div>`;
      return;
    }

    const sampleWords = ["Platero", "es", "pequeño,", "peludo,", "suave;", "tan", "blando", "por", "fuera", "que", "se", "diría", "de", "algodón."];
    const activeIdx = wordLimit !== null ? Math.min(wordLimit, sampleWords.length - 1) : 4;
    const shown = cfg.mode === "word_by_word" && wordLimit !== null
      ? sampleWords.slice(0, activeIdx + 1)
      : sampleWords;

    subPreviewBox.innerHTML = shown.map((w, idx) => {
      if (cfg.mode !== "block" && idx === activeIdx) {
        return `<span style="color:${cfg.highlight_color}">${w}</span>`;
      }
      if (cfg.mode === "scrolling_sentence" && idx < activeIdx) {
        return `<span style="opacity:0.65">${w}</span>`;
      }
      return w;
    }).join(" ");
  }

  function animateSubtitlePreview() {
    if (subAnimTimer) clearInterval(subAnimTimer);
    let step = 0;
    const total = 14;
    updateSubtitlePreview(step);
    subAnimTimer = setInterval(() => {
      step++;
      if (step >= total) {
        clearInterval(subAnimTimer);
        subAnimTimer = null;
        return;
      }
      updateSubtitlePreview(step);
    }, 320);
  }

  if (subEnabledEl) {
    subEnabledEl.addEventListener("change", () => {
      updateSubtitlePreview();
    });
  }

  [subModeEl, subFadeEl, subBgModeEl, subFontFamilyEl, subFontSizeEl, subPositionEl, subTextColorEl, subHighlightColorEl].forEach((el) => {
    if (el) {
      el.addEventListener("change", () => {
        saveSubtitleConfigLocal();
        updateSubtitlePreview();
      });
    }
  });

  if (btnSubReset) {
    btnSubReset.addEventListener("click", () => {
      applySubtitleConfig(DEFAULT_SUB_CFG);
      saveSubtitleConfigLocal();
      showToast("Subtítulos restaurados a valores por defecto", "info");
    });
  }
  if (btnSubGotoRender) {
    btnSubGotoRender.addEventListener("click", () => switchLayer("specific"));
  }
  if (btnSubPreviewAnim) {
    btnSubPreviewAnim.addEventListener("click", animateSubtitlePreview);
  }

  try {
    const savedSubCfg = localStorage.getItem(SUB_STORAGE_KEY);
    if (savedSubCfg) applySubtitleConfig(JSON.parse(savedSubCfg));
    else updateSubtitlePreview();
  } catch (_) {
    updateSubtitlePreview();
  }

  // ========================================================
  // OPCIONES DE MONTAJE Y RENDERIZADO FINAL
  // ========================================================
  const RENDER_STORAGE_KEY = "videostudio_render_config";
  const renderAspectEl = document.getElementById("render-aspect-ratio");
  const renderTransitionEl = document.getElementById("render-transition");
  const renderKbStyleEl = document.getElementById("render-kenburns-style");
  const renderPauseEl = document.getElementById("render-scene-pause");
  const renderVolumeEl = document.getElementById("render-voice-volume");
  const btnOpenSubtitlesTab = document.getElementById("btn-open-subtitles-tab");

  function getRenderConfig() {
    return {
      aspect_ratio: renderAspectEl ? renderAspectEl.value : "9:16",
      transition: renderTransitionEl ? renderTransitionEl.value : "fade",
      ken_burns_style: renderKbStyleEl ? renderKbStyleEl.value : "suave",
      scene_pause_sec: renderPauseEl ? parseFloat(renderPauseEl.value) : 0.35,
      voice_volume: renderVolumeEl ? parseFloat(renderVolumeEl.value) : 1.5,
    };
  }

  function saveRenderConfigLocal() {
    try {
      localStorage.setItem(RENDER_STORAGE_KEY, JSON.stringify(getRenderConfig()));
    } catch (_) {}
  }

  [renderAspectEl, renderTransitionEl, renderKbStyleEl, renderPauseEl, renderVolumeEl].forEach((el) => {
    if (el) {
      el.addEventListener("change", () => {
        if (el === renderKbStyleEl && chkKenBurns) {
          chkKenBurns.checked = el.value !== "fijo";
        }
        saveRenderConfigLocal();
      });
    }
  });

  if (chkKenBurns && renderKbStyleEl) {
    chkKenBurns.addEventListener("change", () => {
      if (!chkKenBurns.checked) renderKbStyleEl.value = "fijo";
      else if (renderKbStyleEl.value === "fijo") renderKbStyleEl.value = "suave";
      saveRenderConfigLocal();
    });
  }

  if (btnOpenSubtitlesTab) {
    btnOpenSubtitlesTab.addEventListener("click", () => switchLayer("subtitles"));
  }

  try {
    const savedRen = localStorage.getItem(RENDER_STORAGE_KEY);
    if (savedRen) {
      const rc = JSON.parse(savedRen);
      if (renderAspectEl && rc.aspect_ratio) renderAspectEl.value = rc.aspect_ratio;
      if (renderTransitionEl && rc.transition) renderTransitionEl.value = rc.transition;
      if (renderKbStyleEl && rc.ken_burns_style) renderKbStyleEl.value = rc.ken_burns_style;
      if (renderPauseEl && rc.scene_pause_sec !== undefined) renderPauseEl.value = String(rc.scene_pause_sec);
      if (renderVolumeEl && rc.voice_volume !== undefined) renderVolumeEl.value = String(rc.voice_volume);
    }
  } catch (_) {}

  // Arrancar la app
  init();
});
