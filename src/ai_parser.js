(function(){
  const RUBRIC = [
    "Content / Relevance",
    "Achievements / Results",
    "Skills / Keywords",
    "Organization / Formatting",
    "Professionalism"
  ];

  function coerceIntInRange(v, min, max, fallback){
    let n = typeof v === 'number' ? v : parseInt(v, 10);
    if (Number.isNaN(n)) n = fallback;
    if (n < min) n = min;
    if (n > max) n = max;
    return n;
  }

  function normalizeScores(inputScores){
    const byName = new Map();
    if (Array.isArray(inputScores)){
      inputScores.forEach(item => {
        if (!item) return;
        const name = typeof item.name === 'string' ? item.name.trim() : '';
        if (!name) return;
        byName.set(name, {
          name,
          score: coerceIntInRange(item.score, 0, 5, 0),
          max: coerceIntInRange(item.max, 0, 5, 5)
        });
      });
    }
    // Build ordered array using canonical rubric names
    return RUBRIC.map(name => {
      const found = byName.get(name);
      if (found) return found;
      // Try some loose matching if exact name not found
      let alt = null;
      for (const [k, v] of byName.entries()){
        const kk = k.toLowerCase();
        if (name.toLowerCase().includes('content') && kk.includes('content')) alt = v;
        else if (name.toLowerCase().includes('achievements') && (kk.includes('achiev') || kk.includes('results'))) alt = v;
        else if (name.toLowerCase().includes('skills') && (kk.includes('skill') || kk.includes('keyword'))) alt = v;
        else if (name.toLowerCase().includes('organization') && (kk.includes('organ') || kk.includes('format'))) alt = v;
        else if (name.toLowerCase().includes('professionalism') && kk.includes('prof')) alt = v;
        if (alt) break;
      }
      if (alt) return {
        name,
        score: coerceIntInRange(alt.score, 0, 5, 0),
        max: coerceIntInRange(alt.max, 0, 5, 5)
      };
      return { name, score: 0, max: 5 };
    });
  }

  function normalizeComments(input){
    const out = [];
    if (Array.isArray(input)){
      for (const it of input){
        if (typeof it === 'string'){
          const t = it.trim();
          if (t) out.push(t);
        } else if (it && typeof it.text === 'string'){
          const t = it.text.trim();
          if (t) out.push(t);
        }
        if (out.length >= 20) break;
      }
    }
    // Fallback if none
    if (out.length === 0){
      out.push("No detailed comments were provided. Consider adding measurable achievements, aligning skills to roles, and ensuring consistent formatting.");
    }
    return out;
  }

  function parseAiAnalysis(raw){
    // Backend may already parse. But support string just in case.
    if (raw && typeof raw === 'object' && raw.error){
      const msg = raw.detail ? `${raw.error}: ${raw.detail}` : raw.error;
      throw new Error(msg);
    }
    let obj = raw;
    if (typeof raw === 'string'){
      try { obj = JSON.parse(raw); }
      catch(e){ throw new Error('AI returned non-JSON output'); }
    }
    if (!obj || typeof obj !== 'object'){
      throw new Error('AI returned empty or invalid analysis object');
    }
    const scores = normalizeScores(obj.scores);
    const comments = normalizeComments(obj.comments);
    return { scores, comments };
  }

  window.parseAiAnalysis = parseAiAnalysis;
})();

async function extractTextFromPdfFile(file) {
  // Assumes pdfjsLib is available globally (you already use it)
  const arrayBuffer = await file.arrayBuffer();
  const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
  const pdf = await loadingTask.promise;
  const numPages = pdf.numPages;
  if (numPages > 2) {
    // show inline UI error rather than alert()
    showInlineError("Resume is longer than 2 pages — please upload a shorter version (max 2 pages).");
    return null;
  }

  let fullText = "";
  const pagesToRead = Math.min(2, numPages);
  for (let i = 1; i <= pagesToRead; i++) {
    const page = await pdf.getPage(i);
    const textContent = await page.getTextContent();
    const pageText = textContent.items.map(item => item.str).join(" ");
    fullText += pageText + "\n\n";
    // optional: break early if text length exceeds some threshold
    if (fullText.length > 6000) {
      fullText = fullText.slice(0, 6000);
      break;
    }
  }
  return { text: fullText.trim(), pages: numPages };
}

async function onUploadAndAnalyze(file) {
  const extracted = await extractTextFromPdfFile(file);
  if (!extracted) return; // user saw error
  // Show spinner / UI state
  setAnalyzing(true);

  try {
    const resp = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(extracted),
    });
    const j = await resp.json();
    if (!resp.ok) {
      showInlineError(j.error || "Analysis failed");
    } else {
      renderResults(j);
    }
  } catch (e) {
    showInlineError("Network or server error. Try again later.");
  } finally {
    setAnalyzing(false);
  }
}
