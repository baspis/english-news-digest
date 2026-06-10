export interface Env {
  AI: Ai;
  TTS_CACHE: R2Bucket;
  ALLOWED_ORIGINS: string;
  MAX_TEXT_CHARS: string;
}

const MODEL = "@cf/myshell-ai/melotts";
const DEFAULT_LANG = "en";

function parseAllowedOrigins(raw: string): string[] {
  return raw
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
}

function corsHeaders(request: Request, env: Env): Headers {
  const origin = request.headers.get("Origin") ?? "";
  const allowed = parseAllowedOrigins(env.ALLOWED_ORIGINS);
  const headers = new Headers({
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    Vary: "Origin",
  });
  if (origin && allowed.includes(origin)) {
    headers.set("Access-Control-Allow-Origin", origin);
  }
  return headers;
}

function withCors(request: Request, env: Env, response: Response): Response {
  const headers = new Headers(response.headers);
  for (const [key, value] of corsHeaders(request, env)) {
    headers.set(key, value);
  }
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

function json(
  request: Request,
  env: Env,
  body: unknown,
  status = 200,
): Response {
  return withCors(
    request,
    env,
    new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json; charset=utf-8" },
    }),
  );
}

function normalizeText(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

async function cacheKey(text: string, lang: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(`${MODEL}:${lang}:${text}`),
  );
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function maxTextChars(env: Env): number {
  const parsed = Number.parseInt(env.MAX_TEXT_CHARS || "500", 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 500;
}

async function synthesize(env: Env, text: string, lang: string): Promise<Uint8Array> {
  const result = (await env.AI.run(MODEL, {
    prompt: text,
    lang,
  })) as { audio?: string } | string;

  const audioBase64 = typeof result === "string" ? result : result.audio;
  if (!audioBase64) {
    throw new Error("melotts returned no audio");
  }

  const binary = atob(audioBase64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function handleTts(request: Request, env: Env): Promise<Response> {
  let text = "";
  let lang = DEFAULT_LANG;

  if (request.method === "GET") {
    const url = new URL(request.url);
    text = url.searchParams.get("text") ?? "";
    lang = url.searchParams.get("lang") ?? DEFAULT_LANG;
  } else {
    const payload = (await request.json()) as { text?: string; lang?: string };
    text = payload.text ?? "";
    lang = payload.lang ?? DEFAULT_LANG;
  }

  const normalized = normalizeText(text);
  if (!normalized) {
    return json(request, env, { error: "text is required" }, 400);
  }

  const limit = maxTextChars(env);
  const clipped = normalized.length > limit ? normalized.slice(0, limit) : normalized;
  const key = `${await cacheKey(clipped, lang)}.mp3`;

  const cached = await env.TTS_CACHE.get(key);
  if (cached) {
    return withCors(
      request,
      env,
      new Response(cached.body, {
        headers: {
          "Content-Type": "audio/mpeg",
          "Cache-Control": "public, max-age=31536000, immutable",
          "X-TTS-Cache": "hit",
        },
      }),
    );
  }

  const audio = await synthesize(env, clipped, lang);
  await env.TTS_CACHE.put(key, audio, {
    httpMetadata: { contentType: "audio/mpeg" },
  });

  return withCors(
    request,
    env,
    new Response(audio, {
      headers: {
        "Content-Type": "audio/mpeg",
        "Cache-Control": "public, max-age=31536000, immutable",
        "X-TTS-Cache": "miss",
      },
    }),
  );
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return withCors(request, env, new Response(null, { status: 204 }));
    }

    if (url.pathname === "/api/tts" && (request.method === "POST" || request.method === "GET")) {
      try {
        return await handleTts(request, env);
      } catch (error) {
        const message = error instanceof Error ? error.message : "tts failed";
        return json(request, env, { error: message }, 500);
      }
    }

    if (url.pathname === "/" || url.pathname === "/health") {
      return json(request, env, { ok: true, model: MODEL });
    }

    return json(request, env, { error: "not found" }, 404);
  },
} satisfies ExportedHandler<Env>;
