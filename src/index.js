import { DurableObject } from "cloudflare:workers";

const PORT = 8080;
const INACTIVITY_TIMEOUT_MS = 5 * 60 * 1000;

export class AcquisitionContainer extends DurableObject {
  starting;

  constructor(ctx, env) {
    super(ctx, env);
    if (ctx.container?.running) {
      void ctx.blockConcurrencyWhile(() =>
        ctx.container.setInactivityTimeout(INACTIVITY_TIMEOUT_MS),
      );
    }
  }

  async fetch(request) {
    this.starting ??= this.startAndWaitForPort().finally(() => {
      this.starting = undefined;
    });
    await this.starting;

    const url = new URL(request.url);
    const originalHost = request.headers.get("host") || url.host;
    url.protocol = "http:";
    url.host = "container";
    const headers = new Headers(request.headers);
    headers.delete("host");
    headers.set("x-forwarded-host", originalHost);
    headers.set("x-forwarded-proto", new URL(request.url).protocol.replace(":", ""));
    const forwarded = new Request(url, { method: request.method, headers, body: request.body, redirect: "manual" });
    return this.ctx.container.getTcpPort(PORT).fetch(forwarded);
  }

  async startAndWaitForPort() {
    const container = this.ctx.container;
    if (!container.running) {
      container.start({
        image: container.images.base,
        instance: "basic",
        enableInternet: true,
        env: {
          DJANGO_SECRET_KEY: this.env.DJANGO_SECRET_KEY,
          DJANGO_ALLOWED_HOSTS: this.env.DJANGO_ALLOWED_HOSTS || "container,localhost",
          DJANGO_CSRF_TRUSTED_ORIGINS: this.env.DJANGO_CSRF_TRUSTED_ORIGINS || "",
          OPENOUTFIND_BETTERCONTACT_API_KEY: this.env.OPENOUTFIND_BETTERCONTACT_API_KEY || "",
          OPENOUTFIND_AI_MODEL: this.env.OPENOUTFIND_AI_MODEL || "",
          OPENOUTFIND_LLM_API_KEY: this.env.OPENOUTFIND_LLM_API_KEY || "",
          OPENOUTFIND_LLM_API_BASE: this.env.OPENOUTFIND_LLM_API_BASE || "",
          R2_ACCOUNT_ID: this.env.R2_ACCOUNT_ID || "",
          R2_ACCESS_KEY_ID: this.env.R2_ACCESS_KEY_ID || "",
          R2_SECRET_ACCESS_KEY: this.env.R2_SECRET_ACCESS_KEY || "",
          R2_BUCKET_NAME: this.env.R2_BUCKET_NAME || "",
          R2_STATE_OBJECT_KEY: this.env.R2_STATE_OBJECT_KEY || "acquisition-agent/state.tar.gz",
        },
      });
    }
    await container.setInactivityTimeout(INACTIVITY_TIMEOUT_MS);
    const port = container.getTcpPort(PORT);
    for (let attempt = 0; attempt < 120; attempt++) {
      try {
        const response = await port.fetch("http://container/health/");
        await response.body?.cancel();
        if (response.ok) return;
      } catch {
        // Container process may still be starting.
      }
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
    throw new Error("Acquisition Agent container did not become ready on port 8080");
  }
}

export default {
  async fetch(request, env) {
    const id = env.ACQUISITION_CONTAINER.idFromName("acquisition-agent-singleton");
    return env.ACQUISITION_CONTAINER.get(id).fetch(request);
  },
};
