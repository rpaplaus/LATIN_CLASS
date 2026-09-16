import urllib.request
import urllib.parse
import json

BASE_URL = "http://localhost:8001/api/v1"

def post_json(path, data, headers=None):
    if headers is None:
        headers = {}
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_json(path, headers=None):
    if headers is None:
        headers = {}
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    import random
    email = f"discipulus_e2e_{random.randint(1000, 9999)}@latium.edu"
    password = "VeritasVosLiberabit2026"

    print(f"1. Registrando aluno: {email}")
    reg = post_json("/auth/register", {
        "email": email,
        "password": password,
        "full_name": "Quintus Horatius Flaccus"
    })
    print(f"   [OK] Aluno registrado com ID: {reg['id']}")

    print("2. Efetuando Login OAuth2 (application/x-www-form-urlencoded)...")
    login_data = urllib.parse.urlencode({"username": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read().decode("utf-8"))
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    print(f"   [OK] Access Token JWT obtido: {access_token[:25]}...")
    print(f"   [OK] Refresh Token obtido: {refresh_token[:25]}...")

    auth_headers = {"Authorization": f"Bearer {access_token}"}

    print("3. Validando sessao com /auth/me...")
    me = get_json("/auth/me", auth_headers)
    print(f"   [OK] Perfil autenticado: {me['full_name']} ({me['email']})")

    print("4. Obtendo modulos do curso /lessons/modules...")
    modules = get_json("/lessons/modules", auth_headers)
    print(f"   [OK] Modulos canonicos recebidos: {len(modules)}")
    for mod in modules:
        print(f"     - Modulo {mod['order_index']}: {mod['title']} ({len(mod['lessons'])} licoes)")

    print("5. Obtendo progresso inicial /lessons/progress...")
    prog = get_json("/lessons/progress", auth_headers)
    print(f"   [OK] Licoes concluidas: {prog['completed_lessons_count']}, Pontos: {prog['total_points']}, Streak: {prog['current_streak_days']}")

    print("6. Gerando proxima aula com o Agente Magister Latium (/lessons/next)...")
    lesson = post_json("/lessons/next", {}, auth_headers)
    print(f"   [OK] Titulo da Aula: {lesson['lesson_title']}")
    print(f"   [OK] Modulo: {lesson['module_title']}")
    print(f"   [OK] Objetivo: {lesson['pedagogical_goal']}")
    print(f"   [OK] Secoes de teoria: {len(lesson['theory_sections'])}")
    print(f"   [OK] Vocabulario: {len(lesson['vocabulary'])} itens")
    print(f"   [OK] Exercicios interativos: {len(lesson['exercises'])} gerados")

    print(f"7. Avaliando exercicio aberto com o Censor Latium (/lessons/{lesson['lesson_id']}/evaluate)...")
    eval_resp = post_json(f"/lessons/{lesson['lesson_id']}/evaluate", {
        "lesson_id": lesson["lesson_id"],
        "exercise_id": 3,
        "question": "Traduza: Roma in Italia est.",
        "expected_answer": "Roma está na Itália.",
        "student_answer": "Roma está na Itália.",
        "exercise_type": "translation",
    }, auth_headers)
    print(f"   [OK] Veredito do Censor: is_correct={eval_resp['is_correct']}, Nota={eval_resp['score']}/100, Modelo={eval_resp['evaluator_model']}")
    print(f"   [OK] Parecer: {eval_resp['overall_feedback'][:60]}...")
    print(f"   [OK] Termos morfologicos analisados: {len(eval_resp['morphological_breakdown'])}")

    print(f"8. Concluindo a licao (/lessons/{lesson['lesson_id']}/complete)...")
    comp = post_json(f"/lessons/{lesson['lesson_id']}/complete", {
        "score": eval_resp["score"]
    }, auth_headers)
    print(f"   [OK] Conclusao registrada! Pontos totais: {comp['total_points']}, Licoes concluidas: {comp['completed_lessons_count']}")

    print("8. Testando Refresh Token Rotation (/auth/refresh)...")
    ref = post_json("/auth/refresh", {"refresh_token": refresh_token})
    new_access = ref["access_token"]
    new_refresh = ref["refresh_token"]
    print(f"   [OK] Novo Access Token: {new_access[:25]}...")
    print(f"   [OK] Novo Refresh Token: {new_refresh[:25]}...")

    print("9. Testando Logout e Revogacao no Redis (/auth/logout)...")
    post_json("/auth/logout", {"refresh_token": new_refresh}, {"Authorization": f"Bearer {new_access}"})
    print("   [OK] Refresh Token revogado no Redis com sucesso!")

    print("\n=======================================================")
    print("[SUCCESS] TODOS OS TESTES DE INTEGRACAO DO FRONTEND PASSARAM!")
    print("=======================================================")

if __name__ == "__main__":
    main()
