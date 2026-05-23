import base64
import logging
import os
import random

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Pawspective API")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8010",
        "http://127.0.0.1:8010",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DOG_REVIEW_PROMPT = """
你是一只正在玩《地球Online | 小狗服》的冒险小狗。请根据这张照片的内容，写一段 30 字以内的“游戏实机评测”。
要求：语气要幽默、充满狗子的网感视角（比如提到闻味道、拆家、户外狂奔、或者NPC人类等）。
最后，请在文本的最后一行严格以该格式输出评分：[RATING:X]，其中 X 必须是 4 或 5 的随机一个数字。
""".strip()

MOCK_REVIEWS = [
    "好评！今日草地副本味道爆炸，NPC人类牵引绳略烦。\n[RATING:5]",
    "室内地图可玩性高，拖鞋掉落率优秀，拆家流狂喜。\n[RATING:4]",
    "这局风很香，跑图顺滑，就是人类拍照打断连招。\n[RATING:5]",
    "发现神秘食盆区域，闻味系统满分，建议加肉干DLC。\n[RATING:5]",
]


def parse_ai_text(raw_text: str) -> tuple[str, int]:
    text = (raw_text or "").strip()
    rating = 5

    marker = "[RATING:"
    marker_index = text.rfind(marker)

    if marker_index != -1:
        rating_start = marker_index + len(marker)
        rating_end = text.find("]", rating_start)
        rating_text = text[rating_start:rating_end].strip() if rating_end != -1 else ""

        if rating_text in {"4", "5"}:
            rating = int(rating_text)

        review = text[:marker_index].strip()
    else:
        review = text

    return review or "好评！今天大世界味道很足，小狗玩家强烈推荐。", rating


def fallback_response() -> dict:
    review, rating = parse_ai_text(random.choice(MOCK_REVIEWS))

    return {
        "success": True,
        "review": review,
        "rating": rating,
        "exp_gained": 35,
        "model_type": "随机抽象",
    }


def generate_with_gemini(image_bytes: bytes, mime_type: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_PLACEHOLDER"))
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[DOG_REVIEW_PROMPT, image_part],
    )

    return response.text or ""


def generate_with_qwen(image_bytes: bytes, mime_type: str) -> str:
    api_key = os.getenv("QWEN_API_KEY", "YOUR_QWEN_API_KEY_PLACEHOLDER")
    if not api_key:
        raise RuntimeError("QWEN_API_KEY is not configured")

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": DOG_REVIEW_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_base64}",
                    },
                },
            ],
        }
    ]

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        response = client.chat.completions.create(
            model="qwen3.6-flash",
            messages=messages,
            extra_body={"enable_thinking": True},
        )

        return response.choices[0].message.content or ""
    except ImportError:
        import openai

        logger.warning("Using legacy openai SDK compatibility path; upgrade openai for full extra_body support.")
        openai.api_key = api_key
        openai.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        response = openai.ChatCompletion.create(
            model="qwen3.6-flash",
            messages=messages,
            request_timeout=60,
        )

        return response["choices"][0]["message"]["content"] or ""


@app.post("/api/upload-dog-pic")
async def upload_dog_pic(
    file: UploadFile = File(...),
    model_type: str = Form("随机抽象"),
):
    try:
        image_bytes = await file.read()
        mime_type = file.content_type or "image/jpeg"

        if model_type == "Gemini":
            ai_text = generate_with_gemini(image_bytes, mime_type)
            actual_model_type = "Gemini"
        elif model_type == "Qwen":
            ai_text = generate_with_qwen(image_bytes, mime_type)
            actual_model_type = "Qwen"
        else:
            ai_text = random.choice(MOCK_REVIEWS)
            actual_model_type = "随机抽象"

        review, rating = parse_ai_text(ai_text)

        return {
            "success": True,
            "review": review,
            "rating": rating,
            "exp_gained": 35,
            "model_type": actual_model_type,
        }
    except Exception as error:
        logger.exception("AI review fallback triggered for model_type=%s: %s", model_type, error)
        return fallback_response()
