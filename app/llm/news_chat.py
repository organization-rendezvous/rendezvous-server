from app.graph.common.helpers import strip_code_block
import json
import logging
logger = logging.getLogger(__name__)


def classify_intent(client,user_message: str) -> tuple[str, str | None]:
    """
    LLM 기반 intent 분류 로직
    return: (intent, claim)
    """

    if client is None:
        logger.warning("OpenAI client is None — fallback to explore")
        return "explore", None

    prompt = f"""
        너는 뉴스 채팅 의도 분류 엔진이다.

        사용자 메시지: "{user_message}"

        아래 두 가지 중 하나로 분류하라.
        - explore : 최근 뉴스/트렌드를 알고 싶은 일반 질문
        - factcheck : 특정 소문/주장이 사실인지 확인하려는 질문

        출력 형식 (JSON):
        {{
          "intent": "explore" | "factcheck",
          "claim": "검증할 주장 (factcheck일 때만, 아니면 null)"
        }}
    """

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )

        content = res.choices[0].message.content or ""
        content = strip_code_block(content)
        parsed = json.loads(content)

        intent = parsed.get("intent", "explore")
        claim = parsed.get("claim")

        return intent, claim

    except Exception as e:
        logger.warning("intent classification failed: %s", e)
        return "explore", None


def explore(client, user_message: str, context: str) -> str:
    if client is None:
        return "현재 AI 서비스를 사용할 수 없습니다."

    prompt = f"""
                너는 최신 뉴스와 트렌드를 알려주는 AI 어시스턴트다.
                
                사용자 질문: {user_message}
                
                아래 뉴스/트렌드 자료를 참고해 자연스럽게 답변하라.
                자료가 부족해도 아는 범위 내에서 답변하라.
                
                참고 자료:
                {context}
            """
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        return res.choices[0].message.content or "답변을 생성할 수 없습니다."
    except Exception as e:
        logger.warning("explore 답변 생성 실패: %s", e)
        return "답변 생성 중 오류가 발생했습니다."



def factcheck(client, claim: str, evidence: list[dict]) -> tuple[str, str]:
    """판정 결과 (answer 텍스트, verdict 문자열) 반환."""
    if client is None:
        return "현재 AI 서비스를 사용할 수 없습니다.", "unclear"

    prompt = f"""
                너는 사실 검증 엔진이다.
                
                확인할 주장: {claim}
                
                아래는 관련 뉴스/문서 자료다:
                {json.dumps(evidence[:6], ensure_ascii=False)}
                
                위 자료를 근거로 주장이 사실인지 판단하라.
                자료가 부족해 판단할 수 없으면 "unclear"로 답하라.
                신뢰도 점수는 제공하지 말 것.
                
                출력 형식 (JSON):
                {{
                  "verdict": "true" | "false" | "unclear",
                  "reason": "판단 근거 한 문단 설명",
                  "used_evidence_index": [0, 1]
                }}
            """
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        content = res.choices[0].message.content or ""
        content = strip_code_block(content)
        parsed = json.loads(content)
        verdict = parsed.get("verdict", "unclear")
        reason = parsed.get("reason", "판단 근거를 확인할 수 없습니다.")
        return reason, verdict
    except Exception as e:
        logger.warning("factcheck 판정 실패: %s", e)
        return "사실 여부를 확인할 수 없습니다.", "unclear"