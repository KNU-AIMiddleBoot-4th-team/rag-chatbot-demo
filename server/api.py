from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from starlette.routing import Route

from server.service import generate_answer


def _validate_history(history):
    if history is None:
        return []
    if not isinstance(history, list):
        raise ValueError("history must be a list.")

    validated_history = []
    for message in history:
        if not isinstance(message, dict):
            raise ValueError("history items must be objects.")

        role = message.get("role", "")
        content = message.get("content", "")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            raise ValueError(
                "history items must have role=user|assistant and string content."
            )

        validated_history.append({"role": role, "content": content})

    return validated_history


async def health(request):
    return JSONResponse({"status": "ok"})


async def answer(request):
    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse({"error": "Invalid JSON body."}, status_code=400)

    question = payload.get("question", "")
    context = payload.get("context", "")
    history = payload.get("history", [])

    if not isinstance(question, str) or not isinstance(context, str):
        return JSONResponse(
            {"error": "question and context must be strings."},
            status_code=400,
        )

    try:
        validated_history = _validate_history(history)
        result = await run_in_threadpool(
            generate_answer, question, context, validated_history
        )
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception:
        return JSONResponse(
            {"error": "답변 생성 중 오류가 발생했습니다."},
            status_code=502,
        )

    return JSONResponse({"answer": result})


app = Starlette(
    debug=False,
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/answer", answer, methods=["POST"]),
    ],
)
