import os
import sys
from pathlib import Path
import traceback
import re

# Nazwa podfolderu zawierającego mody "domyślnie zainstalowane"
PREINSTALLED_SUBFOLDER_NAME = "preinstalled"

# Nazwa głównego folderu modów w strukturze profilu
PROFILE_MODS_BASE_SUBDIR = "mods"

def extract_base_mod_name(filename_str: str) -> str | None:
    """
    Próbuje wyodrębnić bazową nazwę moda z nazwy pliku.
    Jest to heurystyka - może nie być perfekcyjna i wymagać dostosowania.
    """
    stem = Path(filename_str).stem.lower()
    base_name_extracted = None

    # Próba 1: dopasowanie wzorca "nazwa + separator lub v + cyfra"
    match1 = re.match(r"^(.*?)((?:[\-_.\s]v?)?\d)", stem)
    if match1:
        candidate = match1.group(1).strip("._- ")
        if candidate:
            base_name_extracted = candidate

    # Próba 2: podział na nazwę i wersję przy pomocy "-" lub "_"
    if not base_name_extracted:
        parts = re.split(r"[-_](?=\d)", stem, 1)
        if len(parts) > 1:
            candidate = parts[0].strip("._- ")
            if candidate:
                base_name_extracted = candidate

    # Próba 3: usunięcie typowego sufiksu wersji
    if not base_name_extracted:
        match3 = re.search(r"([\-_.\s]v?\d+(\.\d+)*([a-zA-Z0-9.\-_]*))$", stem)
        if match3:
            if match3.start() > 0:
                candidate = stem[:match3.start()].strip("._- ")
                if candidate:
                    base_name_extracted = candidate
            elif not stem[:match3.start()].strip("._- "):
                base_name_extracted = None

    # Ustal, której nazwy użyć – bazowej lub pełnego stemu
    name_to_normalize = None
    if base_name_extracted:
        name_to_normalize = base_name_extracted
    else:
        # Upewnij się, że stem nie wygląda jak sama wersja (np. "1.0")
        is_stem_version_like = re.fullmatch(r"([\-_.\s]v?)?\d+(\.\d+)*([a-zA-Z0-9.\-_]*)?", stem)
        if not is_stem_version_like:
            name_to_normalize = stem.strip("._- ")

    if not name_to_normalize:
        return None

    # Normalizacja: zamień "_" i "." na "-", usuń nadmiarowe myślniki
    normalized_name = name_to_normalize.replace('_', '-')
    normalized_name = normalized_name.replace('.', '-')
    normalized_name = re.sub(r'-+', '-', normalized_name)
    normalized_name = normalized_name.strip('-')

    return normalized_name if normalized_name else None

def get_mod_info_for_name_logic(folder_path: Path,
                                skip_subfolder_named: str | None = None) -> list[dict]:
    """
    Skanuje folder w poszukiwaniu plików .jar/.zip i wyciąga ich bazowe nazwy.
    Pomija pliki znajdujące się w podfolderze o nazwie skip_subfolder_named.
    """
    mod_files_data = []
    path_to_skip_fully_resolved = None
    if skip_subfolder_named:
        path_to_skip_fully_resolved = (folder_path / skip_subfolder_named).resolve()

    # Przeszukiwanie rekurencyjne plików .jar i .zip
    for extension in ['*.jar', '*.zip']:
        for item_path in folder_path.rglob(extension):
            if not item_path.is_file():
                continue

            abs_item_path_resolved = item_path.resolve()

            # Pomijaj pliki z określonego podfolderu
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
    """
    Wyświetla listę podfolderów w base_path i pozwala użytkownikowi wybrać jeden.
    """
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

    # Pętla wyboru folderu
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
    """
    Główna funkcja programu. Wybiera folder z modami, porównuje go z folderem 'preinstalled'
    i usuwa pliki, które mają takie same bazowe nazwy jak w folderze referencyjnym.
    """
    print(r"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║                        OGULNIEGA ON TOP                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
                            
                            BY TOMEL999
""")

    # Pobierz ścieżkę do APPDATA
    appdata_path_str = os.getenv('APPDATA')
    if not appdata_path_str:
        print("Błąd krytyczny: Nie można odnaleźć folderu APPDATA.", file=sys.stderr)
        sys.exit(1)
    appdata_path = Path(appdata_path_str)

    # Ścieżka do katalogu z modami
    ogulniega_selection_base_path = appdata_path / ".ogulniega" / "profile" / PROFILE_MODS_BASE_SUBDIR
    print(f"Oczekiwana ścieżka bazowa do wyboru folderu modyfikacji: {ogulniega_selection_base_path}")

    # Wybór folderu z modami
    main_folder_to_process = select_folder_from_list(
        ogulniega_selection_base_path,
        f"Wybierz folder z '{PROFILE_MODS_BASE_SUBDIR}', który chcesz przetworzyć:"
    )

    if not main_folder_to_process:
        print("Nie wybrano folderu. Zamykanie aplikacji.")
        sys.exit(0)
    
    main_folder_to_process = main_folder_to_process.resolve()
    print(f"\nWybrano folder główny do przetworzenia: '{main_folder_to_process}'")

    # Sprawdź obecność folderu "preinstalled"
    path_to_preinstalled_subfolder = (main_folder_to_process / PREINSTALLED_SUBFOLDER_NAME).resolve()
    if not path_to_preinstalled_subfolder.is_dir():
        print(f"Błąd: Wymagany podfolder '{PREINSTALLED_SUBFOLDER_NAME}' nie istnieje.", file=sys.stderr)
        sys.exit(1)

    # Zbierz informacje o modach z folderu referencyjnego
    preinstalled_mod_info = get_mod_info_for_name_logic(
        path_to_preinstalled_subfolder, 
        skip_subfolder_named=None
    )

    if not preinstalled_mod_info:
        print(f"Folder '{PREINSTALLED_SUBFOLDER_NAME}' jest pusty lub nie znaleziono modów.")
        sys.exit(0)

    # Zbierz unikalne bazowe nazwy modów
    preinstalled_base_mod_names = {mod["base_name"] for mod in preinstalled_mod_info if mod["base_name"]}
    if not preinstalled_base_mod_names:
        print(f"Nie udało się wyodrębnić nazw bazowych z folderu '{PREINSTALLED_SUBFOLDER_NAME}'.")
        sys.exit(0)
    print(f"Znaleziono {len(preinstalled_base_mod_names)} unikalnych bazowych nazw modów.")

    # Zbierz informacje o modach z folderu głównego (z wykluczeniem preinstalled)
    main_folder_mod_info = get_mod_info_for_name_logic(
        main_folder_to_process, 
        skip_subfolder_named=PREINSTALLED_SUBFOLDER_NAME
    )

    if not main_folder_mod_info:
        print(f"Folder '{main_folder_to_process.name}' jest pusty.")
        sys.exit(0)

    # Wyszukaj pliki do usunięcia
    print("\n--- Pliki oznaczone do usunięcia ---")
    files_to_delete_info = []
    for mod in main_folder_mod_info:
        if mod["base_name"] in preinstalled_base_mod_names:
            files_to_delete_info.append(mod)
            print(f"  '{mod['path']}' (bazowa nazwa '{mod['base_name']}')")

    if not files_to_delete_info:
        print("\nNie znaleziono żadnych plików do usunięcia.")
        sys.exit(0)

    print(f"\nŁącznie znaleziono {len(files_to_delete_info)} plików do usunięcia.")

    # Potwierdzenie usuwania
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

    # Usuwanie plików
    if perform_deletion:
        print("\n--- Rozpoczęcie usuwania ---")
        deleted_count = 0
        failed_count = 0
        
        for file in files_to_delete_info:
            try:
                file["path"].unlink()
                print(f"  USUNIĘTO: {file['path']}")
                deleted_count += 1
            except OSError as e:
                print(f"  BŁĄD USUWANIA: {e}", file=sys.stderr)
                failed_count += 1
        
        print("\n--- Zakończono usuwanie ---")
        print(f"  Usunięto: {deleted_count} plików.")
        if failed_count > 0:
            print(f"  Błędy: {failed_count} plików nie udało się usunąć.")
    
    print("\nZakończono działanie programu.")

# Uruchomienie aplikacji (główna funkcja)
if __name__ == "__main__":
    try:
        run_name_based_cleaner()
    except Exception as e:
        print(f"\nNieoczekiwany błąd globalny: {e}", file=sys.stderr)
        traceback.print_exc()
    finally:
        if sys.stdin.isatty():
            input("\nNaciśnij Enter, aby zakończyć...")
