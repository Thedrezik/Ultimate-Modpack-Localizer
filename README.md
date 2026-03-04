# 🌍 MineAI Translator (The Ultimate Modpack Localizer)

*Read this in other languages: [Русский](#-mineai-translator-ультимативный-локализатор-сборок)*

**MineAI Translator** is a powerful, smart, and safe tool for automatically translating Minecraft modpacks (mods, quests, and guidebooks) into **11 different languages**.

This program was created to solve the main problem of translating large modpacks: standard translators break the code hidden inside the text (variables like `%s`, markdown links, item tags), causing the game to crash or hide interfaces (as is common with *Applied Energistics 2* or *Patchouli* guidebooks). Our tool uses a **"Titanium Shield"** system that masks the system code before sending it to the translator and safely puts it back in place.

## 🌍 Multi-Language Support
You can translate your modpack from English into any of the following languages:
**Russian, Spanish, German, French, Simplified Chinese, Japanese, Portuguese, Italian, Polish, Korean, and English (UK).**

## 🖥️ User-Friendly Interface
The program features a modern Graphical User Interface (GUI). You don't need to write console commands — simply select your modpack folder, check the desired boxes, choose your target language, and click "Start".

![Main Window][<img width="1431" height="1093" alt="Без имени" src="https://github.com/user-attachments/assets/23c4022a-39d6-4705-aa37-fb1be4ed7d76" />](https://github.com/Thedrezik/MineAI-Modpack-Translator/blob/main/interface.png?raw=true)


---

## 📥 Installation & Usage (Download .exe)

You don't need to install Python or mess with code! You can download the ready-to-use application.

1. Go to the [Releases]([https://github.com/Y-RyuZU/MinecraftModsLocalizer/releases](https://github.com/Thedrezik/MineAI-Modpack-Translator/releases)) tab on the right. <!-- Using the closest matching repo; replace with actual if different -->
2. Download the latest **`MineAI_Translator.exe`** file.
3. Place it in a convenient folder and run it with a double click.

*(For advanced users and developers, instructions on running from source code are at the bottom of the page).*

---

## ✨ Key Features (Why is this the best translator?)

* 🛡️ **Format Protection (Titanium Shield):** Smart regular expressions protect macros `$(#AE)`, tags `<item:minecraft:dirt>`, Markdown links `](url)`, and YAML headers (`---`) from being corrupted by the translator.
* 🛠️ **Auto-Fix Cache:** Machine translators often make mistakes (e.g., adding spaces in variables: `% s` instead of `%s`). On every run, the program scans its cache and **automatically fixes** broken brackets, links, and variables, ensuring perfect formatting.
* 📖 **Custom Dictionary (`dictionary.json`):** The program automatically generates a dictionary file. If the translator stubbornly translates "Raw Copper" incorrectly, just add a rule to the dictionary, and the script will automatically replace it throughout the entire modpack!
* 🧠 **Local AI Support:** Integration with KoboldCPP for translating text while preserving game lore and context.
* ⚡ **High Speed:** When using Google Translate, the program sends requests in batches using multi-threading, translating thousands of lines in minutes.
* 📦 **Safe Packaging:** The program generates a ready-to-use `Resource Pack` without damaging your original `.jar` mod files.

---

## 🎛️ Processing Modes

The program offers three processing modes to adapt to any situation:

1. **Append (Keep old translations)**
   * *How it works:* Finds only **new, untranslated (English) lines** and translates them, leaving your existing translations untouched.
   * *Why use it:* Perfect for updating a modpack! If a mod updates with 50 new items, it translates only those in seconds.
2. **Skip (If 90%+ done)**
   * *How it works:* If a mod is already 90% or more translated, the program skips it entirely.
   * *Why use it:* Saves time on massive modpacks where authors might have left a few technical lines untranslated.
3. **Force (Translate from scratch)**
   * *How it works:* Completely ignores existing translations and re-translates all English text from scratch.
   * *Why use it:* If the current translation is terrible (machine-translated) and you want to rewrite it using a high-quality AI.

---

## ⚙️ Strategy: How to Get the Perfect Result

For the best quality, a **combined approach (Creating two resource packs)** is recommended.

### Step 1. Interface Translation (Fast & Technical)
Mod interfaces (item names, simple descriptions) don't require literary talent.
1. Select **only "Interface (Mods)"**.
2. Engine: **Google** | Mode: **Append**.
3. Name the resource pack: `Mods_UI_Translated`.
*Result: In 2-3 minutes, you will translate 90% of the modpack (tens of thousands of lines).*

### Step 2. Quests and Guidebooks (Lore & High Quality)
Books and quests contain stories and jokes. Google will translate them poorly. This is where AI shines!
1. Select **"Guidebooks" and "Quests"** (uncheck Interface).
2. Engine: **Local AI** | Mode: **Force** (to overwrite bad old translations).
3. Name the resource pack: `Quests_Lore_Translated`.
*Result: The text will read like a well-written book.*

> 💡 **How to use in-game:** Place both archives in your `resourcepacks` folder. Enable both, but **put `Quests_Lore_Translated` ABOVE `Mods_UI_Translated`**.

---

## 🗃️ Isolated Caching System

To avoid translating the same lines twice, the program uses a **dual independent cache**, as the styles of different engines vary:
* `cache.json` — Machine translation cache (Google/DeepL).
* `ai_cache.json` — High-quality AI translation cache.
*If the program closes unexpectedly, you won't lose a single translated line.*

---

## 🤖 Local AI Setup

The program launches the `koboldcpp.exe` engine itself (just place it in the `AI` folder). You only need to download a language model in **`.gguf`** format.

### GPU Offloading
* **0 (CPU Only):** Runs on your processor (Slow).
* **10-50:** Balanced (Partially in VRAM, partially in RAM).
* **99 (Max):** Entire model loaded into Video RAM. Maximum speed.

### Which model to choose? (Recommended format: `Q4_K_M` or `Q5_K_M`)
1. **Lightweight (7B - 8B)** *(Requires: ~6-8 GB VRAM)*
   * 🏆 **Qwen 2.5 (7B):** [Download Qwen2.5-7B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF)
   * 🥈 **Llama 3.1 (8B):** [Download Llama-3.1-8B-Instruct-GGUF](https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF)
2. **Medium (14B)** *(Requires: ~10-12 GB VRAM)*
   * 🏆 **Qwen 2.5 (14B):** [Download Qwen2.5-14B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF)
3. **Heavyweights (32B+)** *(Requires: 16+ GB VRAM)*
   * 🏆 **Qwen 2.5 (32B)** or **Command-R (32B)**.

---

## 🛠️ Running from Source & Compilation

**To Run:**
1. Install Python 3.10+.
2. Run in terminal: `pip install customtkinter requests`
3. Launch the script: `python translator.py`

**To compile your own .exe file:**
If you modified the code and want to build your own console-less `.exe`:
```
pip install pyinstaller
pyinstaller --noconsole --onefile --icon=icon.ico translator.py
```

(The compiled file will appear in the dist folder).

# 🇷🇺 MineAI Translator (Ультимативный Локализатор Сборок)

MineAI Translator — это мощный, умный и безопасный инструмент для автоматического перевода сборок Minecraft (модов, квестов и справочников) на 11 различных языков.

Программа создана для решения главной проблемы перевода больших сборок: обычные переводчики ломают программный код внутри текста (переменные %s, ссылки, теги предметов), из-за чего игра выдает ошибки или скрывает интерфейс (как это часто бывает со справочниками Applied Energistics 2 или Patchouli). Наш инструмент использует систему «Титанового щита», которая маскирует системный код перед отправкой переводчику и безопасно возвращает его на место.

## 🌍 Поддержка множества языков
Вы можете перевести сборку с английского на любой из доступных языков: Русский, Испанский, Немецкий, Французский, Китайский (упрощ.), Японский, Португальский, Итальянский, Польский, Корейский и Английский (UK).

## 🖥️ Удобный и понятный интерфейс
Программа имеет современный графический интерфейс (GUI), с которым справится любой пользователь. Вам не нужно писать команды в консоли — просто выберите папку сборки, нужные галочки, язык перевода и нажмите кнопку.

![Main Window][<img width="1431" height="1093" alt="Без имени" src="https://github.com/user-attachments/assets/6915d5e4-9168-4625-ad30-7c0d81abc8cf" />](https://github.com/Thedrezik/MineAI-Modpack-Translator/blob/main/interface.png?raw=true)

 

---

## 📥 Установка и Запуск (Скачать .exe)

Вам не обязательно устанавливать Python и возиться с кодом! Вы можете скачать уже готовую, собранную программу.

1. Перейдите в раздел [Releases]([https://github.com/Y-RyuZU/MinecraftModsLocalizer/releases](https://github.com/Thedrezik/MineAI-Modpack-Translator/releases)) справа.
2. Скачайте последний файл MineAI_Translator.exe.
3. Поместите его в удобную папку и запустите двойным кликом.

(Для продвинутых пользователей инструкция по запуску из исходного кода находится внизу страницы).

---

## ✨ Главные особенности (Почему этот переводчик лучший?)

* 🛡️ Защита форматирования (Титановый Щит): Умные регулярные выражения защищают макросы $(#AE), теги <item:minecraft:dirt>, ссылки Markdown ](url) и шапки YAML (---) от искажений переводчиком.
* 🛠️ Самолечение кэша (Auto-Fix): Машинные переводчики часто ошибаются (ставят пробелы в переменных: % s вместо %s). При каждом запуске программа сканирует свой кэш и автоматически чинит сломанные скобки, ссылки и переменные, доводя форматирование до идеала.
* 📖 Пользовательский словарь (dictionary.json): Программа автоматически создает файл словаря. Если переводчик упорно переводит "Raw Copper" как "Сыромятная медь", просто добавьте это правило в словарь, и скрипт автоматически заменит всё на "Сырая медь" во всей сборке!
* 🧠 Поддержка Локальных Нейросетей (AI): Интеграция с KoboldCPP для перевода текста с сохранением игрового лора.
* ⚡ Высокая скорость: При использовании Google Translate программа отправляет запросы пачками, переводя тысячи строк за считанные минуты.
* 📦 Безопасная упаковка: Программа генерирует готовый Resource Pack, не повреждая ваши оригинальные .jar файлы модов.

---

## 🎛️ Режимы обработки (Гибкая настройка перевода)

В программе предусмотрены три режима работы:

1. Доперевод (Сохранить старое)
   * Как работает: Ищет только новые, непереведенные (английские) строки и переводит их, не трогая то, что уже переведено.
   * Зачем нужен: Идеально для обновления сборки! Если мод обновился, программа переведет только новинки за пару секунд.
2. Пропуск (От 90% готовности)
   * Как работает: Если файл уже переведен на 90% и более, программа полностью пропустит его.
   * Зачем нужен: Для экономии времени, чтобы не мучить API ради пары забытых разработчиком технических строк.
3. С нуля (Полная перезапись)
   * Как работает: Полностью игнорирует существующий перевод в моде и переводит абсолютно весь английский текст заново.
   * Зачем нужен: Если текущий перевод в моде отвратителен, и вы хотите полностью переписать его через ИИ.

---

## ⚙️ Стратегия: Как получить идеальный результат

Для получения лучшего качества рекомендуется комбинированный подход (Создание двух ресурспаков).

### Шаг 1. Перевод интерфейса (Быстро и технично)
Интерфейсы модов (названия блоков) не требуют литературного таланта.

1. Выберите в программе только "Интерфейс (Моды)".
2. Движок: Google | Режим: Доперевод.
3. Имя ресурспака: Mods_UI_RU. 
*Результат: За 2-3 минуты вы переведете 90% сборки (десятки тысяч строк).*

### Шаг 2. Перевод Квестов и Справочников (Лорно и качественно)
Книги и квесты содержат сюжет. Здесь нужен ИИ!

1. Выберите "Справочники" и "Квесты" (снимите галочку с интерфейса).
2. Движок: Локальная Нейросеть (AI) | Режим: С нуля.
3. Имя ресурспака: Quests_Lore_RU. 
*Результат: Текст будет читаться как качественная книга.*

> 💡 Как использовать в игре: Поместите оба архива в папку resourcepacks. В меню ресурспаков поместите Quests_Lore_RU ВЫШЕ Mods_UI_RU.

---

## 🗃️ Изолированная система Кэширования

Чтобы не переводить одни и те же строки дважды, программа использует двойной независимый кэш, так как стилистика у движков разная:

* cache.json — кэш машинного перевода (Google/DeepL).
* ai_cache.json — качественный кэш переводов от нейросетей.

---

## 🤖 Настройка Искусственного Интеллекта (AI)

Программа сама запускает движок koboldcpp.exe (положите его в папку AI). Вам нужно лишь скачать языковую модель формата .gguf.

### Нагрузка на видеокарту (GPU)

* 0 (Только CPU): Работает на процессоре (медленно).
* 10-50: Баланс (часть в видеокарте, часть в оперативной памяти).
* 99 (Max): Модель полностью в видеопамяти (VRAM). Максимальная скорость.

### Какую модель выбрать? (Рекомендуемый формат Q4_K_M или Q5_K_M)

1. Легкие (7B - 8B) (Требования: ~6-8 ГБ VRAM)
   * 🏆 Qwen 2.5 (7B): [Скачать Qwen2.5-7B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF)
   * 🥈 Llama 3.1 (8B): [Скачать Llama-3.1-8B-Instruct-GGUF](https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF)
2. Средние (14B) (Требования: ~10-12 ГБ VRAM)
   * 🏆 Qwen 2.5 (14B): [Скачать Qwen2.5-14B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF)
3. Тяжеловесы (32B+) (Требования: От 16 ГБ VRAM)
   * 🏆 Qwen 2.5 (32B) или Command-R (32B).

---

## 🛠️ Запуск из исходного кода & Компиляция

Для запуска:

1. Установите Python 3.10+.
2. Запустите команду в терминале: `pip install customtkinter requests`
3. Запустите скрипт: `python translator.py`

Сборка собственного .exe файла: Если вы модифицировали код и хотите собрать свой .exe файл без консоли (окна командной строки):

```
pip install pyinstaller
pyinstaller --noconsole --onefile --icon=icon.ico translator.py
```

(Готовый файл появится в папке dist).




