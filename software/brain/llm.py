"""Parviz LLM backends: one ask() interface, many brains.

Backend spec strings (PARVIZ_LLM):
  host:port          local llama-server (OpenAI-compatible, grammar via
                     json_schema response_format, KV prompt cache)
  claude-live:[m]    KEPT-OPEN Claude Code CLI session (stream-json);
                     fastest, subscription auth, the model sees its own
                     recent ticks. Default model sonnet.
  claude:[m]         one-shot `claude -p` per call (cold ~8 s)
  grok:[m]           one-shot GrokBuild CLI (default grok-composer-2.5-fast)
  https://base       remote OpenAI-compatible API (+ XAI_API_KEY /
                     PARVIZ_LLM_KEY), default model grok-4.1-fast

A comma-separated spec is a FAILOVER CHAIN for ask_chain(): backends are
tried in order; one that fails is skipped for BREAKER_S seconds (so a
dead wifi doesn't cost a cloud timeout every tick) and re-probed after.
The natural robot config is  claude-live:,127.0.0.1:8081  -- cloud when
the network is up, the local model otherwise.

stdlib only, runs on the Pi as-is.
"""

import json
import os
import queue
import subprocess
import threading
import time
import urllib.error
import urllib.request

BREAKER_S = float(os.environ.get("PARVIZ_LLM_BREAKER_S", 90.0))
# Cloud backends get a short leash so the chain still has time to fall
# back to local within the brain's tick budget.
CLOUD_TIMEOUT = float(os.environ.get("PARVIZ_CLOUD_TIMEOUT", 25.0))

_BREAKER = {}   # backend spec -> unix time until which it is skipped


def _cli_system_prompt(sys_p, shots):
    """System prompt + few-shots folded in (CLIs take one user prompt)."""
    shot_text = "".join(
        f"\n\nExample digest:\n{m['content']}" if m["role"] == "user"
        else f"\nExample answer: {m['content']}" for m in shots)
    return sys_p + shot_text + (
        "\n\nAnswer with ONLY the JSON object, nothing else. "
        "Do not use tools.")


def _claude_bin():
    return os.environ.get("CLAUDE_BIN") or (
        os.path.expanduser("~/.local/bin/claude")
        if os.path.exists(os.path.expanduser("~/.local/bin/claude"))
        else "claude")


def _parse_result_text(res, text_key):
    if res.get("is_error"):
        # Bad model, dead network, auth trouble: a BACKEND failure (the
        # chain should fall over), not a bad tick.
        raise RuntimeError(f"claude error: {str(res.get(text_key))[:200]}")
    parsed = res.get("structured_output")
    if parsed is None:
        try:
            parsed = json.loads(res.get(text_key) or "")
        except (json.JSONDecodeError, TypeError):
            parsed = {"raw": str(res.get(text_key))[:300]}
    ok = (isinstance(parsed, dict)
          and isinstance(parsed.get("actions"), list))
    return parsed, ok


def ask_local(host, sys_p, shots, schema, digest, temperature, timeout):
    """Local llama-server (or any OpenAI-compatible http endpoint)."""
    body = {
        "messages": [
            {"role": "system", "content": sys_p},
            *shots,
            {"role": "user", "content": digest},
        ],
        "temperature": temperature,
        "max_tokens": 120,
        # llama-server keeps the constant system+few-shot prefix in KV
        # cache across requests: prefill drops from ~1400 tokens (~7 s on
        # the Pi) to just the changing digest (~1 s).
        "cache_prompt": True,
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "parviz_actions",
                                            "schema": schema}},
        # Qwen3: kill the thinking pass at the template level; a /no_think
        # string clashes with grammar-constrained decoding (empty replies).
        "chat_template_kwargs": {"enable_thinking": False},
    }
    headers = {"Content-Type": "application/json"}
    if "://" in host:
        # Remote OpenAI-compatible API: named model, no llama-only
        # fields, roomier max_tokens (a reasoning model bills thinking
        # as output and would truncate at 120).
        url = f"{host.rstrip('/')}/v1/chat/completions"
        body["model"] = os.environ.get("PARVIZ_LLM_MODEL", "grok-4.1-fast")
        body["max_tokens"] = 512
        del body["cache_prompt"]
        del body["chat_template_kwargs"]
        key = (os.environ.get("PARVIZ_LLM_KEY")
               or os.environ.get("XAI_API_KEY"))
        if key:
            headers["Authorization"] = f"Bearer {key}"
    else:
        url = f"http://{host}/v1/chat/completions"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers=headers)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        # Surface the API's error body (schema rejects, bad key, quota);
        # the bare HTTPError hides it and made remote failures opaque.
        detail = e.read(500).decode(errors="replace")
        raise RuntimeError(f"LLM HTTP {e.code}: {detail}") from None
    dt = time.time() - t0
    usage = out.get("usage") or {}
    if out.get("timings"):
        usage["timings"] = out["timings"]
    txt = out["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(txt)
        ok = isinstance(parsed.get("actions"), list)
    except (json.JSONDecodeError, AttributeError):
        parsed, ok = {"raw": txt}, False
    return parsed, ok, dt, usage


def ask_grok_cli(model, sys_p, shots, schema, digest, timeout):
    """One-shot GrokBuild CLI (subscription auth, no API key).

    --json-schema constrains the reply like the llama-server grammar;
    tools/memory/subagents disabled make it a pure completion.
    grok-composer-2.5-fast honors the schema reliably; grok-build often
    returns structuredOutputError, hence the default.
    """
    grok_bin = os.environ.get(
        "GROK_BIN", os.path.expanduser("~/.grok/bin/grok"))
    t0 = time.time()
    r = subprocess.run(
        [grok_bin, "-p", digest, "--verbatim",
         "--json-schema", json.dumps(schema),
         "--system-prompt-override", _cli_system_prompt(sys_p, shots),
         "--tools", "", "--max-turns", "2", "--no-subagents",
         "--no-memory", "--disable-web-search", "-m", model],
        capture_output=True, text=True, timeout=timeout)
    dt = time.time() - t0
    if r.returncode != 0:
        err = (r.stderr or r.stdout)[:300]
        if "max turns" in err:
            # Flaky: the model occasionally burns its turns without a
            # final answer. A bad tick, not a dead backend; don't crash.
            return {"raw": err}, False, dt, {}
        raise RuntimeError(f"grok cli rc={r.returncode}: {err}")
    out = json.loads(r.stdout)
    parsed = out.get("structuredOutput")
    if parsed is None:
        try:
            parsed = json.loads(out.get("text") or "")
        except (json.JSONDecodeError, TypeError):
            parsed = {"raw": out.get("structuredOutputError")
                      or (out.get("text") or "")[:300]}
    ok = (isinstance(parsed, dict)
          and isinstance(parsed.get("actions"), list))
    return parsed, ok, dt, {}


def ask_claude_cli(model, sys_p, shots, schema, digest, timeout):
    """One-shot `claude -p` (subscription auth, no key).

    --json-schema gives real structured output; --tools "" and
    --strict-mcp-config strip tools and the MCP plugin bootstrap (which
    otherwise adds seconds); --no-session-persistence avoids a session
    dir per tick.
    """
    t0 = time.time()
    r = subprocess.run(
        [_claude_bin(), "-p", digest,
         "--json-schema", json.dumps(schema),
         "--system-prompt", _cli_system_prompt(sys_p, shots),
         "--tools", "", "--output-format", "json", "--model", model,
         "--no-session-persistence", "--strict-mcp-config"],
        capture_output=True, text=True, timeout=timeout)
    dt = time.time() - t0
    if r.returncode != 0:
        raise RuntimeError(f"claude cli rc={r.returncode}: "
                           f"{(r.stderr or r.stdout)[:300]}")
    out = json.loads(r.stdout)
    res = out[-1] if isinstance(out, list) else out
    parsed, ok = _parse_result_text(res, "result")
    return parsed, ok, dt, {}


class _ClaudeSession:
    """Persistent `claude -p --input-format stream-json` process.

    One process serves many ticks: no per-call CLI bootstrap and the
    prompt cache stays warm, so a turn costs ~2-4 s instead of ~8 s
    cold. The conversation accumulates (the model sees its own recent
    ticks, which doubles as short-term memory) and is recycled every
    RECYCLE_TURNS to cap context growth. Any error kills the process;
    the next tick respawns it.
    """

    RECYCLE_TURNS = 100

    def __init__(self, model, sys_prompt, schema):
        self.model, self.sys_prompt, self.schema = model, sys_prompt, schema
        self.proc, self.queue, self.turns = None, None, 0

    def _spawn(self):
        self.proc = subprocess.Popen(
            [_claude_bin(), "-p", "--input-format", "stream-json",
             "--output-format", "stream-json", "--verbose",
             "--json-schema", json.dumps(self.schema),
             "--system-prompt", self.sys_prompt,
             "--tools", "", "--model", self.model,
             "--no-session-persistence", "--strict-mcp-config"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.queue = queue.Queue()
        threading.Thread(target=self._pump, args=(self.proc, self.queue),
                         daemon=True).start()
        self.turns = 0

    @staticmethod
    def _pump(proc, q):
        for line in proc.stdout:
            q.put(line)
        q.put(None)

    def close(self):
        if self.proc is not None:
            try:
                self.proc.kill()
            except OSError:
                pass
        self.proc = None

    def ask(self, digest, timeout):
        if (self.proc is None or self.proc.poll() is not None
                or self.turns >= self.RECYCLE_TURNS):
            self.close()
            self._spawn()
        try:
            self.proc.stdin.write(json.dumps(
                {"type": "user", "message": {"role": "user", "content":
                 [{"type": "text", "text": digest}]}}) + "\n")
            self.proc.stdin.flush()
            deadline = time.time() + timeout
            while True:
                try:
                    line = self.queue.get(
                        timeout=max(0.1, deadline - time.time()))
                except queue.Empty:
                    raise RuntimeError("claude session timeout") from None
                if line is None:
                    raise RuntimeError("claude session died")
                ev = json.loads(line)
                if ev.get("type") == "result":
                    self.turns += 1
                    return ev
        except Exception:
            self.close()
            raise


_CLAUDE_SESSIONS = {}


def ask_claude_live(model, sys_p, shots, schema, digest, timeout):
    """Tier-2 through a KEPT-OPEN Claude Code CLI session (see above)."""
    if model not in _CLAUDE_SESSIONS:
        _CLAUDE_SESSIONS[model] = _ClaudeSession(
            model, _cli_system_prompt(sys_p, shots), schema)
    t0 = time.time()
    res = _CLAUDE_SESSIONS[model].ask(digest, timeout)
    dt = time.time() - t0
    parsed, ok = _parse_result_text(res, "result")
    return parsed, ok, dt, {}


def ask(spec, digest, sys_p, shots, schema, temperature=0.2, timeout=120):
    """Route one request to the single backend named by spec."""
    if spec.startswith("grok:"):
        return ask_grok_cli(spec[5:] or "grok-composer-2.5-fast",
                            sys_p, shots, schema, digest, timeout)
    if spec.startswith("claude-live:"):
        return ask_claude_live(spec[12:] or "sonnet",
                               sys_p, shots, schema, digest, timeout)
    if spec.startswith("claude:"):
        return ask_claude_cli(spec[7:] or "sonnet",
                              sys_p, shots, schema, digest, timeout)
    return ask_local(spec, sys_p, shots, schema, digest, temperature,
                     timeout)


def broken():
    """Backend specs currently circuit-broken (chains skip them)."""
    now = time.time()
    return [s for s, t in _BREAKER.items() if t > now]


def _is_cloud(spec):
    return not (spec.startswith("127.") or spec.startswith("localhost"))


def ask_chain(chain, digest, sys_p, shots, schema, temperature=0.2,
              timeout=120):
    """Try each backend in the comma-separated chain; circuit-break
    failures. Returns (parsed, ok, dt, usage, backend, note): note
    carries failover detail for the journal, backend is the spec that
    answered. Raises only if every backend fails.
    """
    specs = [s.strip() for s in chain.split(",") if s.strip()]
    now = time.time()
    live = [s for s in specs if _BREAKER.get(s, 0) <= now]
    errors = []
    for spec in (live or specs):    # all broken: probe them anyway
        try:
            to = min(timeout, CLOUD_TIMEOUT) if (
                _is_cloud(spec) and len(specs) > 1) else timeout
            parsed, ok, dt, usage = ask(spec, digest, sys_p, shots,
                                        schema, temperature, to)
            _BREAKER.pop(spec, None)
            note = ("; ".join(errors)) if errors else ""
            return parsed, ok, dt, usage, spec, note
        except Exception as e:
            _BREAKER[spec] = time.time() + BREAKER_S
            errors.append(f"{spec} failed: {str(e)[:120]}")
    raise RuntimeError(" | ".join(errors))
