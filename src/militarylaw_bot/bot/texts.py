"""All user-facing Ukrainian copy, kept separate from conversation logic."""

from __future__ import annotations

WELCOME = (
    "👋 Вітаємо у Vijskove Pravo Bot!\n\n"
    "Це комплексний помічник для військовослужбовців, контрактників та їхніх сімей, "
    "який допоможе вам розібратися у найскладніших питаннях українського військового права:\n\n"
    "📋 <b>Відстрочка після звільнення по закінченню контракту</b> — розрахуйте точний строк відстрочки від призову після закінчення контракту. "
    "Враховуються всі типи контрактів, умови їх укладення та специфіка військового законодавства.\n\n"
    # "✅ <b>Придатність</b> — дізнайтесь, чи маєте право на звільнення за медичними показниками. "
    # "База включає всі категорії та діагнози із військово-медичної класифікації.\n\n"
    "🔄 <b>СЗЧ</b> — отримайте консультацію щодо повернення з добровільної відсутності без дозволу. "
    "Ми розповімо, які існують способи повернення для кожної військової формування.\n\n"
    "↔️ <b>Переведення</b> — розберіться, як оформити переведення до іншої військової частини. "
    "Ми поясним процедури для різних видів переведення та розповімо про необхідні документи.\n\n"
    "Над ботом працювали:\n"
    " • ⚖️ адвокати Дар'я Тарасенко та Назар Олексюк (правова частина)\n"
    " • 💻 Юлія Тарасенко (розробка)\n\n"
    "💛💙 Виберіть, з якої теми вам потрібна допомога:"
)

ASK_GATE_2022 = (
    "Ваш контракт (зі спливом якого ви звільнились чи плануєте звільнятись) "
    "укладений ДО 24.02.2022 р.?"
)

ASK_CONTRACT_STATUS = (
    "Ваш контракт укладений на певний строк, який ще не сплив?"
)

ASK_CONTRACT_EXTENSION = (
    "Чи було автоматичне продовження до закінчення особливого періоду?"
)

SPECIAL_PERIOD_CONTRACT = (
    "Звільнення зі служби у зв'язку із закінченням строку цього контракту неможливе, доки не закінчиться особливий період.\n\n"
    "Пропонуємо розглянути варіант укладення нового контракту. Ви можете обрати контракт "
    "і перевірити, яка може бути відстрочка, якщо ви укладете новий контракт."
)

NO_2022_CONTRACT = (
    "Звільнення зі служби у зв'язку із закінченням строку цього контракту неможливе.\n\n"
    "Пропонуємо розглянути варіант укладення нового контракту. Ви можете обрати контракт "
    "і перевірити, яка може бути відстрочка, якщо ви укладете новий контракт."
)

PLANNING_CONTRACT_DISCLAIMER = (
    "Неможливо напевно розрахувати строк, оскільки невідомо, наприклад, тривалість участі "
    "в бойових діях. Однак, ви можете обрати контракт, який вас цікавить, "
    "і орієнтовано розрахувати строк."
)

ASK_CONTRACT_TYPE = (
    "Який контракт укладений?"
)
ASK_CONTRACT_TERM = "На який строк укладено контракт?"
ASK_AGE_AT_SIGNING = "Який вік був при укладенні контракту?"
ASK_DISCHARGED_BEFORE_768 = "Чи звільнились Ви до 16.06.2026 р.?"

TWELVE_MONTHS_AFTER_DISCHARGE = (
    "Ви маєте право не бути призваним на військову службу протягом 12 міс. після звільнення"
)
NO_DEFERRAL = "Права на відстрочку в цій ситуації на сьогодні законодавство не передбачає."

COMBAT_UNITS_PROMPT = (
    "Чи були у вас безперервні періоди участі у бойових діях тривалістю 30 днів і більше?\n\n"
    "Вкажіть кількість таких періодів:\n"
    " • 0 — якщо жоден безперервний період не становив 30 днів і більше\n"
    " • 1, 2, 3… — якщо такі періоди були (кожен із них — не менше 30 безперервних днів)\n"
)

SERVICE_SINCE_2022_PROMPT = (
    "Скільки повних років військової служби Ви маєте ПІСЛЯ 24.02.2022 р. "
    "до моменту укладення контракту?\n\n"
    "Вкажіть кількість повних років:\n"
    " • 0 — якщо після 24.02.2022 не минув ще жоден повний рік служби\n"
    " • 1, 2, 3… — якщо повні роки є"
)

SERVICE_BEFORE_2022_PROMPT = (
    "Скільки повних років безперервної військової служби Ви мали ДО 24.02.2022 р.?\n\n"
    "Вкажіть кількість повних років:\n"
    " • 0 — якщо до 24.02.2022 не минув жоден повний рік служби\n"
    " • 1, 2, 3… — якщо повні роки є"
)

RETRY_SUFFIX = "Спробуйте ще раз.\n\n"

CLOSING_NOTE = (
    "\n\n💛💙 Якщо цей бот був для вас корисним, будемо вдячні за зворотній зв'язок "
    'у вигляді донату на наш <a href="https://send.monobank.ua/jar/3FXxnbsaGr">'
    "збір на підтримку Сил Оборони</a>\n\n"
    "📞 Якщо у вас залишились питання, запрошуємо отримати консультацію адвоката "
    "Дар'ї Тарасенко та її команди. Для військовослужбовців консультації безкоштовні. "
    "Запис на телефонну консультацію за номером 050-215-05-51 (viber, telegram, whatsapp). "
    'Більше інформації <a href="https://www.facebook.com/share/p/1B17WBeGYJ/">про індивідуальні консультації</a>'
)


RESULT_HEADER = (
    "Бот @VijskovePravoBot порахував, на який строк відстрочки від призову "
    "по закінченню контракту Ви можете розраховувати 🤖\n\n"
)


def with_closing_note(message: str) -> str:
    return f"{RESULT_HEADER}{message}{CLOSING_NOTE}"

# ===== SZCH FLOW TEXTS =====

SZCH_FORMATION_QUESTION = "Вкажіть, у якому військовому формуванні Ви проходите службу:"

SZCH_WANT_RETURN = "Ви хочете добровільно повернутися на військову службу?"

SZCH_FIRST_TIME_AWOL = "Чи це перше СЗЧ?"

SZCH_AWOL_DATE = "Коли почалося СЗЧ?"

SZCH_RETURN_TYPE = "Оберіть варіант повернення:"

SZCH_ZSU_SIMPLIFIED_SUBMISSION = (
    "Як Ви плануєте подати рапорт на добровільне повернення?"
)

SZCH_DSST_SIMPLIFIED_SUBMISSION = (
    "Як Ви плануєте подати рапорт на добровільне повернення?"
)

SZCH_RESULT_HEADER = (
    "Бот @VijskovePravoBot проаналізував Вашу ситуацію щодо добровільного повернення з СЗЧ 🤖\n\n"
)

SZCH_NOT_APPLICABLE_RESULT = (
    "Цей блок зараз налаштований лише для тих, хто має намір добровільно повернутися на військову службу.\n\n"
    "Якщо Ваше питання інше, краще оберіть інший розділ порадника або опишіть ситуацію окремо."
)

SZCH_FIRST_TIME_REQUIRED = (
    "Якщо СЗЧ вчинено не вперше, у цьому алгоритмі повернення з СЗЧ не застосовується.\n\n"
    "Висновок: підстав вважати, що повернення за цим маршрутом можливе, немає."
)

SZCH_GENERAL_ARRIVAL = (
    "Куди Ви плануєте прибути для повернення?"
)

SZCH_COMMANDER_CONSENT = (
    "Чи є у Вас письмова згода командира або начальника військової частини на продовження служби?"
)

SZCH_NEED_DATE = (
    "Без розуміння, чи СЗЧ почалося до 12.06.2026 включно, чи з 13.06.2026, правильно визначити маршрут повернення не вийде.\n\n"
    "Що далі: спершу уточніть дату початку СЗЧ, бо від цього залежить, чи доступний спрощений порядок."
)

SZCH_DPSU_SIMPLIFIED_UNAVAILABLE = (
    "Спрощений порядок за постановою КМУ від 12 червня 2026 року № 767 у цьому вигляді поширюється на ЗСУ, ДССТ і НГУ.\n\n"
    "Для ДПСУ в цій гілці орієнтуйтесь на загальний порядок повернення."
)

SZCH_ERDR_YES = (
    "Якщо відомості до ЄРДР вже внесені, це не скасовує необхідності правильно оформити добровільне повернення. "
    "Питання кримінальної відповідальності далі вирішується в порядку, встановленому законом."
)

SZCH_ERDR_NO = (
    "Якщо про ЄРДР Вам не відомо, все одно варто діяти так, ніби факт СЗЧ уже перевірятиметься офіційно, "
    "і одразу фіксувати добровільне повернення."
)

SZCH_ERDR_UNKNOWN = (
    "Якщо Ви не знаєте, чи є відомості в ЄРДР, це не причина відкладати повернення: дійте за обраним маршрутом "
    "і фіксуйте факт добровільного прибуття."
)

SZCH_COMMANDER_CONSENT_YES = (
    "Якщо письмова згода командира вже є, це ключова умова для подальшого руху через прокурора або суд."
)

SZCH_COMMANDER_CONSENT_NO = (
    "Якщо письмової згоди командира немає, саме це зараз є головною перешкодою для завершення повернення за цим маршрутом."
)

SZCH_COMMANDER_CONSENT_UNKNOWN = (
    "Якщо Ви не знаєте, чи є письмова згода командира, це треба з'ясувати окремо, бо без неї цей механізм не складається."
)

SZCH_ERDR_QUESTION = "Чи відомо Вам, що щодо Вас внесено відомості до ЄРДР (порушена кримінальна справа за СЗЧ)?"


def with_szch_closing_note(message: str) -> str:
    """Add closing note to SZCH result message."""
    return f"{SZCH_RESULT_HEADER}{message}{CLOSING_NOTE}"


def format_bullet_list(title: str, items: list[str]) -> str:
    """Format items as a bulleted list."""
    if not items:
        return ""
    return f"{title}:\n" + "\n".join(f"- {item}" for item in items)


def build_szch_erdr_line(erdr_answer: str) -> str:
    """Build ERDR explanation based on answer (formal Вы form)."""
    if erdr_answer == "Так":
        return "Якщо відомості до ЄРДР вже внесені, це не скасовує необхідності правильно оформити добровільне повернення. Питання кримінальної відповідальності далі вирішується в порядку, встановленому законом."
    elif erdr_answer == "Ні":
        return "Якщо про ЄРДР Вам не відомо, все одно варто діяти так, ніби факт СЗЧ уже перевірятиметься офіційно, і одразу фіксувати добровільне повернення."
    else:
        return "Якщо Ви не знаєте, чи є відомості в ЄРДР, це не причина відкладати повернення: дійте за обраним маршрутом і фіксуйте факт добровільного прибуття."


def build_szch_simplified_result(answers: dict) -> str:
    """Build full simplified return result with all parts (formal Вы form)."""
    formation = answers.get("formation", "")
    submission_method = answers.get("submission_method", "")
    erdr = answers.get("erdr", "")

    is_ngu = formation == "НГУ"

    core_report_items = [
        "обране умовне найменування військової частини, куди хочете повернутися",
        "ПІБ",
        "РНОКПП або серія і номер паспорта",
        "військове звання",
        "умовне найменування частини, яку залишили",
        "дата СЗЧ",
        "посада на момент СЗЧ",
        "контактні дані",
        "дата і підпис",
    ]

    if is_ngu:
        docs = [
            "рекомендаційний лист до обраної військової частини НГУ",
            "копія військового квитка, службового посвідчення або іншого документа, що підтверджує проходження служби",
            "за наявності інші документи, які допоможуть ідентифікувати службу та опрацювати рапорт",
        ]
    else:
        docs = ["за можливості копія військово-облікового документа"]

    if formation == "ЗСУ":
        if submission_method == "Через додаток Армія+":
            route_line = "Подайте рапорт через додаток Армія+ до обраної військової частини ЗСУ."
        elif submission_method == "Через центр рекрутингу":
            route_line = "Подайте рапорт через центр рекрутингу ЗСУ до обраної військової частини."
        else:
            route_line = "Подайте рапорт безпосередньо до обраної військової частини ЗСУ."
    elif formation == "ДССТ":
        if submission_method == "Через додаток Армія+":
            route_line = "Подайте рапорт через додаток Армія+ до обраної військової частини ДССТ."
        else:
            route_line = "Подайте рапорт безпосередньо до обраної військової частини ДССТ."
    else:  # НГУ
        route_line = "Подайте рапорт через додаток Армія+ до обраної військової частини НГУ."

    if is_ngu:
        timing_line = "Після повідомлення про підписання наказу у НГУ потрібно прибути до обраної військової частини протягом 48 годин."
    elif submission_method == "Через центр рекрутингу":
        timing_line = "Якщо рапорт подано через центр рекрутингу ЗСУ і його задовольнили, Вам видається припис для прибуття протягом 5 календарних днів."
    else:
        timing_line = "Якщо рапорт подано через додаток Армія+ і його задовольнили, актуальні відомості в додатку відображаються протягом 120 годин, і в цей проміжок треба прибути до обраної частини."

    what_next_line = "Що далі: після задоволення рапорту прибудьте саме до тієї військової частини, яку Ви обрали для повернення, і збережіть підтвердження подання рапорту та повідомлення про його задоволення."
    consultation_line = "Ситуація потребує індивідуальної оцінки. Первинна консультація безкоштовна."

    parts = [
        f"Для {formation} у Вашій ситуації можна скористатися спрощеним порядком добровільного повернення.",
        route_line,
        format_bullet_list("Що обов'язково вказати в рапорті", core_report_items),
        format_bullet_list(
            "Що треба долучити зі свого боку" if is_ngu else "Що варто мати зі свого боку",
            docs,
        ),
        timing_line,
        build_szch_erdr_line(erdr),
        what_next_line,
        consultation_line,
    ]

    core_text = "\n\n".join(filter(None, parts))
    return with_szch_closing_note(core_text)


def build_szch_general_result(answers: dict) -> str:
    """Build full general return result with all parts (formal Вы form)."""
    formation = answers.get("formation", "")
    arrival_location = answers.get("arrival_location", "")
    commander_consent = answers.get("commander_consent", "")
    erdr = answers.get("erdr", "")

    if arrival_location == "До своєї військової частини":
        arrival_line = "Прибувайте безпосередньо до своєї військової частини і письмово фіксуйте намір добровільно повернутися до виконання обов'язків служби."
    elif arrival_location == "До ВСП":
        arrival_line = "Прибувайте до ВСП і одразу заявляйте, що хочете добровільно повернутися на службу та просите направити Вас до військової частини."
    elif arrival_location == "До ДБР":
        arrival_line = "Прибувайте до ДБР і подавайте письмову заяву або клопотання про добровільне повернення на військову службу."
    elif arrival_location == "До ТЦК та СП":
        arrival_line = "Прибувайте до ТЦК та СП і письмово заявляйте про добровільне повернення на службу та необхідність належно оформити Ваше прибуття."
    else:
        arrival_line = "Прибувайте до іншої військової частини або органу військового управління і письмово фіксуйте, що Ви добровільно повернулися та просите забезпечити належне оформлення повернення."

    chain_items = [
        "добровільно прибути і письмово зафіксувати повернення",
        "у межах кримінального провадження подати клопотання про намір повернутися до військової служби",
        "отримати письмову згоду командира або начальника військової частини на продовження служби",
        "далі питання йде через прокурора або суд",
        "після набрання ухвалою законної сили бути поновленим на службі і прибути до частини не пізніше 72 годин",
    ]

    with_you_items = [
        "паспорт або інший документ, що посвідчує особу",
        "військовий квиток, службове посвідчення або інший військово-обліковий документ, якщо він у Вас є",
        "номер частини, яку Ви залишили, військове звання, посаду та дату СЗЧ",
        "телефон для зв'язку і можливість сфотографувати або зберегти підтвердження прибуття",
    ]

    def build_commander_consent_line(value: str) -> str:
        """Build commander consent line for general order."""
        if value == "Так":
            return "Якщо письмова згода командира вже є, це ключова умова для подальшого руху через прокурора або суд."
        elif value == "Ні":
            return "Якщо письмової згоди командира немає, саме це зараз є головною перешкодою для завершення повернення за цим маршрутом."
        else:
            return "Якщо Ви не знаєте, чи є письмова згода командира, це треба з'ясувати окремо, бо без неї цей механізм не складається."

    parts = [
        f"Для {formation} у цій ситуації орієнтуйтесь на загальний порядок повернення.",
        arrival_line,
        format_bullet_list("Ланцюжок загального порядку", chain_items),
        format_bullet_list("Що варто мати з собою", with_you_items),
        "Що важливо сказати письмово: що Ви добровільно прибули для поновлення проходження військової служби і просите належно зафіксувати Ваше повернення.",
        "Що має відбуватися далі по суті: після фіксації добровільного повернення у межах кримінального провадження подається клопотання про намір повернутися до військової служби.",
        build_commander_consent_line(commander_consent),
        "Ключова умова в цій гілці: потрібна письмова згода командира або начальника військової частини на те, щоб Ви продовжили військову службу.",
        "Після цього питання кримінальної відповідальності вирішується в установленому законом порядку: прокурор або суд враховує клопотання про повернення і письмову згоду командира.",
        "Якщо провадження закривається у зв'язку зі звільненням від кримінальної відповідальності, після набрання ухвалою законної сили особу мають невідкладно поновити на службі, а прибути до відповідної військової частини або місця служби треба не пізніше 72 годин.",
        build_szch_erdr_line(erdr),
        "Що далі: збережіть фото або копію рапорту, заяви, пояснення, відмітки про прийняття чи будь-якого іншого підтвердження того, що Ви справді прибули і заявили про повернення.",
        "Що контролювати: щоб у матеріалах було видно добровільність повернення, факт Вашого прибуття, клопотання про продовження служби і письмову згоду командира.",
        "Ситуація потребує індивідуальної оцінки. Первинна консультація безкоштовна.",
    ]

    core_text = "\n\n".join(filter(None, parts))
    return f"{SZCH_RESULT_HEADER}{core_text}{CLOSING_NOTE}"


# ===== TRANSFER (ПЕРЕВЕДЕННЯ) FLOW TEXTS =====

TRANSFER_RESULT_HEADER = (
    "Бот @VijskovePravoBot проаналізував Вашу ситуацію щодо переведення до іншої військової частини 🤖\n\n"
)


def with_transfer_closing_note(message: str) -> str:
    """Add closing note to transfer result message."""
    return f"{TRANSFER_RESULT_HEADER}{message}{CLOSING_NOTE}"


TRANSFER_FORMATION_QUESTION = "Вкажіть, у якому військовому формуванні Ви проходите службу:"

TRANSFER_SERVICE_TYPE = "Який вид Вашої служби?"

TRANSFER_INITIATIVE = "Переведення відбувається за Вашою ініціативою чи за рішенням командування?"

TRANSFER_GRADUATE_YEAR = "Чи Ви є випускником ВВНЗ / навчального підрозділу і чи минув 1 рік після випуску?"

TRANSFER_ZSU_GROUND = "Яка основна підстава переведення у Вашій ситуації?"

TRANSFER_DPSU_GROUND = "Яка основна підстава переведення у Вашій ситуації?"

TRANSFER_POSITION_LEVEL = "Ви прагнете рівнозначного переведення чи переведення на нижчу / вищу посаду?"

TRANSFER_UNIT_TYPE = "У якій частині Ви проходите службу?"

TRANSFER_UNIT_TYPE_UNKNOWN = (
    "1. До бойових частин належать військові частини бойового складу військ усіх родів (видів) військ (сил) Збройних Сил.\n\n"
    "2. До тилових частин належать військові частини тилового та оперативного забезпечення, вищі військові навчальні заклади, навчальні (навчально-тренувальні) центри (частини), територіальні центри комплектування та соціальної підтримки, військові частини резерву, а також інші військові частини Збройних Сил, які не належать до військових частин бойового складу військ усіх родів (видів) військ (сил) Збройних Сил.\n\n"
    "Після цього треба зробити крок назад та обрати варіант, який відповідає Вашій ситуації."
)

TRANSFER_CURRENT_UNIT_DURATION = "Який строк служби у Вашій поточній частині?"

TRANSFER_PREVIOUS_TRANSFER_GAP = "Чи минув 1 рік з дня Вашого попереднього переведення за власною ініціативою?"

TRANSFER_REAR_DESTINATION = "Куди Ви прагнете переведення?"

TRANSFER_COMBAT_GOAL = "Яка мета переведення?"

TRANSFER_COMMAND_APPROVAL = "Чи є у Вас погодження або відповідний дозвіл від командування на таке переміщення?"

TRANSFER_RECOMMENDATION_LETTER = "Чи є у Вас на руках рекомендаційний лист із частини, куди Ви хочете перевестися?"

TRANSFER_MEDICAL_CONCLUSION = "Чи є у Вас належний медичний висновок / висновок ВЛК для цієї підстави?"

TRANSFER_FAMILY_CIRCUMSTANCE = "Яка сімейна обставина?"

TRANSFER_SUPPORTING_DOCUMENTS = "Чи є у Вас підтвердні документи для цієї сімейної обставини?"

TRANSFER_OFFICER_STATUS = "Чи належите Ви до осіб офіцерського складу?"

TRANSFER_COMMAND_HEALTH_OBSTACLE = "Чи є медичні перешкоди для подальшого проходження служби в поточному форматі?"

TRANSFER_COMMAND_FAMILY_CARE_NEED = "Чи є потреба в догляді за близькими членами сім'ї, яка ускладнює таке переміщення?"


def build_transfer_graduate_restriction_result(answers: dict) -> str:
    """Build result for first-year graduate with non-exceptional transfer ground."""
    formation = answers.get("formation", "")
    ground = answers.get("zsu_ground", "") or answers.get("dpsu_ground", "")

    parts = [
        "Якщо після випуску з ВВНЗ / навчального підрозділу ще не минув 1 рік, звичайне переведення за власною ініціативою сильно обмежене.",
        "Зазвичай тут потрібна окрема виняткова підстава: стан здоров'я, сімейні обставини або родинна підлеглість.",
        f"У Вас обрана підстава: {ground}. Для неї ризик відмови високий.",
        "Ситуація потребує індивідуальної оцінки. Первинна консультація безкоштовна.",
    ]

    core_text = "\n\n".join(filter(None, parts))
    return with_transfer_closing_note(core_text)


def build_transfer_command_decision_result(answers: dict) -> str:
    """Build transfer result for command-initiated transfer (За рішенням командування)."""
    command_health_obstacle = answers.get("command_health_obstacle", "")
    command_family_care_need = answers.get("command_family_care_need", "")

    parts = []
    parts.append("Переведення за рішенням командування треба відділяти від переведення за власною ініціативою.")

    # Check if there are any grounds for exception
    has_health_obstacle = command_health_obstacle == "Так"
    has_family_care = command_family_care_need == "Так"

    if has_health_obstacle or has_family_care:
        exceptions = []
        if has_health_obstacle:
            exceptions.append("Є медичні перешкоди для подальшого проходження служби в поточному форматі самим військовослужбовцем")
        if has_family_care:
            exceptions.append("Є окрема потреба у догляді за близькими членами сім'ї")

        parts.append(f"У твоїй ситуації є важливі обмеження: {'. '.join(exceptions)}.")
        parts.append("Що далі: зберіть підтвердні медичні або сімейні документи і будуй позицію саме на цих винятках.")
    else:
        parts.append("За твоїми відповідями явних винятків поки не видно.")
        parts.append("Що далі: перевір наказ і підставу переміщення, чи є підстави заперечувати.")

    core_text = "\n\n".join(filter(None, parts))
    return with_transfer_closing_note(core_text)


def build_transfer_result(answers: dict) -> str:
    """Build transfer result based on answers."""
    ground = answers.get("zsu_ground", "") or answers.get("dpsu_ground", "")
    position_level = answers.get("position_level", "")
    medical_conclusion = answers.get("medical_conclusion", "")
    recommendation_letter = answers.get("recommendation_letter", "")
    supporting_documents = answers.get("supporting_documents", "")

    parts = []

    # Ground description
    if ground in ["За станом здоров'я військовослужбовця", "За станом здоров'я члена сім'ї", "За станом здоров'я"]:
        parts.append(f"{ground} — це окрема підстава.")
        if position_level:
            parts.append(f"Тип посади: {position_level}.")

        # Medical conclusion
        if medical_conclusion == "Так":
            parts.append("✅ Медичний висновок є — це добра основа для рапорту.")
        else:
            parts.append("⚠️ Без медичного висновку ця підстава буде слабкою.")

        # What to prepare for health-based transfer
        parts.append("Що підготувати: рапорт, медичний висновок / ВЛК, медичні документи.")
        if ground == "За станом здоров'я члена сім'ї":
            parts.append("Додатково варто підготувати документи, що підтверджують родинний зв'язок і стан здоров'я члена сім'ї.")
            
        # Recommendation letter
        if recommendation_letter == "Так":
            parts.append("✅ Рекомендаційний лист уже є.")
        elif recommendation_letter == "Ні":
            parts.append("⚠️ Якщо Ви вже визначили нову частину чи посаду, бажано також мати рекомендаційний лист.")

        # Duration note for health-based transfers
        parts.append("Для такої підстави строки 6 місяців і 1 року не є головними.")

    elif ground == "За сімейними обставинами":
        parts.append("Переведення за сімейними обставинами — це окрема підстава.")

        family_circumstance = answers.get("family_circumstance", "")
        if family_circumstance:
            parts.append(f"Заявлена сімейна обставина: {family_circumstance}.")

        if position_level:
            parts.append(f"Тип посади: {position_level}.")

        if supporting_documents == "Так":
            parts.append("✅ Підтвердні документи є.")
        else:
            parts.append("⚠️ Без підтвердних документів ризик відмови високий.")

        parts.append("Що підготувати: рапорт, документи про родинний зв'язок, медичні або інші підтвердні документи.")

        if recommendation_letter == "Так":
            parts.append("✅ Рекомендаційний лист уже є.")
        elif recommendation_letter == "Ні":
            parts.append("⚠️ Якщо Ви вже визначили нову частину чи посаду, бажано також мати рекомендаційний лист.")
        

        parts.append("Що далі: подавай рапорт саме за сімейними обставинами.")

    elif ground == "Через родинну підлеглість / конфлікт інтересів":
        parts.append("Родинна підлеглість або конфлікт інтересів — окрема підстава для переведення.")

        if position_level:
            parts.append(f"Тип посади: {position_level}.")

        parts.append("Що підготувати: рапорт, документи про родинний зв'язок і документи, які підтверджують підлеглість / залежність.")

        if recommendation_letter == "Так":
            parts.append("✅ Рекомендаційний лист уже є.")
        else:
            parts.append("⚠️ Якщо вже визначили нову частину чи посаду, бажано також мати рекомендаційний лист.")

        parts.append("Цю підставу треба підтвердити документами максимально чітко.")

    elif ground == "Звичайне переведення за власною ініціативою" or ground == "Звичайне переведення за особистим проханням":
        # Regular transfer with unit/duration info
        unit_type = answers.get("unit_type", "")
        destination = answers.get("destination", "")
        command_approval = answers.get("command_approval", "")

        # Build scenario description based on unit type and destination
        if unit_type == "Бойова":
            scenario = "переведення з бойової частини"
            if destination == "До іншої бойової частини":
                scenario += " до іншої бойової"
            elif destination == "За висновком ВЛК до частини забезпечення":
                scenario += " до частини забезпечення за висновком ВЛК"
            elif destination == "До тилової частини без висновку ВЛК":
                scenario += " до тилової без висновку ВЛК"
        elif unit_type == "Тилова":
            scenario = "переведення з тилової частини"
            if destination == "До бойової частини":
                scenario += " до бойової"
            elif destination == "До іншої тилової частини":
                scenario += " до іншої тилової"
        
        parts.append(f"Базовий сценарій: {scenario}.")

        if position_level:
            parts.append(f"Тип посади: {position_level}.")

        parts.append("Що підготувати: рапорт, копію військово-облікового документа та, за можливості, рекомендаційний лист із частини, куди хочеш перевестися.")

        if recommendation_letter == "Так":
            parts.append("✅ Рекомендаційний лист у тебе уже є, його можна одразу додавати до рапорту.")
        else:
            parts.append("⚠️ Рекомендаційного листа ще немає. Якщо вже визначено частину або посаду, куди хочеш перевестися, його варто отримати завчасно.")

        parts.append("Погодження командира поточної частини не завжди є вирішальним, але на практиці його позицію часто перевіряють під час проходження рапорту.")

        # Add command approval info if it was asked (for rear destination without VLK)
        if destination == "До тилової частини без висновку ВЛК":
            if command_approval == "Так":
                parts.append("✅ Погодження або дозвіл від командування у тебе уже є.")
            else:
                parts.append("⚠️ Якщо погодження або дозволу від командування ще немає, його потрібно отримати до подання рапорту.")
                
        # Duration warning if less than 6 months
        current_unit_duration = answers.get("current_unit_duration", "")
        if current_unit_duration == "Менше 6 місяців":
            parts.append("Окремий ризик: якщо у поточній частині ти служиш менше 6 місяців, це може бути підставою для відмови у звичайному переведенні за власною ініціативою.")

        # Warning if previous transfer gap has not passed
        previous_transfer_gap = answers.get("previous_transfer_gap", "")
        if previous_transfer_gap == "Ні, ще не минув":
            parts.append("Окремий ризик: якщо з дня попереднього переведення за власною ініціативою ще не минув 1 рік, це теж може бути підставою для відмови.")

        parts.append("Що далі: підготуй рапорт, перевір строки 6 місяців / 1 рік і подавай пакет документів.")

    elif ground == "Для більш доцільного використання за фахом / досвідом":
        parts.append("Переведення для більш доцільного використання за фахом або досвідом — окрема службова підстава.")

        if position_level:
            parts.append(f"Тип посади: {position_level}.")

        officer_status = answers.get("officer_status", "")
        if officer_status == "Так":
            parts.append("Для офіцера тут зазвичай важливо, чи завершився строк перебування на посаді.")
        else:
            parts.append("Тут потрібне чітке службове обґрунтування.")

        parts.append("Що підготувати: рапорт, службове обґрунтування, за можливості рекомендаційний лист.")

        if recommendation_letter == "Так":
            parts.append("✅ Рекомендаційний лист уже є.")
        else:
            parts.append("⚠️ Якщо вже визначено частину або посаду, за можливості отримайте рекомендаційний лист.")

    else:
        # Default case for other grounds
        parts.append(f"{ground}.")
        if position_level:
            parts.append(f"Тип посади: {position_level}.")

        parts.append("Що підготувати: рапорт, копію військово-облікового документа та, за можливості, рекомендаційний лист.")

        if recommendation_letter == "Так":
            parts.append("✅ Рекомендаційний лист уже є.")
        else:
            parts.append("⚠️ Якщо погодження або дозволу від командування ще немає, його потрібно отримати до подання рапорту.")

    core_text = "\n\n".join(filter(None, parts))
    return with_transfer_closing_note(core_text)


def build_dpsu_result(answers: dict) -> str:
    """Build DPSU transfer result based on ground type."""
    dpsu_ground = answers.get("dpsu_ground", "")

    if dpsu_ground == "Звичайне переведення за особистим проханням":
        return build_dpsu_regular_result(answers)
    elif dpsu_ground == "За станом здоров'я":
        return build_dpsu_health_result(answers)
    elif dpsu_ground == "За сімейними обставинами":
        return build_dpsu_family_result(answers)
    elif dpsu_ground == "На нижчу посаду / менше навантаження":
        return build_dpsu_lower_position_result(answers)
    else:
        # Default
        parts = [f"{dpsu_ground}."]
        position_level = answers.get("position_level", "")
        if position_level:
            parts.append(f"Тип посади: {position_level}.")
        parts.append("Що підготувати: рапорт, копію військово-облікового документа та, за можливості, рекомендаційний лист.")
        recommendation_letter = answers.get("recommendation_letter", "")
        if recommendation_letter == "Так":
            parts.append("✅ Рекомендаційний лист уже є.")
        else:
            parts.append("⚠️ Якщо вже визначено частину чи посаду, за можливості отримайте рекомендаційний лист.")
        core_text = "\n\n".join(parts)
        return with_transfer_closing_note(core_text)


def build_dpsu_regular_result(answers: dict) -> str:
    """Build DPSU regular transfer result."""
    unit_type = answers.get("unit_type", "")
    destination = answers.get("destination", "")
    recommendation_letter = answers.get("recommendation_letter", "")
    command_approval = answers.get("command_approval", "")
    position_level = answers.get("position_level", "")

    # Determine scenario based on unit type and destination
    if unit_type == "Тилова" and destination == "До бойової частини":
        scenario = "переведення з підрозділу забезпечення до підрозділу охорони кордону"
    elif unit_type == "Тилова":
        scenario = "переведення до іншого підрозділу забезпечення"
    elif destination == "До іншої бойової частини":
        scenario = "переведення до іншого підрозділу охорони кордону"
    elif destination == "За висновком ВЛК до частини забезпечення":
        scenario = "переведення за висновком ВЛК до підрозділу забезпечення"
    else:
        scenario = "переведення до підрозділу забезпечення без висновку ВЛК"

    parts = [
        f"Базовий сценарій для ДПСУ: {scenario}.",
        f"Тип посади: {position_level}.",
        "У Положенні ДПСУ логіка йде через переміщення по службі в межах служби, а контракт при цьому не припиняється.",
        "Що підготувати: рапорт, копію військово-облікового документа, за можливості обґрунтування щодо нової посади чи підрозділу.",
    ]

    if recommendation_letter == "Так":
        parts.append("✅ Рекомендаційний лист уже є.")
    else:
        parts.append("⚠️ Рекомендаційний лист не є центральною юридичною підставою, але на практиці може посилити рапорт.")

    if destination == "До тилової частини без висновку ВЛК":
        if command_approval == "Так":
            parts.append("✅ Попереднє погодження командування вже є.")
        else:
            parts.append("⚠️ Без попереднього погодження командування такий сценарій у ДПСУ виглядає слабше.")
    else:
        parts.append("Що далі: подавай рапорт по команді й окремо просіть розглянути саме переміщення по службі до іншого органу ДПСУ.")

    core_text = "\n\n".join(parts)
    return with_transfer_closing_note(core_text)


def build_dpsu_health_result(answers: dict) -> str:
    """Build DPSU health-based transfer result."""
    medical_conclusion = answers.get("medical_conclusion", "")
    recommendation_letter = answers.get("recommendation_letter", "")
    position_level = answers.get("position_level", "")

    parts = [
        "Для ДПСУ стан здоров'я є окремою підставою для переміщення по службі.",
        f"Тип посади: {position_level}.",
    ]

    if medical_conclusion == "Так":
        parts.append("Висновок ВЛК / медичний висновок є.")
    else:
        parts.append("Без висновку ВЛК або належного медичного висновку підстава буде слабкою.")

    parts.append("Що підготувати: рапорт, висновок ВЛК / медичний висновок, медичні документи.")

    if recommendation_letter == "Так":
        parts.append("Рекомендаційний лист уже є.")
    else:
        parts.append("Якщо вже знаєш, куди саме просиш переміщення, додатково можна взяти рекомендаційний лист.")

    if medical_conclusion == "Так":
        parts.append("Що далі: подавай рапорт саме за станом здоров'я.")
    else:
        parts.append("Що далі: спершу оформіть медичний висновок, а вже потім подавай рапорт.")

    core_text = "\n\n".join(parts)
    return with_transfer_closing_note(core_text)


def build_dpsu_family_result(answers: dict) -> str:
    """Build DPSU family circumstances transfer result."""
    supporting_documents = answers.get("supporting_documents", "")
    family_circumstance = answers.get("family_circumstance", "")
    recommendation_letter = answers.get("recommendation_letter", "")
    position_level = answers.get("position_level", "")

    parts = [
        "Для ДПСУ сімейні обставини теж можуть бути окремою підставою для переміщення по службі.",
        f"Сімейна обставина: {family_circumstance}.",
        f"Тип посади: {position_level}.",
    ]

    if supporting_documents == "Так":
        parts.append("Підтвердні документи є.")
    else:
        parts.append("Без підтвердних документів така підстава виглядає слабко.")

    parts.append("Що підготувати: рапорт, документи про родинний зв'язок і підтвердні документи щодо сімейної обставини.")

    if recommendation_letter == "Так":
        parts.append("Рекомендаційний лист уже є.")
    else:
        parts.append("Рекомендаційний лист не замінює підтвердні документи, але може додатково підсилити пакет.")

    if supporting_documents == "Так":
        parts.append("Що далі: подавай рапорт саме за сімейними обставинами.")
    else:
        parts.append("Що далі: спершу зберіть підтвердні документи.")

    core_text = "\n\n".join(parts)
    return with_transfer_closing_note(core_text)


def build_dpsu_lower_position_result(answers: dict) -> str:
    """Build DPSU lower position transfer result."""
    medical_conclusion = answers.get("medical_conclusion", "")
    recommendation_letter = answers.get("recommendation_letter", "")

    parts = [
        "Для ДПСУ окремо варто виділяти сценарій переведення на нижчу посаду або посаду з меншим навантаженням.",
    ]

    if medical_conclusion == "Так":
        parts.append("Медичне підтвердження є, тому підстава виглядає сильніше.")
    else:
        parts.append("Якщо прохання пов'язане зі здоров'ям або меншим навантаженням, без медичного підтвердження ризик вищий.")

    parts.append("Що підготувати: рапорт, обґрунтування, а якщо є медичний мотив - висновок ВЛК / медичний висновок.")

    if recommendation_letter == "Так":
        parts.append("Рекомендаційний лист уже є.")
    else:
        parts.append("Якщо вже є визначена нижча посада або підрозділ, бажано мати й рекомендаційний лист.")

    parts.append("У рапорті краще прямо писати, чому потрібна саме нижча посада або менше навантаження.")

    core_text = "\n\n".join(parts)
    return with_transfer_closing_note(core_text)


def build_dpsu_command_result(answers: dict) -> str:
    """Build DPSU transfer result for service necessity (command-initiated)."""
    command_health_obstacle = answers.get("command_health_obstacle", "")
    command_family_care_need = answers.get("command_family_care_need", "")

    notes = []
    if command_health_obstacle == "Так":
        notes.append("є медичні перешкоди")

    if command_family_care_need == "Так":
        notes.append("є підтверджена потреба в догляді за близькими")

    parts = [
        "Для ДПСУ переведення через службову необхідність або за рішенням командування треба відділяти від особистого прохання.",
    ]

    if notes:
        parts.append(f"У твоїй ситуації додатково важливо, що {' і '.join(notes)}.")
    else:
        parts.append("За відповідями явних пом'якшувальних винятків поки не видно.")

    parts.append("Що підготувати: копію або реквізити наказу, рапорт із запереченнями або поясненнями, медичні чи сімейні документи - якщо вони є.")

    if notes:
        parts.append("Що далі: робіть акцент саме на підтверджених винятках, а не на загальному небажанні переміщення.")
    else:
        parts.append("Що далі: треба дивитися конкретний наказ і підставу службової необхідності.")

    core_text = "\n\n".join(parts)
    return with_transfer_closing_note(core_text)
