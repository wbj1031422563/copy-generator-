"""OpenAI-compatible LLM clients (OpenAI, DeepSeek, Qwen, etc.).

Usage:
    client = OpenAICompat(api_key="...", base_url="https://api.deepseek.com/v1", model="deepseek-chat")
    client = OpenAICompat(api_key="...", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", model="qwen-plus")
"""

from llm.base import BaseLLM


class OpenAICompat(BaseLLM):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def complete(self, prompt: str, **kwargs) -> str:
        system = kwargs.get(
            "system",
            "你是一个专业的学术辅导文案写手，输出格式严格遵循用户要求。",
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            resp = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1200),
            )
            return resp.choices[0].message.content or ""
        except ImportError:
            return self._fallback_http(prompt, system=system, **kwargs)

    def _fallback_http(self, prompt: str, **kwargs) -> str:
        import json
        from urllib.request import Request, urlopen

        system = kwargs.get(
            "system",
            "你是一个专业的学术辅导文案写手，输出格式严格遵循用户要求。",
        )
        body = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1200),
        }).encode()

        req = Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        resp = urlopen(req, timeout=30)
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"] or ""
