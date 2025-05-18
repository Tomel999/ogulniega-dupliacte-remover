
# Ogulniega Mod Cleaner

🧹 **Automatyczne czyszczenie folderów z modami Minecrafta**  
Skrypt w Pythonie do usuwania zduplikowanych modów na podstawie ich bazowych nazw.

## 📦 Opis

Ten skrypt przeszukuje folder z modami Minecrafta w strukturze `.ogulniega/profile/mods/`, porównując go z podfolderem `preinstalled`, i usuwa wszystkie pliki `.jar` i `.zip`, które mają tę samą *bazową nazwę* jak mody w `preinstalled`.

Używa heurystyk do wyodrębniania nazw bazowych z nazw plików modów, ignorując wersje i inne dodatki.

## 🛠️ Wymagania

- Python 3.10+
- System Windows (skrypt zakłada obecność zmiennej `APPDATA`)

## 🚀 Jak używać

1. Umieść skrypt `main.py` w dowolnym miejscu.
2. Upewnij się, że modyfikacje znajdują się w folderze:
   ```
   %APPDATA%\.ogulniega\profile\mods\[NAZWA_PROFILU]
   ```
3. W tym folderze musi znajdować się podfolder `preinstalled` z referencyjnymi modami.
4. Upewnij się, że masz masz zainstalowane wszystkie pakiety.
```bash
pip install requests
```
5. Uruchom skrypt:

   ```bash
   python main.py
   ```

5. Wybierz profil z listy, potwierdź usunięcie modów – skrypt zrobi resztę.

## 📂 Przykładowa struktura folderów

```
.ogulniega/
└── profile/
    └── mods/
        └── moj-profil/
            ├── mod1-1.0.0.jar
            ├── mod2-1.1.0.jar
            └── preinstalled/
                └── mod1-1.0.0.jar
```

W tym przykładzie `mod1-1.0.0.jar` zostanie usunięty z folderu `moj-profil`, ponieważ znajduje się też w `preinstalled`.

## ⚙️ Funkcjonalności

- Wykrywanie i usuwanie zduplikowanych modów na podstawie nazw
- Heurystyczna analiza nazw plików `.jar`/`.zip`
- Interfejs w terminalu z wyborem folderów
- Bezpieczne potwierdzenie przed usunięciem

## ✍️ Kontakt
**Discord: tomel999**  

## ⚠️ Uwaga

Operacja usuwania jest **nieodwracalna** – upewnij się, że masz kopie zapasowe, jeśli to konieczne.
