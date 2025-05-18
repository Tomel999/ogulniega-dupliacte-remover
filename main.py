import os
import sys
from pathlib import Path
import traceback
import re

PREINSTALLED_SUBFOLDER_NAME = "preinstalled"
PROFILE_MODS_BASE_SUBDIR = "mods"

def is_marker_word(word: str) -> bool:
    if not word:
        return False
    if re.fullmatch(r"v?\d+([.\-_x]\d*)*([a-z0-9.\-_+]*)?", word, re.IGNORECASE):
        return True
    if re.fullmatch(r"(?:mc|forge|fabric|neo|optifine|minecraft|build|alpha|beta|rc|pre|snapshot|release|final|hotfix|experimental)[\-_.\w]*\d[\-_.\w]*", word, re.IGNORECASE):
        return True
    if word in [
        "fabric", "forge", "mc", "neo", "optifine" "neoforge",
        "alpha", "beta", "snapshot", "rc", "dev", "lts", "release", "final", "hotfix", "experimental", "pre"
    ]:
        return True
    return False

def extract_base_mod_name(filename_str: str) -> str | None:
    stem = Path(filename_str).stem.lower()
    if not stem:
        return None
    words = re.split(r"[\-_.+\s]+", stem)
    words = [word for word in words if word]
    if not words:
        return None
    num_words_to_keep = len(words)
    for i in range(len(words) - 1, -1, -1):
        current_word = words[i]
        if is_marker_word(current_word):
            num_words_to_keep = i
        else:
            break
    base_name_words = words[:num_words_to_keep]
    if not base_name_words:
        return None
    final_base_name = "-".join(base_name_words)
    final_base_name = final_base_name.strip("-") 
    return final_base_name if final_base_name else None

def get_mod_info_for_name_logic(folder_path: Path,
                                skip_subfolder_named: str | None = None) -> list[dict]:
    mod_files_data = []
    path_to_skip_fully_resolved = None
    if skip_subfolder_named:
        path_to_skip_fully_resolved = (folder_path / skip_subfolder_named).resolve()
    for extension in ['*.jar', '*.zip']:
        for item_path in folder_path.rglob(extension):
            if not item_path.is_file():
                continue
            abs_item_path_resolved = item_path.resolve()
            if path_to_skip_fully_resolved and str(abs_item_path_resolved).startswith(str(path_to_skip_fully_resolved)):
                continue
            base_mod_name = extract_base_mod_name(item_path.name)
            if base_mod_name:
                mod_files_data.append({
                    "path": item_path, 
                    "name": item_path.name, 
                    "base_name": base_mod_name
                })
            else:
                print(f"  Ostrzeżenie: Nie udało się wyodrębnić bazowej nazwy dla: {item_path.name}", file=sys.stderr)
    return mod_files_data

def select_folder_from_list(base_path: Path, prompt_message: str) -> Path | None:
    if not base_path.is_dir():
        print(f"Błąd: Ścieżka bazowa '{base_path}' nie istnieje lub nie jest folderem.", file=sys.stderr)
        return None
    try:
        subfolders = sorted([d for d in base_path.iterdir() if d.is_dir()], key=lambda p: p.name.lower())
    except OSError as e:
        print(f"Błąd podczas odczytu podfolderów w '{base_path}': {e}", file=sys.stderr)
        return None
    if not subfolders:
        print(f"Nie znaleziono żadnych podfolderów w '{base_path}'.", file=sys.stderr)
        return None
    print(f"\n{prompt_message}")
    for i, folder in enumerate(subfolders):
        print(f"  {i+1}. {folder.name}")
    while True:
        try:
            choice_str = input(f"Wybierz numer folderu (1-{len(subfolders)}) lub 'q' aby wyjść: ").strip()
            if choice_str.lower() == 'q':
                print("Wybór anulowany.")
                return None
            choice_idx = int(choice_str) - 1
            if 0 <= choice_idx < len(subfolders):
                return subfolders[choice_idx]
            else:
                print("Nieprawidłowy wybór, spróbuj ponownie.")
        except ValueError:
            print("Proszę wprowadzić liczbę lub 'q'.")
        except KeyboardInterrupt:
            print("\nWybór anulowany przez użytkownika.")
            return None

def run_name_based_cleaner():
    print(r"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║                        OGULNIEGA ON TOP                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
                            
                            BY TOMEL999
""")
    appdata_path_str = os.getenv('APPDATA')
    if not appdata_path_str:
        print("Błąd krytyczny: Nie można odnaleźć folderu APPDATA.", file=sys.stderr)
        sys.exit(1)
    appdata_path = Path(appdata_path_str)
    ogulniega_selection_base_path = appdata_path / ".ogulniega" / "profile" / PROFILE_MODS_BASE_SUBDIR
    print(f"Oczekiwana ścieżka bazowa do wyboru folderu modyfikacji: {ogulniega_selection_base_path}")
    main_folder_to_process = select_folder_from_list(
        ogulniega_selection_base_path,
        f"Wybierz folder z '{PROFILE_MODS_BASE_SUBDIR}', który chcesz przetworzyć:"
    )
    if not main_folder_to_process:
        print("Nie wybrano folderu. Zamykanie aplikacji.")
        sys.exit(0)
    main_folder_to_process = main_folder_to_process.resolve()
    print(f"\nWybrano folder główny do przetworzenia: '{main_folder_to_process}'")
    path_to_preinstalled_subfolder = (main_folder_to_process / PREINSTALLED_SUBFOLDER_NAME).resolve()
    if not path_to_preinstalled_subfolder.is_dir():
        print(f"Błąd: Wymagany podfolder '{PREINSTALLED_SUBFOLDER_NAME}' nie istnieje w '{main_folder_to_process}'.", file=sys.stderr)
        sys.exit(1)
    print(f"\nSkanowanie folderu referencyjnego: '{path_to_preinstalled_subfolder}'...")
    preinstalled_mod_info = get_mod_info_for_name_logic(
        path_to_preinstalled_subfolder, 
        skip_subfolder_named=None
    )
    preinstalled_base_mod_names = {mod["base_name"] for mod in preinstalled_mod_info if mod["base_name"]}
    if not preinstalled_base_mod_names and preinstalled_mod_info:
        print(f"Nie udało się wyodrębnić nazw bazowych z żadnego moda w folderze '{PREINSTALLED_SUBFOLDER_NAME}'.")
        sys.exit(0)
    elif not preinstalled_base_mod_names:
         print(f"Brak modów referencyjnych w '{PREINSTALLED_SUBFOLDER_NAME}' do porównania.")
    else:
        print(f"Znaleziono {len(preinstalled_base_mod_names)} unikalnych bazowych nazw modów w folderze referencyjnym.")
    print(f"\nSkanowanie folderu głównego: '{main_folder_to_process}' (z pominięciem '{PREINSTALLED_SUBFOLDER_NAME}')...")
    main_folder_mod_info = get_mod_info_for_name_logic(
        main_folder_to_process, 
        skip_subfolder_named=PREINSTALLED_SUBFOLDER_NAME
    )
    if not main_folder_mod_info:
        print(f"Folder '{main_folder_to_process.name}' (poza '{PREINSTALLED_SUBFOLDER_NAME}') jest pusty lub nie znaleziono w nim modów.")
        sys.exit(0)
    print("\n--- Pliki oznaczone do usunięcia ---")
    files_to_delete_info = []
    for mod in main_folder_mod_info:
        if mod["base_name"] in preinstalled_base_mod_names:
            files_to_delete_info.append(mod)
            print(f"  '{mod['path']}' (bazowa nazwa '{mod['base_name']}')")
    if not files_to_delete_info:
        print("\nNie znaleziono żadnych plików do usunięcia na podstawie porównania nazw bazowych.")
        sys.exit(0)
    print(f"\nŁącznie znaleziono {len(files_to_delete_info)} plików do usunięcia.")
    perform_deletion = False
    while True:
        try:
            answer = input("Czy chcesz usunąć te pliki? Operacja jest nieodwracalna! [y/n]: ").strip().lower()
            if answer == 'y':
                perform_deletion = True
                break
            elif answer == 'n':
                print("Anulowano usuwanie.")
                break
            else:
                print("Nieprawidłowa odpowiedź.")
        except KeyboardInterrupt:
            print("\nAnulowano przez użytkownika.")
            sys.exit(0)
    if perform_deletion:
        print("\n--- Rozpoczęcie usuwania ---")
        deleted_count = 0
        failed_count = 0
        for file_info in files_to_delete_info:
            try:
                file_info["path"].unlink()
                print(f"  USUNIĘTO: {file_info['path']}")
                deleted_count += 1
            except OSError as e:
                print(f"  BŁĄD USUWANIA: {file_info['path']} - {e}", file=sys.stderr)
                failed_count += 1
        print("\n--- Zakończono usuwanie ---")
        print(f"  Usunięto: {deleted_count} plików.")
        if failed_count > 0:
            print(f"  Błędy: {failed_count} plików nie udało się usunąć.")
    print("\nZakończono działanie programu.")

if __name__ == "__main__":
    try:
        run_name_based_cleaner()
    except Exception as e:
        print(f"\nNieoczekiwany błąd globalny: {e}", file=sys.stderr)
        traceback.print_exc()
    finally:
        if sys.stdin.isatty():
            input("\nNaciśnij Enter, aby zakończyć...")
