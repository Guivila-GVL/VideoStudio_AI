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

    if (!card || !badge) return;

    if (_statusTimeout) {
      clearTimeout(_statusTimeout);
      _statusTimeout = null;
    }

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    // Resetear clases
    card.className = "system-status-card";
    badge.className = "status-indicator-badge";

    if (stateType === "busy") {
      card.classList.add("status-busy");
      badge.classList.add("busy");
      if (tag) tag.textContent = "PROCESANDO";
      if (spinner) spinner.style.display = "flex";
      if (primaryText) primaryText.textContent = title || "Procesando...";
      if (secondaryText) secondaryText.textContent = message || "La Inteligencia Artificial está generando los contenidos...";
      if (timeText) timeText.textContent = timeStr;
    } else if (stateType === "healing") {
      card.classList.add("status-healing");
      badge.classList.add("healing");
      if (tag) tag.textContent = "CORRIGIENDO";
      if (spinner) spinner.style.display = "flex";
      if (primaryText) primaryText.textContent = title || "Corrigiendo incoherencias...";
      if (secondaryText) secondaryText.textContent = message || "Regenerando elementos con IA para garantizar el estándar...";
      if (timeText) timeText.textContent = timeStr;
    } else if (stateType === "success") {
      card.classList.add("status-success");
      if (tag) tag.textContent = "COMPLETADO";
      if (spinner) spinner.style.display = "none";
      if (primaryText) primaryText.textContent = title || "Operación finalizada";
      if (secondaryText) secondaryText.textContent = message || "Listo.";
      if (timeText) timeText.textContent = timeStr;

      _statusTimeout = setTimeout(() => {
        setSystemStatus("idle");
      }, 7000);
    } else if (stateType === "error") {
      card.classList.add("status-error");
      badge.classList.add("error");
      if (tag) tag.textContent = "ERROR";
      if (spinner) spinner.style.display = "none";
      if (primaryText) primaryText.textContent = title || "Error en la operación";
      if (secondaryText) secondaryText.textContent = message || "Ha ocurrido un error al procesar la solicitud.";
      if (timeText) timeText.textContent = timeStr;
    } else {
      // idle
      if (tag) tag.textContent = "EN ESPERA";
      if (spinner) spinner.style.display = "none";
      if (primaryText) primaryText.textContent = title || "Listo para recibir órdenes";
      if (secondaryText) secondaryText.textContent = message || "El sistema está inactivo esperando que selecciones una acción (analizar libro, generar personajes, auditar coherencia o montar vídeo).";
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
        { label: "🌟 Narradores Juveniles & Adolescentes (12-16 años)", filter: v => v.category === "juvenil" || v.age_group === "joven" },
        { label: "📖 Cuentacuentos & Narradores Clásicos", filter: v => v.category === "cuentacuentos" },
        { label: "🎭 Voces Dramáticas & Solemnes", filter: v => v.category === "dramatico" },
        { label: "🌸 Voces Femeninas & Cuentos", filter: v => v.category === "femenino" || v.gender === "femenino" },
        { label: "⚡ Voces Neutras & Fallback Gratuito", filter: v => v.category === "neutro" || v.category === "gratuito" || v.category === "elevenlabs_custom" }
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
        const isHighlight = t.toLowerCase().includes("joven") || t.toLowerCase().includes("lírico") || t.toLowerCase().includes("12-16");
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
        tono: "Lírico, contemplativo, tierno, pausado y reflexivo",
        justificacion: "En Platero y yo el narrador es una voz lírica joven que dialoga en complicidad sensible con su borriquillo.",
        voz_recomendada: "openai_fable",
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

    const chosenVoice = voiceId || narrator.voz_recomendada || "openai_fable";
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
      univStyleDetails.value = project.estilo_detalles || "";
      updateStyleImplications(univStyle.value, false);
      if (project.voz_defecto) univVoice.value = project.voz_defecto;
      if (univRecurrentChars) univRecurrentChars.value = project.personajes_recurrentes_texto || "";

      // Cargar y sincronizar perfil del narrador (Punto 5)
      populateNarratorFields(project.perfil_narrador, project.voz_defecto);

      phoneProjectTag.textContent = `@${project.titulo.replace(/\s+/g, '')} • Capítulos`;

      // Renderizar tarjetas de personajes y escenarios guardados
      renderCharacterCards(project.personajes || []);
      renderEnvironmentCards(project.escenarios || []);

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
          savedBookMeta.textContent = `Manuscrito guardado (${project.documento_activo.tamano_formateado || project.documento_activo.tamano || '1.1 MB'}). ${docsCount} archivo(s) en disco.`;
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
  btnCreateProjectModal.addEventListener("click", () => {
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
    btnAiAnalyzeBook.innerHTML = '<span class="btn-icon-symbol">⏳</span> Analizando Universo y Personajes con IA...';
    setSystemStatus("busy", "Analizando libro con IA...", "Extrayendo universo literario, estilo visual, personajes principales y escenarios clave...");

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
        const a = data.analysis;

        // Auto-completar campos de la Capa Genérica
        if (a.titulo_sugerido && (!univTitle.value.trim() || univTitle.value.startsWith("Nuevo"))) {
          univTitle.value = a.titulo_sugerido;
        }
        if (a.audiencia) univAudience.value = a.audiencia;
        if (a.ambiente) univAmbient.value = a.ambiente;
        if (a.estilo_visual) univStyle.value = a.estilo_visual;
        if (a.estilo_detalles) univStyleDetails.value = a.estilo_detalles;
        if (a.voz_defecto) univVoice.value = a.voz_defecto;
        if (a.personajes_recurrentes_texto && univRecurrentChars) {
          univRecurrentChars.value = a.personajes_recurrentes_texto;
        }

        // Reemplazar o incorporar personajes y escenarios detectados
        if (a.personajes && a.personajes.length > 0) {
          renderCharacterCards(a.personajes);
        }
        if (a.escenarios && a.escenarios.length > 0) {
          renderEnvironmentCards(a.escenarios);
        }

        // Incorporar perfil del narrador detectado por IA (Punto 5)
        if (a.perfil_narrador) {
          populateNarratorFields(a.perfil_narrador, a.voz_defecto || a.perfil_narrador.voz_recomendada);
        }

        // Guardar automáticamente los cambios de la biblia
        await saveUniverse(false);

        showToast("¡Análisis completado! Universo, Estilo, Personajes y Escenarios configurados.", "success");
        setSystemStatus("success", "¡Análisis de libro completado!", "Universo, personajes y escenarios clave listos en la Capa Genérica.");
      } else {
        showToast(data.detail || "Error analizando libro con IA", "error");
        setSystemStatus("error", "Error en análisis de libro", data.detail || "Fallo al procesar el texto con IA.");
      }
    } catch (e) {
      showToast("Error analizando libro con IA", "error");
      setSystemStatus("error", "Error de conexión en análisis", e.message);
    } finally {
      btnAiAnalyzeBook.disabled = false;
      btnAiAnalyzeBook.innerHTML = '<span class="btn-icon-symbol">🔮</span> Analizar Libro con IA';
    }
  }

  // ========================================================
  // 5. GESTIÓN DE LA BIBLIA DE PERSONAJES & RETRATOS
  // ========================================================
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

    const charTipo = char.tipo || ((char.nombre && char.nombre.toLowerCase().includes("platero")) || (char.descripcion_visual && char.descripcion_visual.toLowerCase().includes("burro")) ? "animal" : "humano");
    const isPng = char.imagen_url && (char.imagen_url.includes(".png") || char.imagen_url.includes("nobg"));
    const isSinFondo = char.sin_fondo !== false;
    const formatoVista = char.formato_vista || "giro_360";

    const approvalStatus = card.dataset.estadoAprobacion;
    let statusBadge = "";
    if (approvalStatus === "aprobado") {
      statusBadge = `<span class="badge" style="background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #22c55e; font-size: 0.72rem; padding: 2px 6px; border-radius: 4px;" title="Propuesta aprobada oficialmente">✅ Aprobado</span>`;
    } else if (approvalStatus === "rechazado") {
      statusBadge = `<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; font-size: 0.72rem; padding: 2px 6px; border-radius: 4px;" title="Rechazado: ${char.motivo_rechazo || 'No cuadra'}">❌ Rechazado</span>`;
    } else {
      statusBadge = `<span class="badge" style="background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid #eab308; font-size: 0.72rem; padding: 2px 6px; border-radius: 4px;" title="Pendiente de aprobación en Telegram">⏳ Pendiente</span>`;
    }

    card.innerHTML = `
      <!-- Columna Retrato -->
      <div class="char-portrait-box">
        <div class="char-portrait-frame ${isPng ? 'transparent-bg' : ''}" id="char-frame-${index}">
          ${portraitHtml}
        </div>
        <div class="char-portrait-actions">
          <button class="btn btn-secondary btn-xs btn-gen-portrait" data-index="${index}" title="Generar retrato u hoja de personaje en el estilo del proyecto">
            🎨 ${char.imagen_url ? 'Regenerar IA' : 'Generar IA'}
          </button>
          ${char.imagen_url ? `
            <button type="button" class="btn btn-ghost btn-xs btn-remove-bg" data-index="${index}" title="Recortar y eliminar fondo (PNG transparente con rembg)">
              ✂️ Sin Fondo
            </button>
          ` : ''}
          <label class="btn btn-ghost btn-xs">
            📁 Subir
            <input type="file" class="input-upload-portrait" data-index="${index}" accept="image/*" style="display:none;">
          </label>
        </div>
        <div class="char-approval-bar" style="display: flex; gap: 4px; margin-top: 6px; justify-content: center; flex-wrap: wrap;">
          <button type="button" class="btn btn-outline btn-xxs btn-send-telegram-char" data-index="${index}" title="Enviar propuesta a Telegram para Human-in-the-Loop">📱 Telegram</button>
          <button type="button" class="btn btn-ghost btn-xxs btn-approve-char" data-index="${index}" style="color: #4ade80;" title="Aprobar personaje">✅</button>
          <button type="button" class="btn btn-ghost btn-xxs btn-reject-char" data-index="${index}" style="color: #f87171;" title="Rechazar personaje porque no cuadra">❌</button>
          <button type="button" class="btn btn-ghost btn-xxs btn-redo-char" data-index="${index}" style="color: #60a5fa;" title="Rehacer propuesta">🔄</button>
        </div>
      </div>

      <!-- Columna Detalles -->
      <div class="char-details-box">
        <div class="char-details-header" style="display: flex; gap: 0.5rem; align-items: center;">
          <input type="text" class="char-input-name" placeholder="Nombre (ej: Mateo)" value="${char.nombre || ''}">
          ${statusBadge}
          <select class="char-select-type form-select-xs" title="Tipo de entidad">
            <option value="humano" ${charTipo === 'humano' ? 'selected' : ''}>👤 Humano</option>
            <option value="animal" ${charTipo === 'animal' ? 'selected' : ''}>🐴 Animal</option>
            <option value="criatura" ${charTipo === 'criatura' ? 'selected' : ''}>🐉 Criatura</option>
            <option value="objeto" ${charTipo === 'objeto' ? 'selected' : ''}>📦 Objeto</option>
          </select>
          <button class="btn-remove-char-card" data-index="${index}" title="Eliminar personaje">&times;</button>
        </div>

        <div style="display: flex; gap: 0.5rem; align-items: center;">
          <input type="text" class="char-input-role" placeholder="Rol (ej: Detective, Amigo, Mascota)" value="${char.rol || ''}" style="flex: 1;">
          <select class="char-select-view form-select-xs" title="Formato y Perspectiva de Generación (Estándar obligatorio)">
            <option value="giro_360" ${formatoVista === 'giro_360' ? 'selected' : ''}>🔄 Hoja 4 Vistas (Estándar Darbón)</option>
            <option value="cuerpo_entero" ${formatoVista === 'cuerpo_entero' ? 'selected' : ''}>🧍 Cuerpo Completo Frontal</option>
            <option value="retrato" ${formatoVista === 'retrato' ? 'selected' : ''}>👤 Retrato / Busto</option>
          </select>
          <label class="label-checkbox-nobg" title="Generar sobre fondo blanco puro y aislar recorte transparente (PNG)">
            <input type="checkbox" class="char-check-nobg" ${isSinFondo ? 'checked' : ''}> Sin fondo
          </label>
        </div>

        <textarea class="char-input-desc" rows="4" placeholder="Rasgos visuales inmutables en español (edad, pelaje/ropa, expresión)...">${char.descripcion_visual || ''}</textarea>

        <!-- Prompt en inglés para IA gráfica -->
        <div class="char-prompt-section mt-2">
          <div class="char-prompt-header">
            <span class="label-hint">Prompt en Inglés para IA:</span>
            <button type="button" class="btn btn-ghost btn-xxs btn-optimize-prompt" data-index="${index}" title="Optimizar prompt en inglés con IA">⚡ Optimizar IA</button>
          </div>
          <textarea class="char-input-prompt" rows="2" placeholder="Prompt en inglés optimizado para FLUX/SD (ej: Full body character turnaround sheet...)...">${char.prompt_retrato || ''}</textarea>
        </div>

        <!-- Banco de Consistencia (--cref / LoRA) -->
        <div class="char-consistency-bank-section mt-2" style="background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 6px; padding: 6px 8px; font-size: 0.74rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <strong style="color: #a5b4fc;">🗂️ Banco Consistencia (--cref / LoRA)</strong>
            <span class="text-muted" title="Semilla determinista de consistencia">🎲 Seed: <code>${char.seed_consistencia || 'auto'}</code></span>
          </div>
          <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
            <label style="display: flex; align-items: center; gap: 4px;" title="Peso de fidelidad de referencia (--cw 0-100)">
              <span>--cw:</span>
              <input type="number" class="char-input-cref-weight form-input" min="0" max="100" value="${char.cref_weight !== undefined ? char.cref_weight : 100}" style="width: 56px; padding: 2px 4px; font-size: 0.72rem;">
            </label>
            <label style="display: flex; align-items: center; gap: 4px; flex: 1;" title="Identificador de modelo LoRA del personaje">
              <span>LoRA:</span>
              <input type="text" class="char-input-lora-model form-input" value="${char.lora_model || ''}" placeholder="modelo_lora" style="padding: 2px 6px; font-size: 0.72rem; flex: 1;">
            </label>
            <label style="display: flex; align-items: center; gap: 4px;" title="Trigger word del personaje">
              <span>Trigger:</span>
              <input type="text" class="char-input-lora-trigger form-input" value="${char.lora_trigger || ''}" placeholder="chr_id" style="width: 90px; padding: 2px 6px; font-size: 0.72rem;">
            </label>
          </div>
          ${char.cref_directive ? `<div style="margin-top: 4px; color: #94a3b8; font-family: monospace; font-size: 0.68rem; word-break: break-all;"><code>${char.cref_directive}</code> | <code>${char.lora_directive || ''}</code></div>` : ''}
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

    const selectView = card.querySelector(".char-select-view");
    if (selectView) {
      selectView.addEventListener("change", () => {
        card.dataset.descDirty = "true";
      });
    }

    const checkNobg = card.querySelector(".char-check-nobg");
    if (checkNobg) {
      checkNobg.addEventListener("change", () => {
        card.dataset.descDirty = "true";
      });
    }

    card.querySelector(".btn-remove-char-card").addEventListener("click", async () => {
      await removeCharacterCard(index, char.id);
    });

    card.querySelector(".btn-gen-portrait").addEventListener("click", async () => {
      await generateCharacterPortrait(card, char.id, index);
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

    return card;
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
      const role = card.querySelector(".char-input-role").value.trim();
      const tipo = card.querySelector(".char-select-type")?.value || "humano";
      const desc = card.querySelector(".char-input-desc").value.trim();
      const prompt = card.querySelector(".char-input-prompt")?.value.trim() || "";
      const img = card.querySelector(".char-portrait-frame img");
      const imgUrl = img ? img.getAttribute("src") : null;
      const formatoVista = card.querySelector(".char-select-view")?.value || "giro_360";
      const sinFondo = card.querySelector(".char-check-nobg") ? card.querySelector(".char-check-nobg").checked : true;
      const crefWeight = parseInt(card.querySelector(".char-input-cref-weight")?.value || "100", 10);
      const loraModel = card.querySelector(".char-input-lora-model")?.value.trim() || "";
      const loraTrigger = card.querySelector(".char-input-lora-trigger")?.value.trim() || "";

      characters.push({
        id: charId,
        nombre: name || `Personaje ${idx+1}`,
        rol: role,
        tipo: tipo,
        descripcion_visual: desc,
        imagen_url: imgUrl,
        prompt_retrato: prompt,
        sin_fondo: sinFondo,
        formato_vista: formatoVista,
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
    const role = card.querySelector(".char-input-role")?.value.trim() || "";
    const tipo = card.querySelector(".char-select-type")?.value || "humano";
    const formatoVista = card.querySelector(".char-select-view")?.value || "giro_360";
    const sinFondo = card.querySelector(".char-check-nobg") ? card.querySelector(".char-check-nobg").checked : true;

    const btn = card.querySelector(".btn-optimize-prompt");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "⚡ Optimizando...";
    }

    setSystemStatus(
      "busy",
      `Optimizando prompt de ${name}...`,
      "Traduciendo descripción en español a inglés y blindando cuerpo completo y fondo blanco puro..."
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
          sin_fondo: sinFondo
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
        btn.textContent = "⚡ Optimizar IA";
      }
    }
  }

  // Generar Retrato / Hoja de Personaje con IA
  async function generateCharacterPortrait(card, charId, index) {
    if (!state.currentProject) return;
    if (!card) card = document.querySelector(`.char-card[data-id="${charId}"]`) || document.querySelector(`.char-card[data-index="${index}"]`);
    if (!card) return;

    const actualId = charId || card.dataset.id;
    const charName = card.querySelector(".char-input-name")?.value.trim() || "Personaje";

    // Si la descripción en español ha cambiado o se marcó dirty, optimizar y traducir primero
    if (card.dataset.descDirty === "true") {
      await optimizeCharacterPrompt(card, actualId);
      card.dataset.descDirty = "false";
    }

    // Primero guardar el estado actual de los campos
    await saveUniverse(false);

    const promptOverride = card.querySelector(".char-input-prompt")?.value.trim() || "";
    const desc = card.querySelector(".char-input-desc")?.value.trim() || "";
    const sinFondo = card.querySelector(".char-check-nobg") ? card.querySelector(".char-check-nobg").checked : true;
    const formatoVista = card.querySelector(".char-select-view")?.value || "giro_360";

    const btn = card.querySelector(".btn-gen-portrait");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "🎨 Dibujando...";
    }

    setSystemStatus(
      "busy",
      `Generando ${charName} con IA...`,
      `Pintando hoja de 4 perspectivas de cuerpo completo sobre fondo blanco puro en técnica ${state.currentProject?.estilo_visual || 'acuarela'}...`
    );

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/characters/generate-portrait`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          character_id: actualId,
          prompt_override: promptOverride,
          sin_fondo: sinFondo,
          formato_vista: formatoVista,
          descripcion_visual: desc
        })
      });
      const data = await res.json();
      if (data.success && data.imagen_url) {
        const frame = (index !== undefined ? document.getElementById(`char-frame-${index}`) : null) || card.querySelector(".char-portrait-frame");
        if (frame) {
          if (data.sin_fondo) frame.classList.add("transparent-bg");
          else frame.classList.remove("transparent-bg");
          const freshUrl = `${data.imagen_url.split('?')[0]}?t=${Date.now()}`;
          frame.innerHTML = `<img src="${freshUrl}" alt="${charName}">`;
        }
        if (btn) btn.textContent = "🎨 Regenerar IA";

        // Asegurar que exista el botón de Sin Fondo
        const actionsBox = card.querySelector(".char-portrait-actions");
        if (actionsBox && !actionsBox.querySelector(".btn-remove-bg")) {
          const remBtn = document.createElement("button");
          remBtn.type = "button";
          remBtn.className = "btn btn-ghost btn-xs btn-remove-bg";
          remBtn.dataset.index = index;
          remBtn.title = "Recortar y eliminar fondo (PNG transparente con rembg)";
          remBtn.textContent = "✂️ Sin Fondo";
          remBtn.addEventListener("click", () => removeCharacterBackground(index));
          actionsBox.insertBefore(remBtn, actionsBox.querySelector("label"));
        }

        if (data.prompt_used) {
          const promptInput = card.querySelector(".char-input-prompt");
          if (promptInput) promptInput.value = data.prompt_used;
        }
        showToast(data.sin_fondo ? `¡${charName} generado sobre fondo blanco puro!` : `¡${charName} generado con éxito!`, "success");
        setSystemStatus("success", `¡${charName} generado con éxito!`, "Hoja de 4 perspectivas de cuerpo completo sobre fondo blanco puro lista.");
      } else {
        showToast(data.detail || "Error generando personaje", "error");
        if (btn) btn.textContent = "🎨 Reintentar";
        setSystemStatus("error", `Error generando ${charName}`, data.detail || "Fallo en motor de imagen.");
      }
    } catch (e) {
      showToast("Error generando personaje con IA", "error");
      if (btn) btn.textContent = "🎨 Reintentar";
      setSystemStatus("error", `Error generando ${charName}`, "No se pudo conectar con el motor gráfico.");
    } finally {
      if (btn) btn.disabled = false;
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
  }

  function createEnvironmentCardElement(env, index) {
    const card = document.createElement("div");
    card.className = "env-card";
    card.dataset.index = index;
    card.dataset.id = env.id || `esc_${index+1}`;
    card.dataset.estadoAprobacion = env.estado_aprobacion || (env.imagen_url ? "aprobado" : "pendiente");
    card.dataset.motivoRechazo = env.motivo_rechazo || "";
    card.dataset.telegramMessageId = env.telegram_message_id || "";

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

    const envTipo = env.tipo || "exterior_urbano";
    const approvalStatus = card.dataset.estadoAprobacion;
    let statusBadge = "";
    if (approvalStatus === "aprobado") {
      statusBadge = `<span class="badge" style="background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #22c55e; font-size: 0.72rem; padding: 2px 6px; border-radius: 4px;" title="Escenario aprobado oficialmente">✅ Aprobado</span>`;
    } else if (approvalStatus === "rechazado") {
      statusBadge = `<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; font-size: 0.72rem; padding: 2px 6px; border-radius: 4px;" title="Rechazado: ${env.motivo_rechazo || 'No cuadra'}">❌ Rechazado</span>`;
    } else {
      statusBadge = `<span class="badge" style="background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid #eab308; font-size: 0.72rem; padding: 2px 6px; border-radius: 4px;" title="Pendiente de aprobación en Telegram">⏳ Pendiente</span>`;
    }

    card.innerHTML = `
      <!-- Columna Visual del Escenario -->
      <div class="env-preview-box">
        <div class="env-preview-frame" id="env-frame-${index}">
          ${previewHtml}
        </div>
        <div class="env-preview-actions">
          <button class="btn btn-secondary btn-xs btn-gen-env" data-index="${index}" title="Generar arte conceptual del escenario">
            🎨 ${env.imagen_url ? 'Regenerar IA' : 'Generar IA'}
          </button>
          <label class="btn btn-ghost btn-xs">
            📁 Subir
            <input type="file" class="input-upload-env" data-index="${index}" accept="image/*" style="display:none;">
          </label>
        </div>
        <div class="env-approval-bar" style="display: flex; gap: 4px; margin-top: 6px; justify-content: center; flex-wrap: wrap;">
          <button type="button" class="btn btn-outline btn-xxs btn-send-telegram-env" data-index="${index}" title="Enviar propuesta a Telegram">📱 Telegram</button>
          <button type="button" class="btn btn-ghost btn-xxs btn-approve-env" data-index="${index}" style="color: #4ade80;" title="Aprobar escenario">✅</button>
          <button type="button" class="btn btn-ghost btn-xxs btn-reject-env" data-index="${index}" style="color: #f87171;" title="Rechazar escenario porque no cuadra">❌</button>
          <button type="button" class="btn btn-ghost btn-xxs btn-redo-env" data-index="${index}" style="color: #60a5fa;" title="Rehacer escenario">🔄</button>
        </div>
      </div>

      <!-- Columna Detalles del Escenario -->
      <div class="env-details-box">
        <div class="env-details-header" style="display: flex; gap: 0.5rem; align-items: center;">
          <input type="text" class="env-input-name" placeholder="Nombre del Escenario (ej: Calles de Moguer)" value="${env.nombre || ''}">
          ${statusBadge}
          <select class="env-select-type form-select-xs" title="Tipo de entorno">
            <option value="exterior_urbano" ${envTipo === 'exterior_urbano' ? 'selected' : ''}>🏛️ Urbano / Calles</option>
            <option value="naturaleza" ${envTipo === 'naturaleza' ? 'selected' : ''}>🌿 Naturaleza / Paisaje</option>
            <option value="interior" ${envTipo === 'interior' ? 'selected' : ''}>🏠 Interior / Rústico</option>
            <option value="panoramica" ${envTipo === 'panoramica' ? 'selected' : ''}>🌄 Vista Panorámica</option>
          </select>
          <button class="btn-remove-env-card" data-index="${index}" title="Eliminar escenario">&times;</button>
        </div>
        <textarea class="env-input-desc" rows="4" placeholder="Descripción visual detallada (arquitectura, colores, iluminación, clima)...">${env.descripcion_visual || ''}</textarea>

        <!-- Prompt en inglés para IA gráfica -->
        <div class="env-prompt-section mt-2">
          <div class="env-prompt-header">
            <span class="label-hint">Prompt en Inglés para Escenario (Sin Personas):</span>
            <button type="button" class="btn btn-ghost btn-xxs btn-optimize-env-prompt" data-index="${index}" title="Optimizar prompt en inglés con IA">⚡ Optimizar IA</button>
          </div>
          <textarea class="env-input-prompt" rows="2" placeholder="Scenic background art, empty street, no people, vertical 9:16...">${env.prompt_escenario || ''}</textarea>
        </div>
      </div>
    `;

    // Eventos
    card.querySelector(".btn-remove-env-card").addEventListener("click", async () => {
      await removeEnvironmentCard(index, env.id);
    });

    card.querySelector(".btn-gen-env").addEventListener("click", async () => {
      await generateEnvironmentImage(index);
    });

    card.querySelector(".btn-optimize-env-prompt").addEventListener("click", async () => {
      await optimizeEnvironmentPrompt(index);
    });

    card.querySelector(".btn-send-telegram-env")?.addEventListener("click", async () => {
      await sendEnvironmentToTelegram(env.id, index);
    });

    card.querySelector(".btn-approve-env")?.addEventListener("click", async () => {
      await applyApprovalDecision("environment", env.id, "approve");
    });

    card.querySelector(".btn-reject-env")?.addEventListener("click", async () => {
      const feedback = prompt("Indica el motivo del rechazo o qué revisar porque no cuadra:", "No cuadra con la visión del escenario.");
      if (feedback !== null) {
        await applyApprovalDecision("environment", env.id, "reject", feedback);
      }
    });

    card.querySelector(".btn-redo-env")?.addEventListener("click", async () => {
      if (confirm(`¿Rehacer y regenerar la propuesta para '${env.nombre || env.id}'?`)) {
        await applyApprovalDecision("environment", env.id, "redo", "Rehacer porque no cuadra");
      }
    });

    card.querySelector(".input-upload-env").addEventListener("change", async e => {
      if (e.target.files.length > 0) {
        await uploadEnvironmentImage(index, e.target.files[0]);
      }
    });

    return card;
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
      environments.push({
        id: card.dataset.id || `esc_${idx+1}`,
        nombre: card.querySelector(".env-input-name")?.value.trim() || `Escenario ${idx+1}`,
        tipo: card.querySelector(".env-select-type")?.value || "exterior_urbano",
        descripcion_visual: card.querySelector(".env-input-desc")?.value.trim() || "",
        imagen_url: imgEl ? imgEl.getAttribute("src") : null,
        prompt_escenario: card.querySelector(".env-input-prompt")?.value.trim() || "",
        estado_aprobacion: card.dataset.estadoAprobacion || "pendiente",
        motivo_rechazo: card.dataset.motivoRechazo || "",
        telegram_message_id: card.dataset.telegramMessageId || null
      });
    });
    return environments;
  }

  async function optimizeEnvironmentPrompt(index) {
    if (!state.currentProject) return;
    await saveUniverse(false);
    const card = document.querySelector(`.env-card[data-index="${index}"]`);
    if (!card) return;
    const envId = card.dataset.id;
    const btn = card.querySelector(".btn-optimize-env-prompt");
    btn.disabled = true;
    btn.textContent = "⏳ Optimizando...";
    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/environments/${envId}/optimize-prompt`, {
        method: "POST"
      });
      const data = await res.json();
      if (data.success && data.prompt_escenario) {
        const promptInput = card.querySelector(".env-input-prompt");
        if (promptInput) promptInput.value = data.prompt_escenario;
        showToast("¡Prompt de escenario optimizado para fondo limpio!", "success");
      }
    } catch (e) {
      showToast("Error optimizando prompt de escenario", "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "⚡ Optimizar IA";
    }
  }

  async function generateEnvironmentImage(index) {
    if (!state.currentProject) return;
    await saveUniverse(false);
    const card = document.querySelector(`.env-card[data-index="${index}"]`);
    if (!card) return;
    const envId = card.dataset.id;
    const envName = card.querySelector(".env-input-nombre")?.value.trim() || "Escenario";
    const promptOverride = card.querySelector(".env-input-prompt")?.value.trim() || "";
    const btn = card.querySelector(".btn-gen-env");
    btn.disabled = true;
    btn.textContent = "🎨 Dibujando...";
    setSystemStatus(
      "busy",
      `Pintando ${envName}...`,
      "Generando arte conceptual en formato 9:16 con el estilo visual del universo..."
    );
    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/environments/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          environment_id: envId,
          prompt_override: promptOverride
        })
      });
      const data = await res.json();
      if (data.success && data.imagen_url) {
        const frame = document.getElementById(`env-frame-${index}`);
        const freshUrl = data.imagen_url.includes("?") ? `${data.imagen_url}&t=${Date.now()}` : `${data.imagen_url}?t=${Date.now()}`;
        frame.innerHTML = `<img src="${freshUrl}" alt="Escenario">`;
        btn.textContent = "🎨 Regenerar IA";
        if (data.prompt_used) {
          const promptInput = card.querySelector(".env-input-prompt");
          if (promptInput && !promptInput.value) promptInput.value = data.prompt_used;
        }
        showToast("¡Arte de escenario generado con éxito!", "success");
        setSystemStatus("success", `¡${envName} generado!`, "Escenario de referencia listo para las escenas del proyecto.");
      } else {
        showToast(data.detail || "Error generando escenario", "error");
        setSystemStatus("error", `Error generando ${envName}`, data.detail || "Fallo en motor de imagen.");
        btn.textContent = "🎨 Reintentar";
      }
    } catch (e) {
      showToast("Error generando escenario con IA", "error");
      setSystemStatus("error", `Error de conexión generando ${envName}`, e.message);
      btn.textContent = "🎨 Reintentar";
    } finally {
      btn.disabled = false;
    }
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
    if (!state.currentProject) return;

    const title = univTitle.value.trim() || state.currentProject.titulo;
    const chars = collectCharactersFromUI();
    const envs = collectEnvironmentsFromUI();

    const activeVoice = (narratorVoiceSelect ? narratorVoiceSelect.value : null) || univVoice.value || "openai_fable";
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
      estilo_detalles: univStyleDetails.value.trim(),
      voz_defecto: activeVoice,
      perfil_narrador: narratorProfile,
      personajes_recurrentes_texto: univRecurrentChars ? univRecurrentChars.value.trim() : "",
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

    const voiceId = voiceIdOverride || (narratorVoiceSelect ? narratorVoiceSelect.value : univVoice.value) || "openai_fable";
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

  // Recomendar narrador con IA
  if (btnAiRecommendNarrator) {
    btnAiRecommendNarrator.addEventListener("click", async () => {
      if (!state.currentProject) {
        showToast("Selecciona un proyecto primero", "warning");
        return;
      }

      btnAiRecommendNarrator.disabled = true;
      btnAiRecommendNarrator.innerHTML = '<span class="btn-icon-symbol">⏳</span> Analizando Narrador con IA...';
      setSystemStatus("busy", "Analizando voz del narrador con IA...", "Deduciendo perfil psicológico, edad y timbre idóneo a partir del libro...");

      try {
        const res = await fetch(`/api/projects/${state.currentProject.id}/narrator/recommend-ai`, {
          method: "POST"
        });
        const data = await res.json();
        if (data.success && data.perfil_narrador) {
          populateNarratorFields(data.perfil_narrador, data.perfil_narrador.voz_recomendada);
          showToast("¡Perfil del narrador y voz recomendada actualizados con IA!", "success");
          setSystemStatus("success", "Narrador configurado", `Recomendado: ${data.perfil_narrador.nombre} (${data.perfil_narrador.edad_aprox || ''})`);
        } else {
          showToast(data.detail || "Error recomendando narrador", "error");
          setSystemStatus("error", "Error en análisis de narrador", data.detail || "");
        }
      } catch (e) {
        showToast("Error al recomendar narrador con IA", "error");
        setSystemStatus("error", "Error de red en análisis de narrador", e.message);
      } finally {
        btnAiRecommendNarrator.disabled = false;
        btnAiRecommendNarrator.innerHTML = '🔮 Recomendar Narrador con IA';
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
  function updateStyleImplications(styleKey, updateDetailsField = false) {
    const meta = STYLE_METADATA[styleKey] || STYLE_METADATA["watercolor"];
    if (styleImplicationsIcon) styleImplicationsIcon.textContent = meta.icon;
    if (styleImplicationsTitle) styleImplicationsTitle.textContent = `Implicaciones Técnicas: ${meta.name}`;
    if (styleImplicationsTags) {
      styleImplicationsTags.innerHTML = meta.tags.map(t => `<span class="style-badge-tag">${t}</span>`).join("");
    }
    if (styleImplicationsDesc) {
      styleImplicationsDesc.textContent = meta.desc;
    }
    const noteEl = document.querySelector(".style-implications-coherence-note span");
    if (noteEl) {
      noteEl.innerHTML = `<b>Regla de Coherencia Absoluta:</b> ${meta.coherenceNote}`;
    }

    if (updateDetailsField && univStyleDetails) {
      const currentVal = univStyleDetails.value.trim();
      const isDefaultOfAny = Object.values(STYLE_METADATA).some(m => m.defaultDetails.trim() === currentVal);
      if (!currentVal || isDefaultOfAny) {
        univStyleDetails.value = meta.defaultDetails;
      }
    }
  }

  // Sincronizar y propagar técnica visual a todos los personajes y escenarios
  async function syncStyleToAllEntities() {
    if (!state.currentProject) {
      showToast("Selecciona un proyecto primero", "warning");
      return;
    }

    const currentStyle = univStyle.value;
    const currentDetails = univStyleDetails.value.trim();

    if (btnSyncStyleToAll) {
      btnSyncStyleToAll.disabled = true;
      btnSyncStyleToAll.textContent = "⏳ Sincronizando con IA...";
    }

    setSystemStatus(
      "busy",
      "Sincronizando Estilo del Universo...",
      `Traduciendo descripciones y adaptando hojas de 4 vistas (2x2 grid) y escenarios a la técnica '${currentStyle}'...`
    );

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/sync-style`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          estilo_visual: currentStyle,
          estilo_detalles: currentDetails
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

        showToast(`✅ ¡Estilo sincronizado! ${data.characters_synced} personajes (hojas 4 vistas estándar Darbón) y ${data.environments_synced} escenarios actualizados.`, "success");
        setSystemStatus(
          "success",
          "Estilo sincronizado en todo el universo",
          `${data.characters_synced} personajes (2x2 grid) y ${data.environments_synced} escenarios adaptados a '${currentStyle}'.`
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
        btnSyncStyleToAll.textContent = "⚡ Sincronizar estilo en Personajes y Escenarios";
      }
    }
  }

  if (univStyle) {
    univStyle.addEventListener("change", () => updateStyleImplications(univStyle.value, true));
  }
  if (btnSyncStyleToAll) {
    btnSyncStyleToAll.addEventListener("click", syncStyleToAllEntities);
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
      btnAuditCharacters.innerHTML = `⏳ Auditando con Visión IA...`;
    }

    showToast("🔍 Auditando personajes: verificando 4 perspectivas, fondo limpio y técnica plástica uniforme...", "info");
    setSystemStatus(
      "busy",
      "Auditando Coherencia de Personajes...",
      "GPT-4o Vision revisando que cada personaje tenga 4 vistas en cuadrícula 2x2, fondo limpio y técnica uniforme..."
    );

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/audit-characters?auto_heal=true`, {
        method: "POST"
      });
      const data = await res.json();
      if (data.success) {
        await selectProject(state.currentProject.id);

        let toastMsg = `Auditoría finalizada: ${data.approved} coherentes`;
        if (data.healed > 0) {
          toastMsg += ` y ${data.healed} corregidos automáticamente`;
          setSystemStatus(
            "healing",
            "Personajes corregidos automáticamente",
            `${data.healed} personaje(s) regenerados con cuadrícula 2x2. ${data.approved} personajes aprobados.`
          );
        } else {
          setSystemStatus(
            "success",
            "Auditoría de personajes aprobada (100%)",
            `Los ${data.approved} personajes cumplen el estándar de 4 vistas (2x2 grid) y técnica de acuarela.`
          );
        }
        showToast(toastMsg, data.healed > 0 ? "warning" : "success");

        openAuditModal(
          "🔍 Auditoría de Coherencia de Personajes",
          `Evaluación exhaustiva de 4 perspectivas, fondo blanco y técnica artística (${data.style}).`
        );
        renderAuditResults(data, "characters");
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
      btnAuditEnvironments.innerHTML = `⏳ Auditando con Visión IA...`;
    }

    showToast("🔍 Auditando escenarios: verificando ausencia de personas, técnica artística y encuadre 9:16...", "info");
    setSystemStatus(
      "busy",
      "Auditando Coherencia de Escenarios...",
      "GPT-4o Vision comprobando que los fondos escénicos estén libres de personas y cumplan el formato 9:16..."
    );

    try {
      const res = await fetch(`/api/projects/${state.currentProject.id}/audit-environments?auto_heal=true`, {
        method: "POST"
      });
      const data = await res.json();
      if (data.success) {
        await selectProject(state.currentProject.id);

        let toastMsg = `Auditoría finalizada: ${data.approved} escenarios coherentes`;
        if (data.healed > 0) {
          toastMsg += ` y ${data.healed} regenerados automáticamente`;
          setSystemStatus(
            "healing",
            "Escenarios corregidos automáticamente",
            `${data.healed} fondo(s) regenerados sin personas en formato 9:16. ${data.approved} aprobados.`
          );
        } else {
          setSystemStatus(
            "success",
            "Auditoría de escenarios aprobada (100%)",
            `Los ${data.approved} escenarios cumplen con fondos escénicos limpios y técnica de acuarela.`
          );
        }
        showToast(toastMsg, data.healed > 0 ? "warning" : "success");

        openAuditModal(
          "🔍 Auditoría de Coherencia de Escenarios",
          `Evaluación de fondos limpios sin personas, encuadre 9:16 y técnica plástica (${data.style}).`
        );
        renderAuditResults(data, "environments");
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

    btnGenerateStoryboard.disabled = true;
    btnGenerateStoryboard.innerHTML = '<span class="btn-icon-symbol">⏳</span> Desglosando con Biblia de Personajes...';

    const title = chapterTitleInput.value.trim() || "Capítulo";
    setSystemStatus(
      "busy",
      `Desglosando guión: ${title}...`,
      "Extrayendo escenas y vinculando personajes canónicos de la biblia..."
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
          target_scenes: parseInt(scenesCountSelect.value)
        })
      });

      const data = await res.json();
      if (data.success && data.scenes) {
        state.scenes = data.scenes;
        storyboardTitle.textContent = `Storyboard: ${title}`;
        renderStoryboard();
        storyboardContainer.style.display = "block";
        storyboardContainer.scrollIntoView({ behavior: "smooth" });
        showToast(`Capítulo adaptado en ${state.scenes.length} escenas consistentes`, "success");
        setSystemStatus("success", `¡Storyboard generado!`, `${state.scenes.length} escenas desglosadas con consistencia de personajes.`);
      } else {
        showToast(data.detail || "Error generando storyboard", "error");
        setSystemStatus("error", "Error generando storyboard", data.detail || "No se pudo generar el guión.");
      }
    } catch (e) {
      showToast(`Error generando storyboard: ${e.message}`, "error");
      setSystemStatus("error", "Error de conexión en storyboard", e.message);
    } finally {
      btnGenerateStoryboard.disabled = false;
      btnGenerateStoryboard.innerHTML = '<span class="btn-icon-symbol">✨</span> Desglosar Capítulo con Biblia de Personajes';
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

    return `
      Escena #${index + 1}
      <span class="scene-badge-pill" id="dur-badge-${index}">
        ${sc.duracion_real ? sc.duracion_real + 's' : '~' + sc.duracion_estimada + 's'}
      </span>
      ${charsInScene}
      ${envInScene}
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

      const audioPlayerHtml = sc.audio_url
        ? `<audio controls class="audio-player-mini" src="${sc.audio_url}"></audio>`
        : `<small class="text-muted">Audio no generado aún</small>`;

      card.innerHTML = `
        <!-- Panel Visual (Izquierda) -->
        <div class="scene-visual-pane">
          <div class="scene-image-preview" id="img-preview-${index}">
            ${imgPreviewHtml}
          </div>
          <div class="scene-image-actions">
            <button class="btn btn-secondary btn-xs btn-gen-img" data-idx="${index}">
              🎨 ${sc.image_url ? 'Regenerar Foto' : 'Generar Foto'}
            </button>
            <label class="btn btn-ghost btn-xs btn-upload-label">
              📁 Subir Foto
              <input type="file" class="input-upload-img" data-idx="${index}" accept="image/*" style="display:none;">
            </label>
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
                <button class="btn btn-ghost btn-xs btn-inject-anchors" data-idx="${index}" title="Inyectar y reforzar rasgos canónicos inmutables de la biblia">
                  🛡️ Consistencia
                </button>
                <button class="btn btn-ghost btn-xs btn-rewrite-scene" data-idx="${index}" title="Pedir cambios con IA">
                  ✨ Reescribir
                </button>
                <button class="btn btn-ghost btn-xs btn-delete-scene" data-idx="${index}" title="Eliminar escena">
                  🗑️
                </button>
              </div>
            </div>

            <div class="mt-3">
              <label class="field-label">Locución del Narrador</label>
              <textarea class="form-textarea input-narrador" data-idx="${index}" rows="2">${sc.narrador}</textarea>
            </div>

            <div class="audio-controls-row" id="audio-row-${index}">
              ${audioPlayerHtml}
              <button class="btn btn-secondary btn-xs btn-gen-audio" data-idx="${index}">
                🔊 ${sc.audio_url ? 'Regenerar Voz' : 'Generar Voz'}
              </button>
            </div>

            <!-- Vinculación Canónica de Personajes y Escenarios de la Capa Genérica -->
            <div class="scene-canon-binding-box">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.72rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">
                  👥 Personajes en esta escena
                </span>
                <span style="font-size: 0.68rem; color: var(--primary-glow); font-weight: 500;">
                  (Vincula el modelo canónico oficial)
                </span>
              </div>
              <div class="scene-char-selector-row">
                ${renderSceneCharacterChips(sc, index)}
              </div>

              <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px; margin-bottom: 4px;">
                <span style="font-size: 0.72rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">
                  🏛️ Escenario clave
                </span>
                <span style="font-size: 0.68rem; color: var(--text-muted);">
                  (Entorno de la biblia general)
                </span>
              </div>
              ${renderSceneEnvSelect(sc, index)}
            </div>

            <div class="mt-3">
              <label class="field-label">Prompt Visual (Inglés con rasgos del personaje)</label>
              <textarea class="form-textarea input-prompt" data-idx="${index}" rows="2" style="font-family: var(--font-mono); font-size: 0.8rem;">${sc.prompt_imagen}</textarea>
            </div>
          </div>
        </div>
      `;

      scenesGrid.appendChild(card);
    });

    attachSceneEventListeners();
  }

  function attachSceneEventListeners() {
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
    setSystemStatus("busy", `Locución Escena #${idx + 1}...`, "Sintetizando voz con ElevenLabs...");

    const voiceKey = state.currentProject ? state.currentProject.voz_defecto : "eleven_george";

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
        audioRow.innerHTML = `
          <audio controls class="audio-player-mini" src="${data.url}"></audio>
          <button class="btn btn-secondary btn-xs btn-gen-audio" data-idx="${idx}">
            🔊 Regenerar Voz
          </button>
        `;
        document.getElementById(`dur-badge-${idx}`).textContent = `${data.duration}s`;
        audioRow.querySelector(".btn-gen-audio").addEventListener("click", () => generateAudioForScene(idx));
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

  // Generación de Imagen Escena con Inyección de Referencia
  async function generateImageForScene(idx) {
    const sc = state.scenes[idx];
    const btn = document.querySelector(`.btn-gen-img[data-idx="${idx}"]`);
    btn.disabled = true;
    btn.textContent = "🎨 Dibujando...";
    setSystemStatus("busy", `Pintando Escena #${idx + 1}...`, "Dibujando fotograma 9:16 con estilo consistente y referencias...");

    // Detectar si algún personaje de la escena tiene imagen de referencia canónica aprobada
    let refImageUrl = null;
    if (state.currentProject?.personajes && sc.personajes_en_escena && sc.personajes_en_escena.length > 0) {
      for (const charName of sc.personajes_en_escena) {
        const pMatch = state.currentProject.personajes.find(p => 
          p.nombre.toLowerCase() === charName.toLowerCase() ||
          (p.id && p.id.toLowerCase() === charName.toLowerCase())
        );
        if (pMatch && pMatch.imagen_url) {
          refImageUrl = pMatch.imagen_url;
          break;
        }
      }
    }
    // Si no hay imagen de personaje pero sí de escenario clave
    if (!refImageUrl && state.currentProject?.escenarios && sc.escenario_clave) {
      const eMatch = state.currentProject.escenarios.find(e =>
        e.nombre.toLowerCase() === sc.escenario_clave.toLowerCase() ||
        (e.id && e.id.toLowerCase() === sc.escenario_clave.toLowerCase())
      );
      if (eMatch && eMatch.imagen_url) {
        refImageUrl = eMatch.imagen_url;
      }
    }

    try {
      const res = await fetch("/api/image/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: sc.prompt_imagen,
          provider: "flux",
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
          enable_subtitles: chkSubtitles.checked,
          enable_ken_burns: chkKenBurns.checked
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
    const filtered = state.chapters.filter(c => {
      if (!query) return true;
      const titleMatch = (c.titulo || "").toLowerCase().includes(query);
      const originMatch = (c.origen_ref || "").toString().toLowerCase().includes(query);
      return titleMatch || originMatch;
    });

    if (filtered.length === 0) {
      if (state.chapters.length === 0) {
        chaptersTreeList.innerHTML = `
          <div class="tree-empty-state">
            <p class="text-muted" style="font-size:0.82rem; margin-bottom:0.5rem;">
              No hay capítulos creados en este libro.
            </p>
            <div style="font-size:0.75rem; color:var(--text-secondary); line-height:1.4;">
              Usa <strong>⚡ Importar</strong> para convertir el manuscrito en capítulos o pulsa <strong>➕ Nuevo</strong>.
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
      return;
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
      storyboardTitle.textContent = `Storyboard: ${cap.titulo}`;

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
      orden: state.currentChapterOrden || (state.chapters.length + 1)
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
          selectManuscriptSection.innerHTML = "";
          doc.chapters.forEach((sec, idx) => {
            const opt = document.createElement("option");
            opt.value = idx;
            opt.textContent = `${sec.title} (~${sec.word_count || 0} palabras)`;
            selectManuscriptSection.appendChild(opt);
          });

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

  function updateSectionPreview(secIdx) {
    if (!state.manuscriptDoc || !state.manuscriptDoc.chapters) return;
    const idx = parseInt(secIdx);
    state.selectedSectionIdx = idx;

    const sec = state.manuscriptDoc.chapters[idx];
    if (!sec) return;

    if (sectionPreviewBadge) {
      sectionPreviewBadge.textContent = sec.title || `Sección ${idx + 1}`;
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

      chapterTitleInput.value = sec.title;
      rawChapterText.value = sec.text;
      state.currentChapterOriginType = "section";
      state.currentChapterOriginRef = sec.title;
      updateChapterWordsCounter();

      if (currentChapterHeading) currentChapterHeading.textContent = sec.title;
      if (currentChapterOriginPill) {
        currentChapterOriginPill.textContent = `📑 ${sec.title}`;
        currentChapterOriginPill.style.display = "inline-flex";
      }
      showToast(`Sección "${sec.title}" asignada al capítulo`, "info");
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
      renderSettingItem("GEMINI_API_KEY", "badge-status-gemini", "masked-gemini", settingGemini);

    } catch (err) {
      console.error("Error cargando ajustes:", err);
    }
  }

  btnOpenSettings.addEventListener("click", () => {
    modalSettings.classList.add("open");
    loadSettingsModal();
  });

  btnSaveSettings.addEventListener("click", async () => {
    const payload = {};
    if (settingOpenai && settingOpenai.value) payload.OPENAI_API_KEY = settingOpenai.value.trim();
    if (settingEleven && settingEleven.value) payload.ELEVENLABS_API_KEY = settingEleven.value.trim();
    if (settingPollinations && settingPollinations.value) payload.POLLINATIONS_API_KEY = settingPollinations.value.trim();
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

  // Arrancar la app
  init();
});
