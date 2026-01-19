import json
from pathlib import Path
from function_display import (
    display_project_structure,
    display_file_functions,
    display_function_calls,
    select_file_interactive,
    select_function_interactive
)


def load_data():
    file_path = Path(__file__).parent / "judgments.json"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def display_judgment_list(judgments):
    print("\n판단 카테고리")
    print("=" * 70)
    for key, judgment in judgments.items():
        print(f"{key}: {judgment['name']}")
    print("0: 종료")
    print("S: 프로젝트 구조 보기 (Structure)")
    print("F: 파일 함수 보기 (File Functions)")
    print("C: 함수 호출 관계 보기 (Call Graph)")
    print("=" * 70)


def display_information_detail(info_id, information):
    info = information.get(info_id)
    if not info:
        return
    
    print(f"\n  [{info['type'].upper()}] {info['label']}")
    print(f"  {info['description']}")
    
    if info['type'] == 'user_note':
        print(f"  예시: {info.get('example', 'N/A')}")
    elif info['type'] == 'code':
        print(f"  출처: {info.get('source', 'N/A')}")
        print(f"  상태: 아직 구현되지 않음")
    elif info['type'] == 'knowledge':
        if 'content' in info:
            print("  사용 가능한 옵션:")
            for category, items in info['content'].items():
                print(f"    {category}: {', '.join(items)}")


def display_judgment_info(judgment_id, data):
    judgments = data['judgments']
    information = data['information']
    
    judgment = judgments.get(judgment_id)
    if not judgment:
        print("\n잘못된 선택입니다.")
        return
    
    print(f"\n{judgment['name']}")
    print("=" * 70)
    print(f"{judgment['description']}\n")
    
    print("왜 중요한가:")
    print(f"  {judgment['guidance']['why']}\n")
    
    print("필요한 정보:")
    print("-" * 70)
    for info_id in judgment['required_information']:
        display_information_detail(info_id, information)
    
    print("\n" + "-" * 70)
    print("고려할 질문들:")
    for i, question in enumerate(judgment['guidance']['questions'], 1):
        print(f"  {i}. {question}")
    
    print("\n일반적인 패턴:")
    for i, example in enumerate(judgment['guidance']['examples'], 1):
        print(f"  {i}. {example}")
    print()


def main():
    data = load_data()
    judgments = data['judgments']
    project_dir = Path(__file__).parent
    
    while True:
        display_judgment_list(judgments)
        choice = input("\n판단을 선택하세요: ").strip()
        
        if choice == "0":
            print("\n종료합니다!")
            break
        
        if choice.upper() == "S":
            display_project_structure(project_dir)
            input("\n계속하려면 Enter를 누르세요...")
        
        elif choice.upper() == "F":
            selected_file = select_file_interactive(project_dir)
            if selected_file:
                display_file_functions(selected_file)
                input("\n계속하려면 Enter를 누르세요...")
        
        elif choice.upper() == "C":
            selected_file = select_file_interactive(project_dir)
            if selected_file:
                functions = display_file_functions(selected_file)
                selected_func = select_function_interactive(functions)
                if selected_func:
                    display_function_calls(selected_func, functions)
                    input("\n계속하려면 Enter를 누르세요...")
        
        elif choice in judgments:
            display_judgment_info(choice, data)
            input("\n계속하려면 Enter를 누르세요...")
        else:
            print("\n잘못된 선택입니다. 다시 시도하세요.")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()