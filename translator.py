import os
import re
import json
import time
import zipfile
import shutil
import requests
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.prompt import Prompt
from rich.table import Table
from deep_translator import GoogleTranslator

console = Console()
AI_DIR = "AI"
MODS_DIR = "mods"
QUESTS_DIR = os.path.join("config", "ftbquests", "quests")
KOBOLD_API = "http://localhost:5001/v1/chat/completions"

FORMAT_PATTERN = re.compile(r'(\$\([^)]+\)|§[0-9a-fk-orlmn]|\&[0-9a-fk-orlmn]|<br>|\n|%[0-9]*\$?[a-zA-Z])')
KEYS_TO_TRANSLATE = {"name", "title", "text", "description", "subtitle"}

def get_mod_name(filepath):
    filename = os.path.basename(filepath)
    name = filename.replace('.jar', '')
    name = re.split(r'-\d', name)[0] 
    return name.replace('_', ' ').title()

def is_translation_key(text):
    t = text.strip()
    if not t or ' ' in t or '\n' in t: return False
    if re.match(r'^[a-zA-Z0-9_-]+[.:][a-zA-Z0-9_.-]+$', t): return True
    return False

def load_lenient_json(raw_bytes):
    text = raw_bytes.decode('utf-8', errors='ignore')
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL) 
    text = re.sub(r'(?<!:)//.*', '', text) 
    text = re.sub(r',\s*}', '}', text) 
    text = re.sub(r',\s*]', ']', text)
    return json.loads(text, strict=False)

# ================= АУДИТ СБОРКИ (АНАЛИЗ) =================

def analyze_modpack():
    console.print("\n[cyan]Запуск сканирования сборки... Это займет немного времени.[/cyan]")
    
    total_en_strings = 0
    total_ru_strings = 0
    
    table = Table(title="Статистика локализации сборки")
    table.add_column("Файл / Название", style="cyan")
    table.add_column("Тип", style="magenta")
    table.add_column("Переведено", justify="right")
    table.add_column("Прогресс", justify="right")

    if os.path.exists(MODS_DIR):
        jar_files = [os.path.join(MODS_DIR, f) for f in os.listdir(MODS_DIR) if f.endswith('.jar')]
        with Progress(SpinnerColumn(), TextColumn("[yellow]Анализ модов...")) as progress:
            task = progress.add_task("analyze_mods", total=len(jar_files))
            for filepath in jar_files:
                mod_name = get_mod_name(filepath)
                interface_en, interface_ru = 0, 0
                book_en, book_ru = 0, 0
                
                try:
                    with zipfile.ZipFile(filepath, 'r') as zin:
                        ru_stats = {}
                        for item in zin.infolist():
                            filename_lower = item.filename.lower()
                            if 'ru_ru.json' in filename_lower or '/ru_ru/' in filename_lower:
                                try:
                                    ru_data = load_lenient_json(zin.read(item))
                                    if '/ru_ru/' in filename_lower and ('patchouli' in filename_lower or 'lexicon' in filename_lower or 'guide' in filename_lower):
                                        ru_stats[item.filename.lower()] = len([s for s in extract_book_strings(ru_data) if s.strip()])
                                    else:
                                        ru_stats[item.filename.lower()] = len([k for k, v in ru_data.items() if isinstance(v, str) and v.strip()])
                                except: pass
                        
                        for item in zin.infolist():
                            filename_lower = item.filename.lower()
                            is_book = ('/en_us/' in filename_lower and filename_lower.endswith('.json') and ('patchouli' in filename_lower or 'lexicon' in filename_lower or 'guide' in filename_lower))
                            is_lang = (filename_lower.endswith('en_us.json') and not is_book)

                            if is_lang:
                                try:
                                    en_data = load_lenient_json(zin.read(item))
                                    count = len([k for k, v in en_data.items() if isinstance(v, str) and v.strip()])
                                    interface_en += count
                                    ru_target = item.filename.lower().replace('en_us.json', 'ru_ru.json')
                                    interface_ru += ru_stats.get(ru_target, 0)
                                except: pass
                            elif is_book:
                                try:
                                    en_data = load_lenient_json(zin.read(item))
                                    count = len([s for s in extract_book_strings(en_data) if s.strip()])
                                    book_en += count
                                    ru_target = item.filename.lower().replace('/en_us/', '/ru_ru/')
                                    book_ru += ru_stats.get(ru_target, 0)
                                except: pass
                except: pass
                
                # Добавляем строку для интерфейса
                if interface_en > 0:
                    percent = min(100, int((interface_ru / interface_en) * 100))
                    total_en_strings += interface_en
                    total_ru_strings += interface_ru
                    color = "green" if percent >= 90 else "yellow" if percent >= 50 else "red"
                    table.add_row(mod_name, "Интерфейс", f"[{color}]{interface_ru} / {interface_en}[/{color}]", f"[{color}]{percent}%[/{color}]")
                
                # Добавляем отдельную строку для книг
                if book_en > 0:
                    percent = min(100, int((book_ru / book_en) * 100))
                    total_en_strings += book_en
                    total_ru_strings += book_ru
                    color = "green" if percent >= 90 else "yellow" if percent >= 50 else "red"
                    table.add_row(mod_name, "Книга", f"[{color}]{book_ru} / {book_en}[/{color}]", f"[{color}]{percent}%[/{color}]")
                    
                progress.update(task, advance=1)

    if os.path.exists(QUESTS_DIR):
        with Progress(SpinnerColumn(), TextColumn("[yellow]Анализ квестов...")) as progress:
            snbt_files = []
            for root, _, files in os.walk(QUESTS_DIR):
                for f in files:
                    if f.endswith('.snbt'): snbt_files.append(os.path.join(root, f))
            
            task = progress.add_task("analyze_quests", total=len(snbt_files))        
            for filepath in snbt_files:
                filename = os.path.basename(filepath)
                q_en, q_ru = 0, 0
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    strings_to_check = []
                    for m in re.finditer(r'(title|subtitle|text)\s*:\s*"((?:[^"\\]|\\.)*)"', content):
                        val = m.group(2)
                        if val.strip() and not is_translation_key(val): strings_to_check.append(val)
                        
                    for m in re.finditer(r'description\s*:\s*\[(.*?)\]', content, re.DOTALL):
                        desc_content = m.group(1)
                        for str_m in re.finditer(r'"((?:[^"\\]|\\.)*)"', desc_content):
                            val = str_m.group(1)
                            if val.strip() and not is_translation_key(val): strings_to_check.append(val)
                    
                    strings_to_check = list(set(strings_to_check))
                    q_en = len(strings_to_check)
                    
                    for s in strings_to_check:
                        if re.search(r'[А-Яа-яЁё]', s): q_ru += 1
                            
                    if q_en > 0:
                        percent = min(100, int((q_ru / q_en) * 100))
                        total_en_strings += q_en
                        total_ru_strings += q_ru
                        color = "green" if percent >= 90 else "yellow" if percent >= 50 else "red"
                        table.add_row(filename, "Квест", f"[{color}]{q_ru} / {q_en}[/{color}]", f"[{color}]{percent}%[/{color}]")
                except: pass
                progress.update(task, advance=1)

    console.print(table)
    
    if total_en_strings > 0:
        global_percent = int((total_ru_strings / total_en_strings) * 100)
        color = "green" if global_percent >= 90 else "yellow" if global_percent >= 50 else "red"
        console.print(Panel(f"[bold]Общая готовность перевода сборки:[/bold] [{color}]{global_percent}%[/{color}]\nВсего строк текста: {total_en_strings} | Из них на русском: {total_ru_strings}", title="Итог Аудита", border_style=color))
    else:
        console.print("[yellow]В сборке не найдено файлов для перевода или папки mods/quests пусты![/yellow]")

# ================= АВТОМАТИЗАЦИЯ ИИ =================

def setup_ai():
    if not os.path.exists(AI_DIR):
        os.makedirs(AI_DIR)
        console.print(f"[green]Создана папка {AI_DIR}[/green]")

    kobold_path = os.path.join(AI_DIR, "koboldcpp.exe")
    if not os.path.exists(kobold_path):
        console.print("[yellow]Ищем актуальную версию KoboldCPP...[/yellow]")
        try:
            api_url = "https://api.github.com/repos/LostRuins/koboldcpp/releases/latest"
            release_data = requests.get(api_url).json()
            exe_asset = next(a for a in release_data['assets'] if a['name'].endswith('.exe') and 'nocuda' not in a['name'])
            
            with requests.get(exe_asset['browser_download_url'], stream=True) as r:
                r.raise_for_status()
                with Progress(TextColumn("[cyan]Скачивание KoboldCPP..."), BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%")) as progress:
                    task = progress.add_task("download", total=int(r.headers.get('content-length', 0)))
                    with open(kobold_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))
        except Exception as e:
            console.print(f"[red]Ошибка скачивания: {e}[/red]")
            return None

    models = [f for f in os.listdir(AI_DIR) if f.endswith('.gguf')]
    if not models:
        console.print(Panel("[red]В папке AI нет файла модели![/red]\nПоложите .gguf файл в папку AI.", title="Внимание"))
        return None
    return models[0]

def start_kobold(model_name):
    console.print(f"[cyan]Запуск нейросети: {model_name}...[/cyan]")
    model_path = os.path.join(AI_DIR, model_name)
    process = subprocess.Popen(
        [os.path.join(AI_DIR, "koboldcpp.exe"), model_path, "--port", "5001", "--quiet"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    with Progress(SpinnerColumn(), TextColumn("[yellow]Разогрев нейросети...")) as progress:
        progress.add_task("wait", total=None)
        for _ in range(60):
            try:
                if requests.get("http://localhost:5001/api/v1/model", timeout=1).status_code == 200:
                    console.print("[green]Сервер ИИ готов![/green]")
                    return process
            except: time.sleep(1)
    console.print("[red]Не удалось запустить сервер ИИ![/red]")
    process.terminate()
    return None

def log_translation(progress, en_text, ru_text):
    en_clean = en_text.replace('\n', ' ')
    ru_clean = ru_text.replace('\n', ' ')
    progress.console.print(f"[dim]EN:[/dim] {en_clean[:37] + '...' if len(en_clean) > 40 else en_clean:<40} [yellow]>[/yellow] [green]RU:[/green] {ru_clean[:37] + '...' if len(ru_clean) > 40 else ru_clean}")

# ================= ДВИЖКИ ПЕРЕВОДА =================

def translate_ai_batch(data_dict, context_name, progress, task):
    batch_size = 20
    keys = list(data_dict.keys())
    result = {}
    
    for i in range(0, len(keys), batch_size):
        chunk_keys = keys[i:i + batch_size]
        chunk_masked = {}
        mappings = {}
        keys_to_ai = []
        
        for k in chunk_keys:
            text = data_dict[k]
            if is_translation_key(text):
                result[k] = text
                progress.console.print(f"[dim]EN:[/dim] {text[:37]:<40} [yellow]>[/yellow] [blue]ПРОПУСК (СИСТЕМНЫЙ КЛЮЧ)[/blue]")
                progress.update(task, advance=1)
                continue
                
            keys_to_ai.append(k)
            mapping = {}
            def mask_format(m):
                marker = f" [#{len(mapping)}#] "
                mapping[marker.strip()] = m.group(0)
                return marker
            
            chunk_masked[k] = re.sub(r'\s+', ' ', FORMAT_PATTERN.sub(mask_format, text)).strip()
            mappings[k] = mapping

        if not keys_to_ai: continue

        prompt = f"""Ты — локализатор модов Minecraft. Переведи значения JSON на русский язык. Контекст: {context_name}. 
ПРАВИЛА: 1. Ключи оставь на английском. 2. Термины: Amethyst->Аметист, Bricks->Кирпичи, Slab->Плита, Stairs->Ступени. 3. НЕ смешивай буквы. 4. Сохраняй [#0#]. 5. Верни ТОЛЬКО валидный JSON без ``` разметки. 6. Непереводимое оставляй в оригинале.
Текст: {json.dumps(chunk_masked, ensure_ascii=False)}"""

        try:
            res = requests.post(KOBOLD_API, json={"messages": [{"role": "user", "content": prompt}], "temperature": 0.1, "max_tokens": 2048}, timeout=120).json()
            trans_text = re.sub(r'^```json\s*|^```\s*|```$', '', res['choices'][0]['message']['content'].strip(), flags=re.IGNORECASE).strip()
            translated_chunk = json.loads(trans_text, strict=False)
            
            for k in keys_to_ai:
                if k in translated_chunk:
                    trans = translated_chunk[k]
                    for marker_idx, (marker, orig) in enumerate(mappings[k].items()):
                        trans = re.sub(rf'\[\s*#\s*{marker_idx}\s*#\s*\]', lambda m, o=orig: o, trans)
                    result[k] = trans
                    log_translation(progress, data_dict[k], trans)
                else:
                    result[k] = data_dict[k]
                progress.update(task, advance=1)
        except Exception:
            for k in keys_to_ai:
                result[k] = data_dict[k]
                progress.update(task, advance=1)
                
    return result

def translate_google_batch(data_dict, context_name, progress, task):
    translator = GoogleTranslator(source='en', target='ru')
    keys = list(data_dict.keys())
    result = {}
    
    masked_dict = {}
    mappings = {}
    keys_to_translate = []
    
    for k in keys:
        text = data_dict[k]
        if is_translation_key(text):
            result[k] = text
            progress.console.print(f"[dim]EN:[/dim] {text[:37]:<40} [yellow]>[/yellow] [blue]ПРОПУСК (СИСТЕМНЫЙ КЛЮЧ)[/blue]")
            progress.update(task, advance=1)
            continue
        
        mapping = {}
        def mask_format(m):
            marker = f" [#{len(mapping)}#] "
            mapping[marker.strip()] = m.group(0)
            return marker
            
        masked_dict[k] = re.sub(r'\s+', ' ', FORMAT_PATTERN.sub(mask_format, text)).strip()
        mappings[k] = mapping
        keys_to_translate.append(k)

    delimiter = "\n@@@\n"
    current_keys, current_text, chunks = [], "", []

    for k in keys_to_translate:
        text = masked_dict[k]
        if len(current_text) + len(text) + len(delimiter) > 4000:
            chunks.append((current_keys, current_text))
            current_keys, current_text = [k], text
        else:
            current_keys.append(k)
            current_text = current_text + delimiter + text if current_text else text
    if current_keys: chunks.append((current_keys, current_text))

    for chunk_keys, text_to_send in chunks:
        try:
            res = translator.translate(text_to_send)
            time.sleep(0.5)
            parts = [p.strip() for p in res.split('@@@')]
            
            if len(parts) == len(chunk_keys):
                for idx, k in enumerate(chunk_keys):
                    trans = parts[idx]
                    for m_idx, (m, orig) in enumerate(mappings[k].items()):
                        trans = re.sub(rf'\[\s*#\s*{m_idx}\s*#\s*\]', lambda x, o=orig: o, trans)
                    result[k] = trans
                    log_translation(progress, data_dict[k], trans)
                    progress.update(task, advance=1)
            else:
                for k in chunk_keys:
                    res_single = translator.translate(masked_dict[k])
                    for m_idx, (m, orig) in enumerate(mappings[k].items()):
                        res_single = re.sub(rf'\[\s*#\s*{m_idx}\s*#\s*\]', lambda x, o=orig: o, res_single)
                    result[k] = res_single
                    log_translation(progress, data_dict[k], res_single)
                    progress.update(task, advance=1)
        except Exception:
            for k in chunk_keys:
                result[k] = data_dict[k]
                progress.update(task, advance=1)
                
    return result

def translate_list_batch(string_list, context_name, progress, task, engine):
    chunk_dict = {str(idx): val for idx, val in enumerate(string_list)}
    if engine == "ai":
        translated_dict = translate_ai_batch(chunk_dict, context_name, progress, task)
    else:
        translated_dict = translate_google_batch(chunk_dict, context_name, progress, task)
        
    return [translated_dict.get(str(idx), string_list[idx]) for idx in range(len(string_list))]

# ================= ОБРАБОТКА МОДОВ (JAR) =================

def extract_book_strings(data):
    strings = []
    if isinstance(data, dict):
        for k, v in data.items():
            if k in KEYS_TO_TRANSLATE and isinstance(v, str): strings.append(v)
            elif k in KEYS_TO_TRANSLATE and isinstance(v, list) and all(isinstance(i, str) for i in v): strings.extend(v)
            elif isinstance(v, (dict, list)): strings.extend(extract_book_strings(v))
    elif isinstance(data, list):
        for item in data: strings.extend(extract_book_strings(item))
    return strings

def inject_book_strings(data, t_iter):
    if isinstance(data, dict):
        for k, v in data.items():
            if k in KEYS_TO_TRANSLATE and isinstance(v, str): data[k] = next(t_iter)
            elif k in KEYS_TO_TRANSLATE and isinstance(v, list) and all(isinstance(i, str) for i in v): data[k] = [next(t_iter) for _ in v]
            elif isinstance(v, (dict, list)): inject_book_strings(v, t_iter)
    elif isinstance(data, list):
        for item in data: inject_book_strings(item, t_iter)

def process_jar(filepath, progress, overall_task, string_task, modes, engine, force_overwrite):
    temp_filepath = filepath + ".temp"
    translated_any = False
    mod_name = get_mod_name(filepath)
    
    try:
        with zipfile.ZipFile(filepath, 'r') as zin:
            ru_stats = {}
            for item in zin.infolist():
                filename_lower = item.filename.lower()
                if 'ru_ru.json' in filename_lower or '/ru_ru/' in filename_lower:
                    try:
                        ru_data = load_lenient_json(zin.read(item))
                        if '/ru_ru/' in filename_lower and ('patchouli_books' in filename_lower or 'lexicon' in filename_lower or 'guide' in filename_lower):
                            ru_stats[item.filename] = len([s for s in extract_book_strings(ru_data) if s.strip()])
                        else:
                            ru_stats[item.filename] = len([k for k, v in ru_data.items() if isinstance(v, str) and v.strip()])
                    except: ru_stats[item.filename] = 0

            with zipfile.ZipFile(temp_filepath, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
                ru_files_written = set()

                for item in zin.infolist():
                    filename_lower = item.filename.lower()
                    is_book_lang = ('/en_us/' in filename_lower and filename_lower.endswith('.json') and ('patchouli_books' in filename_lower or 'lexicon' in filename_lower or 'guide' in filename_lower))
                    is_interface_lang = (filename_lower.endswith('en_us.json') and not is_book_lang)
                    is_ru = 'ru_ru.json' in filename_lower or '/ru_ru/' in filename_lower

                    try: content = zin.read(item)
                    except Exception: continue 

                    if not is_ru: zout.writestr(item, content)

                    if "mods" in modes and is_interface_lang:
                        ru_filename = re.sub(r'en_us\.json$', 'ru_ru.json', item.filename, flags=re.IGNORECASE)
                        try:
                            data = load_lenient_json(content)
                            keys_to_translate = {k: v for k, v in data.items() if isinstance(v, str) and v.strip()}
                            en_count = len(keys_to_translate)
                            ru_count = ru_stats.get(ru_filename, 0)

                            if en_count > 0:
                                if not force_overwrite and ru_count >= en_count * 0.9:
                                    progress.console.print(f"[bold dim][ПРОПУСК][/bold dim] [cyan]{mod_name}[/cyan] (Интерфейс): Перевод готов")
                                    if ru_filename in zin.namelist():
                                        zout.writestr(zin.getinfo(ru_filename), zin.read(ru_filename))
                                        ru_files_written.add(ru_filename)
                                else:
                                    progress.update(string_task, description=f"[cyan]Мод {mod_name}...", total=en_count, completed=0, visible=True)
                                    if engine == "ai": translated_dict = translate_ai_batch(keys_to_translate, mod_name, progress, string_task)
                                    else: translated_dict = translate_google_batch(keys_to_translate, mod_name, progress, string_task)
                                        
                                    for k, v in translated_dict.items(): data[k] = v
                                    zout.writestr(ru_filename, json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
                                    ru_files_written.add(ru_filename)
                                    translated_any = True
                        except Exception as e: progress.console.print(f"[bold red]Ошибка мода {mod_name}: {e}[/bold red]")

                    elif "books" in modes and is_book_lang:
                        ru_filename = re.sub(r'/en_us/', '/ru_ru/', item.filename, flags=re.IGNORECASE)
                        try:
                            data = load_lenient_json(content)
                            strings = [s for s in extract_book_strings(data) if s.strip()]
                            en_count = len(strings)
                            ru_count = ru_stats.get(ru_filename, 0)

                            if en_count > 0:
                                if not force_overwrite and ru_count >= en_count * 0.9:
                                    progress.console.print(f"[bold dim][ПРОПУСК][/bold dim] [magenta]{mod_name}[/magenta] (Книга): Перевод готов")
                                    if ru_filename in zin.namelist():
                                        zout.writestr(zin.getinfo(ru_filename), zin.read(ru_filename))
                                        ru_files_written.add(ru_filename)
                                else:
                                    progress.update(string_task, description=f"[magenta]Книга {mod_name}...", total=en_count, completed=0, visible=True)
                                    translated_strings = translate_list_batch(strings, mod_name, progress, string_task, engine)
                                    inject_book_strings(data, iter(translated_strings))
                                    zout.writestr(ru_filename, json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
                                    ru_files_written.add(ru_filename)
                                    translated_any = True
                        except Exception as e: progress.console.print(f"[bold red]Ошибка книги {mod_name}: {e}[/bold red]")

                for item in zin.infolist():
                    if ('ru_ru.json' in item.filename.lower() or '/ru_ru/' in item.filename.lower()) and item.filename not in ru_files_written:
                        try: zout.writestr(item, zin.read(item))
                        except: pass

        if translated_any:
            shutil.move(temp_filepath, filepath)
            progress.update(string_task, visible=False)
        else: os.remove(temp_filepath)
            
    except Exception as e:
        if os.path.exists(temp_filepath): os.remove(temp_filepath)
        progress.console.print(f"[bold red]Критическая ошибка архива {mod_name}: {e}[/bold red]")

# ================= ОБРАБОТКА КВЕСТОВ (SNBT) =================

def process_snbt(filepath, progress, overall_task, string_task, engine, force_overwrite):
    filename = os.path.basename(filepath)
    bak_path = filepath + ".bak"
    
    if not os.path.exists(bak_path):
        shutil.copy2(filepath, bak_path)
        content_path = filepath
    else:
        content_path = bak_path 
        
    try:
        with open(content_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        strings_to_translate = []
        for m in re.finditer(r'(title|subtitle|text)\s*:\s*"((?:[^"\\]|\\.)*)"', content):
            val = m.group(2)
            if val.strip() and not is_translation_key(val): strings_to_translate.append(val)
            
        for m in re.finditer(r'description\s*:\s*\[(.*?)\]', content, re.DOTALL):
            desc_content = m.group(1)
            for str_m in re.finditer(r'"((?:[^"\\]|\\.)*)"', desc_content):
                val = str_m.group(1)
                if val.strip() and not is_translation_key(val): strings_to_translate.append(val)
                
        strings_to_translate = list(set(strings_to_translate))
        en_count = len(strings_to_translate)
        
        if en_count == 0: return
            
        if not force_overwrite and os.path.exists(bak_path):
            with open(filepath, 'r', encoding='utf-8') as f:
                if re.search(r'[А-Яа-я]', f.read()):
                    progress.console.print(f"[bold dim][ПРОПУСК][/bold dim] [yellow]{filename}[/yellow] (Квесты): Перевод готов")
                    return

        progress.update(string_task, description=f"[yellow]Квесты {filename}...", total=en_count, completed=0, visible=True)
        
        chunk_dict = {str(i): val for i, val in enumerate(strings_to_translate)}
        if engine == "ai":
            translated_dict = translate_ai_batch(chunk_dict, "FTB Quests", progress, string_task)
        else:
            translated_dict = translate_google_batch(chunk_dict, "FTB Quests", progress, string_task)
            
        trans_map = {strings_to_translate[i]: translated_dict.get(str(i), strings_to_translate[i]) for i in range(en_count)}
        
        def repl_single(m):
            key, val = m.group(1), m.group(2)
            new_val = trans_map.get(val, val).replace('\\"', '"').replace('"', '\\"')
            return f'{key}: "{new_val}"'
            
        content = re.sub(r'(title|subtitle|text)\s*:\s*"((?:[^"\\]|\\.)*)"', repl_single, content)
        
        def repl_desc(m):
            desc_content = m.group(1)
            def repl_inner(str_m):
                val = str_m.group(1)
                new_val = trans_map.get(val, val).replace('\\"', '"').replace('"', '\\"')
                return f'"{new_val}"'
            new_desc_content = re.sub(r'"((?:[^"\\]|\\.)*)"', repl_inner, desc_content)
            return f'description: [{new_desc_content}]'
            
        content = re.sub(r'description\s*:\s*\[(.*?)\]', repl_desc, content, flags=re.DOTALL)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        progress.update(string_task, visible=False)
        
    except Exception as e:
        progress.console.print(f"[bold red]Ошибка квеста {filename}: {e}[/bold red]")

# ================= ГЛАВНОЕ МЕНЮ =================

def main():
    console.print(Panel.fit("[bold bright_green]ULTIMATE Minecraft Translator[/bold bright_green]\nКомплексный инструмент локализации", border_style="green"))
    
    console.print("\n[bold]ЧТО делаем?[/bold]")
    console.print("1. Интерфейс и предметы (В папке mods)")
    console.print("2. Внутриигровые справочники/книги (В папке mods)")
    console.print("3. Квесты FTB Quests (В папке config/ftbquests/quests)")
    console.print("4. ВСЁ ВМЕСТЕ (Полный перевод)")
    console.print("5. [bold cyan]Анализ сборки (Узнать % перевода)[/bold cyan]")
    target_choice = Prompt.ask("Введите номер", choices=["1", "2", "3", "4", "5"], default="5")
    
    if target_choice == "5":
        analyze_modpack()
        return

    modes = []
    if target_choice == "1": modes = ["mods"]
    elif target_choice == "2": modes = ["books"]
    elif target_choice == "3": modes = ["quests"]
    elif target_choice == "4": modes = ["mods", "books", "quests"]

    jar_files = []
    snbt_files = []

    if "mods" in modes or "books" in modes:
        if os.path.exists(MODS_DIR):
            jar_files = [os.path.join(MODS_DIR, f) for f in os.listdir(MODS_DIR) if f.endswith('.jar')]
        else:
            console.print("[yellow]Внимание: Папка 'mods' не найдена в текущей директории![/yellow]")

    if "quests" in modes:
        if os.path.exists(QUESTS_DIR):
            for root, _, files in os.walk(QUESTS_DIR):
                for f in files:
                    if f.endswith('.snbt'):
                        snbt_files.append(os.path.join(root, f))
        else:
            console.print("[yellow]Внимание: Папка 'config/ftbquests/quests' не найдена![/yellow]")

    total_files = len(jar_files) + len(snbt_files)
    if total_files == 0:
        console.print("[red]Нет файлов для перевода. Проверьте, что скрипт лежит в папке с игрой![/red]")
        return

    console.print("\n[bold]КАКИМ ДВИЖКОМ переводим?[/bold]")
    console.print("1. Google Переводчик (Быстро, но машинный текст)")
    console.print("2. Локальная Нейросеть (Высокое качество, литературный лор)")
    engine_choice = Prompt.ask("Введите номер", choices=["1", "2"], default="2")
    engine = "google" if engine_choice == "1" else "ai"

    console.print("\n[bold]РЕЖИМ ПЕРЕЗАПИСИ:[/bold]")
    console.print("1. Умный пропуск (Пропускать готовые переводы >=90%)")
    console.print("2. ПРИНУДИТЕЛЬНАЯ ПЕРЕЗАПИСЬ (Стереть старое и перевести заново)")
    force_choice = Prompt.ask("Введите номер", choices=["1", "2"], default="1")
    force_overwrite = (force_choice == "2")

    ai_process = None
    if engine == "ai":
        model_name = setup_ai()
        if not model_name: return
        ai_process = start_kobold(model_name)
        if not ai_process: return

    try:
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("[yellow]({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            overall_task = progress.add_task("[bold green]Обработка файлов...", total=total_files)
            string_task = progress.add_task("[cyan]Подготовка...", total=100, visible=False)
            
            for filename in jar_files:
                process_jar(filename, progress, overall_task, string_task, modes, engine, force_overwrite)
                progress.update(overall_task, advance=1)
                
            for filename in snbt_files:
                process_snbt(filename, progress, overall_task, string_task, engine, force_overwrite)
                progress.update(overall_task, advance=1)
                
        console.print(Panel("[bold green]Глобальный перевод успешно завершен![/bold green]"))
    finally:
        if ai_process:
            console.print("[dim]Остановка сервера ИИ...[/dim]")
            ai_process.terminate()

if __name__ == '__main__':
    main()