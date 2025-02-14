import os
from flask import Flask, request, render_template_string
import google.generativeai as genai

# api_key.txt 파일에서 API 키를 읽어 환경 변수에 설정합니다.
try:
    with open("api_key.txt", "r") as f:
        api_key = f.read().strip()
    os.environ["GEMINI_API_KEY"] = api_key
except FileNotFoundError:
    print("api_key.txt 파일이 없습니다. API 키를 설정해주세요.")

# 환경변수에서 Gemini API 키를 가져와 구성합니다.
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    # 사용 가능한 모델 목록을 가져옵니다.
    models = list(genai.list_models())
    model_names = [model.name for model in models]

    if request.method == "POST":
        # 사용자가 입력한 코드를 문자열로 받습니다.
        code_input = request.form.get("code", "")

        # 사용자가 선택한 모델을 가져옵니다.
        selected_model = request.form.get("model", "gemini-2.0-pro-exp-02-05")

        # 선택한 모델로 GenerativeModel 인스턴스를 생성합니다.
        model = genai.GenerativeModel(
            model_name=selected_model,
            generation_config={
                "temperature": 0.7,  # 창의성 (0.0~1.0)
                "top_p": 0.95,  # 후보 검색 범위
                "max_output_tokens": 8192  # 최대 출력 길이
            }
        )

        # 5단계 추론 과정을 위한 프롬프트를 단계별로 작성합니다.
        prompt_step1 = (
            "1단계: 코드 구조 분석 - 입력된 코드를 분석하여, 함수, 클래스, 조건문, 반복문 등 주요 구문으로 분해합니다.\n"
            "코드 구조 분석 결과: [여기에 분석 결과가 포함될 것임]"
        )

        prompt_step2 = (
            "2단계: 각 구성 요소의 역할 및 작동 방식 상세 설명 - 함수의 인자, 반환값, 클래스의 상속, 조건문의 분기 등 "
            "각 요소가 수행하는 역할과 작동 방식을 상세하게 기술합니다.\n"
            "상세 설명 결과: [여기에 상세 설명이 포함될 것임]"
        )

        prompt_step3 = (
            "3단계: 기술적 비유 적용 - 30대 전문 컴퓨터 혹은 모바일 사용자가 공감할 수 있도록(윈도우, 엑셀, 인터넷 등), "
            "디버깅, API 호출, 데이터 흐름, 버전 관리 등 실제 업무 경험에 기반한 비유를 적용합니다.\n"
            "비유 적용 결과: [여기에 기술적 비유가 포함될 것임]"
        )

        prompt_step4 = (
            "4단계: 코드 문맥 및 흐름 정리 - 코드의 전체 문맥과 계층적 흐름을 일관성 있게 정리하여, "
            "각 부분이 전체 시스템에서 어떤 역할을 하는지 명확하게 연결합니다.\n"
            "문맥 정리 결과: [여기에 문맥 정리 내용이 포함될 것임]"
        )

        prompt_step5 = (
            "5단계: 최종 종합 - 앞의 4단계 결과를 종합하여, 초보자도 쉽게 이해할 수 있는 자연어 설명을 생성합니다.\n"
            "최종 자연어 설명:\n"
            "처리된 자연어를 코드파일처럼 출력해줘\n"
            "라이브러리 불러오기 및 앱 실행 등 모든 코드 파일의 문단구조를 유지해줘\n"
            "들여쓰기를 코드 파일 처럼 그대로 적용해서 출력해줘"
        )

        # 5단계 추론 프롬프트를 하나로 결합합니다.
        final_prompt = (
            # prompt_step1 + "\n\n" +
            # prompt_step2 + "\n\n" +
            # prompt_step3 + "\n\n" +
            # prompt_step4 + "\n\n" +
            prompt_step5 + "\n\n" +
            "입력 코드:\n" + code_input
        )

        app.logger.info("5단계 추론 프롬프트 생성 완료")

        # Gemini API를 호출하여 프롬프트에 따른 자연어 설명을 생성합니다.
        output_text = ""
        try:
            for i, prompt in enumerate([prompt_step1, prompt_step2, prompt_step3, prompt_step4, prompt_step5]):
                app.logger.info(f"{i+1}단계 Gemini API 호출 시작")
                response = model.generate_content(
                    prompt + "\n\n입력 코드:\n" + code_input,
                    stream=False  # 스트리밍 미사용
                )
                app.logger.info(f"{i+1}단계 Gemini API 호출 완료")

                # 새 응답 포맷 처리
                if response.candidates:
                    output_text += f"{i+1}단계 결과:\n```\n" + response.candidates[0].content.parts[0].text + "\n```\n\n"
                else:
                    output_text += f"{i+1}단계: 유효한 응답을 받지 못했습니다\n\n"
                    app.logger.warning(f"{i+1}단계: 유효한 응답을 받지 못함")

        except Exception as e:
            output_text = f"API 오류 발생: {str(e)}"
            app.logger.error(f"API 오류 발생: {str(e)}")

        return render_template_string('''
            <!doctype html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>자연어 코드 설명 생성기</title>
                <style>
                    body { font-family: '나눔고딕', sans-serif; margin: 20px; }
                    textarea { width: 100%; height: 300px; }
                    pre { background: #f4f4f4; padding: 10px; white-space: pre-wrap;}
                </style>
            </head>
            <body>
                <h1>자연어 코드 설명 생성기</h1>
                <form method="post">
                    <label for="model">모델 선택:</label>
                    <select name="model" id="model">
                        {% for model_name in model_names %}
                            <option value="{{ model_name }}" {% if model_name == selected_model %}selected{% endif %}>{{ model_name }}</option>
                        {% endfor %}
                    </select><br><br>
                    <textarea name="code" placeholder="코드를 입력하세요...">{{ code_input }}</textarea><br>
                    <input type="submit" value="설명 생성">
                </form>
                <h2>생성된 자연어 설명:</h2>
                <pre><code>{{ output_text }}</code></pre>
            </body>
            </html>
        ''', code_input=code_input, output_text=output_text, models=models, model_names=model_names, selected_model=selected_model)

    # GET 요청 시, 코드 입력 폼 및 모델 선택 드롭다운을 표시합니다.
    return render_template_string('''
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>자연어 코드 설명 생성기</title>
            <style>
                body { font-family: '나눔고딕', sans-serif; margin: 20px; }
                textarea { width: 100%; height: 300px; }
                pre { background: #f4f4f4; padding: 10px; white-space: pre-wrap;}
            </style>
        </head>
        <body>
            <h1>자연어 코드 설명 생성기</h1>
            <form method="post">
                <label for="model">모델 선택:</label>
                <select name="model" id="model">
                    {% for model_name in model_names %}
                        <option value="{{ model_name }}" {% if model_name == selected_model %}selected{% endif %}>{{ model_name }}</option>
                    {% endfor %}
                </select><br><br>
                <textarea name="code" placeholder="코드를 입력하세요...">{{ code_input }}</textarea><br>
                <input type="submit" value="설명 생성">
            </form>
            <h2>생성된 자연어 설명:</h2>
            <pre><code>{{ output_text }}</code></pre>
        </body>
        </html>
    ''', code_input="", output_text="", models=models, model_names=model_names, selected_model="gemini-2.0-pro-exp-02-05")

if __name__ == "__main__":
    app.run(debug=True)
